"""
netParams.py 

Reads param files from command line and runs simulation

Contributors: salvadordura@gmail.com
"""

import hnn_api
import os
import sys
from time import sleep

hnn_api.load_custom_mechanisms(os.path.dirname(__file__))

from netpyne import sim
cfg, netParams = sim.readCmdLineArgs(simConfigDefault='cfg.py', netParamsDefault='netParams.py')
sim.createSimulateAnalyze(netParams, cfg)
while sim.pc.working():
    sleep(1)

if sim.pc.id()==0: 
    sys.exit()
