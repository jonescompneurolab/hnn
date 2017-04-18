#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QToolTip, QPushButton, QFormLayout
from PyQt5.QtWidgets import QMenu, QSizePolicy, QMessageBox, QWidget, QFileDialog, QComboBox, QTabWidget
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QDialog, QGridLayout, QLineEdit, QLabel
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal, QObject, pyqtSlot
from PyQt5 import QtCore
import multiprocessing
from subprocess import Popen, PIPE, call
import shlex
from time import time, clock, sleep
import pickle, tempfile
from conf import readconf, setfcfg, fcfg, dconf
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import random
from math import ceil
import spikefn
import params_default
from paramrw import quickreadprm
from simdat import *

prtime = True

simf = dconf['simf']
paramf = dconf['paramf']

ncore = multiprocessing.cpu_count()

# based on https://nikolak.com/pyqt-threading-tutorial/
class RunSimThread (QThread):
  def __init__ (self,c):
    QThread.__init__(self)
    self.c = c
    self.killed = False
    self.proc = None

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

  # run sim command via mpi, then delete the temp file. returns job index and fitness.
  def runsim (self):
    global ddat,dfile
    self.killed = False
    print("Running simulation using",ncore,"cores.")
    cmd = 'mpiexec -np ' + str(ncore) + ' nrniv -python -mpi ' + simf + ' ' + paramf
    maxruntime = 1200 # 20 minutes - will allow terminating sim later
    dfile = getinputfiles(paramf)
    cmdargs = shlex.split(cmd)
    print("cmd:",cmd,"cmdargs:",cmdargs)
    if prtime:
      self.proc = Popen(cmdargs,cwd=os.getcwd())
    else:
      self.proc = Popen(cmdargs,stdout=PIPE,stderr=PIPE,cwd=os.getcwd())
    if debug: print("proc:",self.proc)
    cstart = time(); 
    while not self.killed and self.proc.poll() is None: # job is not done
      sleep(1)
      cend = time(); rtime = cend - cstart
      if rtime >= maxruntime:
        self.killed = True
        print(' ran for ' , round(rtime,2) , 's. too slow , killing.')
        self.killproc()
    if not self.killed:
      try: self.proc.communicate() # avoids deadlock due to stdout/stderr buffer overfill
      except: print('could not communicate') # Process finished.
      # no output to read yet
      try: # lack of output file may occur if invalid param values lead to an nrniv crash
        ddat['dpl'] = np.loadtxt(dfile['dpl'])
        ddat['spec'] = np.load(dfile['spec'])
        ddat['spk'] = np.loadtxt(dfile['spk'])
        print("Read simulation outputs:",dfile.values())
      except:
        print('WARN: could not read simulation outputs:',dfile.values())
    else:
      self.killproc()

# for signaling
class Communicate (QObject):    
  finishSim = pyqtSignal()

