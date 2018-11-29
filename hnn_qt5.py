#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QToolTip, QPushButton, QFormLayout
from PyQt5.QtWidgets import QMenu, QSizePolicy, QMessageBox, QWidget, QFileDialog, QComboBox, QTabWidget
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QDialog, QGridLayout, QLineEdit, QLabel
from PyQt5.QtWidgets import QCheckBox, QTextEdit, QInputDialog
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal, QObject, pyqtSlot, Qt
from PyQt5 import QtCore
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import multiprocessing
from subprocess import Popen, PIPE, call
import shlex, shutil
from collections import OrderedDict
from time import time, clock, sleep
import pickle, tempfile
from conf import dconf
import conf
import numpy as np
import random
from math import ceil
import spikefn
import params_default
from paramrw import quickreadprm, usingOngoingInputs, countEvokedInputs, usingEvokedInputs
from simdat import SIMCanvas, getinputfiles, readdpltrials
from gutils import scalegeom, scalefont, setscalegeom, lowresdisplay, setscalegeomcenter, getmplDPI, getscreengeom
from ctune import expval, expvals, logval, logvals

prtime = False

def isWindows ():
  # are we on windows? or linux/mac ?
  return sys.platform.startswith('win')

def getPyComm ():
  # get the python command - Windows only has python linux/mac have python3
  if sys.executable is not None: # check python command interpreter path - if available
    pyc = sys.executable
    if pyc.count('python') > 0 and len(pyc) > 0:
      return pyc # full path to python
  if isWindows():
    return 'python'
  return 'python3'

def parseargs ():
  for i in range(len(sys.argv)):
    if sys.argv[i] == '-dataf' and i + 1 < len(sys.argv):
      print('-dataf is ', sys.argv[i+1])
      conf.dconf['dataf'] = dconf['dataf'] = sys.argv[i+1]
      i += 1
    elif sys.argv[i] == '-paramf' and i + 1 < len(sys.argv):
      print('-paramf is ', sys.argv[i+1])
      conf.dconf['paramf'] = dconf['paramf'] = sys.argv[i+1]
      i += 1

parseargs()

simf = dconf['simf']
paramf = dconf['paramf']
debug = dconf['debug']
testLFP = dconf['testlfp'] or dconf['testlaminarlfp']

defncore = multiprocessing.cpu_count() # default number of cores

if dconf['fontsize'] > 0: plt.rcParams['font.size'] = dconf['fontsize']
else: plt.rcParams['font.size'] = dconf['fontsize'] = 10

if debug: print('getPyComm:',getPyComm())

# for signaling
class Communicate (QObject):    
  finishSim = pyqtSignal()

# for signaling - passing text
class TextSignal (QObject):
  tsig = pyqtSignal(str)

# for signaling - updating GUI & param file during optimization
class ParamSignal (QObject):
  psig = pyqtSignal(OrderedDict)

class CanvSignal (QObject):
  csig = pyqtSignal(bool)

def bringwintobot (win):
  #win.show()
  #win.lower()
  win.hide()

def bringwintotop (win):
  # bring a pyqt5 window to the top (parents still stay behind children)
  # based on examples from https://www.programcreek.com/python/example/101663/PyQt5.QtCore.Qt.WindowActive
  #win.show()
  #win.setWindowState(win.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
  #win.raise_()
  win.showNormal()
  win.activateWindow()
  #win.setWindowState((win.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
  #win.activateWindow()
  #win.raise_()
  #win.show() 

# based on https://nikolak.com/pyqt-threading-tutorial/
class RunSimThread (QThread):
  def __init__ (self,c,ntrial,ncore,waitsimwin,opt=False,baseparamwin=None,mainwin=None,onNSG=False):
    QThread.__init__(self)
    self.c = c
    self.killed = False
    self.proc = None
    self.ntrial = ntrial
    self.ncore = ncore
    self.waitsimwin = waitsimwin
    self.opt = opt
    self.baseparamwin = baseparamwin
    self.mainwin = mainwin
    self.onNSG = onNSG

    self.txtComm = TextSignal()
    self.txtComm.tsig.connect(self.waitsimwin.updatetxt)

    self.prmComm = ParamSignal()
    if self.baseparamwin is not None:
      self.prmComm.psig.connect(self.baseparamwin.updatesaveparams)

    self.canvComm = CanvSignal()
    if self.mainwin is not None:
      self.canvComm.csig.connect(self.mainwin.initSimCanvas)

  def updatewaitsimwin (self, txt):
    # print('RunSimThread updatewaitsimwin, txt=',txt)
    self.txtComm.tsig.emit(txt)

  def updatebaseparamwin (self, d):
    self.prmComm.psig.emit(d)

  def updatedrawerr (self):
    self.canvComm.csig.emit(False) # False means do not recalculate error

  def stop (self): self.killed = True

  def __del__ (self):
    self.quit()
    self.wait()

  def run (self):
    if self.opt and self.baseparamwin is not None:
      self.optmodel() # run optimization
    else:
      self.runsim() # run simulation
    self.c.finishSim.emit() # send the finish signal

  def killproc (self):
    if self.proc is None: return
    if debug: print('Thread killing sim. . .')
    try:
      self.proc.kill() # has to be called before proc ends
      self.proc = None
    except:
      print('ERR: could not stop simulation process.')

  # run sim command via mpi, then delete the temp file.
  def runsim (self):
    import simdat
    self.killed = False
    if debug: print("Running simulation using",self.ncore,"cores.")
    if debug: print('self.onNSG:',self.onNSG)
    if self.onNSG:
      cmd = 'python nsgr.py ' + paramf + ' ' + str(self.ntrial) + ' 710.0'
    else:
      cmd = 'mpiexec -np ' + str(self.ncore) + ' nrniv -python -mpi ' + simf + ' ' + paramf + ' ntrial ' + str(self.ntrial)
    maxruntime = 1200 # 20 minutes - will allow terminating sim later
    simdat.dfile = getinputfiles(paramf)
    cmdargs = shlex.split(cmd,posix="win" not in sys.platform) # https://github.com/maebert/jrnl/issues/348
    if debug: print("cmd:",cmd,"cmdargs:",cmdargs)
    if prtime:
      self.proc = Popen(cmdargs,cwd=os.getcwd())
    else: 
      #self.proc = Popen(cmdargs,stdout=PIPE,stderr=PIPE,cwd=os.getcwd()) # may want to read/display stderr too
      self.proc = Popen(cmdargs,stdout=PIPE,cwd=os.getcwd(),universal_newlines=True)
    #cstart = time(); 
    while not self.killed and self.proc.poll() is None: # job is not done
      for stdout_line in iter(self.proc.stdout.readline, ""):
        try: # see https://stackoverflow.com/questions/2104779/qobject-qplaintextedit-multithreading-issues
          self.updatewaitsimwin(stdout_line.strip()) # sends a pyqtsignal to waitsimwin, which updates its textedit
        except:
          if debug: print('RunSimThread updatewaitsimwin exception...')
          pass # catch exception in case anything else goes wrong
        if self.killed:
          self.killproc()
          return
      self.proc.stdout.close()
      sleep(1)
      # cend = time(); rtime = cend - cstart
    if debug: print('sim finished')
    if not self.killed:  
      if debug: print('not self.killed')
      try: # lack of output file may occur if invalid param values lead to an nrniv crash

        simdat.ddat['dpl'] = np.loadtxt(simdat.dfile['dpl'])
        if debug: print('loaded new dpl file:', simdat.dfile['dpl'])#,'time=',time())
        if os.path.isfile(simdat.dfile['spec']):
          simdat.ddat['spec'] = np.load(simdat.dfile['spec'])
        else:
          simdat.ddat['spec'] = None
        simdat.ddat['spk'] = np.loadtxt(simdat.dfile['spk'])
        simdat.ddat['dpltrials'] = readdpltrials(os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0]),self.ntrial)
        if debug: print("Read simulation outputs:",simdat.dfile.values())

        simdat.updatelsimdat(paramf,simdat.ddat['dpl']) # update lsimdat and its current sim index

      except: # no output to read yet
        print('WARN: could not read simulation outputs:',simdat.dfile.values())
    else:
      if debug: print('self.killproc')
      self.killproc()
    print(''); self.updatewaitsimwin('')
  
  def optmodel (self):
    self.updatewaitsimwin('Optimizing model. . .')
    from neuron import h # for praxis
    self.optiter = 0 # optimization iteration
    fpopt = open(os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0],'optinf.txt'),'w')
    fpopt.close()
    self.minopterr = 1e9

    def optrun (vparam):
      # create parameter dictionary of current values to test
      lparam = list(dconf['params'].values())
      dtest = OrderedDict() # parameter values to test      
      for prm,val in zip(lparam,expvals(vparam,lparam)): # set parameters
        if val >= prm.minval and val <= prm.maxval:
          if debug: print('optrun prm:',prm.var,prm.minval,prm.maxval,val)
          dtest[prm.var] = val
        else:
          if debug: print('optrun:', val, 'out of bounds for ' , prm.var, prm.minval, prm.maxval)
          return 1e9 # invalid param value -> large error
      if debug:
        if type(vparam)==list: print('set params:', vparam)
        else: print('set params:', vparam.as_numpy())

      self.updatebaseparamwin(dtest) # put new param values into GUI
      sleep(1)

      self.runsim() # run the simulation as usual and read its output
      import simdat
      simdat.calcerr(simdat.ddat) # make sure error re-calculated (synchronously)
      self.updatedrawerr() # send event to draw updated error (asynchronously)
      self.updatewaitsimwin(os.linesep+'Simulation finished: error='+str(simdat.ddat['errtot'])+os.linesep) # print error
      print(os.linesep+'Simulation finished: error='+str(simdat.ddat['errtot'])+os.linesep)#,'time=',time())

      with open(os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0],'optinf.txt'),'a') as fpopt:
        fpopt.write(str(simdat.ddat['errtot'])+os.linesep) # write error

      # backup the current param file
      outdir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
      prmloc0 = os.path.join(outdir,paramf.split(os.path.sep)[-1])
      prmloc1 = os.path.join(outdir,str(self.optiter)+'.param')
      shutil.copyfile(prmloc0,prmloc1)
      if simdat.ddat['errtot'] < self.minopterr:
        self.minopterr = simdat.ddat['errtot']
        shutil.copyfile(prmloc0,os.path.join(outdir,'best.param')) # convenience, save best here
      self.optiter += 1

      return simdat.ddat['errtot'] # return error to praxis

    tol = 1e-5; nstep = 100; stepsz = 0.5 # 1.0 #stepsz = 0.5
    h.attr_praxis(tol, stepsz, 3)
    h.stop_praxis(nstep) # 
    lparam = list(dconf['params'].values())
    lvar = [p.var for p in lparam]
    if debug: print('lparam=',lparam)
    vparam = h.Vector()
    # read current parameters from GUI
    s = str(self.baseparamwin)
    for l in s.split(os.linesep):
      if l.count(': ') < 1: continue
      k,v = l.split(': ')
      if debug: print('k=',k,'v=',v)
      if k in lvar:
        prm = lparam[lvar.index(k)]
        vparam.append(logval(prm,float(v)))
        if debug: print('optmodel: k',k,'in lparam')
    x = h.fit_praxis(optrun, vparam) #x = optrun(vparam)

# look up resource adjusted for screen resolution
def lookupresource (fn):
  lowres = lowresdisplay() # low resolution display
  if lowres:
    return os.path.join('res',fn+'2.png')
  else:
    return os.path.join('res',fn+'.png')

