#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import shlex
from subprocess import Popen, PIPE, call
from time import sleep

from hnn_qt5 import *

from signal import signal, SIGPIPE, SIG_DFL

#
def runnrnui ():
  signal(SIGPIPE,SIG_DFL) 
  pnrnui = Popen(shlex.split(os.path.join('NEURON-UI','NEURON-UI')),cwd=os.getcwd())
  sleep(7)
  pjup = Popen(shlex.split('jupyter console --existing'),cwd=os.getcwd(),stdin=PIPE,stdout=PIPE,stderr=PIPE,shell=True)
  sleep(5)
  lproc = [pnrnui,pjup]
  lns = ["import os\n",
         "os.chdir('NEURON-UI/neuron_ui/models/hnn')\n",
         "import hnn_nrnui\n",
         "net=hnn_nrnui.HNN()\n"]
  for s in lns:
    pjup.stdin.write(s.encode())
    sleep(1)
    pjup.stdin.flush()
    sleep(1)
    #print(pjup.communicate(input=s.encode())[0])
    while pjup.poll() is None: pass
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

