"""
netParams.py 

Reads param files from command line and runs simulation

Contributors: salvadordura@gmail.com
"""

import hnn_func
import os
import sys

hnn_func.load_custom_mechanisms(os.path.dirname(__file__))

from netpyne import sim
cfg, netParams = sim.readCmdLineArgs(simConfigDefault='cfg.py', netParamsDefault='netParams.py')
sim.createSimulateAnalyze(netParams, cfg)
sys.exit()