# DictDialog - dictionary-based dialog with tabs - should make all dialogs
# specifiable via cfg file format - then can customize gui without changing py code
# and can reduce code explosion / overlap between dialogs 
class DictDialog (QDialog):

  def __init__ (self, parent, din):
    super(DictDialog, self).__init__(parent)
    self.ldict = [] # subclasses should override
    self.ltitle = []
    self.dtransvar = {} # for translating model variable name to more human-readable form
    self.stitle = ''
    self.initd()
    self.initUI()
    self.initExtra()
    self.setfromdin(din) # set values from input dictionary
    self.addtips()

  def addtips (self):
    for ktip in dconf.keys():
      if ktip in self.dqline:
        self.dqline[ktip].setToolTip(dconf[ktip])
      elif ktip in self.dqextra:
        self.dqextra[ktip].setToolTip(dconf[ktip])

  def __str__ (self):
    s = ''
    for k,v in self.dqline.items(): s += k + ': ' + v.text().strip() + os.linesep
    return s

  def saveparams (self): self.hide()

  def initd (self): pass # implemented in subclass

  def getval (self,k):
    if k in self.dqline.keys():
      return self.dqline[k].text().strip()

  def lines2val (self,ksearch,val):
    for k in self.dqline.keys():
      if k.count(ksearch) > 0:
        self.dqline[k].setText(str(val))

  def setfromdin (self,din):
    if not din: return
    for k,v in din.items():
      if k in self.dqline:
        self.dqline[k].setText(str(v).strip())

  def transvar (self,k):
    if k in self.dtransvar: return self.dtransvar[k]
    return k

  def addtransvar (self,k,strans):
    self.dtransvar[k] = strans
    self.dtransvar[strans] = k

  def initExtra (self): self.dqextra = OrderedDict() # extra items not written to param file

  def initUI (self):
    self.layout = QVBoxLayout(self)

    # Add stretch to separate the form layout from the button
    self.layout.addStretch(1)

    # Initialize tab screen
    self.ltabs = []
    self.tabs = QTabWidget(); self.layout.addWidget(self.tabs)

    for i in range(len(self.ldict)): self.ltabs.append(QWidget())

    self.tabs.resize(575,200) 

    # create tabs and their layouts
    for tab,s in zip(self.ltabs,self.ltitle):
      self.tabs.addTab(tab,s)
      tab.layout = QFormLayout()
      tab.setLayout(tab.layout)

    self.dqline = OrderedDict() # QLineEdits dict; key is model variable
    for d,tab in zip(self.ldict, self.ltabs):
      for k,v in d.items():
        self.dqline[k] = QLineEdit(self)
        self.dqline[k].setText(str(v))
        tab.layout.addRow(self.transvar(k),self.dqline[k]) # adds label,QLineEdit to the tab

    # Add tabs to widget        
    self.layout.addWidget(self.tabs)
    self.setLayout(self.layout)
    self.setWindowTitle(self.stitle)  
    nw, nh = setscalegeom(self, 150, 150, 825, 300)
    #nx = parent.rect().x()+parent.rect().width()/2-nw/2
    #ny = parent.rect().y()+parent.rect().height()/2-nh/2
    #print(parent.rect(),nx,ny)
    #self.move(nx, ny)
    #self.move(self.parent.
    #self.move(self.parent.widget.rect().x+self.parent.widget.rect().width()/2-nw,
    #          self.parent.widget.rect().y+self.parent.widget.rect().height()/2-nh)

  def TurnOff (self): pass

  def addOffButton (self):
    # Create a horizontal box layout to hold the button
    self.button_box = QHBoxLayout() 
    self.btnoff = QPushButton('Turn Off Inputs',self)
    self.btnoff.resize(self.btnoff.sizeHint())
    self.btnoff.clicked.connect(self.TurnOff)
    self.btnoff.setToolTip('Turn Off Inputs')
    self.button_box.addWidget(self.btnoff)
    self.layout.addLayout(self.button_box)

  def addHideButton (self):
    self.bbhidebox = QHBoxLayout() 
    self.btnhide = QPushButton('Hide Window',self)
    self.btnhide.resize(self.btnhide.sizeHint())
    self.btnhide.clicked.connect(self.hide)
    self.btnhide.setToolTip('Hide Window')
    self.bbhidebox.addWidget(self.btnhide)
    self.layout.addLayout(self.bbhidebox)

# widget to specify ongoing input params (proximal, distal)
class OngoingInputParamDialog (DictDialog):
  def __init__ (self, parent, inty, din=None):
    self.inty = inty
    if self.inty.startswith('Proximal'):
      self.prefix = 'input_prox_A_'
      self.postfix = '_prox'
      self.isprox = True
    else:
      self.prefix = 'input_dist_A_'
      self.postfix = '_dist'
      self.isprox = False
    super(OngoingInputParamDialog, self).__init__(parent,din)
    self.addOffButton()
    self.addImages()
    self.addHideButton()

  # add png cartoons to tabs
  def addImages (self):
    if self.isprox: self.pix = QPixmap(lookupresource('proxfig'))
    else: self.pix = QPixmap(lookupresource('distfig'))
    for tab in self.ltabs:      
      pixlbl = ClickLabel(self)
      pixlbl.setPixmap(self.pix)
      tab.layout.addRow(pixlbl)


  # turn off by setting all weights to 0.0
  def TurnOff (self): self.lines2val('weight',0.0)

  def initd (self):
    self.dtiming = OrderedDict([#('distribution' + self.postfix, 'normal'),
                                ('t0_input' + self.postfix, 1000.),
                                ('t0_input_stdev' + self.postfix, 0.),
                                ('tstop_input' + self.postfix, 250.),
                                ('f_input' + self.postfix, 10.),
                                ('f_stdev' + self.postfix, 20.),
                                ('events_per_cycle' + self.postfix, 2),
                                ('repeats' + self.postfix, 10)])

    self.dL2 = OrderedDict([(self.prefix + 'weight_L2Pyr_ampa', 0.),
                            (self.prefix + 'weight_L2Pyr_nmda', 0.),
                            (self.prefix + 'weight_L2Basket_ampa', 0.),
                            (self.prefix + 'weight_L2Basket_nmda',0.),
                            (self.prefix + 'delay_L2', 0.1),])

    self.dL5 = OrderedDict([(self.prefix + 'weight_L5Pyr_ampa', 0.),
                            (self.prefix + 'weight_L5Pyr_nmda', 0.)])

    if self.isprox:
      self.dL5[self.prefix + 'weight_L5Basket_ampa'] = 0.0
      self.dL5[self.prefix + 'weight_L5Basket_nmda'] = 0.0
    self.dL5[self.prefix + 'delay_L5'] = 0.1

    self.ldict = [self.dtiming, self.dL2, self.dL5]
    self.ltitle = ['Timing', 'Layer 2/3', 'Layer 5']
    self.stitle = 'Set Rhythmic '+self.inty+' Inputs'

    dtmp = {'L2':'L2/3 ','L5':'L5 '}
    for d in [self.dL2, self.dL5]:
      for k in d.keys():
        lk = k.split('_')
        if k.count('weight') > 0:
          self.addtransvar(k, dtmp[lk[-2][0:2]] + lk[-2][2:]+' '+lk[-1].upper()+u' weight (µS)')
        else:
          self.addtransvar(k, 'Delay (ms)')

    #self.addtransvar('distribution'+self.postfix,'Distribution')
    self.addtransvar('t0_input'+self.postfix,'Start time mean (ms)')
    self.addtransvar('t0_input_stdev'+self.postfix,'Start time stdev (ms)')
    self.addtransvar('tstop_input'+self.postfix,'Stop time (ms)')
    self.addtransvar('f_input'+self.postfix,'Burst frequency (Hz)')
    self.addtransvar('f_stdev'+self.postfix,'Burst stdev (ms)')
    self.addtransvar('events_per_cycle'+self.postfix,'Spikes/burst')
    self.addtransvar('repeats'+self.postfix,'Number bursts')

class EvokedOrRhythmicDialog (QDialog):
  def __init__ (self, parent, distal, evwin, rhythwin):
    super(EvokedOrRhythmicDialog, self).__init__(parent)
    if distal: self.prefix = 'Distal'
    else: self.prefix = 'Proximal'
    self.evwin = evwin
    self.rhythwin = rhythwin
    self.initUI()

  def initUI (self):
    self.layout = QVBoxLayout(self)
    # Add stretch to separate the form layout from the button
    self.layout.addStretch(1)

    self.btnrhythmic = QPushButton('Rhythmic ' + self.prefix + ' Inputs',self)
    self.btnrhythmic.resize(self.btnrhythmic.sizeHint())
    self.btnrhythmic.clicked.connect(self.showrhythmicwin)
    self.layout.addWidget(self.btnrhythmic)

    self.btnevoked = QPushButton('Evoked Inputs',self)
    self.btnevoked.resize(self.btnevoked.sizeHint())
    self.btnevoked.clicked.connect(self.showevokedwin)
    self.layout.addWidget(self.btnevoked)

    self.addHideButton()

    setscalegeom(self, 150, 150, 270, 120)
    self.setWindowTitle("Pick Input Type")     

  def showevokedwin (self):
    bringwintotop(self.evwin)
    self.hide()

  def showrhythmicwin (self):
    bringwintotop(self.rhythwin)
    self.hide()

  def addHideButton (self):
    self.bbhidebox = QHBoxLayout() 
    self.btnhide = QPushButton('Hide Window',self)
    self.btnhide.resize(self.btnhide.sizeHint())
    self.btnhide.clicked.connect(self.hide)
    self.btnhide.setToolTip('Hide Window')
    self.bbhidebox.addWidget(self.btnhide)
    self.layout.addLayout(self.bbhidebox)


class SynGainParamDialog (QDialog):
  def __init__ (self, parent, netparamwin):
    super(SynGainParamDialog, self).__init__(parent)
    self.netparamwin = netparamwin
    self.initUI()

  def scalegain (self, k, fctr):
    oldval = float(self.netparamwin.dqline[k].text().strip())
    newval = oldval * fctr
    self.netparamwin.dqline[k].setText(str(newval))
    if debug: print('scaling ',k,' by', fctr, 'from ',oldval,'to ',newval,'=',oldval*fctr)
    return newval

  def isE (self,ty): return ty.count('Pyr') > 0
  def isI (self,ty): return ty.count('Basket') > 0

  def tounity (self):
    for k in self.dqle.keys(): self.dqle[k].setText('1.0')

  def scalegains (self):
    if debug: print('scaling synaptic gains')
    for i,k in enumerate(self.dqle.keys()):
      fctr = float(self.dqle[k].text().strip())
      if fctr < 0.:
        fctr = 0.
        self.dqle[k].setText(str(fctr))
      elif fctr == 1.0:
        continue
      if debug: print(k,fctr)
      for k2 in self.netparamwin.dqline.keys():
        l = k2.split('_')
        ty1,ty2 = l[1],l[2]
        if self.isE(ty1) and self.isE(ty2) and k == 'E -> E':
          self.scalegain(k2,fctr)
        elif self.isE(ty1) and self.isI(ty2) and k == 'E -> I':
          self.scalegain(k2,fctr)
        elif self.isI(ty1) and self.isE(ty2) and k == 'I -> E':
          self.scalegain(k2,fctr)
        elif self.isI(ty1) and self.isI(ty2) and k == 'I -> I':
          self.scalegain(k2,fctr)
    self.tounity() # go back to unity since pressed OK - next call to this dialog will reset new values
    self.hide()

  def initUI (self):
    grid = QGridLayout()
    grid.setSpacing(10)

    self.dqle = OrderedDict()
    for row,k in enumerate(['E -> E', 'E -> I', 'I -> E', 'I -> I']):
      lbl = QLabel(self)
      lbl.setText(k)
      lbl.adjustSize()
      grid.addWidget(lbl,row, 0)
      qle = QLineEdit(self)
      qle.setText('1.0')
      grid.addWidget(qle,row, 1)
      self.dqle[k] = qle

    row += 1
    self.btnok = QPushButton('OK',self)
    self.btnok.resize(self.btnok.sizeHint())
    self.btnok.clicked.connect(self.scalegains)
    grid.addWidget(self.btnok, row, 0, 1, 1)
    self.btncancel = QPushButton('Cancel',self)
    self.btncancel.resize(self.btncancel.sizeHint())
    self.btncancel.clicked.connect(self.hide)
    grid.addWidget(self.btncancel, row, 1, 1, 1); 

    self.setLayout(grid)  
    setscalegeom(self, 150, 150, 270, 180)
    self.setWindowTitle("Synaptic Gains")  

# widget to specify tonic inputs
class TonicInputParamDialog (DictDialog):
  def __init__ (self, parent, din):
    super(TonicInputParamDialog, self).__init__(parent,din)
    self.addOffButton()
    self.addHideButton()

  # turn off by setting all weights to 0.0
  def TurnOff (self): self.lines2val('A',0.0)

  def initd (self):

    self.dL2 = OrderedDict([
      # IClamp params for L2Pyr
      ('Itonic_A_L2Pyr_soma', 0.),
      ('Itonic_t0_L2Pyr_soma', 0.),
      ('Itonic_T_L2Pyr_soma', -1.),
      # IClamp param for L2Basket
      ('Itonic_A_L2Basket', 0.),
      ('Itonic_t0_L2Basket', 0.),
      ('Itonic_T_L2Basket', -1.)])

    self.dL5 = OrderedDict([
      # IClamp params for L5Pyr
      ('Itonic_A_L5Pyr_soma', 0.),
      ('Itonic_t0_L5Pyr_soma', 0.),
      ('Itonic_T_L5Pyr_soma', -1.),
      # IClamp param for L5Basket
      ('Itonic_A_L5Basket', 0.),
      ('Itonic_t0_L5Basket', 0.),
      ('Itonic_T_L5Basket', -1.)])

    dtmp = {'L2':'L2/3 ','L5':'L5 '} # temporary dictionary for string translation
    for d in [self.dL2, self.dL5]:
      for k in d.keys():
        cty = k.split('_')[2] # cell type
        tcty = dtmp[cty[0:2]] + cty[2:] # translated cell type
        if k.count('A') > 0:
          self.addtransvar(k, tcty + ' amplitude (nA)')
        elif k.count('t0') > 0:
          self.addtransvar(k, tcty + ' start time (ms)')
        elif k.count('T') > 0:
          self.addtransvar(k, tcty + ' stop time (ms)')

    self.ldict = [self.dL2, self.dL5]
    self.ltitle = ['Layer 2/3', 'Layer 5']
    self.stitle = 'Set Tonic Inputs'

