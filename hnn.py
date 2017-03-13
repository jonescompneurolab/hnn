#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QToolTip, QPushButton, QFormLayout
from PyQt5.QtWidgets import QMenu, QSizePolicy, QMessageBox, QWidget, QFileDialog, QComboBox, QTabWidget
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QDialog, QGridLayout, QLineEdit, QLabel
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal, QObject, pyqtSlot
from PyQt5 import QtCore
import multiprocessing
from subprocess import Popen, PIPE, call
import shlex
from time import time, clock, sleep
import pickle, tempfile
from conf import readconf
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import random
from math import ceil
import spikefn

ncore = multiprocessing.cpu_count()

"""
# backup the config file
def backupcfg (simstr):
  safemkdir('backupcfg')
  fout = 'backupcfg/' + simstr + '.cfg'
  if os.path.exists(fout):
    print 'removing prior cfg file' , fout
    os.system('rm ' + fout)  
  os.system('cp ' + fcfg + ' ' + fout) # fcfg created in geom.py via conf.py
"""

# determine config file name
def setfcfg ():
  fcfg = "hnn.cfg" # default config file name
  for i in range(len(sys.argv)):
    if sys.argv[i].endswith(".cfg") and os.path.exists(sys.argv[i]):
      fcfg = sys.argv[i]
  print("hnn config file is " , fcfg)
  return fcfg

fcfg = setfcfg() # config file name
dconf = readconf(fcfg)
simf = dconf['simf']
paramf = dconf['paramf']

debug = True
prtime = True

ddat = {}
dfile = {}

def getinputfiles (paramf):
  global dfile,basedir
  dfile = {}
  basedir = os.path.join('data',paramf.split(os.path.sep)[-1].split('.param')[0])
  dfile['dpl'] = os.path.join(basedir,'dpl.txt')
  dfile['spec'] = os.path.join(basedir,'rawspec.npz')
  dfile['spk'] = os.path.join(basedir,'spk.txt')
  dfile['outparam'] = os.path.join(basedir,'param.txt')
  return dfile

if debug:
  try:
    getinputfiles(paramf)
    ddat['dpl'] = np.loadtxt(dfile['dpl']);
    ddat['spec'] = np.load(dfile['spec']); 
    ddat['spk'] = np.loadtxt(dfile['spk']); 
  except:
    pass

# based on https://nikolak.com/pyqt-threading-tutorial/
class RunSimThread (QThread):
  def __init__ (self,c):
    QThread.__init__(self)
    self.c = c
    self.killed = False
    self.proc = None

  def stop (self):
    self.killed = True

  def __del__ (self):
    self.quit()
    self.wait()

  def run (self):
    self.runsim() # your logic here
    self.c.finishSim.emit()

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

# from https://pythonspot.com/pyqt5-tabs/
class OngoingInputTab (QWidget):

  def __init__ (self, parent,inty):   
    super(QWidget, self).__init__(parent)
    self.inty = inty
    if self.inty.startswith('prox'): self.prefix = 'input_prox_A_'
    else: self.prefix = 'input_dist_A_'
    self.initd()
    self.initUI()

  def initd (self):
    self.dtiming = {'distribution_prox': 'normal',
                    't0_input_prox': 1000.,
                    'tstop_input_prox': 250.,
                    'f_input_prox': 10.,
                    'f_stdev_prox': 20.,
                    'events_per_cycle_prox': 2}
    self.dL2 = {self.prefix + 'L2Pyr_ampa': 0.,
                self.prefix + 'L2Pyr_nmda': 0.,
                self.prefix + 'delay_L2': 0.1}
    self.dL5 = {
        self.prefix + 'L5Pyr_ampa': 0.,
        self.prefix + 'L5Pyr_nmda': 0.,
        self.prefix + 'delay_L5': 0.1}
    self.dInhib = {self.prefix + 'weight_inh_ampa': 0.,
                   self.prefix + 'weight_inh_nmda': 0.}

  def initUI (self):
    self.layout = QVBoxLayout()

    # Initialize tab screen
    self.ltabs = []
    self.tabs = QTabWidget()
    self.tabTiming = QWidget()	
    self.tabL2 = QWidget()
    self.tabL5 = QWidget()
    self.tabInhib = QWidget()
    self.tabs.resize(300,200) 

    # Add tabs
    self.tabs.addTab(self.tabTiming,"Timing"); 
    self.tabs.addTab(self.tabL2,"Layer 2")
    self.tabs.addTab(self.tabL5,"Layer 5")
    self.tabs.addTab(self.tabInhib,"Inhib")
  
    self.ltabs = [self.tabTiming, self.tabL2, self.tabL5, self.tabInhib]

    # Create first tab
    for tab in self.ltabs:
      tab.layout = QFormLayout()
      tab.setLayout(tab.layout)

    self.lqline = []
    for d,tab in zip([self.dtiming,self.dL2,self.dL5,self.dInhib],self.ltabs):
      for k,v in d.items():
        self.lqline.append(QLineEdit(self))
        self.lqline[-1].setText(str(v))
        tab.layout.addRow(k,self.lqline[-1])

    # Add tabs to widget        
    self.layout.addWidget(self.tabs)
    self.setLayout(self.layout)

  @pyqtSlot()
  def on_click(self):
    print("\n")
    for currentQTableWidgetItem in self.tableWidget.selectedItems():
      print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())


