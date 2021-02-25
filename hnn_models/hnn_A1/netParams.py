
"""
netParams.py 

High-level specifications for HNN network model using NetPyNE

Contributors: salvadordura@gmail.com
"""

from netpyne import specs

try:
  from __main__ import cfg  # import SimConfig object with params from parent module
except:
  from cfg import cfg  # if no simConfig in parent module, import directly from cfg module

import numpy as np
import itertools as it
import json

from netpyne import specs

with open('netParams_small.json', 'r') as f:
    data = json.load(f)


# ----------------------------------------------------------------------------
#
# NETWORK PARAMETERS
#
# ----------------------------------------------------------------------------

netParams = specs.NetParams(data['net']['params'])  # object of class NetParams to store the network parameters

# add dipoles
for cp in [v for k,v in netParams.cellParams.items() if 'IT' in k  or 'PT' in k or 'CT' in k]:
    cp['secs']['soma']['mechs']['dipole'] = {}  