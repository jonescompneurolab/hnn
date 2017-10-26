#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QToolTip, QPushButton, QFormLayout
from PyQt5.QtWidgets import QMenu, QSizePolicy, QMessageBox, QWidget, QFileDialog, QComboBox, QTabWidget
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QDialog, QGridLayout, QLineEdit, QLabel
from PyQt5.QtWidgets import QCheckBox, QTextEdit
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal, QObject, pyqtSlot, Qt
from PyQt5 import QtCore
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import multiprocessing
from subprocess import Popen, PIPE, call
import shlex
from collections import OrderedDict
from time import time, clock, sleep
import pickle, tempfile
from conf import dconf
import numpy as np
import random
from math import ceil
import spikefn
import params_default
from paramrw import quickreadprm, usingOngoingInputs, countEvokedInputs
from simdat import SIMCanvas, getinputfiles, readdpltrials
from gutils import scalegeom, scalefont, setscalegeom, lowresdisplay, setscalegeomcenter, getmplDPI

prtime = False

simf = dconf['simf']
paramf = dconf['paramf']
debug = dconf['debug']
testLFP = dconf['testlfp']

defncore = multiprocessing.cpu_count() # default number of cores

# for signaling
class Communicate (QObject):    
  finishSim = pyqtSignal()

# for signaling - passing text
class TextSignal (QObject):
  tsig = pyqtSignal(str)