# widget to specify ongoing input params (proximal, distal)
class OngoingInputParamDialog (QDialog):
  def __init__ (self, parent, inty):
    super(OngoingInputParamDialog, self).__init__(parent)
    self.inty = inty
    self.dprm = {}
    self.initUI()




  def writeparams (self):
    print("OngoingInputParamDialog: set params for saving to ",paramf)

  def initUI (self):         
    self.layout = QVBoxLayout(self)

    # Add stretch to separate the form layout from the button
    self.layout.addStretch(1)

    self.tabwidget = OngoingInputTab(self,self.inty)
    self.layout.addWidget(self.tabwidget)
 
    # Create a horizontal box layout to hold the button
    self.button_box = QHBoxLayout()
 
    self.btnok = QPushButton('OK',self)
    self.btnok.resize(self.btnok.sizeHint())
    self.btnok.clicked.connect(self.writeparams)
    self.button_box.addWidget(self.btnok)

    self.btncancel = QPushButton('Cancel',self)
    self.btncancel.resize(self.btncancel.sizeHint())
    self.btncancel.clicked.connect(self.hide)
    self.button_box.addWidget(self.btncancel)

    self.layout.addLayout(self.button_box)

    self.setGeometry(150, 150, 400, 300)
    self.setWindowTitle('Set '+self.inty+' Inputs')    
    self.show()

# widget to specify ongoing input params (proximal, distal)
class NetworkParamDialog (QDialog):
  def __init__ (self, parent):
    super(NetworkParamDialog, self).__init__(parent)
    self.initd()
    self.initUI()

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

  def saveparams (self):
    print("NetworkParamDialog: setting params for saving to ",paramf)

  def initUI (self):         
    self.layout = QVBoxLayout(self)

    # Add stretch to separate the form layout from the button
    self.layout.addStretch(1)

    # Initialize tab screen
    self.ltabs = []
    self.tabs = QTabWidget(); self.layout.addWidget(self.tabs)
    self.tabCells = QWidget()
    self.tabL2Pyr = QWidget()
    self.tabL5Pyr = QWidget()
    self.tabL2Bas = QWidget()
    self.tabL5Bas = QWidget()
    self.tabs.resize(500,200) 

    # Add tabs
    self.tabs.addTab(self.tabCells,"Cells"); 
    self.tabs.addTab(self.tabL2Pyr,"Layer 2 Pyr")
    self.tabs.addTab(self.tabL5Pyr,"Layer 5 Pyr")
    self.tabs.addTab(self.tabL2Bas,"Layer 2 Bas")
    self.tabs.addTab(self.tabL5Bas,"Layer 5 Bas")
  
    self.ltabs = [self.tabCells, self.tabL2Pyr, self.tabL5Pyr, self.tabL2Bas, self.tabL5Bas]

    # Create first tab
    for tab in self.ltabs:
      tab.layout = QFormLayout()
      tab.setLayout(tab.layout)

    self.lqline = []
    for d,tab in zip(self.ldict, self.ltabs):
      for k,v in d.items():
        self.lqline.append(QLineEdit(self))
        self.lqline[-1].setText(str(v))
        tab.layout.addRow(k,self.lqline[-1])

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

    self.setGeometry(150, 150, 400, 300)
    self.setWindowTitle('Set Network Parameters')
    self.show()


