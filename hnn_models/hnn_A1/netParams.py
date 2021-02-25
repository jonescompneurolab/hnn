
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
import os

from netpyne import specs

# ----------------------------------------------------------------------------
#
# NETWORK PARAMETERS
#
# ----------------------------------------------------------------------------

import hnn_api 

root =  os.path.dirname(hnn_api.__file__)+'/../hnn_models/hnn_A1/'
with open(root+'netParams_small.json', 'r') as f:
    data = json.load(f)

netParams = specs.NetParams(data['net']['params'])  # object of class NetParams to store the network parameters

# add dipoles
for cp in [v for k,v in netParams.cellParams.items() if 'IT' in k  or 'PT' in k or 'CT' in k]:
    cp['secs']['soma']['mechs']['dipole'] = {}  

# set random seed
cfg.seeds['input'] = cfg.hnn_params['prng_seedcore']