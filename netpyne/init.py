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

cfgFile = '../param/ERPYes100Trials.param' #../param/ERPYes1Trial_test.param' # ../param/netpyne_test.param'  # ../param/OnlyRhythmicProx.param'

from cfg import cfg
cfg = setCfgFromFile(cfgFile, cfg)
from netParams import netParams

sim.createSimulateAnalyze(simConfig=cfg, netParams=netParams) # SimulateAnalyze