# DictDialog - dictionary-based dialog with tabs - should make all dialogs
# specifiable via cfg file format - then can customize gui without changing py code
# and can reduce code explosion / overlap between dialogs 
class DictDialog (QDialog):

  def __init__ (self, parent, din):
    super(DictDialog, self).__init__(parent)
    self.ldict = [] # subclasses should override
    self.ltitle = []
    self.stitle = ''
    self.initd()
    self.initUI()
    self.setfromdin(din) # set values from input dictionary

  def __str__ (self):
    s = ''
    for k,v in self.dqline.items(): s += k + ': ' + v.text().strip() + '\n'
    return s

  def saveparams (self): self.hide()

  def initd (self): pass # implemented in subclass

  def setfromdin (self,din):
    if not din: return
    for k1,v1 in din.items():
      for k in self.dqline.keys():
        if k1 == k:
          self.dqline[k].setText(str(v1).strip())

  def initUI (self):         
    self.layout = QVBoxLayout(self)

    # Add stretch to separate the form layout from the button
    self.layout.addStretch(1)

    # Initialize tab screen
    self.ltabs = []
    self.tabs = QTabWidget(); self.layout.addWidget(self.tabs)

    for i in range(len(self.ldict)): self.ltabs.append(QWidget())

    self.tabs.resize(400,200) 

    # create tabs and their layouts
    for tab,s in zip(self.ltabs,self.ltitle):
      self.tabs.addTab(tab,s)
      tab.layout = QFormLayout()
      tab.setLayout(tab.layout)

    self.dqline = {}
    for d,tab in zip(self.ldict, self.ltabs):
      for k,v in d.items():
        self.dqline[k] = QLineEdit(self)
        self.dqline[k].setText(str(v))
        tab.layout.addRow(k,self.dqline[k])

    # Add tabs to widget        
    self.layout.addWidget(self.tabs)
    self.setLayout(self.layout)
 
    # Create a horizontal box layout to hold the button
    self.button_box = QHBoxLayout()
 
    self.btnok = QPushButton('OK',self)
    self.btnok.resize(self.btnok.sizeHint())
    self.btnok.clicked.connect(self.saveparams)
    self.button_box.addWidget(self.btnok)

    self.btncancel = QPushButton('Cancel',self)
    self.btncancel.resize(self.btncancel.sizeHint())
    self.btncancel.clicked.connect(self.hide)
    self.button_box.addWidget(self.btncancel)

    self.layout.addLayout(self.button_box)

    self.setGeometry(150, 150, 450, 300)
    self.setWindowTitle(self.stitle)  

# widget to specify ongoing input params (proximal, distal)
class OngoingInputParamDialog (DictDialog):
  def __init__ (self, parent, inty, din=None):
    self.inty = inty
    if self.inty.startswith('Proximal'):
      self.prefix = 'input_prox_A_'
      self.postfix = '_prox'
    else:
      self.prefix = 'input_dist_A_'
      self.postfix = '_dist'
    super(OngoingInputParamDialog, self).__init__(parent,din)

  def initd (self):
    self.dtiming = {'distribution' + self.postfix: 'normal',
                    't0_input' + self.postfix: 1000.,
                    'tstop_input' + self.postfix: 250.,
                    'f_input' + self.postfix: 10.,
                    'f_stdev' + self.postfix: 20.,
                    'events_per_cycle' + self.postfix: 2}

    self.dL2 = {self.prefix + 'weight_L2Pyr_ampa': 0.,
                self.prefix + 'weight_L2Pyr_nmda': 0.,
                self.prefix + 'delay_L2': 0.1}

    self.dL5 = {
        self.prefix + 'weight_L5Pyr_ampa': 0.,
        self.prefix + 'weight_L5Pyr_nmda': 0.,
        self.prefix + 'delay_L5': 0.1}

    self.dInhib = {self.prefix + 'weight_inh_ampa': 0.,
                   self.prefix + 'weight_inh_nmda': 0.}

    self.ldict = [self.dtiming, self.dL2, self.dL5, self.dInhib]
    self.ltitle = ['Timing', 'Layer2', 'Layer5', 'Inhib']
    self.stitle = 'Set '+self.inty+' Inputs'

# widget to specify ongoing input params (proximal, distal)
class EvokedInputParamDialog (DictDialog):
  def __init__ (self, parent, din):
    super(EvokedInputParamDialog, self).__init__(parent,din)

  def initd (self):
    # times and stdevs for evoked responses
    self.dtiming = {'t_evprox_early': 2000.,
                    'sigma_t_evprox_early': 2.5,
                    'dt_evprox0_evdist': -1,
                    't_evdist': 2000.,
                    'sigma_t_evdist': 6.,
                    'dt_evprox0_evprox1': -1,
                    't_evprox_late': 2000.,
                    'sigma_t_evprox_late': 7.}

    # evprox (early) feed strength
    self.dproxearly = {'gbar_evprox_early_L2Pyr': 0.,
                       'gbar_evprox_early_L5Pyr': 0.,
                       'gbar_evprox_early_L2Basket': 0.,
                       'gbar_evprox_early_L5Basket': 0.,
    }

    # evprox (late) feed strength
    self.dproxlate = {'gbar_evprox_late_L2Pyr': 0.,
                      'gbar_evprox_late_L5Pyr': 0.,
                      'gbar_evprox_late_L2Basket': 0.,
                      'gbar_evprox_late_L5Basket': 0.,
    }

    # evdist feed strengths
    self.ddist = {'gbar_evdist_L2Pyr': 0.,
                  'gbar_evdist_L5Pyr': 0.,
                  'gbar_evdist_L2Basket': 0.,
    }

    self.ldict = [self.dtiming, self.dproxearly, self.dproxlate, self.ddist]
    self.ltitle = ['Timing', 'Proximal Early', 'Proximal Late', 'Distal']
    self.stitle = 'Set Evoked Inputs'

