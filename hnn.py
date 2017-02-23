#!/usr/bin/python3
# -*- coding: utf-8 -*-
# jnk4
#
import sys, os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QToolTip, QPushButton
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QCoreApplication

import multiprocessing
ncore = multiprocessing.cpu_count()

if not os.path.exists('model'):
  print("No model found!")
  sys.exit(1)

def runsim ():
  print("Running simulation using",ncore,"cores.")

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
  app = QApplication(sys.argv)
  ex = HNNGUI()
  sys.exit(app.exec_())  