# widget to specify ongoing poisson inputs
class PoissonInputParamDialog (DictDialog):
  def __init__ (self, parent, din):
    super(PoissonInputParamDialog, self).__init__(parent,din)
    self.addOffButton()
    self.addHideButton()

  # turn off by setting all weights to 0.0
  def TurnOff (self): self.lines2val('weight',0.0)

  def initd (self):

    self.dL2,self.dL5 = OrderedDict(),OrderedDict()
    ld = [self.dL2,self.dL5]

    for i,lyr in enumerate(['L2','L5']):
      d = ld[i]
      for ty in ['Pyr', 'Basket']:
        for sy in ['ampa','nmda']: d[lyr+ty+'_Pois_A_weight'+'_'+sy]=0.
        d[lyr+ty+'_Pois_lamtha']=0.

    self.dtiming = OrderedDict([('t0_pois', 0.),
                                ('T_pois', -1)])

    self.addtransvar('t0_pois','Start time (ms)')
    self.addtransvar('T_pois','Stop time (ms)')

    dtmp = {'L2':'L2/3 ','L5':'L5 '} # temporary dictionary for string translation
    for d in [self.dL2, self.dL5]:
      for k in d.keys():
        ks = k.split('_')
        cty = ks[0] # cell type
        tcty = dtmp[cty[0:2]] + cty[2:] # translated cell type
        if k.count('weight'):
          self.addtransvar(k, tcty+ ' ' + ks[-1].upper() + u' weight (µS)')
        elif k.endswith('lamtha'):
          self.addtransvar(k, tcty+ ' freq (Hz)')

    self.ldict = [self.dL2, self.dL5, self.dtiming]
    self.ltitle = ['Layer 2/3', 'Layer 5', 'Timing']
    self.stitle = 'Set Poisson Inputs'