# widget to specify run params (tstop, dt, etc.) -- not many params here
class RunParamDialog (DictDialog):
  def __init__ (self, parent, din = None):
    super(RunParamDialog, self).__init__(parent,din)

  def initd (self):

    self.drun = {'tstop': 250., # simulation end time (ms)
                 'dt': 0.025 # timestep
                 # cvode - not currently used by simulation
                 # ncores - add
    }

    self.drand = {'prng_seedcore_input_prox': 0,
                  'prng_seedcore_input_dist': 0,
                  'prng_seedcore_extpois': 0,
                  'prng_seedcore_extgauss': 0,
                  'prng_seedcore_evprox_early': 0,
                  'prng_seedcore_evdist': 0,
                  'prng_seedcore_evprox_late': 0,
    }

    # analysis    
    self.danalysis = {'save_spec_data': 0,
                      'f_max_spec': 40.
    }

    self.ldict = [self.drun, self.drand, self.danalysis]
    self.ltitle = ['Run', 'Randomization','Analysis']
    self.stitle = 'Set Run Parameters'


# widget to specify network parameters (number cells, weights, etc.)
class NetworkParamDialog (DictDialog):
  def __init__ (self, parent = None, din = None):
    super(NetworkParamDialog, self).__init__(parent,din)

  def initd (self):
    # number of cells
    self.dcells = {'N_pyr_x': 10,
                   'N_pyr_y': 10}

    # max conductances TO L2Pyr
    self.dL2Pyr = {
      'gbar_L2Pyr_L2Pyr_ampa': 0.,
      'gbar_L2Pyr_L2Pyr_nmda': 0.,
      'gbar_L2Basket_L2Pyr_gabaa': 0.,
      'gbar_L2Basket_L2Pyr_gabab': 0.
    }

    # max conductances TO L2Baskets
    self.dL2Bas = {
      'gbar_L2Pyr_L2Basket': 0.,
      'gbar_L2Basket_L2Basket': 0.
    }

    # max conductances TO L5Pyr
    self.dL5Pyr = {
      'gbar_L5Pyr_L5Pyr_ampa': 0.,
      'gbar_L5Pyr_L5Pyr_nmda': 0.,
      'gbar_L2Pyr_L5Pyr': 0.,
      'gbar_L2Basket_L5Pyr': 0.,
      'gbar_L5Basket_L5Pyr_gabaa': 0.,
      'gbar_L5Basket_L5Pyr_gabab': 0.
    }

    # max conductances TO L5Baskets
    self.dL5Bas = {
      'gbar_L5Basket_L5Basket': 0.,
      'gbar_L5Pyr_L5Basket': 0.,
      'gbar_L2Pyr_L5Basket': 0.,
    }  

    self.ldict = [self.dcells, self.dL2Pyr, self.dL5Pyr, self.dL2Bas, self.dL5Bas]
    self.ltitle = ['Cells', 'Layer2 Pyr', 'Layer5 Pyr', 'Layer2 Bas', 'Layer5 Bas']
    self.stitle = 'Set Network Parameters'

