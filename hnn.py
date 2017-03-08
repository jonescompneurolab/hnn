#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QToolTip, QPushButton
from PyQt5.QtWidgets import QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal, QObject
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
    global ddat
    self.killed = False
    print("Running simulation using",ncore,"cores.")
    cmd = 'mpiexec -np ' + str(ncore) + ' nrniv -python -mpi ' + simf + ' ' + paramf
    maxruntime = 1200 # 20 minutes - will allow terminating sim later
    dfile = getinputfiles(paramf)
    cmdargs = shlex.split(cmd)
    print("cmd:",cmd,"cmdargs:",cmdargs)
    if prtime:
      self.proc = Popen(cmdargs,cwd=os.path.join(os.getcwd(),'model'))
    else:
      self.proc = Popen(cmdargs,stdout=PIPE,stderr=PIPE,cwd=os.path.join(os.getcwd(),'model'))
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

class Communicate (QObject):    
  finishSim = pyqtSignal()

class HNNGUI (QMainWindow):

  def __init__ (self):
    super().__init__()        
    self.initUI()
    self.runningsim = False
    self.runthread = None

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

    self.btnsim = btn = QPushButton('Run sim', self)
    btn.setToolTip('Run simulation')
    btn.resize(btn.sizeHint())
    btn.clicked.connect(self.controlsim)
    btn.move(50, 50)       

    self.qbtn = qbtn = QPushButton('Quit', self)
    qbtn.clicked.connect(QCoreApplication.instance().quit)
    qbtn.resize(qbtn.sizeHint())
    qbtn.move(175, 50) 

    self.setGeometry(300, 300, 600, 550)
    self.setWindowTitle('HNN')    

    self.m = m = PlotCanvas(self, width=5, height=4)
    m.move(50,100)

    self.c = Communicate()
    self.c.finishSim.connect(self.done)

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
      self.statusBar().showMessage('')

  def startsim (self):
    print('Starting sim. . .')
    self.runningsim = True

    self.statusBar().showMessage("Running sim. . .")

    self.runthread = RunSimThread(self.c)

    # Next we need to connect the events from that thread to functions we want
    # to be run when those signals get fired

    # Adding post will be handeled in the add_post method and the signal that
    # the thread will emit is  SIGNAL("add_post(QString)")
    # the rest is same as we can use to connect any signal
    # self.connect(self.runthread, SIGNAL("add_post(QString)"), self.add_post)

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

  """
  def add_post(self, post_text):
    #Add the text that's given to this function to the
    #list_submissions QListWidget we have in our GUI and
    #increase the current value of progress bar by 1
    #:param post_text: text of the item to add to the list
    #:type post_text: str
    self.list_submissions.addItem(post_text)
    self.progress_bar.setValue(self.progress_bar.value()+1)
  """

  def done(self):
    self.runningsim = False
    self.statusBar().showMessage("")
    self.btnsim.setText("Start sim")
    #self.btn_stop.setEnabled(False)
    #QtGui.QMessageBox.information(self, "Done!", "Done running sim!") # Show the message that sim is done.


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
  