# evoked input param dialog (allows adding/removing arbitrary number of evoked inputs)
class EvokedInputParamDialog (QDialog):
  def __init__ (self, parent, din):
    super(EvokedInputParamDialog, self).__init__(parent)
    self.nprox = self.ndist = 0 # number of proximal,distal inputs
    self.ld = [] # list of dictionaries for proximal/distal inputs
    self.dqline = OrderedDict()
    self.dtransvar = {} # for translating model variable name to more human-readable form
    self.initUI()
    self.setfromdin(din)

  def addtips (self):
    for ktip in dconf.keys():
      if ktip in self.dqline:
        self.dqline[ktip].setToolTip(dconf[ktip])

  def transvar (self,k):
    if k in self.dtransvar: return self.dtransvar[k]
    return k

  def addtransvar (self,k,strans):
    self.dtransvar[k] = strans
    self.dtransvar[strans] = k

  def setfromdin (self,din):
    if not din: return
    self.removeAllInputs() # turn off any previously set inputs
    nprox, ndist = countEvokedInputs(din)
    for i in range(nprox+ndist):
      if i % 2 == 0:
        if self.nprox < nprox:
          self.addProx()
        elif self.ndist < ndist:
          self.addDist()
      else:
        if self.ndist < ndist:          
          self.addDist()
        elif self.nprox < nprox:
          self.addProx()
    for k,v in din.items():
      if k == 'sync_evinput':
        if float(v)==0.0:
          self.chksync.setChecked(False)
        elif float(v)==1.0:
          self.chksync.setChecked(True)
      elif k == 'inc_evinput':
        self.incedit.setText(str(v).strip())
      elif k in self.dqline:
        self.dqline[k].setText(str(v).strip())
      elif k.count('gbar') > 0 and (k.count('evprox')>0 or k.count('evdist')>0): 
        # for back-compat with old-style specification which didn't have ampa,nmda in evoked gbar
        lks = k.split('_')
        eloc = lks[1]
        enum = lks[2]
        if eloc == 'evprox':
          for ct in ['L2Pyr','L2Basket','L5Pyr','L5Basket']:
            # ORIGINAL MODEL/PARAM: only ampa for prox evoked inputs
            self.dqline['gbar_'+eloc+'_'+enum+'_'+ct+'_ampa'].setText(str(v).strip()) 
        elif eloc == 'evdist':
          for ct in ['L2Pyr','L2Basket','L5Pyr']:
            # ORIGINAL MODEL/PARAM: both ampa and nmda for distal evoked inputs
            self.dqline['gbar_'+eloc+'_'+enum+'_'+ct+'_ampa'].setText(str(v).strip()) 
            self.dqline['gbar_'+eloc+'_'+enum+'_'+ct+'_nmda'].setText(str(v).strip()) 

  def initUI (self):
    self.layout = QVBoxLayout(self)

    # Add stretch to separate the form layout from the button
    self.layout.addStretch(1)

    self.ltabs = []
    self.tabs = QTabWidget(); 
    self.layout.addWidget(self.tabs)
    
    self.button_box = QVBoxLayout() 
    self.btnprox = QPushButton('Add Proximal Input',self)
    self.btnprox.resize(self.btnprox.sizeHint())
    self.btnprox.clicked.connect(self.addProx)
    self.btnprox.setToolTip('Add Proximal Input')
    self.button_box.addWidget(self.btnprox)

    self.btndist = QPushButton('Add Distal Input',self)
    self.btndist.resize(self.btndist.sizeHint())
    self.btndist.clicked.connect(self.addDist)
    self.btndist.setToolTip('Add Distal Input')
    self.button_box.addWidget(self.btndist)

    self.chksync = QCheckBox('Synchronous Inputs',self)
    self.chksync.resize(self.chksync.sizeHint())
    self.chksync.setChecked(True)
    self.button_box.addWidget(self.chksync)

    self.incbox = QHBoxLayout()
    self.inclabel = QLabel(self)
    self.inclabel.setText('Increment start time (ms)')
    self.inclabel.adjustSize()
    self.inclabel.setToolTip('Increment mean evoked input start time(s) by this amount on each trial.')
    self.incedit = QLineEdit(self)
    self.incedit.setText('0.0')
    self.incbox.addWidget(self.inclabel)
    self.incbox.addWidget(self.incedit)

    self.layout.addLayout(self.button_box)
    self.layout.addLayout(self.incbox)

    self.tabs.resize(425,200) 

    # Add tabs to widget        
    self.layout.addWidget(self.tabs)
    self.setLayout(self.layout)

    setscalegeom(self, 150, 150, 475, 300)
    self.setWindowTitle('Evoked Inputs')

    self.addRemoveInputButton()
    self.addHideButton()
    self.addtips()

  def lines2val (self,ksearch,val):
    for k in self.dqline.keys():
      if k.count(ksearch) > 0:
        self.dqline[k].setText(str(val))

  def allOff (self): self.lines2val('gbar',0.0)

  def removeAllInputs (self):
    for i in range(len(self.ltabs)): self.removeCurrentInput()
    self.nprox = self.ndist = 0

  def removeInput (self,idx):
    if idx < 0 or idx > len(self.ltabs): return
    # print('removing input at index', idx)
    self.tabs.removeTab(idx)
    tab = self.ltabs[idx]
    self.ltabs.remove(tab)
    d = self.ld[idx]
    for k in d.keys(): 
      if k in self.dqline:
        del self.dqline[k]
    self.ld.remove(d)
    tab.setParent(None)
    # print(self) # for testing

  def removeCurrentInput (self): # removes currently selected input
    idx = self.tabs.currentIndex()
    if idx < 0: return
    self.removeInput(idx)

  def __str__ (self):
    s = ''
    for k,v in self.dqline.items(): s += k + ': ' + v.text().strip() + os.linesep
    if self.chksync.isChecked(): s += 'sync_evinput: 1'+os.linesep
    else: s += 'sync_evinput: 0'+os.linesep
    s += 'inc_evinput: ' + self.incedit.text().strip() + os.linesep
    return s

  def addRemoveInputButton (self):
    self.bbremovebox = QHBoxLayout() 
    self.btnremove = QPushButton('Remove Input',self)
    self.btnremove.resize(self.btnremove.sizeHint())
    self.btnremove.clicked.connect(self.removeCurrentInput)
    self.btnremove.setToolTip('Remove This Input')
    self.bbremovebox.addWidget(self.btnremove)
    self.layout.addLayout(self.bbremovebox)

  def addHideButton (self):
    self.bbhidebox = QHBoxLayout() 
    self.btnhide = QPushButton('Hide Window',self)
    self.btnhide.resize(self.btnhide.sizeHint())
    self.btnhide.clicked.connect(self.hide)
    self.btnhide.setToolTip('Hide Window')
    self.bbhidebox.addWidget(self.btnhide)
    self.layout.addLayout(self.bbhidebox)

  def addTab (self,prox,s):
    tab = QWidget()
    self.ltabs.append(tab)
    self.tabs.addTab(tab,s)
    tab.layout = QFormLayout()
    tab.setLayout(tab.layout)
    return tab

  def addFormToTab (self,d,tab):
    for k,v in d.items():
      self.dqline[k] = QLineEdit(self)
      self.dqline[k].setText(str(v))
      tab.layout.addRow(self.transvar(k),self.dqline[k]) # adds label,QLineEdit to the tab

  def makePixLabel (self,fn):
    pix = QPixmap(fn)
    pixlbl = ClickLabel(self)
    pixlbl.setPixmap(pix)
    return pixlbl

  def addtransvarfromdict (self,d):
    dtmp = {'L2':'L2/3 ','L5':'L5 '}
    for k in d.keys():
      if k.startswith('gbar'):
        ks = k.split('_')
        stmp = ks[-2]
        self.addtransvar(k,dtmp[stmp[0:2]] + stmp[2:] + ' ' + ks[-1].upper() + u' weight (µS)')
      elif k.startswith('t'):
        self.addtransvar(k,'Start time mean (ms)')
      elif k.startswith('sigma'):
        self.addtransvar(k,'Start time stdev (ms)')
      elif k.startswith('numspikes'):
        self.addtransvar(k,'Number spikes')

  def addProx (self):
    self.nprox += 1 # starts at 1
    # evprox feed strength
    dprox = OrderedDict([('t_evprox_' + str(self.nprox), 0.), # times and stdevs for evoked responses
                         ('sigma_t_evprox_' + str(self.nprox), 2.5),
                         ('numspikes_evprox_' + str(self.nprox), 1),
                         ('gbar_evprox_' + str(self.nprox) + '_L2Pyr_ampa', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L2Pyr_nmda', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L2Basket_ampa', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L2Basket_nmda', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L5Pyr_ampa', 0.),                                   
                         ('gbar_evprox_' + str(self.nprox) + '_L5Pyr_nmda', 0.),                                   
                         ('gbar_evprox_' + str(self.nprox) + '_L5Basket_ampa', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L5Basket_nmda', 0.)])
    self.ld.append(dprox)
    self.addtransvarfromdict(dprox)
    self.addFormToTab(dprox, self.addTab(True,'Proximal ' + str(self.nprox)))
    self.ltabs[-1].layout.addRow(self.makePixLabel(lookupresource('proxfig')))
    #print('index to', len(self.ltabs)-1)
    self.tabs.setCurrentIndex(len(self.ltabs)-1)
    #print('index now', self.tabs.currentIndex(), ' of ', self.tabs.count())
    self.addtips()

  def addDist (self):
    self.ndist += 1
    # evdist feed strengths
    ddist = OrderedDict([('t_evdist_' + str(self.ndist), 0.),
                         ('sigma_t_evdist_' + str(self.ndist), 6.),
                         ('numspikes_evdist_' + str(self.ndist), 1),
                         ('gbar_evdist_' + str(self.ndist) + '_L2Pyr_ampa', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L2Pyr_nmda', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L2Basket_ampa', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L2Basket_nmda', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L5Pyr_ampa', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L5Pyr_nmda', 0.)])
    self.ld.append(ddist)
    self.addtransvarfromdict(ddist)
    self.addFormToTab(ddist,self.addTab(True,'Distal ' + str(self.ndist)))
    self.ltabs[-1].layout.addRow(self.makePixLabel(lookupresource('distfig')))
    #print('index to', len(self.ltabs)-1)
    self.tabs.setCurrentIndex(len(self.ltabs)-1)
    #print('index now', self.tabs.currentIndex(), ' of ', self.tabs.count())
    self.addtips()
    
# widget to specify run params (tstop, dt, etc.) -- not many params here
class RunParamDialog (DictDialog):
  def __init__ (self, parent, din = None):
    super(RunParamDialog, self).__init__(parent,din)
    self.addHideButton()

  def initd (self):

    self.drun = OrderedDict([('tstop', 250.), # simulation end time (ms)
                             ('dt', 0.025), # timestep
                             ('celsius',37.0), # temperature
                             ('N_trials',1), # number of trials
                             ('threshold',0.0)]) # firing threshold
                             # cvode - not currently used by simulation

    # analysis    
    self.danalysis = OrderedDict([('save_figs',0),
                                  ('save_spec_data', 0),
                                  ('f_max_spec', 40),
                                  ('dipole_scalefctr',30e3),
                                  ('dipole_smooth_win',15.0),
                                  ('save_vsoma',0),
                                  ('save_isoma',0)])

    self.drand = OrderedDict([('prng_seedcore_input_prox', 0),
                              ('prng_seedcore_input_dist', 0),
                              ('prng_seedcore_extpois', 0),
                              ('prng_seedcore_extgauss', 0),
                              ('prng_seedcore_evprox_1', 0),
                              ('prng_seedcore_evdist_1', 0),
                              ('prng_seedcore_evprox_2', 0),
                              ('prng_seedcore_evdist_2', 0)])

    self.ldict = [self.drun, self.danalysis, self.drand]
    self.ltitle = ['Run', 'Analysis', 'Randomization Seeds']
    self.stitle = 'Run Parameters'

    self.addtransvar('tstop','Duration (ms)')
    self.addtransvar('dt','Integration timestep (ms)')
    self.addtransvar('celsius','Temperature (C)')
    self.addtransvar('threshold','Firing threshold (mV)')
    self.addtransvar('N_trials','Trials')
    self.addtransvar('save_spec_data','Save spectral data')
    self.addtransvar('save_figs','Save figures')
    self.addtransvar('f_max_spec', 'Max spectral frequency (Hz)')
    self.addtransvar('dipole_scalefctr','Dipole Scaling')
    self.addtransvar('dipole_smooth_win','Dipole Smooth Window (ms)')
    self.addtransvar('save_vsoma','Save Somatic Voltages')
    self.addtransvar('save_isoma','Save Somatic Transmembrane currents')
    self.addtransvar('prng_seedcore_input_prox','Ongoing Proximal Input')
    self.addtransvar('prng_seedcore_input_dist','Ongoing Distal Input')
    self.addtransvar('prng_seedcore_extpois','External Poisson')
    self.addtransvar('prng_seedcore_extgauss','External Gaussian')
    self.addtransvar('prng_seedcore_evprox_1','Evoked Proximal 1')
    self.addtransvar('prng_seedcore_evdist_1','Evoked Distal 1 ')
    self.addtransvar('prng_seedcore_evprox_2','Evoked Proximal 2')
    self.addtransvar('prng_seedcore_evdist_2','Evoked Distal 2')

  def initExtra (self):
    DictDialog.initExtra(self)
    self.dqextra['NumCores'] = QLineEdit(self)
    self.dqextra['NumCores'].setText(str(defncore))
    self.addtransvar('NumCores','Number Cores')
    self.ltabs[0].layout.addRow('NumCores',self.dqextra['NumCores']) 

  def getntrial (self): return int(self.dqline['N_trials'].text().strip())

  def getncore (self): return int(self.dqextra['NumCores'].text().strip())

# widget to specify (pyramidal) cell parameters (geometry, synapses, biophysics)
class CellParamDialog (DictDialog):
  def __init__ (self, parent = None, din = None):
    super(CellParamDialog, self).__init__(parent,din)
    self.addHideButton()

  def initd (self):
    
    self.dL2PyrGeom = OrderedDict([('L2Pyr_soma_L', 22.1), # Soma
                                   ('L2Pyr_soma_diam', 23.4),
                                   ('L2Pyr_soma_cm', 0.6195),
                                   ('L2Pyr_soma_Ra', 200.),
                                   # Dendrites
                                   ('L2Pyr_dend_cm', 0.6195),
                                   ('L2Pyr_dend_Ra', 200.),
                                   ('L2Pyr_apicaltrunk_L', 59.5),
                                   ('L2Pyr_apicaltrunk_diam', 4.25),
                                   ('L2Pyr_apical1_L', 306.),
                                   ('L2Pyr_apical1_diam', 4.08),
                                   ('L2Pyr_apicaltuft_L', 238.),
                                   ('L2Pyr_apicaltuft_diam', 3.4),
                                   ('L2Pyr_apicaloblique_L', 340.),
                                   ('L2Pyr_apicaloblique_diam', 3.91),
                                   ('L2Pyr_basal1_L', 85.),
                                   ('L2Pyr_basal1_diam', 4.25),
                                   ('L2Pyr_basal2_L', 255.),
                                   ('L2Pyr_basal2_diam', 2.72),
                                   ('L2Pyr_basal3_L', 255.),
                                   ('L2Pyr_basal3_diam', 2.72)])

    self.dL2PyrSyn = OrderedDict([('L2Pyr_ampa_e', 0.),         # Synapses
                                  ('L2Pyr_ampa_tau1', 0.5),
                                  ('L2Pyr_ampa_tau2', 5.),
                                  ('L2Pyr_nmda_e', 0.),
                                  ('L2Pyr_nmda_tau1', 1.),
                                  ('L2Pyr_nmda_tau2', 20.),
                                  ('L2Pyr_gabaa_e', -80.),
                                  ('L2Pyr_gabaa_tau1', 0.5),
                                  ('L2Pyr_gabaa_tau2', 5.),
                                  ('L2Pyr_gabab_e', -80.),
                                  ('L2Pyr_gabab_tau1', 1.),
                                  ('L2Pyr_gabab_tau2', 20.)])

    self.dL2PyrBiophys = OrderedDict([('L2Pyr_soma_gkbar_hh2', 0.01), # Biophysics soma
                                      ('L2Pyr_soma_gnabar_hh2', 0.18),
                                      ('L2Pyr_soma_el_hh2', -65.),
                                      ('L2Pyr_soma_gl_hh2', 4.26e-5),
                                      ('L2Pyr_soma_gbar_km', 250.),
                                      # Biophysics dends
                                      ('L2Pyr_dend_gkbar_hh2', 0.01),
                                      ('L2Pyr_dend_gnabar_hh2', 0.15),
                                      ('L2Pyr_dend_el_hh2', -65.),
                                      ('L2Pyr_dend_gl_hh2', 4.26e-5),
                                      ('L2Pyr_dend_gbar_km', 250.)])


    self.dL5PyrGeom = OrderedDict([('L5Pyr_soma_L', 39.),  # Soma
                                   ('L5Pyr_soma_diam', 28.9),
                                   ('L5Pyr_soma_cm', 0.85),
                                   ('L5Pyr_soma_Ra', 200.),
                                   # Dendrites
                                   ('L5Pyr_dend_cm', 0.85),
                                   ('L5Pyr_dend_Ra', 200.),
                                   ('L5Pyr_apicaltrunk_L', 102.),
                                   ('L5Pyr_apicaltrunk_diam', 10.2),
                                   ('L5Pyr_apical1_L', 680.),
                                   ('L5Pyr_apical1_diam', 7.48),
                                   ('L5Pyr_apical2_L', 680.),
                                   ('L5Pyr_apical2_diam', 4.93),
                                   ('L5Pyr_apicaltuft_L', 425.),
                                   ('L5Pyr_apicaltuft_diam', 3.4),
                                   ('L5Pyr_apicaloblique_L', 255.),
                                   ('L5Pyr_apicaloblique_diam', 5.1),
                                   ('L5Pyr_basal1_L', 85.),
                                   ('L5Pyr_basal1_diam', 6.8),
                                   ('L5Pyr_basal2_L', 255.),
                                   ('L5Pyr_basal2_diam', 8.5),
                                   ('L5Pyr_basal3_L', 255.),
                                   ('L5Pyr_basal3_diam', 8.5)])

    self.dL5PyrSyn = OrderedDict([('L5Pyr_ampa_e', 0.), # Synapses
                                  ('L5Pyr_ampa_tau1', 0.5),
                                  ('L5Pyr_ampa_tau2', 5.),
                                  ('L5Pyr_nmda_e', 0.),
                                  ('L5Pyr_nmda_tau1', 1.),
                                  ('L5Pyr_nmda_tau2', 20.),
                                  ('L5Pyr_gabaa_e', -80.),
                                  ('L5Pyr_gabaa_tau1', 0.5),
                                  ('L5Pyr_gabaa_tau2', 5.),
                                  ('L5Pyr_gabab_e', -80.),
                                  ('L5Pyr_gabab_tau1', 1.),
                                  ('L5Pyr_gabab_tau2', 20.)])

    self.dL5PyrBiophys = OrderedDict([('L5Pyr_soma_gkbar_hh2', 0.01), # Biophysics soma
                                       ('L5Pyr_soma_gnabar_hh2', 0.16),
                                       ('L5Pyr_soma_el_hh2', -65.),
                                       ('L5Pyr_soma_gl_hh2', 4.26e-5),
                                       ('L5Pyr_soma_gbar_ca', 60.),
                                       ('L5Pyr_soma_taur_cad', 20.),
                                       ('L5Pyr_soma_gbar_kca', 2e-4),
                                       ('L5Pyr_soma_gbar_km', 200.),
                                       ('L5Pyr_soma_gbar_cat', 2e-4),
                                       ('L5Pyr_soma_gbar_ar', 1e-6),
                                       # Biophysics dends
                                       ('L5Pyr_dend_gkbar_hh2', 0.01),
                                       ('L5Pyr_dend_gnabar_hh2', 0.14),
                                       ('L5Pyr_dend_el_hh2', -71.),
                                       ('L5Pyr_dend_gl_hh2', 4.26e-5),
                                       ('L5Pyr_dend_gbar_ca', 60.),
                                       ('L5Pyr_dend_taur_cad', 20.),
                                       ('L5Pyr_dend_gbar_kca', 2e-4),
                                       ('L5Pyr_dend_gbar_km', 200.),
                                       ('L5Pyr_dend_gbar_cat', 2e-4),
                                       ('L5Pyr_dend_gbar_ar', 1e-6)])

    dtrans = {'gkbar':'Kv', 'gnabar':'Na', 'km':'Km', 'gl':'leak',\
              'ca':'Ca', 'kca':'KCa','cat':'CaT','ar':'HCN','dend':'Dendrite',\
              'soma':'Soma','apicaltrunk':'Apical Dendrite Trunk',\
              'apical1':'Apical Dendrite 1','apical2':'Apical Dendrite 2',\
              'apical3':'Apical Dendrite 3','apicaltuft':'Apical Dendrite Tuft',\
              'apicaloblique':'Oblique Apical Dendrite','basal1':'Basal Dendrite 1',\
              'basal2':'Basal Dendrite 2','basal3':'Basal Dendrite 3'}

    for d in [self.dL2PyrGeom, self.dL5PyrGeom]:
      for k in d.keys():
        lk = k.split('_')
        if lk[-1] == 'L':
          self.addtransvar(k,dtrans[lk[1]] + ' ' + r'length (micron)')
        elif lk[-1] == 'diam':
          self.addtransvar(k,dtrans[lk[1]] + ' ' + r'diameter (micron)')
        elif lk[-1] == 'cm':
          self.addtransvar(k,dtrans[lk[1]] + ' ' + r'capacitive density (F/cm2)')
        elif lk[-1] == 'Ra':
          self.addtransvar(k,dtrans[lk[1]] + ' ' + r'resistivity (ohm-cm)')

    for d in [self.dL2PyrSyn, self.dL5PyrSyn]:
      for k in d.keys():
        lk = k.split('_')
        if k.endswith('e'):
          self.addtransvar(k,lk[1].upper() + ' ' + ' reversal (mV)')
        elif k.endswith('tau1'):
          self.addtransvar(k,lk[1].upper() + ' ' + ' rise time (ms)')
        elif k.endswith('tau2'):
          self.addtransvar(k,lk[1].upper() + ' ' + ' decay time (ms)')

    for d in [self.dL2PyrBiophys, self.dL5PyrBiophys]:
      for k in d.keys():
        lk = k.split('_')
        if lk[2].count('g') > 0:
          if lk[3]=='km' or lk[3]=='ca' or lk[3]=='kca' or lk[3]=='cat' or lk[3]=='ar':
            nv = dtrans[lk[1]] + ' ' + dtrans[lk[3]] + ' ' + ' channel density '
          else:
            nv = dtrans[lk[1]] + ' ' + dtrans[lk[2]] + ' ' + ' channel density '
          if lk[3] == 'hh2': nv += '(S/cm2)'
          else: nv += '(pS/micron2)'
        elif lk[2].count('el') > 0: nv = dtrans[lk[1]] + ' leak reversal (mV)'
        self.addtransvar(k,nv)

    self.ldict = [self.dL2PyrGeom, self.dL2PyrSyn, self.dL2PyrBiophys,\
                  self.dL5PyrGeom, self.dL5PyrSyn, self.dL5PyrBiophys]
    self.ltitle = [ 'L2/3 Pyr Geometry', 'L2/3 Pyr Synapses', 'L2/3 Pyr Biophysics',\
                    'L5 Pyr Geometry', 'L5 Pyr Synapses', 'L5 Pyr Biophysics']
    self.stitle = 'Cell Parameters'


# widget to specify network parameters (number cells, weights, etc.)
class NetworkParamDialog (DictDialog):
  def __init__ (self, parent = None, din = None):
    super(NetworkParamDialog, self).__init__(parent,din)
    self.addHideButton()

  def initd (self):
    # number of cells
    self.dcells = OrderedDict([('N_pyr_x', 10),
                               ('N_pyr_y', 10)])

    # max conductances TO L2Pyr
    self.dL2Pyr = OrderedDict([('gbar_L2Pyr_L2Pyr_ampa', 0.),
                               ('gbar_L2Pyr_L2Pyr_nmda', 0.),
                               ('gbar_L2Basket_L2Pyr_gabaa', 0.),
                               ('gbar_L2Basket_L2Pyr_gabab', 0.)])

    # max conductances TO L2Baskets
    self.dL2Bas = OrderedDict([('gbar_L2Pyr_L2Basket', 0.),
                               ('gbar_L2Basket_L2Basket', 0.)])

    # max conductances TO L5Pyr
    self.dL5Pyr = OrderedDict([('gbar_L2Pyr_L5Pyr', 0.),
                               ('gbar_L2Basket_L5Pyr', 0.),
                               ('gbar_L5Pyr_L5Pyr_ampa', 0.),
                               ('gbar_L5Pyr_L5Pyr_nmda', 0.),
                               ('gbar_L5Basket_L5Pyr_gabaa', 0.),
                               ('gbar_L5Basket_L5Pyr_gabab', 0.)])

    # max conductances TO L5Baskets
    self.dL5Bas = OrderedDict([('gbar_L2Pyr_L5Basket', 0.),
                               ('gbar_L5Pyr_L5Basket', 0.),
                               ('gbar_L5Basket_L5Basket', 0.)])

    self.ldict = [self.dcells, self.dL2Pyr, self.dL5Pyr, self.dL2Bas, self.dL5Bas]
    self.ltitle = ['Cells', 'Layer 2/3 Pyr', 'Layer 5 Pyr', 'Layer 2/3 Bas', 'Layer 5 Bas']
    self.stitle = 'Local Network Parameters'

    self.addtransvar('N_pyr_x', 'Num Pyr Cells (X direction)')
    self.addtransvar('N_pyr_y', 'Num Pyr Cells (Y direction)')

    dtmp = {'L2':'L2/3 ','L5':'L5 '}

    for d in [self.dL2Pyr, self.dL5Pyr, self.dL2Bas, self.dL5Bas]:
      for k in d.keys():
        lk = k.split('_')
        sty1 = dtmp[lk[1][0:2]] + lk[1][2:]
        sty2 = dtmp[lk[2][0:2]] + lk[2][2:]
        if len(lk) == 3:
          self.addtransvar(k,sty1+' -> '+sty2+u' weight (µS)')
        else:
          self.addtransvar(k,sty1+' -> '+sty2+' '+lk[3].upper()+u' weight (µS)')

class HelpDialog (QDialog):
  def __init__ (self, parent):
    super(HelpDialog, self).__init__(parent)
    self.initUI()

  def initUI (self):
    self.layout = QVBoxLayout(self)
    # Add stretch to separate the form layout from the button
    self.layout.addStretch(1)

    setscalegeom(self, 100, 100, 300, 100)
    self.setWindowTitle('Help')    

# dialog for visualizing model
class VisnetDialog (QDialog):
  def __init__ (self, parent):
    super(VisnetDialog, self).__init__(parent)
    self.initUI()

  def showcells3D (self): Popen([getPyComm(), 'visnet.py', 'cells', paramf]) # nonblocking
  def showEconn (self): Popen([getPyComm(), 'visnet.py', 'Econn', paramf]) # nonblocking
  def showIconn (self): Popen([getPyComm(), 'visnet.py', 'Iconn', paramf]) # nonblocking

  def runvisnet (self):
    lcmd = [getPyComm(), 'visnet.py', 'cells']
    #if self.chkcells.isChecked(): lcmd.append('cells')
    #if self.chkE.isChecked(): lcmd.append('Econn')
    #if self.chkI.isChecked(): lcmd.append('Iconn')
    lcmd.append(paramf)
    Popen(lcmd) # nonblocking

  def initUI (self):

    self.layout = QVBoxLayout(self)

    # Add stretch to separate the form layout from the button
    # self.layout.addStretch(1)

    """
    self.chkcells = QCheckBox('Cells in 3D',self)
    self.chkcells.resize(self.chkcells.sizeHint())
    self.chkcells.setChecked(True)
    self.layout.addWidget(self.chkcells)
    self.chkE = QCheckBox('Excitatory Connections',self)
    self.chkE.resize(self.chkE.sizeHint())
    self.layout.addWidget(self.chkE)

    self.chkI = QCheckBox('Inhibitory Connections',self)
    self.chkI.resize(self.chkI.sizeHint())
    self.layout.addWidget(self.chkI)
    """

    # Create a horizontal box layout to hold the buttons
    self.button_box = QHBoxLayout()
 
    self.btnok = QPushButton('Visualize',self)
    self.btnok.resize(self.btnok.sizeHint())
    self.btnok.clicked.connect(self.runvisnet)
    self.button_box.addWidget(self.btnok)

    self.btncancel = QPushButton('Cancel',self)
    self.btncancel.resize(self.btncancel.sizeHint())
    self.btncancel.clicked.connect(self.hide)
    self.button_box.addWidget(self.btncancel)

    self.layout.addLayout(self.button_box)
        
    setscalegeom(self, 100, 100, 300, 100)

    self.setWindowTitle('Visualize Model')

class SchematicDialog (QDialog):
  # class for holding model schematics (and parameter shortcuts)
  def __init__ (self, parent):
    super(SchematicDialog, self).__init__(parent)
    self.initUI()

  def initUI (self):

    self.setWindowTitle('Model Schematics')
    QToolTip.setFont(QFont('SansSerif', 10))

    self.grid = grid = QGridLayout()
    grid.setSpacing(10)

    gRow = 0

    self.locbtn = QPushButton('Local Network'+os.linesep+'Connections',self)
    self.locbtn.setIcon(QIcon(lookupresource('connfig')))
    self.locbtn.clicked.connect(self.parent().shownetparamwin)
    self.grid.addWidget(self.locbtn,gRow,0,1,1)

    self.proxbtn = QPushButton('Proximal Drive'+os.linesep+'Thalamus',self)
    self.proxbtn.setIcon(QIcon(lookupresource('proxfig')))
    self.proxbtn.clicked.connect(self.parent().showproxparamwin)
    self.grid.addWidget(self.proxbtn,gRow,1,1,1)

    self.distbtn = QPushButton('Distal Drive NonLemniscal'+os.linesep+'Thal./Cortical Feedback',self)
    self.distbtn.setIcon(QIcon(lookupresource('distfig')))
    self.distbtn.clicked.connect(self.parent().showdistparamwin)
    self.grid.addWidget(self.distbtn,gRow,2,1,1)

    self.netbtn = QPushButton('Model'+os.linesep+'Visualization',self)
    self.netbtn.setIcon(QIcon(lookupresource('netfig')))
    self.netbtn.clicked.connect(self.parent().showvisnet)
    self.grid.addWidget(self.netbtn,gRow,3,1,1)

    gRow = 1

    # for schematic dialog box
    self.pixConn = QPixmap(lookupresource('connfig'))
    self.pixConnlbl = ClickLabel(self)
    self.pixConnlbl.setScaledContents(True)
    #self.pixConnlbl.resize(self.pixConnlbl.size())
    self.pixConnlbl.setPixmap(self.pixConn)    
    # self.pixConnlbl.clicked.connect(self.shownetparamwin)
    self.grid.addWidget(self.pixConnlbl,gRow,0,1,1)

    self.pixProx = QPixmap(lookupresource('proxfig'))
    self.pixProxlbl = ClickLabel(self)
    self.pixProxlbl.setScaledContents(True)
    self.pixProxlbl.setPixmap(self.pixProx)
    # self.pixProxlbl.clicked.connect(self.showproxparamwin)
    self.grid.addWidget(self.pixProxlbl,gRow,1,1,1)

    self.pixDist = QPixmap(lookupresource('distfig'))
    self.pixDistlbl = ClickLabel(self)
    self.pixDistlbl.setScaledContents(True)
    self.pixDistlbl.setPixmap(self.pixDist)
    # self.pixDistlbl.clicked.connect(self.showdistparamwin)
    self.grid.addWidget(self.pixDistlbl,gRow,2,1,1)

    self.pixNet = QPixmap(lookupresource('netfig'))
    self.pixNetlbl = ClickLabel(self)
    self.pixNetlbl.setScaledContents(True)
    self.pixNetlbl.setPixmap(self.pixNet)
    # self.pixNetlbl.clicked.connect(self.showvisnet)
    self.grid.addWidget(self.pixNetlbl,gRow,3,1,1)

    self.setLayout(grid)

class BaseParamDialog (QDialog):
  # base widget for specifying params (contains buttons to create other widgets
  def __init__ (self, parent):
    super(BaseParamDialog, self).__init__(parent)
    self.proxparamwin = self.distparamwin = self.netparamwin = self.syngainparamwin = None
    self.initUI()
    self.runparamwin = RunParamDialog(self)
    self.cellparamwin = CellParamDialog(self)
    self.netparamwin = NetworkParamDialog(self)    
    self.syngainparamwin = SynGainParamDialog(self,self.netparamwin)
    self.proxparamwin = OngoingInputParamDialog(self,'Proximal')
    self.distparamwin = OngoingInputParamDialog(self,'Distal')
    self.evparamwin = EvokedInputParamDialog(self,None)
    self.poisparamwin = PoissonInputParamDialog(self,None)
    self.tonicparamwin = TonicInputParamDialog(self,None)
    self.lsubwin = [self.runparamwin, self.cellparamwin, self.netparamwin, self.proxparamwin, self.distparamwin, self.evparamwin,self.poisparamwin, self.tonicparamwin]
    self.updateDispParam()

  def updateDispParam (self):
    # now update the GUI components to reflect the param file selected
    try:
      din = quickreadprm(paramf)
      if usingEvokedInputs(din): # default for evoked is to show average dipole
        conf.dconf['drawavgdpl'] = True        
      elif usingOngoingInputs(din): # default for ongoing is NOT to show average dipole
        conf.dconf['drawavgdpl'] = False        
    except:
      print('could not read',paramf)
    ddef = params_default.get_params_default()
    for dlg in self.lsubwin: dlg.setfromdin(ddef) # first set to default?
    try:
      for dlg in self.lsubwin: dlg.setfromdin(din) # then update to values from file
      self.qle.setText(paramf.split(os.path.sep)[-1].split('.param')[0]) # update simulation name
    except:
      print('WARNING: could not read dialog settings.')

  def setrunparam (self): bringwintotop(self.runparamwin)
  def setcellparam (self): bringwintotop(self.cellparamwin)
  def setnetparam (self): bringwintotop(self.netparamwin)
  def setsyngainparam (self): bringwintotop(self.syngainparamwin)
  def setproxparam (self): bringwintotop(self.proxparamwin)
  def setdistparam (self): bringwintotop(self.distparamwin)
  def setevparam (self): bringwintotop(self.evparamwin)
  def setpoisparam (self): bringwintotop(self.poisparamwin)
  def settonicparam (self): bringwintotop(self.tonicparamwin)

  def initUI (self):

    grid = QGridLayout()
    grid.setSpacing(10)

    row = 1

    self.lbl = QLabel(self)
    self.lbl.setText('Simulation Name:')
    self.lbl.adjustSize()
    self.lbl.setToolTip('Simulation Name used to save parameter file and simulation data')
    grid.addWidget(self.lbl, row, 0)
    self.qle = QLineEdit(self)
    self.qle.setText(paramf.split(os.path.sep)[-1].split('.param')[0])
    grid.addWidget(self.qle, row, 1)
    row+=1

    self.btnrun = QPushButton('Run',self)
    self.btnrun.resize(self.btnrun.sizeHint())
    self.btnrun.setToolTip('Set Run Parameters')
    self.btnrun.clicked.connect(self.setrunparam)
    grid.addWidget(self.btnrun, row, 0, 1, 1); 

    self.btncell = QPushButton('Cell',self)
    self.btncell.resize(self.btncell.sizeHint())
    self.btncell.setToolTip('Set Cell (Geometry, Synapses, Biophysics) Parameters')
    self.btncell.clicked.connect(self.setcellparam)
    grid.addWidget(self.btncell, row, 1, 1, 1); row+=1

    self.btnnet = QPushButton('Local Network',self)
    self.btnnet.resize(self.btnnet.sizeHint())
    self.btnnet.setToolTip('Set Local Network Parameters')
    self.btnnet.clicked.connect(self.setnetparam)
    grid.addWidget(self.btnnet, row, 0, 1, 1); 

    self.btnsyngain = QPushButton('Synaptic Gains',self)
    self.btnsyngain.resize(self.btnsyngain.sizeHint())
    self.btnsyngain.setToolTip('Set Local Network Synaptic Gains')
    self.btnsyngain.clicked.connect(self.setsyngainparam)
    grid.addWidget(self.btnsyngain, row, 1, 1, 1); 

    row+=1

    self.btnprox = QPushButton('Rhythmic Proximal Inputs',self)
    self.btnprox.resize(self.btnprox.sizeHint())
    self.btnprox.setToolTip('Set Rhythmic Proximal Inputs')
    self.btnprox.clicked.connect(self.setproxparam)
    grid.addWidget(self.btnprox, row, 0, 1, 2); row+=1

    self.btndist = QPushButton('Rhythmic Distal Inputs',self)
    self.btndist.resize(self.btndist.sizeHint())
    self.btndist.setToolTip('Set Rhythmic Distal Inputs')
    self.btndist.clicked.connect(self.setdistparam)
    grid.addWidget(self.btndist, row, 0, 1, 2); row+=1

    self.btnev = QPushButton('Evoked Inputs',self)
    self.btnev.resize(self.btnev.sizeHint())
    self.btnev.setToolTip('Set Evoked Inputs')
    self.btnev.clicked.connect(self.setevparam)
    grid.addWidget(self.btnev, row, 0, 1, 2); row+=1

    self.btnpois = QPushButton('Poisson Inputs',self)
    self.btnpois.resize(self.btnpois.sizeHint())
    self.btnpois.setToolTip('Set Poisson Inputs')
    self.btnpois.clicked.connect(self.setpoisparam)
    grid.addWidget(self.btnpois, row, 0, 1, 2); row+=1

    self.btntonic = QPushButton('Tonic Inputs',self)
    self.btntonic.resize(self.btntonic.sizeHint())
    self.btntonic.setToolTip('Set Tonic (Current Clamp) Inputs')
    self.btntonic.clicked.connect(self.settonicparam)
    grid.addWidget(self.btntonic, row, 0, 1, 2); row+=1

    self.btnsave = QPushButton('Save Parameters To File',self)
    self.btnsave.resize(self.btnsave.sizeHint())
    self.btnsave.setToolTip('Save All Parameters to File (Specified by Simulation Name)')
    self.btnsave.clicked.connect(self.saveparams)
    grid.addWidget(self.btnsave, row, 0, 1, 2); row+=1

    self.btnhide = QPushButton('Hide Window',self)
    self.btnhide.resize(self.btnhide.sizeHint())
    self.btnhide.clicked.connect(self.hide)
    self.btnhide.setToolTip('Hide Window')
    grid.addWidget(self.btnhide, row, 0, 1, 2)

    self.setLayout(grid) 
        
    setscalegeom(self, 100, 100, 400, 100)

    self.setWindowTitle('Set Parameters')    

  def saveparams (self, checkok = True):
    global paramf,basedir
    tmpf = os.path.join(dconf['paramoutdir'],self.qle.text() + '.param')
    oktosave = True
    if os.path.isfile(tmpf) and checkok:
      self.show()
      oktosave = False
      msg = QMessageBox()
      msg.setIcon(QMessageBox.Warning)
      msg.setText(tmpf + ' already exists. Over-write?')
      msg.setWindowTitle('Over-write file(s)?')
      msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)      
      if msg.exec_() == QMessageBox.Ok: oktosave = True
    if oktosave:
      if debug: print('Saving params to ',  tmpf)
      try:
        with open(tmpf,'w') as fp: fp.write(str(self))
        paramf = dconf['paramf'] = tmpf # success? update paramf
        basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
      except:
        print('Exception in saving param file!',tmpf)
    return oktosave

  def updatesaveparams (self, dtest):
    if debug: print('BaseParamDialog updatesaveparams: dtest=',dtest)
    # update parameter values in GUI (so user can see and so GUI will save these param values)
    for win in self.lsubwin: win.setfromdin(dtest)
    # save parameters - do not ask if can over-write the param file
    self.saveparams(checkok = False)

  def __str__ (self):
    s = 'sim_prefix: ' + self.qle.text() + os.linesep
    s += 'expmt_groups: {' + self.qle.text() + '}' + os.linesep
    for win in self.lsubwin: s += str(win)
    return s

# clickable label
class ClickLabel (QLabel):
  """
  def __init__(self, *args, **kwargs):
    QLabel.__init__(self)
    # self._pixmap = QPixmap(self.pixmap())
    # spolicy = QSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding)
    spolicy = QSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
    # spolicy = QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred)
    # spolicy.setHorizontalStretch(0)
    # spolicy.setVerticalStretch(0)
    self.setSizePolicy(spolicy)
    self.setMinimumWidth(150)
    self.setMinimumHeight(150)
  def setPixmap (self, pm):
    QLabel.setPixmap(self,pm)
    self._pixmap = pm
  """
  clicked = pyqtSignal()
  def mousePressEvent(self, event):
    self.clicked.emit()
  """
  def resizeEvent(self, event):
    self.setPixmap(self._pixmap.scaled(
      self.width(), self.height(),
      QtCore.Qt.KeepAspectRatio))
  """

class WaitSimDialog (QDialog):
  def __init__ (self, parent):
    super(WaitSimDialog, self).__init__(parent)
    self.initUI()
    self.txt = '' # text for display

  def updatetxt (self,txt):
    self.qtxt.append(txt)

  def initUI (self):
    self.layout = QVBoxLayout(self)
    self.layout.addStretch(1)

    self.qtxt = QTextEdit(self)
    self.layout.addWidget(self.qtxt)

    self.stopbtn = stopbtn = QPushButton('Stop All Simulations', self)
    stopbtn.setToolTip('Stop All Simulations')
    stopbtn.resize(stopbtn.sizeHint())
    stopbtn.clicked.connect(self.stopsim)
    self.layout.addWidget(stopbtn)

    setscalegeomcenter(self, 500, 250)
    self.setWindowTitle("Simulation Log")

  def stopsim (self):
    self.parent().stopsim()
    self.hide()


class HNNGUI (QMainWindow):
  # main HNN GUI class
  def __init__ (self):
    # initialize the main HNN GUI
    global dfile, ddat, paramf
    super().__init__()   
    self.runningsim = False
    self.runthread = None
    self.fontsize = dconf['fontsize']
    self.linewidth = plt.rcParams['lines.linewidth'] = 1
    self.markersize = plt.rcParams['lines.markersize'] = 5
    self.dextdata = OrderedDict() # external data
    self.schemwin = SchematicDialog(self)
    self.initUI()
    self.baseparamwin = BaseParamDialog(self)
    self.visnetwin = VisnetDialog(self)
    self.helpwin = HelpDialog(self)
    self.erselectdistal = EvokedOrRhythmicDialog(self, True, self.baseparamwin.evparamwin, self.baseparamwin.distparamwin)
    self.erselectprox = EvokedOrRhythmicDialog(self, False, self.baseparamwin.evparamwin, self.baseparamwin.proxparamwin)
    self.waitsimwin = WaitSimDialog(self)

  def redraw (self):
    # redraw simulation & external data
    self.m.plotsimdat()
    self.m.draw()
    self.m.plot()

  def changeFontSize (self):
    # bring up window to change font sizes
    i, ok = QInputDialog.getInt(self, "Set Font Size","Font Size:", plt.rcParams['font.size'], 1, 100, 1)
    if ok:
      self.fontsize = plt.rcParams['font.size'] = dconf['fontsize'] = i
      self.redraw()

  def changeLineWidth (self):
    # bring up window to change line width(s)
    i, ok = QInputDialog.getInt(self, "Set Line Width","Line Width:", plt.rcParams['lines.linewidth'], 1, 20, 1)
    if ok:
      self.linewidth = plt.rcParams['lines.linewidth'] = i
      self.redraw()

  def changeMarkerSize (self):
    # bring up window to change marker size
    i, ok = QInputDialog.getInt(self, "Set Marker Size","Font Size:", self.markersize, 1, 100, 1)
    if ok:
      self.markersize = plt.rcParams['lines.markersize'] = i
      self.redraw()
    
  def selParamFileDialog (self):
    # bring up window to select simulation parameter file
    global paramf,dfile
    fn = QFileDialog.getOpenFileName(self, 'Open file', 'param') # uses forward slash, even on Windows OS
    if fn[0]:
      paramf = os.path.abspath(fn[0]) # to make sure have right path separators on Windows OS
      try:
        dfile = getinputfiles(paramf) # reset input data - if already exists
      except:
        pass
      # now update the GUI components to reflect the param file selected
      self.baseparamwin.updateDispParam()
      self.initSimCanvas() # recreate canvas 
      # self.m.plot() # replot data
      self.setWindowTitle(paramf)
      # store the sim just loaded in simdat's list - is this the desired behavior? or should we first erase prev sims?
      import simdat
      if 'dpl' in simdat.ddat:
        simdat.updatelsimdat(paramf,simdat.ddat['dpl']) # update lsimdat and its current sim index
      self.populateSimCB() # populate the combobox

  def loadDataFile (self, fn):
    # load a dipole data file
    import simdat
    try:
      self.dextdata[fn] = np.loadtxt(fn)
      simdat.ddat['dextdata'] = self.dextdata
      print('Loaded data in ', fn)
    except:
      print('Could not load data in ', fn)
      return False
    try:
      self.m.plotextdat()
      self.m.draw() # make sure new lines show up in plot
      return True
    except:
      print('Could not plot data from ', fn)
      return False

  def loadDataFileDialog (self):
    # bring up window to select/load external dipole data file
    fn = QFileDialog.getOpenFileName(self, 'Open file', 'data')
    if fn[0]: self.loadDataFile(os.path.abspath(fn[0])) # use abspath to make sure have right path separators

  def clearDataFile (self):
    # clear external dipole data
    import simdat
    self.m.clearlextdatobj()
    self.dextdata = simdat.ddat['dextdata'] = OrderedDict()
    self.m.draw()

  def setparams (self):
    # show set parameters dialog window
    if self.baseparamwin:
      for win in self.baseparamwin.lsubwin: bringwintobot(win)
      bringwintotop(self.baseparamwin)

  def showAboutDialog (self):
    # show HNN's about dialog box
    from __init__ import __version__
    msgBox = QMessageBox(self)
    msgBox.setTextFormat(Qt.RichText)
    msgBox.setWindowTitle('About')
    msgBox.setText("Human Neocortical Neurosolver (HNN) v" + __version__ + "<br>"+\
                   "<a href=https://hnn.brown.edu>https://hnn.brown.edu</a><br>"+\
                   "<a href=https://github.com/jonescompneurolab/hnn>HNN On Github</a><br>"+\
                   "© 2017-2018 <a href=http://brown.edu>Brown University, Providence, RI</a><br>"+\
                   "<a href=https://github.com/jonescompneurolab/hnn/blob/master/LICENSE>Software License</a>")
    msgBox.setStandardButtons(QMessageBox.Ok)
    msgBox.exec_()

  def showHelpDialog (self):
    # show the help dialog box
    bringwintotop(self.helpwin)

  def showSomaVPlot (self): 
    # start the somatic voltage visualization process (separate window)
    global basedir, dfile
    if not float(self.baseparamwin.runparamwin.getval('save_vsoma')):
      smsg='In order to view somatic voltages you must first rerun the simulation with saving somatic voltages. To do so from the main GUI, click on Set Parameters -> Run -> Analysis -> Save Somatic Voltages, enter a 1 and then rerun the simulation.'
      msg = QMessageBox()
      msg.setIcon(QMessageBox.Information)
      msg.setText(smsg)
      msg.setWindowTitle('Rerun simulation')
      msg.setStandardButtons(QMessageBox.Ok)      
      msg.exec_()
    else:
      basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
      lcmd = [getPyComm(), 'visvolt.py',paramf]
      if debug: print('visvolt cmd:',lcmd)
      Popen(lcmd) # nonblocking

  def showPSDPlot (self):
    # start the PSD visualization process (separate window)
    global basedir
    basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
    lcmd = [getPyComm(), 'vispsd.py',paramf]
    if debug: print('vispsd cmd:',lcmd)
    Popen(lcmd) # nonblocking

  def showLFPPlot (self):
    # start the LFP visualization process (separate window)
    global basedir
    basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
    lcmd = [getPyComm(), 'vislfp.py',paramf]
    if debug: print('vislfp cmd:',lcmd)
    Popen(lcmd) # nonblocking

  def showSpecPlot (self):
    # start the spectrogram visualization process (separate window)
    global basedir
    basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
    lcmd = [getPyComm(), 'visspec.py',paramf]
    if debug: print('visspec cmd:',lcmd)
    Popen(lcmd) # nonblocking

  def showRasterPlot (self):
    # start the raster plot visualization process (separate window)
    global basedir
    basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
    lcmd = [getPyComm(), 'visrast.py',paramf,os.path.join(basedir,'spk.txt')]
    if dconf['drawindivrast']: lcmd.append('indiv')
    if debug: print('visrast cmd:',lcmd)
    Popen(lcmd) # nonblocking

  def showDipolePlot (self):
    # start the dipole visualization process (separate window)
    global basedir
    basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
    lcmd = [getPyComm(), 'visdipole.py',paramf,os.path.join(basedir,'dpl.txt')]
    if debug: print('visdipole cmd:',lcmd)
    Popen(lcmd) # nonblocking    

  def showwaitsimwin (self):
    # show the wait sim window (has simulation log)
    bringwintotop(self.waitsimwin)

  def togAvgDpl (self):
    # toggle drawing of the average (across trials) dipole
    conf.dconf['drawavgdpl'] = not conf.dconf['drawavgdpl']
    self.m.plotsimdat()
    self.m.draw()

  def hidesubwin (self):
    # hide GUI's sub windows
    self.baseparamwin.hide()
    self.schemwin.hide()
    self.baseparamwin.syngainparamwin.hide()
    for win in self.baseparamwin.lsubwin: win.hide()
    self.activateWindow()

  def distribsubwin (self):
    # distribute GUI's sub-windows on screen
    sw,sh = getscreengeom()
    lwin = [win for win in self.baseparamwin.lsubwin if win.isVisible()]
    if self.baseparamwin.isVisible(): lwin.insert(0,self.baseparamwin)
    if self.schemwin.isVisible(): lwin.insert(0,self.schemwin)
    if self.baseparamwin.syngainparamwin.isVisible(): lwin.append(self.baseparamwin.syngainparamwin)
    curx,cury,maxh=0,0,0
    for win in lwin: 
      widget = win.geometry()
      win.move(curx, cury)
      curx += win.width()
      maxh = max(maxh,win.height())
      if curx >= sw: 
        curx = 0
        cury += maxh
        maxh = win.height()
      if cury >= sh: cury = cury = 0

  def updateDatCanv (self,fn):
    # update the simulation data and canvas
    try:
      dfile = getinputfiles(fn) # reset input data - if already exists
    except:
      pass
    # now update the GUI components to reflect the param file selected
    self.baseparamwin.updateDispParam()
    self.initSimCanvas() # recreate canvas 
    self.setWindowTitle(fn)

  def removeSim (self):
    # remove the currently selected simulation
    global paramf,dfile
    import simdat
    if debug: print('removeSim',paramf,simdat.lsimidx)
    if len(simdat.lsimdat) > 0 and simdat.lsimidx >= 0:
      cidx = self.cbsim.currentIndex() # 
      a = simdat.lsimdat[:cidx]
      b = simdat.lsimdat[cidx+1:]
      c = [x for x in a]
      for x in b: c.append(x)
      simdat.lsimdat = c
      self.cbsim.removeItem(cidx)
      simdat.lsimidx = max(0,len(simdat.lsimdat) - 1)
      if len(simdat.lsimdat) > 0:
        paramf = simdat.lsimdat[simdat.lsimidx][0]
        if debug: print('new paramf:',paramf,simdat.lsimidx)
        self.updateDatCanv(paramf)
        self.cbsim.setCurrentIndex(simdat.lsimidx)
      else:
        self.clearSimulations()

  def prevSim (self):
    # go to previous simulation 
    global paramf,dfile
    import simdat
    if debug: print('prevSim',paramf,simdat.lsimidx)
    if len(simdat.lsimdat) > 0 and simdat.lsimidx > 0:
      simdat.lsimidx -= 1
      paramf = simdat.lsimdat[simdat.lsimidx][0]
      if debug: print('new paramf:',paramf,simdat.lsimidx)
      self.updateDatCanv(paramf)
      self.cbsim.setCurrentIndex(simdat.lsimidx)

  def nextSim (self):
    # go to next simulation
    global paramf,dfile
    import simdat
    if debug: print('nextSim',paramf,simdat.lsimidx)
    if len(simdat.lsimdat) > 0 and simdat.lsimidx + 1 < len(simdat.lsimdat):
      simdat.lsimidx += 1
      paramf = simdat.lsimdat[simdat.lsimidx][0]
      if debug: print('new paramf:',paramf,simdat.lsimidx)
      self.updateDatCanv(paramf)
      self.cbsim.setCurrentIndex(simdat.lsimidx)

  def clearSimulationData (self):
    # clear the simulation data
    global paramf
    import simdat
    paramf = '' # set paramf to empty so no data gets loaded
    simdat.ddat = {} # clear data in simdat.ddat
    simdat.lsimdat = []
    simdat.lsimidx = 0
    self.populateSimCB() # un-populate the combobox

  def clearSimulations (self):
    # clear all simulation data and erase simulations from canvas (does not clear external data)
    self.clearSimulationData()
    self.initSimCanvas() # recreate canvas 
    self.m.draw()
    self.setWindowTitle('')

  def clearCanvas (self):
    # clear all simulation & external data and erase everything from the canvas
    import simdat
    self.clearSimulationData()
    self.m.clearlextdatobj() # clear the external data
    self.dextdata = simdat.ddat['dextdata'] = OrderedDict()
    self.initSimCanvas() # recreate canvas 
    self.m.draw()
    self.setWindowTitle('')

  def initMenu (self):
    # initialize the GUI's menu
    exitAction = QAction(QIcon.fromTheme('exit'), 'Exit', self)        
    exitAction.setShortcut('Ctrl+Q')
    exitAction.setStatusTip('Exit HNN application')
    exitAction.triggered.connect(qApp.quit)

    selParamFile = QAction(QIcon.fromTheme('open'), 'Load parameter file', self)
    selParamFile.setShortcut('Ctrl+P')
    selParamFile.setStatusTip('Load simulation parameter (.param) file')
    selParamFile.triggered.connect(self.selParamFileDialog)

    clearCanv = QAction('Clear canvas', self)
    clearCanv.setShortcut('Ctrl+X')
    clearCanv.setStatusTip('Clear canvas (simulation+data)')
    clearCanv.triggered.connect(self.clearCanvas)

    clearSims = QAction('Clear simulation(s)', self)
    #clearSims.setShortcut('Ctrl+X')
    clearSims.setStatusTip('Clear simulation(s)')
    clearSims.triggered.connect(self.clearSimulations)

    loadDataFile = QAction(QIcon.fromTheme('open'), 'Load data file', self)
    loadDataFile.setShortcut('Ctrl+D')
    loadDataFile.setStatusTip('Load (dipole) data file')
    loadDataFile.triggered.connect(self.loadDataFileDialog)

    clearDataFileAct = QAction(QIcon.fromTheme('close'), 'Clear data file(s)', self)
    clearDataFileAct.setShortcut('Ctrl+C')
    clearDataFileAct.setStatusTip('Clear (dipole) data file(s)')
    clearDataFileAct.triggered.connect(self.clearDataFile)

    runSimAct = QAction('Run simulation', self)
    runSimAct.setShortcut('Ctrl+S')
    runSimAct.setStatusTip('Run simulation')
    runSimAct.triggered.connect(self.controlsim)

    runSimNSGAct = QAction('Run simulation on NSG', self)
    runSimNSGAct.setShortcut('Ctrl+N')
    runSimNSGAct.setStatusTip('Run simulation on Neuroscience Gateway Portal (requires NSG account and internet connection).')
    runSimNSGAct.triggered.connect(self.controlNSGsim)

    if dconf['optrun']:
      optSimAct = QAction('Optimize model', self)
      optSimAct.setShortcut('Ctrl+O')
      optSimAct.setStatusTip('Optimize Model')
      optSimAct.triggered.connect(self.startoptmodel)

    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')
    menubar.setNativeMenuBar(False)
    fileMenu.addAction(selParamFile)
    fileMenu.addSeparator()
    fileMenu.addAction(loadDataFile)
    fileMenu.addAction(clearDataFileAct)
    fileMenu.addSeparator()
    fileMenu.addAction(exitAction)

    # part of edit menu for changing drawing properties (line thickness, font size, toggle avg dipole drawing)
    editMenu = menubar.addMenu('&Edit')
    viewAvgDplAction = QAction('Toggle Average Dipole Drawing',self)
    viewAvgDplAction.setStatusTip('Toggle Average Dipole Drawing')
    viewAvgDplAction.triggered.connect(self.togAvgDpl)
    editMenu.addAction(viewAvgDplAction)
    changeFontSizeAction = QAction('Change Font Size',self)
    changeFontSizeAction.setStatusTip('Change Font Size.')
    changeFontSizeAction.triggered.connect(self.changeFontSize)
    editMenu.addAction(changeFontSizeAction)
    changeLineWidthAction = QAction('Change Line Width',self)
    changeLineWidthAction.setStatusTip('Change Line Width.')
    changeLineWidthAction.triggered.connect(self.changeLineWidth)
    editMenu.addAction(changeLineWidthAction)
    changeMarkerSizeAction = QAction('Change Marker Size',self)
    changeMarkerSizeAction.setStatusTip('Change Marker Size.')
    changeMarkerSizeAction.triggered.connect(self.changeMarkerSize)
    editMenu.addAction(changeMarkerSizeAction)    
    editMenu.addSeparator()
    editMenu.addAction(clearSims)
    clearDataFileAct2 = QAction(QIcon.fromTheme('close'), 'Clear data file(s)', self) # need new act to avoid DBus warning
    clearDataFileAct2.setStatusTip('Clear (dipole) data file(s)')
    clearDataFileAct2.triggered.connect(self.clearDataFile)
    editMenu.addAction(clearDataFileAct2)
    editMenu.addAction(clearCanv)
    
    # view menu - to view drawing/visualizations
    viewMenu = menubar.addMenu('&View')
    viewDipoleAction = QAction('View Simulation Dipoles',self)
    viewDipoleAction.setStatusTip('View Simulation Dipoles')
    viewDipoleAction.triggered.connect(self.showDipolePlot)
    viewMenu.addAction(viewDipoleAction)
    viewRasterAction = QAction('View Simulation Spiking Activity',self)
    viewRasterAction.setStatusTip('View Simulation Raster Plot')
    viewRasterAction.triggered.connect(self.showRasterPlot)
    viewMenu.addAction(viewRasterAction)
    viewPSDAction = QAction('View PSD',self)
    viewPSDAction.setStatusTip('View PSD')
    viewPSDAction.triggered.connect(self.showPSDPlot)
    viewMenu.addAction(viewPSDAction)

    viewSomaVAction = QAction('View Somatic Voltage',self)
    viewSomaVAction.setStatusTip('View Somatic Voltage')
    viewSomaVAction.triggered.connect(self.showSomaVPlot)
    viewMenu.addAction(viewSomaVAction)

    if testLFP:
      viewLFPAction = QAction('View Simulation LFPs',self)
      viewLFPAction.setStatusTip('View LFP')
      viewLFPAction.triggered.connect(self.showLFPPlot)
      viewMenu.addAction(viewLFPAction)

    viewSpecAction = QAction('View Spectrograms',self)
    viewSpecAction.setStatusTip('View Spectrograms/Dipoles from Experimental Data')
    viewSpecAction.triggered.connect(self.showSpecPlot)
    viewMenu.addAction(viewSpecAction)

    viewMenu.addSeparator()
    viewSchemAction = QAction('View Model Schematics',self)
    viewSchemAction.setStatusTip('View Model Schematics')
    viewSchemAction.triggered.connect(self.showschematics)
    viewMenu.addAction(viewSchemAction)
    viewNetAction = QAction('View Local Network (3D)',self)
    viewNetAction.setStatusTip('View Local Network Model (3D)')
    viewNetAction.triggered.connect(self.showvisnet)
    viewMenu.addAction(viewNetAction)
    viewSimLogAction = QAction('View Simulation Log',self)
    viewSimLogAction.setStatusTip('View Detailed Simulation Log')
    viewSimLogAction.triggered.connect(self.showwaitsimwin)
    viewMenu.addAction(viewSimLogAction)
    viewMenu.addSeparator()    
    distributeWindowsAction = QAction('Distribute Windows',self)
    distributeWindowsAction.setStatusTip('Distribute Parameter Windows Across Screen.')
    distributeWindowsAction.triggered.connect(self.distribsubwin)
    viewMenu.addAction(distributeWindowsAction)
    hideWindowsAction = QAction('Hide Windows',self)
    hideWindowsAction.setStatusTip('Hide Parameter Windows.')
    hideWindowsAction.triggered.connect(self.hidesubwin)
    hideWindowsAction.setShortcut('Ctrl+H')
    viewMenu.addAction(hideWindowsAction)

    simMenu = menubar.addMenu('&Simulation')
    setParmAct = QAction('Set Parameters',self)
    setParmAct.setStatusTip('Set Simulation Parameters')
    setParmAct.triggered.connect(self.setparams)
    simMenu.addAction(setParmAct)
    simMenu.addAction(runSimAct)    
    if dconf['nsgrun']: simMenu.addAction(runSimNSGAct)
    if dconf['optrun']: simMenu.addAction(optSimAct)
    prevSimAct = QAction('Go to Previous Simulation',self)
    prevSimAct.setShortcut('Ctrl+Z')
    prevSimAct.setStatusTip('Go Back to Previous Simulation')
    prevSimAct.triggered.connect(self.prevSim)
    simMenu.addAction(prevSimAct)
    nextSimAct = QAction('Go to Next Simulation',self)
    nextSimAct.setShortcut('Ctrl+Y')
    nextSimAct.setStatusTip('Go Forward to Next Simulation')
    nextSimAct.triggered.connect(self.nextSim)
    simMenu.addAction(nextSimAct)
    clearSims2 = QAction('Clear simulation(s)', self) # need another QAction to avoid DBus warning
    clearSims2.setStatusTip('Clear simulation(s)')
    clearSims2.triggered.connect(self.clearSimulations)
    simMenu.addAction(clearSims2)

    aboutMenu = menubar.addMenu('&About')
    aboutAction = QAction('About HNN',self)
    aboutAction.setStatusTip('About HNN')
    aboutAction.triggered.connect(self.showAboutDialog)
    aboutMenu.addAction(aboutAction)
    helpAction = QAction('Help',self)
    helpAction.setStatusTip('Help on how to use HNN (parameters).')
    helpAction.triggered.connect(self.showHelpDialog)
    #aboutMenu.addAction(helpAction)

  def addButtons (self, gRow):
    self.pbtn = pbtn = QPushButton('Set Parameters', self)
    pbtn.setToolTip('Set Parameters')
    pbtn.resize(pbtn.sizeHint())
    pbtn.clicked.connect(self.setparams)
    self.grid.addWidget(self.pbtn, gRow, 0, 1, 1)

    self.pfbtn = pfbtn = QPushButton('Set Parameters From File', self)
    pfbtn.setToolTip('Set Parameters From File')
    pfbtn.resize(pfbtn.sizeHint())
    pfbtn.clicked.connect(self.selParamFileDialog)
    self.grid.addWidget(self.pfbtn, gRow, 1, 1, 1)

    self.btnsim = btn = QPushButton('Run Simulation', self)
    btn.setToolTip('Run Simulation')
    btn.resize(btn.sizeHint())
    btn.clicked.connect(self.controlsim)
    self.grid.addWidget(self.btnsim, gRow, 2, 1, 1)

    self.qbtn = qbtn = QPushButton('Quit', self)
    qbtn.clicked.connect(QCoreApplication.instance().quit)
    qbtn.resize(qbtn.sizeHint())
    self.grid.addWidget(self.qbtn, gRow, 3, 1, 1)
    
  def shownetparamwin (self): bringwintotop(self.baseparamwin.netparamwin)
  def showdistparamwin (self): bringwintotop(self.erselectdistal)
  def showproxparamwin (self): bringwintotop(self.erselectprox)
  def showvisnet (self): Popen([getPyComm(), 'visnet.py', 'cells', paramf]) # nonblocking
  def showschematics (self): bringwintotop(self.schemwin)

  def addParamImageButtons (self,gRow):
    # add parameter image buttons to the GUI

    self.locbtn = QPushButton('Local Network'+os.linesep+'Connections',self)
    self.locbtn.setIcon(QIcon(lookupresource('connfig')))
    self.locbtn.clicked.connect(self.shownetparamwin)
    self.grid.addWidget(self.locbtn,gRow,0,1,1)

    self.proxbtn = QPushButton('Proximal Drive'+os.linesep+'Thalamus',self)
    self.proxbtn.setIcon(QIcon(lookupresource('proxfig')))
    self.proxbtn.clicked.connect(self.showproxparamwin)
    self.grid.addWidget(self.proxbtn,gRow,1,1,1)

    self.distbtn = QPushButton('Distal Drive NonLemniscal'+os.linesep+'Thal./Cortical Feedback',self)
    self.distbtn.setIcon(QIcon(lookupresource('distfig')))
    self.distbtn.clicked.connect(self.showdistparamwin)
    self.grid.addWidget(self.distbtn,gRow,2,1,1)

    self.netbtn = QPushButton('Model'+os.linesep+'Visualization',self)
    self.netbtn.setIcon(QIcon(lookupresource('netfig')))
    self.netbtn.clicked.connect(self.showvisnet)
    self.grid.addWidget(self.netbtn,gRow,3,1,1)

    gRow += 1

    return

    # for schematic dialog box
    self.pixConn = QPixmap(lookupresource('connfig'))
    self.pixConnlbl = ClickLabel(self)
    self.pixConnlbl.setScaledContents(True)
    #self.pixConnlbl.resize(self.pixConnlbl.size())
    self.pixConnlbl.setPixmap(self.pixConn)    
    # self.pixConnlbl.clicked.connect(self.shownetparamwin)
    self.grid.addWidget(self.pixConnlbl,gRow,0,1,1)

    self.pixProx = QPixmap(lookupresource('proxfig'))
    self.pixProxlbl = ClickLabel(self)
    self.pixProxlbl.setScaledContents(True)
    self.pixProxlbl.setPixmap(self.pixProx)
    # self.pixProxlbl.clicked.connect(self.showproxparamwin)
    self.grid.addWidget(self.pixProxlbl,gRow,1,1,1)

    self.pixDist = QPixmap(lookupresource('distfig'))
    self.pixDistlbl = ClickLabel(self)
    self.pixDistlbl.setScaledContents(True)
    self.pixDistlbl.setPixmap(self.pixDist)
    # self.pixDistlbl.clicked.connect(self.showdistparamwin)
    self.grid.addWidget(self.pixDistlbl,gRow,2,1,1)

    self.pixNet = QPixmap(lookupresource('netfig'))
    self.pixNetlbl = ClickLabel(self)
    self.pixNetlbl.setScaledContents(True)
    self.pixNetlbl.setPixmap(self.pixNet)
    # self.pixNetlbl.clicked.connect(self.showvisnet)
    self.grid.addWidget(self.pixNetlbl,gRow,3,1,1)


  def initUI (self):
    # initialize the user interface (UI)

    self.initMenu()
    self.statusBar()

    setscalegeomcenter(self, 1500, 1300) # start GUI in center of screenm, scale based on screen w x h 

    self.setWindowTitle(paramf)
    QToolTip.setFont(QFont('SansSerif', 10))        

    self.grid = grid = QGridLayout()
    #grid.setSpacing(10)

    gRow = 0

    self.addButtons(gRow)

    gRow += 1

    self.initSimCanvas(gRow)
    gRow += 2

    # store any sim just loaded in simdat's list - is this the desired behavior? or should we start empty?
    import simdat
    if 'dpl' in simdat.ddat:
      simdat.updatelsimdat(paramf,simdat.ddat['dpl']) # update lsimdat and its current sim index

    self.cbsim = QComboBox(self)
    self.populateSimCB() # populate the combobox
    self.cbsim.activated[str].connect(self.onActivateSimCB)
    self.grid.addWidget(self.cbsim, gRow, 0, 1, 3)#, 1, 3)
    self.btnrmsim = QPushButton('Remove Simulation',self)
    self.btnrmsim.resize(self.btnrmsim.sizeHint())
    self.btnrmsim.clicked.connect(self.removeSim)
    self.btnrmsim.setToolTip('Remove Currently Selected Simulation')
    self.grid.addWidget(self.btnrmsim, gRow, 3)#, 4, 1)

    gRow += 1
    self.addParamImageButtons(gRow)

    # need a separate widget to put grid on
    widget = QWidget(self)
    widget.setLayout(grid)
    self.setCentralWidget(widget);

    self.c = Communicate()
    self.c.finishSim.connect(self.done)

    try: self.setWindowIcon(QIcon(os.path.join('res','icon.png')))
    except: pass

    self.schemwin.show() # so it's underneath main window

    if 'dataf' in dconf:
      if os.path.isfile(dconf['dataf']):
        self.loadDataFile(dconf['dataf'])

    self.show()

  def onActivateSimCB (self, s):
    # load simulation when activating simulation combobox
    global paramf,dfile
    import simdat
    if debug: print('onActivateSimCB',s,paramf,self.cbsim.currentIndex(),simdat.lsimidx)
    if self.cbsim.currentIndex() != simdat.lsimidx:
      if debug: print('Loading',s)
      paramf = s
      simdat.lsimidx = self.cbsim.currentIndex()
      self.updateDatCanv(paramf)

  def populateSimCB (self):
    # populate the simulation combobox
    if debug: print('populateSimCB')
    global paramf
    self.cbsim.clear()
    import simdat
    for l in simdat.lsimdat:
      self.cbsim.addItem(l[0])
    self.cbsim.setCurrentIndex(simdat.lsimidx)

  def initSimCanvas (self,gRow=1,recalcErr=True):
    # initialize the simulation canvas, loading any required data
    try: # to avoid memory leaks remove any pre-existing widgets before adding new ones
      self.grid.removeWidget(self.m)
      self.grid.removeWidget(self.toolbar)
      self.m.setParent(None)
      self.toolbar.setParent(None)
      self.m = self.toolbar = None
    except:
      pass
    if debug: print('paramf in initSimCanvas:',paramf)
    self.m = SIMCanvas(paramf, parent = self, width=10, height=1, dpi=getmplDPI()) # also loads data
    # this is the Navigation widget
    # it takes the Canvas widget and a parent
    self.toolbar = NavigationToolbar(self.m, self)
    gCol = 0
    gWidth = 4
    self.grid.addWidget(self.toolbar, gRow, gCol, 1, gWidth); 
    self.grid.addWidget(self.m, gRow + 1, gCol, 1, gWidth); 
    if len(self.dextdata.keys()) > 0:
      import simdat
      simdat.ddat['dextdata'] = self.dextdata
      self.m.plotextdat(recalcErr)
      # self.m.plotsimdat()
      self.m.draw()

  def setcursors (self,cursor):
    # set cursors of self and children
    self.setCursor(cursor)
    self.update()
    kids = self.children()
    kids.append(self.m) # matplotlib simcanvas
    for k in kids:
      try:
        k.setCursor(cursor)
        k.update()
      except:
        pass

  def startoptmodel (self):
    # start model optimization
    if self.runningsim:
      self.stopsim() # stop sim works but leaves subproc as zombie until this main GUI thread exits
    else:
      self.optmodel(self.baseparamwin.runparamwin.getntrial(),self.baseparamwin.runparamwin.getncore())

  def controlsim (self):
    # control the simulation
    if self.runningsim:
      self.stopsim() # stop sim works but leaves subproc as zombie until this main GUI thread exits
    else:
      self.startsim(self.baseparamwin.runparamwin.getntrial(),self.baseparamwin.runparamwin.getncore())

  def controlNSGsim (self):
    # control simulation on NSG
    if self.runningsim:
      self.stopsim() # stop sim works but leaves subproc as zombie until this main GUI thread exits
    else:
      self.startsim(self.baseparamwin.runparamwin.getntrial(),self.baseparamwin.runparamwin.getncore(),True)

  def stopsim (self):
    # stop the simulation
    if self.runningsim:
      self.waitsimwin.hide()
      print('Terminating simulation. . .')
      self.statusBar().showMessage('Terminating sim. . .')
      self.runningsim = False
      self.runthread.stop() # killed = True # terminate()
      self.btnsim.setText("Start Simulation")
      self.qbtn.setEnabled(True)
      self.statusBar().showMessage('')
      self.setcursors(Qt.ArrowCursor)

  def optmodel (self, ntrial, ncore):
    # optimize the model
    self.setcursors(Qt.WaitCursor)
    print('Starting model optimization. . .')

    if debug: print('in optmodel')
    self.runningsim = True

    self.statusBar().showMessage("Optimizing model. . .")
    self.btnsim.setText("Stop Optimization") 
    self.qbtn.setEnabled(False)

    self.runthread = RunSimThread(self.c, ntrial, ncore, self.waitsimwin, opt=True, baseparamwin=self.baseparamwin, mainwin=self, onNSG=False)

    # We have all the events we need connected we can start the thread
    self.runthread.start()
    # At this point we want to allow user to stop/terminate the thread
    # so we enable that button
    self.btnsim.setText("Stop Optimization") 
    self.qbtn.setEnabled(False)
    bringwintotop(self.waitsimwin)

  def startsim (self, ntrial, ncore, onNSG=False):
    # start the simulation
    if not self.baseparamwin.saveparams(): return # make sure params saved and ok to run

    self.setcursors(Qt.WaitCursor)

    print('Starting simulation. . .')
    self.runningsim = True

    if onNSG:
      self.statusBar().showMessage("Running simulation on Neuroscience Gateway Portal. . .")
    else:
      self.statusBar().showMessage("Running simulation. . .")

    self.runthread=RunSimThread(self.c,ntrial,ncore,self.waitsimwin,opt=False,baseparamwin=None,mainwin=None,onNSG=onNSG)

    # We have all the events we need connected we can start the thread
    self.runthread.start()
    # At this point we want to allow user to stop/terminate the thread
    # so we enable that button
    self.btnsim.setText("Stop Simulation") # setEnabled(False)
    # We don't want to enable user to start another thread while this one is
    # running so we disable the start button.
    # self.btn_start.setEnabled(False)
    self.qbtn.setEnabled(False)

    bringwintotop(self.waitsimwin)

  def done (self):
    # called when the simulation completes running
    if debug: print('done')
    self.runningsim = False
    self.waitsimwin.hide()
    self.statusBar().showMessage("")
    self.btnsim.setText("Start Simulation")
    self.qbtn.setEnabled(True)
    self.initSimCanvas() # recreate canvas (plots too) to avoid incorrect axes
    # self.m.plot()
    global basedir
    basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
    self.setcursors(Qt.ArrowCursor)
    QMessageBox.information(self, "Done!", "Finished running sim using " + paramf + '. Saved data/figures in: ' + basedir)
    self.setWindowTitle(paramf)
    self.populateSimCB() # populate the combobox

if __name__ == '__main__':    
  app = QApplication(sys.argv)
  ex = HNNGUI()
  sys.exit(app.exec_())  