# base widget for specifying params (contains buttons to create other widgets
class BaseParamDialog (QDialog):

  def __init__ (self, parent):
    super(BaseParamDialog, self).__init__(parent)
    global netparamwin, proxparamwin, di
    self.proxparamwin = self.distparamwin = self.netparamwin = None
    self.initUI()
    self.runparamwin = RunParamDialog(self)
    self.netparamwin = NetworkParamDialog(self)    
    self.proxparamwin = OngoingInputParamDialog(self,'Proximal')
    self.distparamwin = OngoingInputParamDialog(self,'Distal')
    self.evparamwin = EvokedInputParamDialog(self,None)
    self.lsubwin = [self.runparamwin, self.netparamwin, self.proxparamwin, self.distparamwin, self.evparamwin]
    self.updateDispParam()

  def updateDispParam (self):
    # now update the GUI components to reflect the param file selected
    din = quickreadprm(paramf)
    ddef = params_default.get_params_default()
    for dlg in self.lsubwin: dlg.setfromdin(ddef) # first set to default?
    for dlg in self.lsubwin: dlg.setfromdin(din) # then update to values from file

  def setnetparam (self): self.netparamwin.show()
  def setproxparam (self): self.proxparamwin.show()
  def setdistparam (self): self.distparamwin.show()
  def setevparam (self): self.evparamwin.show()
  def setrunparam (self): self.runparamwin.show()

  def initUI (self):

    grid = QGridLayout()
    grid.setSpacing(10)

    row = 1

    self.lbl = QLabel(self)
    self.lbl.setText('Simulation name:')
    self.lbl.adjustSize()
    grid.addWidget(self.lbl, row, 0)
    self.qle = QLineEdit(self)
    self.qle.setText(paramf.split(os.path.sep)[-1].split('.param')[0])
    grid.addWidget(self.qle, row, 1)
    row+=1

    self.btnrun = QPushButton('Set Run Parameters',self)
    self.btnrun.resize(self.btnrun.sizeHint())
    self.btnrun.clicked.connect(self.setrunparam)
    grid.addWidget(self.btnrun, row, 0, 1, 2); row+=1

    self.btnnet = QPushButton('Set Network Parameters',self)
    self.btnnet.resize(self.btnnet.sizeHint())
    self.btnnet.clicked.connect(self.setnetparam)
    grid.addWidget(self.btnnet, row, 0, 1, 2); row+=1

    self.btnprox = QPushButton('Set Ongoing Proximal Inputs',self)
    self.btnprox.resize(self.btnprox.sizeHint())
    self.btnprox.clicked.connect(self.setproxparam)
    grid.addWidget(self.btnprox, row, 0, 1, 2); row+=1

    self.btndist = QPushButton('Set Ongoing Distal Inputs',self)
    self.btndist.resize(self.btndist.sizeHint())
    self.btndist.clicked.connect(self.setdistparam)
    grid.addWidget(self.btndist, row, 0, 1, 2); row+=1

    self.btnev = QPushButton('Set Evoked Inputs',self)
    self.btnev.resize(self.btnev.sizeHint())
    self.btnev.clicked.connect(self.setevparam)
    grid.addWidget(self.btnev, row, 0, 1, 2); row+=1

    self.btnok = QPushButton('OK',self)
    self.btnok.resize(self.btnok.sizeHint())
    self.btnok.clicked.connect(self.saveparams)
    grid.addWidget(self.btnok, row, 0, 1, 1)
    self.btncancel = QPushButton('Cancel',self)
    self.btncancel.resize(self.btncancel.sizeHint())
    self.btncancel.clicked.connect(self.hide)
    grid.addWidget(self.btncancel, row, 1, 1, 1); row+=1

    self.setLayout(grid) 
        
    self.setGeometry(100, 100, 400, 100)
    self.setWindowTitle('Set Sim Parameters')    

  def saveparams (self):
    global paramf
    tmpf = os.path.join('param',self.qle.text() + '.param')
    print('Saving params to ',  tmpf)
    self.hide()
    oktosave = True
    if os.path.isfile(tmpf):
      oktosave = False
      msg = QMessageBox()
      msg.setIcon(QMessageBox.Warning)
      msg.setText(tmpf + ' already exists. Over-write?')
      msg.setWindowTitle('Over-write file?')
      msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)      
      if msg.exec_() == QMessageBox.Ok: oktosave = True
    if oktosave:
      try:
        with open(tmpf,'w') as fp: fp.write(str(self))
        paramf = tmpf # success? update paramf
      except:
        print('exception in saving param file ',tmpf)

  def __str__ (self):
    s = 'sim_prefix: ' + self.qle.text() + '\n'
    s += 'expmt_groups: {' + self.qle.text() + '}\n'
    for win in self.lsubwin: s += str(win)
    return s

