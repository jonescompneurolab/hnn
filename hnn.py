#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QToolTip, QPushButton
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QCoreApplication
import multiprocessing
from subprocess import Popen, PIPE, call
import shlex
from time import time, clock
import pickle, tempfile

ncore = multiprocessing.cpu_count()
fprm = './model/param/default.param'

if not os.path.exists('model'):
  print("No model found!")
  sys.exit(1)

cmd = 'mpiexec -np ' + str(ncore) + ' nrniv -python -mpi run.py param/default.param'
maxruntime = 120
foutput = './data/sim.out'
debug = False

# run sim command via mpi, then delete the temp file. returns job index and fitness.
def runsim ():
  print("Running simulation using",ncore,"cores.")
  cmdargs = shlex.split(cmd)
  print("cmd:",cmd,"cmdargs:",cmdargs)
  #proc = Popen(cmdargs,stdout=PIPE,stderr=PIPE,cwd=os.path.join(os.getcwd(),'model'))
  proc = Popen(cmdargs,cwd=os.path.join(os.getcwd(),'model'))
  print("proc:",proc)
  cstart = time(); killed = False
  while not killed and proc.poll() is None: # job is not done
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
    try: # lack of output file may occur if invalid param values lead to an nrniv crash
      with open(foutput,'r') as fp:
        i = 0
        for ln in fp.readlines():
          i += 1
        print("Read ",i," lines from",foutput)
    except:
      print('WARN: could not read simulation output:',foutput)

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
    qbtn.move(50, 100) 

    self.setGeometry(300, 300, 300, 200)
    self.setWindowTitle('HNN')    
    self.show()
        
if __name__ == '__main__':    
  if debug:
    pass
  else:
    app = QApplication(sys.argv)
    ex = HNNGUI()
    sys.exit(app.exec_())  
  
