"""
cfg.py 

Simulationg configuration for NetPyNE-based A1 network model

Contributors: salvadordura@gmail.com
"""

import json
from netpyne import specs

# ############################################################################
#
# SIMULATION CONFIGURATION
#
# ############################################################################

with open('cfg_small.json', 'r') as f:
    data = json.load(f)

cfg = specs.SimConfig(data['simConfig'])  