# clickable label
class ClickLabel (QLabel):
  clicked = pyqtSignal()
  def mousePressEvent(self, event):
    self.clicked.emit()

# main GUI class
class HNNGUI (QMainWindow):

  def __init__ (self):
    global dfile, ddat, paramf
    super().__init__()        
    self.initUI()
    self.runningsim = False
    self.runthread = None
    self.baseparamwin = BaseParamDialog(self)

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

  def setparams (self):
    if self.baseparamwin:
      self.baseparamwin.show()

  def initMenu (self):
    exitAction = QAction(QIcon.fromTheme('exit'), 'Exit', self)        
    exitAction.setShortcut('Ctrl+Q')
    exitAction.setStatusTip('Exit HNN application.')
    exitAction.triggered.connect(qApp.quit)

    selParamFile = QAction(QIcon.fromTheme('open'), 'Set parameter file.', self)
    selParamFile.setShortcut('Ctrl+P')
    selParamFile.setStatusTip('Set parameter file.')
    selParamFile.triggered.connect(self.selParamFileDialog)

    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')
    menubar.setNativeMenuBar(False)
    fileMenu.addAction(selParamFile)
    fileMenu.addAction(exitAction)

  def addButtons (self, gRow):
    self.pbtn = pbtn = QPushButton('Set Parameters (Advanced)', self)
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
  def showdistparamwin (self): self.baseparamwin.distparamwin.show()
  def showproxparamwin (self): self.baseparamwin.proxparamwin.show()
  def showvisnet (self):
    Popen(['python', 'visnet.py']) # nonblocking
    """
    cmdargs = shlex.split('python visnet.py')
    proc = Popen(cmdargs,cwd=os.getcwd())
    while proc.poll() is None:
      sleep(1)
    proc.communicate()
    """

  def addParamImageButtons (self,gRow):

    self.locbtn = QPushButton('Local Network\nConnections',self)
    self.locbtn.setIcon(QIcon("res/connfig.png"))
    self.locbtn.clicked.connect(self.shownetparamwin)
    self.grid.addWidget(self.locbtn,gRow,0,1,1)

    self.proxbtn = QPushButton('Proximal Drive\nThalamus',self)
    self.proxbtn.setIcon(QIcon("res/proxfig.png"))
    self.proxbtn.clicked.connect(self.showproxparamwin)
    self.grid.addWidget(self.proxbtn,gRow,1,1,1)

    self.distbtn = QPushButton('Distal Drive\nNonLemn. Thal',self)
    self.distbtn.setIcon(QIcon("res/distfig.png"))
    self.distbtn.clicked.connect(self.showdistparamwin)
    self.grid.addWidget(self.distbtn,gRow,2,1,1)

    self.netbtn = QPushButton('Network Visualization\n',self)
    self.netbtn.setIcon(QIcon("res/netfig.png"))
    self.netbtn.clicked.connect(self.showvisnet)
    self.grid.addWidget(self.netbtn,gRow,3,1,1)

    gRow += 1

    self.pixConn = QPixmap("res/connfig.png")
    self.pixConnlbl = ClickLabel(self)
    self.pixConnlbl.setPixmap(self.pixConn)
    self.pixConnlbl.clicked.connect(self.shownetparamwin)
    self.grid.addWidget(self.pixConnlbl,gRow,0,1,1)

    self.pixProx = QPixmap("res/proxfig.png")
    self.pixProxlbl = ClickLabel(self)
    self.pixProxlbl.setPixmap(self.pixProx)
    self.pixProxlbl.clicked.connect(self.showproxparamwin)
    self.grid.addWidget(self.pixProxlbl,gRow,1,1,1)

    self.pixDist = QPixmap("res/distfig.png")
    self.pixDistlbl = ClickLabel(self)
    self.pixDistlbl.setPixmap(self.pixDist)
    self.pixDistlbl.clicked.connect(self.showdistparamwin)
    self.grid.addWidget(self.pixDistlbl,gRow,2,1,1)

    self.pixNet = QPixmap("res/netfig.png")
    self.pixNetlbl = ClickLabel(self)
    self.pixNetlbl.setPixmap(self.pixNet)
    self.pixNetlbl.clicked.connect(self.showvisnet)
    self.grid.addWidget(self.pixNetlbl,gRow,3,1,1)


  def initUI (self):       

    self.initMenu()
    self.statusBar()
    self.setGeometry(300, 300, 1200, 1100)
    self.setWindowTitle('HNN')
    QToolTip.setFont(QFont('SansSerif', 10))        

    self.grid = grid = QGridLayout()
    #grid.setSpacing(10)

    # addWidget(QWidget *widget, int fromRow, int fromColumn, int rowSpan, int columnSpan, Qt::Alignment alignment = Qt::Alignment())

    gRow = 0

    self.addButtons(gRow)

    gRow += 1

    self.mnelabel = QLabel()
    self.mnelabel.setText('MNE Viewer')
    grid.addWidget(self.mnelabel, gRow, 0, 1, 2)

    self.simlabel = QLabel()
    self.simlabel.setText('Simulation Output Viewer')
    grid.addWidget(self.simlabel, gRow, 2, 1, 2)

    gRow += 1

    self.mne = mne = QLabel() 
    self.mne.setText('MNE (To Be Added)')
    grid.addWidget(self.mne, gRow, 0, 1, 2)

    self.m = SIMCanvas(self, width=10, height=1)
    grid.addWidget(self.m, gRow, 2, 1, 2)

    gRow += 1

    self.netlabel = QLabel()
    self.netlabel.setText('Simulation Parameters')
    self.netlabel.resize(self.netlabel.sizeHint())
    grid.addWidget(self.netlabel,gRow,2,1,4)

    gRow += 1

    self.addParamImageButtons(gRow)

    self.c = Communicate()
    self.c.finishSim.connect(self.done)

    # need a separate widget to put grid on
    widget = QWidget(self)
    widget.setLayout(grid)
    self.setCentralWidget(widget);

    self.show()

  def controlsim (self):
    if self.runningsim:
      self.stopsim() # stop sim works but leaves subproc as zombie until this main GUI thread exits
    else:
      self.startsim()

  def stopsim (self):
    if self.runningsim:
      print('Terminating simulation. . .')
      self.statusBar().showMessage('Terminating sim. . .')
      self.runningsim = False
      self.runthread.stop() # killed = True # terminate()
      self.btnsim.setText("Start Simulation")
      self.qbtn.setEnabled(True)
      self.statusBar().showMessage('')

  def startsim (self):
    print('Starting simulation. . .')
    self.runningsim = True

    self.statusBar().showMessage("Running simulation. . .")

    self.runthread = RunSimThread(self.c)

    # We have all the events we need connected we can start the thread
    self.runthread.start()
    # At this point we want to allow user to stop/terminate the thread
    # so we enable that button
    self.btnsim.setText("Stop Simulation") # setEnabled(False)
    # We don't want to enable user to start another thread while this one is
    # running so we disable the start button.
    # self.btn_start.setEnabled(False)
    self.qbtn.setEnabled(False)

  def done(self):
    self.runningsim = False
    self.statusBar().showMessage("")
    self.btnsim.setText("Start Simulation")
    self.qbtn.setEnabled(True)
    self.m.plot()
    QMessageBox.information(self, "Done!", "Finished running sim using " + paramf + '. Saved data/figures in: ' + basedir)

if __name__ == '__main__':    
  app = QApplication(sys.argv)
  ex = HNNGUI()
  sys.exit(app.exec_())  
