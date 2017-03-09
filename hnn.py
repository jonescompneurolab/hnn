#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QToolTip, QPushButton
from PyQt5.QtWidgets import QMenu, QSizePolicy, QMessageBox, QWidget, QFileDialog
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QDialog, QGridLayout, QLineEdit, QLabel
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal, QObject
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
fprm = 'param/default.param'

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

# widget to specify proximal params
class ProxParamWidget (QWidget):
  def __init__ (self, parent):
    super(ProxParamWidget, self).__init__(parent)

# widget to specify distal params
class DistParamWidget (QWidget):
  def __init__ (self, parent):
    super(DistParamWidget, self).__init__(parent)

# base widget for specifying params (contains buttons to create other widgets
class BaseParamDialog (QDialog):

  def __init__ (self, parent):
    super(BaseParamDialog, self).__init__(parent)
    self.initUI()

  def initUI (self):

    grid = QGridLayout()
    grid.setSpacing(10)

    self.lbl = QLabel(self)
    self.lbl.setText('Simulation name:')
    self.lbl.adjustSize()
    grid.addWidget(self.lbl, 1, 0)
    self.qle = QLineEdit(self)
    self.qle.setText(paramf.split(os.path.sep)[-1].split('.param')[0])
    grid.addWidget(self.qle, 1, 1)

    self.btnprox = QPushButton('Set Proximal Inputs',self)
    self.btnprox.resize(self.btnprox.sizeHint())
    grid.addWidget(self.btnprox, 2, 0, 1, 2)

    self.btndist = QPushButton('Set Distal Inputs',self)
    self.btndist.resize(self.btndist.sizeHint())
    grid.addWidget(self.btndist, 3, 0, 1, 2)

    self.btnok = QPushButton('OK',self)
    self.btnok.resize(self.btnok.sizeHint())
    grid.addWidget(self.btnok, 4, 0, 1, 1)

    self.btncancel = QPushButton('Cancel',self)
    self.btncancel.resize(self.btncancel.sizeHint())
    grid.addWidget(self.btncancel, 4, 1, 1, 1)

    self.setLayout(grid) 
        
    self.setGeometry(100, 100, 400, 100)
    self.setWindowTitle('Set Sim Parameters')    
    self.show()

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

    # Next we need to connect the events from that thread to functions we want
    # to be run when those signals get fired

    # This is pretty self explanatory
    # regardless of whether the thread finishes or the user terminates it
    # we want to show the notification to the user that adding is done
    # and regardless of whether it was terminated or finished by itself
    # the finished signal will go off. So we don't need to catch the
    # terminated one specifically, but we could if we wanted.

    # We have all the events we need connected we can start the thread
    self.runthread.start()
    # At this point we want to allow user to stop/terminate the thread
    # so we enable that button
    self.btnsim.setText("Stop sim") # setEnabled(False)
    # And we connect the click of that button to the built in
    # terminate method that all QThread instances have
    # self.btnsim.clicked.connect(self.runthread.terminate)
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
  
