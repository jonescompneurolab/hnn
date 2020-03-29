#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import shlex
from subprocess import Popen, PIPE, call
from time import sleep

from hnn_qt5 import *

#
def runnrnui ():
  pnrnui = Popen(shlex.split(os.path.join('NEURON-UI','NEURON-UI')),cwd=os.getcwd())
  sleep(5) # make sure NEURON-UI had a chance to start
  pjup = Popen(shlex.split('jupyter run loadmodel_nrnui.py --existing'),cwd=os.getcwd())
  lproc = [pnrnui, pjup]; done = [False, False]
  while pnrnui.poll() is None or pjup.poll() is None: sleep(1)
  for p in lproc:
    try: p.communicate()
    except: pass
  return lproc

def runqt5 ():
  app = QApplication(sys.argv)
  ex = HNNGUI()
  sys.exit(app.exec_())
  # app.exec_()
  # print('\n'.join(repr(w) for w in app.allWidgets()))

if __name__ == '__main__':
  useqt5 = True
  for s in sys.argv:
    if s == 'nrnui':
      useqt5 = False
  if useqt5:
    runqt5()
  else:
    lproc = runnrnui()

