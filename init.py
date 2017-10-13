in# init.py - Starting script to run NetPyNE-based model.
# Usage:  python init.py  # Run simulation, optionally plot a raster
# MPI usage:  mpiexec -n 4 nrniv -python -mpi init.py

from netpyne import sim
cfg, netParams = sim.readCmdLineArgs('cfg.py','netParams.py') # read cfg and netParams from command line arguments
#sim.create(simConfig=cfg, netParams=netParams)
sim.createSimulateAnalyze(simConfig = cfg, netParams = netParams) 

