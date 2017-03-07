#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QToolTip, QPushButton
from PyQt5.QtWidgets import QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QCoreApplication
import multiprocessing
from subprocess import Popen, PIPE, call
import shlex
from time import time, clock, sleep
import pickle, tempfile
from conf import readconf
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import random

ncore = multiprocessing.cpu_count()
fprm = './model/param/default.param'

if not os.path.exists('model'):
  print("No model found!")
  sys.exit(1)

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

debug = False
prtime = True

ddat = {}

def getinputfiles (paramf):
  dfile = {}
  basedir = os.path.join('model','data',paramf.split(os.path.sep)[1].split('.param')[0])
  dfile['dpl'] = os.path.join(basedir,'dpl.txt')
  dfile['spec'] = os.path.join(basedir,'rawspec.npz')
  dfile['spk'] = os.path.join(basedir,'spk.txt')
  return dfile

# run sim command via mpi, then delete the temp file. returns job index and fitness.
def runsim ():
  global ddat
  print("Running simulation using",ncore,"cores.")
  cmd = 'mpiexec -np ' + str(ncore) + ' nrniv -python -mpi ' + simf + ' ' + paramf
  maxruntime = 1200 # 20 minutes - will allow terminating sim later
  foutput = './data/sim.out'
  dfile = getinputfiles(paramf)
  cmdargs = shlex.split(cmd)
  print("cmd:",cmd,"cmdargs:",cmdargs)
  if prtime:
    proc = Popen(cmdargs,cwd=os.path.join(os.getcwd(),'model'))
  else:
    proc = Popen(cmdargs,stdout=PIPE,stderr=PIPE,cwd=os.path.join(os.getcwd(),'model'))
  if debug: print("proc:",proc)
  cstart = time(); killed = False
  while not killed and proc.poll() is None: # job is not done
    sleep(1)
    cend = time(); rtime = cend - cstart
    if rtime >= maxruntime:
      killed = True
      print(' ran for ' , round(rtime,2) , 's. too slow , killing.')
      try:
        proc.kill() # has to be called before proc ends
      except:
        print('could not kill')
  if not killed:
    try: proc.communicate() # avoids deadlock due to stdout/stderr buffer overfill
    except: print('could not communicate') # Process finished.
    # no output to read yet
    try: # lack of output file may occur if invalid param values lead to an nrniv crash
      ddat['dpl'] = np.loadtxt(dfile['dpl'])
      ddat['spec'] = np.load(dfile['spec'])
      ddat['spk'] = np.loadtxt(dfile['spk'])
      print("Read simulation outputs:",dfile.values())
    except:
      print('WARN: could not read simulation outputs:',dfile.values())

class HNNGUI (QMainWindow):

  def __init__ (self):
    super().__init__()        
    self.initUI()

  def initUI (self):       
    exitAction = QAction(QIcon.fromTheme('exit'), 'Exit', self)        
    exitAction.setShortcut('Ctrl+Q')
    exitAction.setStatusTip('Exit application')
    exitAction.triggered.connect(qApp.quit)

    self.statusBar()

    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')
    menubar.setNativeMenuBar(False)
    fileMenu.addAction(exitAction)

    QToolTip.setFont(QFont('SansSerif', 10))        
    #self.setToolTip('This is a <b>QWidget</b> widget')        
    btn = QPushButton('Run model', self)
    btn.setToolTip('Run simulation')
    btn.resize(btn.sizeHint())
    btn.clicked.connect(runsim)
    btn.move(50, 50)       

    qbtn = QPushButton('Quit', self)
    qbtn.clicked.connect(QCoreApplication.instance().quit)
    qbtn.resize(qbtn.sizeHint())
    qbtn.move(175, 50) 

    self.setGeometry(300, 300, 600, 550)
    self.setWindowTitle('HNN')    

    m = PlotCanvas(self, width=5, height=4)
    m.move(50,100)

    self.show()

# based on https://pythonspot.com/en/pyqt5-matplotlib/
class PlotCanvas (FigureCanvas): 
  def __init__ (self, parent=None, width=5, height=4, dpi=100):
    fig = Figure(figsize=(width, height), dpi=dpi)
    self.axes = fig.add_subplot(111)
    FigureCanvas.__init__(self, fig)
    self.setParent(parent)
    FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
    FigureCanvas.updateGeometry(self)
    self.plot()
  def plot (self):
    data = [random.random() for i in range(25)]
    ax = self.figure.add_subplot(111)
    ax.plot(data, 'r-')
    ax.set_title('PyQt Matplotlib Example')
    self.draw()
        
if __name__ == '__main__':    
  if debug:
    pass
  else:
    app = QApplication(sys.argv)
    ex = HNNGUI()
    sys.exit(app.exec_())  
  
