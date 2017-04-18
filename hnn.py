#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import shlex
from subprocess import Popen, PIPE, call

from hnn_qt5 import *

#
def runnrnui ():
  lcmd = [os.path.join('NEURON-UI','NEURON-UI'), 'jupyter console --existing']
  lproc = []
  for cmd in lcmd:
    cmdargs = shlex.split(cmd)
    proc = Popen(cmdargs,cwd=os.getcwd())
    lproc.append(proc)
  """
  import os
  os.chdir('/u/samn/hnn/NEURON-UI/neuron_ui/models/hnn')
  import hnn_nrnui
  net=hnn_nrnui.HNN()
  """

def runqt5 ():
  app = QApplication(sys.argv)
  ex = HNNGUI()
  sys.exit(app.exec_()) 

if __name__ == '__main__':
  useqt5 = True
  for s in sys.argv:
    if s == 'nrnui':
      useqt5 = False
  if useqt5:
    runqt5()
  else:
    runnrnui()