# base widget for specifying params (contains buttons to create other widgets
class BaseParamDialog (QDialog):

  def __init__ (self, parent):
    super(BaseParamDialog, self).__init__(parent)
    self.proxparamwin = self.distparamwin = self.netparamwin = None
    self.initUI()

  def setnetparam (self):
    if self.netparamwin:
      self.netparamwin.show()
    else:
      self.netparamwin = NetworkParamDialog(self)

  def setproxparam (self):
    if self.proxparamwin:
      self.proxparamwin.show()
    else:
      self.proxparamwin = OngoingInputParamDialog(self,'Proximal')

  def setdistparam (self):
    if self.distparamwin:
      self.distparamwin.show()
    else:
      self.distparamwin = OngoingInputParamDialog(self,'Distal')

  def onChangeSimName(self, text):        
    self.lbl.setText(text)
    self.lbl.adjustSize()      

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
    self.qle.textChanged[str].connect(self.onChangeSimName)
    grid.addWidget(self.qle, row, 1)
    row+=1

    self.btnnet = QPushButton('Set Network Params',self)
    self.btnnet.resize(self.btnnet.sizeHint())
    self.btnnet.clicked.connect(self.setnetparam)
    grid.addWidget(self.btnnet, row, 0, 1, 2); row+=1

    self.btnprox = QPushButton('Set Proximal Inputs',self)
    self.btnprox.resize(self.btnprox.sizeHint())
    self.btnprox.clicked.connect(self.setproxparam)
    grid.addWidget(self.btnprox, row, 0, 1, 2); row+=1

    self.btndist = QPushButton('Set Distal Inputs',self)
    self.btndist.resize(self.btndist.sizeHint())
    self.btndist.clicked.connect(self.setdistparam)
    grid.addWidget(self.btndist, row, 0, 1, 2); row+=1

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
    self.show()

  def saveparams (self):
    print('Saving params to ', os.path.join('param',self.qle.text() + '.param') )

class HNNGUI (QMainWindow):

  def __init__ (self):
    global dfile, ddat, paramf
    super().__init__()        
    self.initUI()
    self.runningsim = False
    self.runthread = None
    self.baseparamwin = None

  def selParamFileDialog (self):
    global paramf,dfile
    fn = QFileDialog.getOpenFileName(self, 'Open file', 'param')
    if fn[0]:
      paramf = fn[0]
      try:
        dfile = getinputfiles(paramf) # reset input data - if already exists
      except:
        pass

  def setparams (self):
    if self.baseparamwin:
      self.baseparamwin.show()
    else:
      self.baseparamwin = BaseParamDialog(self)

  def initUI (self):       

    exitAction = QAction(QIcon.fromTheme('exit'), 'Exit', self)        
    exitAction.setShortcut('Ctrl+Q')
    exitAction.setStatusTip('Exit HNN application.')
    exitAction.triggered.connect(qApp.quit)

    selParamFile = QAction(QIcon.fromTheme('open'), 'Set parameter file.', self)
    selParamFile.setShortcut('Ctrl+P')
    selParamFile.setStatusTip('Set param file')
    selParamFile.triggered.connect(self.selParamFileDialog)

    self.statusBar()

    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')
    menubar.setNativeMenuBar(False)
    fileMenu.addAction(selParamFile)
    fileMenu.addAction(exitAction)

    QToolTip.setFont(QFont('SansSerif', 10))        

    grid = QGridLayout()
    grid.setSpacing(10)

    self.btnsim = btn = QPushButton('Run Simulation', self)
    btn.setToolTip('Run simulation')
    btn.resize(btn.sizeHint())
    btn.clicked.connect(self.controlsim)
    grid.addWidget(self.btnsim, 1, 0, 1, 1)

    self.pbtn = pbtn = QPushButton('Set Parameters', self)
    pbtn.setToolTip('Set parameters')
    pbtn.resize(pbtn.sizeHint())
    pbtn.clicked.connect(self.setparams)
    grid.addWidget(self.pbtn, 1, 1, 1, 1)

    self.qbtn = qbtn = QPushButton('Quit', self)
    qbtn.clicked.connect(QCoreApplication.instance().quit)
    qbtn.resize(qbtn.sizeHint())
    grid.addWidget(self.qbtn, 1, 2, 1, 1)

    self.setGeometry(300, 300, 1200, 1100)
    self.setWindowTitle('HNN')

    self.m = m = PlotCanvas(self, width=10, height=8)
    grid.addWidget(self.m, 2, 0, 1, 3)

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
      print('Terminating sim. . .')
      self.statusBar().showMessage('Terminating sim. . .')
      self.runningsim = False
      self.runthread.stop() # killed = True # terminate()
      self.btnsim.setText("Start sim")
      self.qbtn.setEnabled(True)
      self.statusBar().showMessage('')

  def startsim (self):
    print('Starting sim. . .')
    self.runningsim = True

    self.statusBar().showMessage("Running simulation. . .")

    self.runthread = RunSimThread(self.c)

    # We have all the events we need connected we can start the thread
    self.runthread.start()
    # At this point we want to allow user to stop/terminate the thread
    # so we enable that button
    self.btnsim.setText("Stop sim") # setEnabled(False)
    # We don't want to enable user to start another thread while this one is
    # running so we disable the start button.
    # self.btn_start.setEnabled(False)
    self.qbtn.setEnabled(False)

  def done(self):
    self.runningsim = False
    self.statusBar().showMessage("")
    self.btnsim.setText("Start sim")
    self.qbtn.setEnabled(True)
    self.m.plot()
    #self.btn_stop.setEnabled(False)
    QMessageBox.information(self, "Done!", "Finished running sim using " + paramf + '. Saved data/figures in: ' + basedir)


