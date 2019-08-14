'''
init.py

Starting script to run NetPyNE-based HNN model.

Usage:
    python init.py # Run simulation, optionally plot a raster

MPI usage:
    mpiexec -n 4 nrniv -python -mpi init.py

Contributors: salvadordura@gmail.com
'''

from netpyne import sim
from utils import setCfgFromFile



# Parameters file to read
cfgFile = 'param/AlphaAndBeta_netpyne.param' #'../param/ERPYes100Trials.param' # '../param/AlphaAndBeta.param' # #../param/ERPYes1Trial_test.param'

# Import simConfig and set parameters from file
from cfg import cfg
cfg = setCfgFromFile(cfgFile, cfg)

# Import netParams
from netParams import netParams

# Create, simulate and analyze model
# sim.initialize(simConfig=cfg, netParams=netParams) 
# sim.net.createPops()
# sim.net.createCells()
sim.createSimulateAnalyze(simConfig=cfg, netParams=netParams) 
