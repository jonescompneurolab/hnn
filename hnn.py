#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import shlex
from subprocess import Popen, PIPE, call

from hnn_qt5 import *

#
def runnrnui ():
  pnrnui = Popen(shlex.split(os.path.join('NEURON-UI','NEURON-UI')),cwd=os.getcwd())
  pjup = Popen(shlex.split('jupyter console --existing'),cwd=os.getcwd(),stdin=PIPE,stdout=PIPE,stderr=PIPE)
  sleep(5)
  lproc = [pnrnui,pjup]
  lns = ["import os\n","os.chdir('/u/samn/hnn/NEURON-UI/neuron_ui/models/hnn')\n","import hnn_nrnui\n","net=hnn_nrnui.HNN()\n"]
  for s in lns:
    pjup.stdin.write(s.encode())
    pjup.stdin.flush()
    sleep(1)
    # print(pjup.communicate(input=s.encode())[0])
  return lproc

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
    lproc = runnrnui()