# based on https://pythonspot.com/en/pyqt5-matplotlib/
class PlotCanvas (FigureCanvas): 

  def __init__ (self, parent=None, width=5, height=4, dpi=100):
    self.fig = fig = Figure(figsize=(width, height), dpi=dpi)
    FigureCanvas.__init__(self, fig)
    self.setParent(parent)
    FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
    FigureCanvas.updateGeometry(self)
    self.G = gridspec.GridSpec(10,1)
    self.invertedhistax = False
    self.plot()

  def plot (self):
    if len(ddat.keys()) == 0: return
    try:
      fig,ax = plt.subplots(); ax.cla()

      xlim_new = (ddat['dpl'][0,0],ddat['dpl'][-1,0])
      # set number of bins (150 bins per 1000ms)
      bins = ceil(150. * (xlim_new[1] - xlim_new[0]) / 1000.) # bins needs to be an int

      # plot histograms of inputs
      print(dfile['spk'],dfile['outparam'])
      extinputs = None
      try:
        extinputs = spikefn.ExtInputs(dfile['spk'], dfile['outparam'])
        extinputs.add_delay_times()
      except:
        pass
      hist = {}
      axprox = self.figure.add_subplot(self.G[0,0]); axprox.cla() # proximal inputs
      axdist = self.figure.add_subplot(self.G[1,0]); axdist.cla() # distal inputs
      if extinputs is not None: # only valid param.txt file after sim was run
        hist['feed_prox'] = extinputs.plot_hist(axprox,'prox',ddat['dpl'][:,0],bins,xlim_new,color='red')
        hist['feed_dist'] = extinputs.plot_hist(axdist,'dist',ddat['dpl'][:,0],bins,xlim_new,color='green')
        for ax in [axprox,axdist]:
          if not self.invertedhistax: # only need to invert axes 1X
            ax.invert_yaxis()
            self.invertedhistax = True
          ax.set_xlim(xlim_new)
          ax.legend()          

      ax = self.figure.add_subplot(self.G[2:5,0]); ax.cla() # dipole
      ax.plot(ddat['dpl'][:,0],ddat['dpl'][:,1],'b')
      ax.set_ylabel('dipole (nA m)')
      ax.set_xlim(ddat['dpl'][0,0],ddat['dpl'][-1,0])
      ax.set_ylim(np.amin(ddat['dpl'][:,1]),np.amax(ddat['dpl'][:,1]))

      ax = self.figure.add_subplot(self.G[6:10,0]); ax.cla() # specgram
      ds = ddat['spec']
      cax = ax.imshow(ds['TFR'],extent=(ds['time'][0],ds['time'][-1],ds['freq'][-1],ds['freq'][0]),aspect='auto',origin='upper',cmap=plt.get_cmap('jet'))
      ax.set_ylabel('Frequency (Hz)')
      ax.set_xlabel('Time (ms)')
      ax.set_xlim(ds['time'][0],ds['time'][-1])
      ax.set_ylim(ds['freq'][-1],ds['freq'][0])
      cbaxes = self.fig.add_axes([0.915, 0.125, 0.03, 0.2]) 
      cb = plt.colorbar(cax, cax = cbaxes)  
      #self.fig.tight_layout() # tight_layout will mess up colorbar location
    except:
      print('ERR: in plot')
    self.draw()
        
if __name__ == '__main__':    
  app = QApplication(sys.argv)
  ex = HNNGUI()
  sys.exit(app.exec_())  
  
