"""
cfg.py 

Simulationg configuration for NetPyNE-based A1 network model

Contributors: salvadordura@gmail.com
"""

import json
import os
from netpyne import specs

# ############################################################################
#
# SIMULATION CONFIGURATION
#
# ############################################################################

root = os.path.dirname(__file__) + '/'

with open(root+'cfg_small.json', 'r') as f:
    data = json.load(f)

cfg = specs.SimConfig(data['simConfig'])  

cfg.hnn_params = {'prng_seedcore': 1}

cfg.recordDipoles = {'L4': ['ITS4', 'ITP4'], 'L5': ['IT5A', 'IT5B', 'PT5B'], 'L6': ['IT6', 'CT6']}
