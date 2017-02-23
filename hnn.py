#!/usr/bin/python3
# -*- coding: utf-8 -*-
# jnk4
#
import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication
from PyQt5.QtGui import QIcon

class Example(QMainWindow):

  def __init__(self):
    super().__init__()        
    self.initUI()

  def initUI(self):       
    exitAction = QAction(QIcon.fromTheme('exit'), 'Exit', self)        
    exitAction.setShortcut('Ctrl+Q')
    exitAction.setStatusTip('Exit application')
    exitAction.triggered.connect(qApp.quit)

    self.statusBar()

    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')
    menubar.setNativeMenuBar(False)
    fileMenu.addAction(exitAction)

    self.setGeometry(300, 300, 300, 200)
    self.setWindowTitle('HNN')    
    self.show()
        
if __name__ == '__main__':    
  app = QApplication(sys.argv)
  ex = Example()
  sys.exit(app.exec_())  
