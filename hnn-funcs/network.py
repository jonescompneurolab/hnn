"""
params.py 

Useful functions for the NetPyNE-based implementation of HNN

Contributors: salvadordura@gmail.com
"""

#network file
def create_network():
    sim.initialize(simConfig=cfg, netParams=netParams)  
    sim.net.createPops()
    sim.net.createCells()
    sim.gatherData()

''' 
from init.py
from netpyne import sim
from utils import setCfgFromFile



# Parameters file to read
cfgFile = '../param/ERPYes100Trials.param'      # ERP
# cfgFile = '../param/AlphaAndBeta.param'         # Alpha and Beta
# cfgFile = '../param/gamma_L5weak_L2weak.param'  # Gamma weak
# cfgFile = '../param/gamma_L5ping_L2ping.param'  # Gamma ping


# Import simConfig and set parameters from file
cfg, netParams = sim.readCmdLineArgs()
cfg = setCfgFromFile(cfgFile, cfg)#, exclude = ['prng_seedcore_input_prox', 'prng_seedcore_input_dist']) # exclude parameters modified in batch.py

from netParams import netParams

# Create, simulate and analyze model
sim.createSimulateAnalyze(simConfig = cfg, netParams = netParams)  
'''