# based on https://nikolak.com/pyqt-threading-tutorial/
class RunSimThread (QThread):
  def __init__ (self,c,ntrial,ncore,waitsimwin):
    QThread.__init__(self)
    self.c = c
    self.killed = False
    self.proc = None
    self.ntrial = ntrial
    self.ncore = ncore
    self.waitsimwin = waitsimwin

    self.txtComm = TextSignal()
    self.txtComm.tsig.connect(self.waitsimwin.updatetxt)

  def updatewaitsimwin (self, txt):
    # print('RunSimThread updatewaitsimwin, txt=',txt)
    self.txtComm.tsig.emit(txt)

  def stop (self): self.killed = True

  def __del__ (self):
    self.quit()
    self.wait()

  def run (self):
    self.runsim() # run simulation
    self.c.finishSim.emit() # send the finish signal

  def killproc (self):
    if self.proc is None: return
    print('Thread killing sim. . .')
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
    cmd = 'mpiexec -np ' + str(self.ncore) + ' nrniv -python -mpi ' + simf + ' ' + paramf + ' ntrial ' + str(self.ntrial)
    maxruntime = 1200 # 20 minutes - will allow terminating sim later
    simdat.dfile = getinputfiles(paramf)
    cmdargs = shlex.split(cmd)
    if debug: print("cmd:",cmd,"cmdargs:",cmdargs)
    if prtime:
      self.proc = Popen(cmdargs,cwd=os.getcwd())
    else: 
      #self.proc = Popen(cmdargs,stdout=PIPE,stderr=PIPE,cwd=os.getcwd()) # may want to read/display stderr too
      self.proc = Popen(cmdargs,stdout=PIPE,cwd=os.getcwd(),universal_newlines=True)
    cstart = time(); 
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
      """ do not need to set upper bound on sim run time
      cend = time(); rtime = cend - cstart
      if rtime >= maxruntime:
        self.killed = True
        print(' ran for ' , round(rtime,2) , 's. too slow , killing.')
        self.killproc()
      """
    if not self.killed:
      # no output to read yet
      try: # lack of output file may occur if invalid param values lead to an nrniv crash
        simdat.ddat['dpl'] = np.loadtxt(simdat.dfile['dpl'])
        if os.path.isfile(simdat.dfile['spec']):
          simdat.ddat['spec'] = np.load(simdat.dfile['spec'])
        else:
          simdat.ddat['spec'] = None
        simdat.ddat['spk'] = np.loadtxt(simdat.dfile['spk'])
        simdat.ddat['dpltrials'] = readdpltrials(os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0]),self.ntrial)
        if debug: print("Read simulation outputs:",simdat.dfile.values())
      except:
        print('WARN: could not read simulation outputs:',simdat.dfile.values())
    else:
      self.killproc()
    print('')

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
    nw, nh = setscalegeom(self, 150, 150, 625, 300)
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
    self.dtiming = OrderedDict([('distribution' + self.postfix, 'normal'),
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
    self.ltitle = ['Timing', 'Layer2', 'Layer5']
    self.stitle = 'Set Rhythmic '+self.inty+' Inputs'

    for d in [self.dL2, self.dL5]:
      for k in d.keys():
        lk = k.split('_')
        if k.count('weight') > 0:
          self.addtransvar(k, lk[-2]+' '+lk[-1].upper()+' weight (nS)')
        else:
          self.addtransvar(k, 'Delay (ms)')

    self.addtransvar('distribution'+self.postfix,'Distribution')
    self.addtransvar('t0_input'+self.postfix,'Start time mean (ms)')
    self.addtransvar('t0_input_stdev'+self.postfix,'Start time stdev (ms)')
    self.addtransvar('tstop_input'+self.postfix,'Stop time (ms)')
    self.addtransvar('f_input'+self.postfix,'Frequency mean (Hz)')
    self.addtransvar('f_stdev'+self.postfix,'Frequency stdev (Hz)')
    self.addtransvar('events_per_cycle'+self.postfix,'Events/cycle')
    self.addtransvar('repeats'+self.postfix,'Repeats')

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
    self.evwin.show()
    self.hide()

  def showrhythmicwin (self):
    self.rhythwin.show()
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

    for d in [self.dL2, self.dL5]:
      for k in d.keys():
        cty = k.split('_')[2]
        if k.count('A') > 0:
          self.addtransvar(k, cty + ' amplitude (nA)')
        elif k.count('t0') > 0:
          self.addtransvar(k, cty + ' start time (ms)')
        elif k.count('T') > 0:
          self.addtransvar(k, cty + ' stop time (ms)')

    self.ldict = [self.dL2, self.dL5]
    self.ltitle = ['Layer2', 'Layer5']
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

    self.dL2 = OrderedDict([('L2Pyr_Pois_A_weight', 0.),
                            ('L2Pyr_Pois_lamtha', 0.),
                            ('L2Basket_Pois_A_weight', 0.),
                            ('L2Basket_Pois_lamtha', 0.)])

    self.dL5 = OrderedDict([('L5Pyr_Pois_A_weight', 0.),
                            ('L5Pyr_Pois_lamtha', 0.),
                            ('L5Basket_Pois_A_weight', 0.),
                            ('L5Basket_Pois_lamtha', 0.)])

    self.dtiming = OrderedDict([('t0_pois', 0.),
                                ('T_pois', -1)])

    self.addtransvar('t0_pois','Start time (ms)')
    self.addtransvar('T_pois','Stop time (ms)')

    for d in [self.dL2, self.dL5]:
      for k in d.keys():
        cty = k.split('_')[0]
        if k.endswith('weight'):
          self.addtransvar(k, cty+ ' weight (nS)')
        elif k.endswith('lamtha'):
          self.addtransvar(k, cty+ ' Freq (Hz)')

    self.ldict = [self.dL2, self.dL5, self.dtiming]
    self.ltitle = ['Layer2', 'Layer5', 'Timing']
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
      if k in self.dqline:
        self.dqline[k].setText(str(v).strip())
      elif k == 'sync_evinput':
        if float(v)==0.0:
          self.chksync.setChecked(False)
        elif float(v)==1.0:
          self.chksync.setChecked(True)
      elif k == 'inc_evinput':
        self.incedit.setText(str(v).strip())
  
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
    for k in d.keys(): del self.dqline[k]
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
    for k in d.keys():
      if k.startswith('gbar'):
        self.addtransvar(k,k.split('_')[-1] + ' weight (nS)')
      elif k.startswith('t'):
        self.addtransvar(k,'Start time mean (ms)')
      elif k.startswith('sigma'):
        self.addtransvar(k,'Start time stdev (ms)')

  def addProx (self):
    self.nprox += 1 # starts at 1
    # evprox feed strength
    dprox = OrderedDict([('t_evprox_' + str(self.nprox), 0.), # times and stdevs for evoked responses
                         ('sigma_t_evprox_' + str(self.nprox), 2.5),
                         ('gbar_evprox_' + str(self.nprox) + '_L2Pyr', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L2Basket', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L5Pyr', 0.),                                   
                         ('gbar_evprox_' + str(self.nprox) + '_L5Basket', 0.)])
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
                         ('gbar_evdist_' + str(self.ndist) + '_L2Pyr', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L2Basket', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L5Pyr', 0.)])
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
                             # ('celsius',6.3), # temperature
                             ('N_trials',0)]) # number of trials
                             # cvode - not currently used by simulation

    # analysis    
    self.danalysis = OrderedDict([('save_figs',0),
                                  ('save_spec_data', 0),
                                  ('f_max_spec', 40),
                                  ('dipole_scalefctr',30e3),
                                  ('dipole_smooth_win',15.0)])#,
                                  #('save_vsoma',0)])

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
    #self.addtransvar('celsius','Temperature (C)')
    self.addtransvar('N_trials','Trials')
    self.addtransvar('save_spec_data','Save spectral data')
    self.addtransvar('save_figs','Save figures')
    self.addtransvar('f_max_spec', 'Max spectral frequency (Hz)')
    self.addtransvar('dipole_scalefctr','Dipole Scaling')
    self.addtransvar('dipole_smooth_win','Dipole Smooth Window (ms)')
    self.addtransvar('save_vsoma','Save Somatic Voltages')
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

    self.dL2PyrBiophys = OrderedDict([('L2Pyr_soma_gkbar_hh', 0.01), # Biophysics soma
                                      ('L2Pyr_soma_gnabar_hh', 0.18),
                                      ('L2Pyr_soma_el_hh', -65.),
                                      ('L2Pyr_soma_gl_hh', 4.26e-5),
                                      ('L2Pyr_soma_gbar_km', 250.),
                                      # Biophysics dends
                                      ('L2Pyr_dend_gkbar_hh', 0.01),
                                      ('L2Pyr_dend_gnabar_hh', 0.15),
                                      ('L2Pyr_dend_el_hh', -65.),
                                      ('L2Pyr_dend_gl_hh', 4.26e-5),
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

    self.dL5PyrBiophys = OrderedDict([('L5Pyr_soma_gkbar_hh', 0.01), # Biophysics soma
                                       ('L5Pyr_soma_gnabar_hh', 0.16),
                                       ('L5Pyr_soma_el_hh', -65.),
                                       ('L5Pyr_soma_gl_hh', 4.26e-5),
                                       ('L5Pyr_soma_gbar_ca', 60.),
                                       ('L5Pyr_soma_taur_cad', 20.),
                                       ('L5Pyr_soma_gbar_kca', 2e-4),
                                       ('L5Pyr_soma_gbar_km', 200.),
                                       ('L5Pyr_soma_gbar_cat', 2e-4),
                                       ('L5Pyr_soma_gbar_ar', 1e-6),
                                       # Biophysics dends
                                       ('L5Pyr_dend_gkbar_hh', 0.01),
                                       ('L5Pyr_dend_gnabar_hh', 0.14),
                                       ('L5Pyr_dend_el_hh', -71.),
                                       ('L5Pyr_dend_gl_hh', 4.26e-5),
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
          if lk[3] == 'hh': nv += '(S/cm2)'
          else: nv += '(pS/micron2)'
        elif lk[2].count('el') > 0: nv = dtrans[lk[1]] + ' leak reversal (mV)'
        self.addtransvar(k,nv)

    self.ldict = [self.dL2PyrGeom, self.dL2PyrSyn, self.dL2PyrBiophys,\
                  self.dL5PyrGeom, self.dL5PyrSyn, self.dL5PyrBiophys]
    self.ltitle = [ 'L2Pyr Geometry', 'L2Pyr Synapses', 'L2Pyr Biophysics',\
                    'L5Pyr Geometry', 'L5Pyr Synapses', 'L5Pyr Biophysics']
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
    self.ltitle = ['Cells', 'Layer2 Pyr', 'Layer5 Pyr', 'Layer2 Bas', 'Layer5 Bas']
    self.stitle = 'Local Network Parameters'

    self.addtransvar('N_pyr_x', 'Num Pyr Cells (X direction)')
    self.addtransvar('N_pyr_y', 'Num Pyr Cells (Y direction)')

    for d in [self.dL2Pyr, self.dL5Pyr, self.dL2Bas, self.dL5Bas]:
      for k in d.keys():
        lk = k.split('_')
        if len(lk) == 3:
          self.addtransvar(k,lk[1]+'->'+lk[2]+' weight (nS)')
        else:
          self.addtransvar(k,lk[1]+'->'+lk[2]+' '+lk[3].upper()+' weight (nS)')

class HelpDialog (QDialog):
  def __init__ (self, parent):
    super(HelpDialog, self).__init__(parent)
    self.initUI()

  def initUI (self):
    self.layout = QVBoxLayout(self)
    # Add stretch to separate the form layout from the button
    self.layout.addStretch(1)

    setscalegeom(self, 100, 100, 300, 100)
    self.setWindowTitle('HNN Help')    

# dialog for visualizing model
class VisnetDialog (QDialog):
  def __init__ (self, parent):
    super(VisnetDialog, self).__init__(parent)
    self.initUI()

  def showcells3D (self): Popen(['python3', 'visnet.py', 'cells', paramf]) # nonblocking
  def showEconn (self): Popen(['python3', 'visnet.py', 'Econn', paramf]) # nonblocking
  def showIconn (self): Popen(['python3', 'visnet.py', 'Iconn', paramf]) # nonblocking

  def runvisnet (self):
    lcmd = ['python3', 'visnet.py']
    if self.chkcells.isChecked(): lcmd.append('cells')
    if self.chkE.isChecked(): lcmd.append('Econn')
    if self.chkI.isChecked(): lcmd.append('Iconn')
    lcmd.append(paramf)
    Popen(lcmd) # nonblocking

  def initUI (self):

    self.layout = QVBoxLayout(self)

    # Add stretch to separate the form layout from the button
    self.layout.addStretch(1)

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

# base widget for specifying params (contains buttons to create other widgets
class BaseParamDialog (QDialog):

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
    except:
      print('could not read',paramf)
    ddef = params_default.get_params_default()
    for dlg in self.lsubwin: dlg.setfromdin(ddef) # first set to default?
    try:
      for dlg in self.lsubwin: dlg.setfromdin(din) # then update to values from file
      self.qle.setText(paramf.split(os.path.sep)[-1].split('.param')[0]) # update simulation name
    except:
      pass

  def setrunparam (self): self.runparamwin.show()
  def setcellparam (self): self.cellparamwin.show()
  def setnetparam (self): self.netparamwin.show()
  def setsyngainparam (self): self.syngainparamwin.show()
  def setproxparam (self): self.proxparamwin.show()
  def setdistparam (self): self.distparamwin.show()
  def setevparam (self): self.evparamwin.show()
  def setpoisparam (self): self.poisparamwin.show()
  def settonicparam (self): self.tonicparamwin.show()

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

  def saveparams (self):
    global paramf,basedir
    tmpf = os.path.join(dconf['paramoutdir'],self.qle.text() + '.param')
    oktosave = True
    if os.path.isfile(tmpf):
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
    stopbtn.setToolTip('Set parameters')
    stopbtn.resize(stopbtn.sizeHint())
    stopbtn.clicked.connect(self.stopsim)
    self.layout.addWidget(stopbtn)

    setscalegeomcenter(self, 500, 250)
    self.setWindowTitle("Simulation Log")

  def stopsim (self):
    self.parent().stopsim()
    self.hide()


# main GUI class
class HNNGUI (QMainWindow):

  def __init__ (self):
    global dfile, ddat, paramf
    super().__init__()        
    self.runningsim = False
    self.runthread = None
    self.dextdata = OrderedDict() # external data
    self.initUI()
    self.baseparamwin = BaseParamDialog(self)
    self.visnetwin = VisnetDialog(self)
    self.helpwin = HelpDialog(self)
    self.erselectdistal = EvokedOrRhythmicDialog(self, True, self.baseparamwin.evparamwin, self.baseparamwin.distparamwin)
    self.erselectprox = EvokedOrRhythmicDialog(self, False, self.baseparamwin.evparamwin, self.baseparamwin.proxparamwin)
    self.waitsimwin = WaitSimDialog(self)
    
  def selParamFileDialog (self):
    global paramf,dfile
    fn = QFileDialog.getOpenFileName(self, 'Open file', 'param')
    if fn[0]:
      paramf = fn[0]
      try:
        dfile = getinputfiles(paramf) # reset input data - if already exists
      except:
        pass
      # now update the GUI components to reflect the param file selected
      self.baseparamwin.updateDispParam()
      self.initSimCanvas() # recreate canvas 
      # self.m.plot() # replot data
      self.setWindowTitle('HNN - ' + paramf)

  def loadDataFileDialog (self):
    import simdat
    fn = QFileDialog.getOpenFileName(self, 'Open file', 'data')
    if fn[0]:
      try:
        self.dextdata[fn[0]] = np.loadtxt(fn[0])
        simdat.ddat['dextdata'] = self.dextdata
        print('Loaded data in ', fn[0])
      except:
        print('Could not load data in ', fn[0])
      try:
        self.m.plotextdat()
        self.m.draw() # make sure new lines show up in plot
      except:
        print('Could not plot data from ', fn[0])

  def clearDataFile (self):
    import simdat
    self.m.clearlextdatobj()
    self.dextdata = simdat.ddat['dextdata'] = OrderedDict()
    self.m.draw()

  def setparams (self):
    if self.baseparamwin:
      self.baseparamwin.show()

  def showAboutDialog (self):
    QMessageBox.information(self, "HNN", "Human Neocortical Neurosolver"+os.linesep+"https://bitbucket.org/samnemo/hnn"+os.linesep+"2017.")

  def showHelpDialog (self):
    self.helpwin.show()

  def showSomaVPlot (self): 
    global basedir
    basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
    lcmd = ['python3', 'visvolt.py',paramf]
    if debug: print('visvolt cmd:',lcmd)
    Popen(lcmd) # nonblocking

  def showPSDPlot (self):
    global basedir
    basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
    lcmd = ['python3', 'vispsd.py',paramf]
    if debug: print('vispsd cmd:',lcmd)
    Popen(lcmd) # nonblocking

  def showLFPPlot (self):
    global basedir
    basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
    lcmd = ['python3', 'vislfp.py',paramf]
    if debug: print('vislfp cmd:',lcmd)
    Popen(lcmd) # nonblocking

  def showSpecPlot (self):
    lcmd = ['python3', 'visspec.py']
    if debug: print('visspec cmd:',lcmd)
    Popen(lcmd) # nonblocking

  def showRasterPlot (self):
    global basedir
    basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
    lcmd = ['python3', 'visrast.py',paramf,os.path.join(basedir,'spk.txt')]
    if dconf['drawindivrast']: lcmd.append('indiv')
    if debug: print('visrast cmd:',lcmd)
    Popen(lcmd) # nonblocking

  def showDipolePlot (self):
    global basedir
    basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
    lcmd = ['python3', 'visdipole.py',paramf,os.path.join(basedir,'dpl.txt')]
    if debug: print('visdipole cmd:',lcmd)
    Popen(lcmd) # nonblocking    

  def showwaitsimwin (self):
    self.waitsimwin.show()

  def initMenu (self):
    exitAction = QAction(QIcon.fromTheme('exit'), 'Exit', self)        
    exitAction.setShortcut('Ctrl+Q')
    exitAction.setStatusTip('Exit HNN application.')
    exitAction.triggered.connect(qApp.quit)

    selParamFile = QAction(QIcon.fromTheme('open'), 'Set parameter file.', self)
    selParamFile.setShortcut('Ctrl+P')
    selParamFile.setStatusTip('Set parameter file.')
    selParamFile.triggered.connect(self.selParamFileDialog)

    loadDataFile = QAction(QIcon.fromTheme('open'), 'Load data file.', self)
    loadDataFile.setShortcut('Ctrl+D')
    loadDataFile.setStatusTip('Load (dipole) data file.')
    loadDataFile.triggered.connect(self.loadDataFileDialog)

    clearDataFileAct = QAction(QIcon.fromTheme('close'), 'Clear data file.', self)
    clearDataFileAct.setShortcut('Ctrl+C')
    clearDataFileAct.setStatusTip('Clear (dipole) data file.')
    clearDataFileAct.triggered.connect(self.clearDataFile)

    runSimAct = QAction('Run simulation.', self)
    runSimAct.setShortcut('Ctrl+S')
    runSimAct.setStatusTip('Run simulation.')
    runSimAct.triggered.connect(self.controlsim)

    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')
    menubar.setNativeMenuBar(False)
    fileMenu.addAction(runSimAct)
    fileMenu.addAction(selParamFile)
    fileMenu.addAction(loadDataFile)
    fileMenu.addAction(clearDataFileAct)
    fileMenu.addAction(exitAction)

    # view menu - drawing/visualization
    viewMenu = menubar.addMenu('&View')
    viewDipoleAction = QAction('View Simulation Dipoles',self)
    viewDipoleAction.setStatusTip('View Simulation Dipoles.')
    viewDipoleAction.triggered.connect(self.showDipolePlot)
    viewMenu.addAction(viewDipoleAction)
    viewRasterAction = QAction('View Simulation Spiking Activity',self)
    viewRasterAction.setStatusTip('View Simulation Raster Plot.')
    viewRasterAction.triggered.connect(self.showRasterPlot)
    viewMenu.addAction(viewRasterAction)
    viewPSDAction = QAction('View PSD',self)
    viewPSDAction.setStatusTip('View PSD.')
    viewPSDAction.triggered.connect(self.showPSDPlot)
    viewMenu.addAction(viewPSDAction)

    if testLFP:
      viewLFPAction = QAction('View Simulation LFPs',self)
      viewLFPAction.setStatusTip('View LFP.')
      viewLFPAction.triggered.connect(self.showLFPPlot)
      viewMenu.addAction(viewLFPAction)

    viewSpecAction = QAction('View Experiment Spectrograms',self)
    viewSpecAction.setStatusTip('View Spectrograms/Dipoles from Experimental Data.')
    viewSpecAction.triggered.connect(self.showSpecPlot)
    viewMenu.addAction(viewSpecAction)
    viewNetAction = QAction('View Local Network (3D)',self)
    viewNetAction.setStatusTip('View Local Network Model (3D).')
    viewNetAction.triggered.connect(self.showvisnet)
    viewMenu.addAction(viewNetAction)
    viewSimLogAction = QAction('View Simulation Log',self)
    viewSimLogAction.setStatusTip('View Detailed Simulation Logging.')
    viewSimLogAction.triggered.connect(self.showwaitsimwin)
    viewMenu.addAction(viewSimLogAction)

    aboutMenu = menubar.addMenu('&About')
    aboutAction = QAction('About HNN.',self)
    aboutAction.setStatusTip('About HNN.')
    aboutAction.triggered.connect(self.showAboutDialog)
    aboutMenu.addAction(aboutAction)
    helpAction = QAction('Help',self)
    helpAction.setStatusTip('Help on how to use HNN (parameters).')
    helpAction.triggered.connect(self.showHelpDialog)
    #aboutMenu.addAction(helpAction)

  def addButtons (self, gRow):
    self.pbtn = pbtn = QPushButton('Set Parameters', self)
    pbtn.setToolTip('Set parameters')
    pbtn.resize(pbtn.sizeHint())
    pbtn.clicked.connect(self.setparams)
    self.grid.addWidget(self.pbtn, gRow, 0, 1, 1)

    self.pfbtn = pfbtn = QPushButton('Set Parameters From File', self)
    pfbtn.setToolTip('Set Parameters From File')
    pfbtn.resize(pfbtn.sizeHint())
    pfbtn.clicked.connect(self.selParamFileDialog)
    self.grid.addWidget(self.pfbtn, gRow, 1, 1, 1)

    self.btnsim = btn = QPushButton('Run Simulation', self)
    btn.setToolTip('Run simulation')
    btn.resize(btn.sizeHint())
    btn.clicked.connect(self.controlsim)
    self.grid.addWidget(self.btnsim, gRow, 2, 1, 1)

    self.qbtn = qbtn = QPushButton('Quit', self)
    qbtn.clicked.connect(QCoreApplication.instance().quit)
    qbtn.resize(qbtn.sizeHint())
    self.grid.addWidget(self.qbtn, gRow, 3, 1, 1)

    
  def shownetparamwin (self): self.baseparamwin.netparamwin.show()
  def showdistparamwin (self):
    self.erselectdistal.show()
    #self.baseparamwin.evparamwin.show()
    #self.baseparamwin.evparamwin.tabs.setCurrentIndex(1)
  def showproxparamwin (self):
    self.erselectprox.show()
    #self.baseparamwin.evparamwin.show()
    #self.baseparamwin.evparamwin.tabs.setCurrentIndex(0)
  def showvisnet (self): self.visnetwin.show() 

  def addParamImageButtons (self,gRow):

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

    self.netbtn = QPushButton('Model Visualization',self)
    self.netbtn.setIcon(QIcon(lookupresource('netfig')))
    self.netbtn.clicked.connect(self.showvisnet)
    self.grid.addWidget(self.netbtn,gRow,3,1,1)

    gRow += 1

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

    self.initMenu()
    self.statusBar()

    setscalegeomcenter(self, 1300, 1100) # start GUI in center of screen

    self.setWindowTitle('HNN - ' + paramf)
    QToolTip.setFont(QFont('SansSerif', 10))        

    self.grid = grid = QGridLayout()
    #grid.setSpacing(10)

    # addWidget(QWidget *widget, int fromRow, int fromColumn, int rowSpan, int columnSpan, Qt::Alignment alignment = Qt::Alignment())

    gRow = 0

    self.addButtons(gRow)

    gRow += 1

    """
    self.mne = mne = QLabel() 
    self.mne.setText('MNE (To Be Added)')
    grid.addWidget(self.mne, gRow, 0, 1, 2)
    """
    self.initSimCanvas(gRow)
    gRow += 2

    self.addParamImageButtons(gRow)

    self.c = Communicate()
    self.c.finishSim.connect(self.done)

    # need a separate widget to put grid on
    widget = QWidget(self)
    widget.setLayout(grid)
    self.setCentralWidget(widget);

    self.show()

  def initSimCanvas (self,gRow=1):
    try: # to avoid memory leaks remove any pre-existing widgets before adding new ones
      self.grid.removeWidget(self.m)
      self.grid.removeWidget(self.toolbar)
      self.m.setParent(None)
      self.toolbar.setParent(None)
      self.m = self.toolbar = None
    except:
      pass
    if debug: print('paramf in initSimCanvas:',paramf)
    self.m = SIMCanvas(paramf, parent = self, width=10, height=1, dpi=getmplDPI())
    # this is the Navigation widget
    # it takes the Canvas widget and a parent
    gCol = 0 # 2
    gWidth = 4 # 2
    self.toolbar = NavigationToolbar(self.m, self)
    self.grid.addWidget(self.toolbar, gRow, gCol, 1, gWidth); 
    self.grid.addWidget(self.m, gRow + 1, gCol, 1, gWidth); 
    if len(self.dextdata.keys()) > 0:
      import simdat
      simdat.ddat['dextdata'] = self.dextdata
      self.m.plotextdat()
      self.m.draw()

  # set cursors of self and children
  def setcursors (self,cursor):
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

  def controlsim (self):
    if self.runningsim:
      self.stopsim() # stop sim works but leaves subproc as zombie until this main GUI thread exits
    else:
      self.startsim(self.baseparamwin.runparamwin.getntrial(),self.baseparamwin.runparamwin.getncore())

  def stopsim (self):
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

  def startsim (self, ntrial, ncore):

    if not self.baseparamwin.saveparams(): return # make sure params saved and ok to run

    self.setcursors(Qt.WaitCursor)

    print('Starting simulation. . .')
    self.runningsim = True

    self.statusBar().showMessage("Running simulation. . .")

    self.runthread = RunSimThread(self.c, ntrial, ncore, self.waitsimwin)

    # We have all the events we need connected we can start the thread
    self.runthread.start()
    # At this point we want to allow user to stop/terminate the thread
    # so we enable that button
    self.btnsim.setText("Stop Simulation") # setEnabled(False)
    # We don't want to enable user to start another thread while this one is
    # running so we disable the start button.
    # self.btn_start.setEnabled(False)
    self.qbtn.setEnabled(False)

    self.waitsimwin.show()

  def done (self):
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
    self.setWindowTitle('HNN - ' + paramf)

if __name__ == '__main__':    
  app = QApplication(sys.argv)
  ex = HNNGUI()
  sys.exit(app.exec_())  
