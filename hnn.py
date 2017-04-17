#!/usr/bin/python3
# -*- coding: utf-8 -*-

from hnn_qt5 import *

if __name__ == '__main__':    
  app = QApplication(sys.argv)
  ex = HNNGUI()
  sys.exit(app.exec_()) 
 
