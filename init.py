# init.py - Starting script to run NetPyNE-based model.
# Usage:  python init.py  # Run simulation, optionally plot a raster
# MPI usage:  mpiexec -n 4 nrniv -python -mpi init.py

from netpyne import sim
from utils import setCfgFromFile

from cfg import cfg
cfg = setCfgFromFile('param/ERPYes100Trials.param', cfg)
from netParams import netParams

sim.create(simConfig = cfg, netParams = netParams) 
#SimulateAnalyze
sim.gatherData()
sim.saveData()