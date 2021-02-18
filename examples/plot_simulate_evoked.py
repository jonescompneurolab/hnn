"""
===============
Simulate dipole
===============

This example demonstrates how to simulate a dipole for evoked-like
waveforms using HNN-netpyne.
"""


###############################################################################
# Let us import hnn_netpyne
from netpyne import sim
from utils import setCfgFromFile

###############################################################################
# Then we read the parameters file
cfgFile = '../param/ERPYes100Trials.param'      # ERP

# Import simConfig and set parameters from file
cfg, netParams = sim.readCmdLineArgs()
cfg = setCfgFromFile(cfgFile, cfg)#, exclude = ['prng_seedcore_input_prox', 'prng_seedcore_input_dist']) # exclude parameters modified in batch.py

from netParams import netParams

###############################################################################
# Let us first create our network from the params file and visualize the cells
# inside it.
sim.initialize(simConfig=cfg, netParams=netParams)  
sim.net.createPops()
sim.net.createCells()
sim.gatherData()
sim.analysis.plotShape(includePost=['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket'])

###############################################################################
# Now let's simulate the dipole, running 2 trials with the Joblib backend.
# To run them in parallel we could set n_jobs to equal the number of trials.

n_trials = 2
dpls = []
for trial in range(n_trials):
    print('Trial %d ...' % (trial))
    cfg.prng_seedcore_input_prox += 1
    sim.createSimulateAnalyze(simConfig=cfg, netParams=netParams)  
    dpls.append(sim.allSimData['dipole'])

from matplotlib import pyplot as plt
plt.plot(dpls)

''' Alternative using batch
from netpyne.batch import Batch

params = {'prng_seedcore_input_prox': [13, 14]}  # set params 
b = Batch(params=params)  # create netpyne Batch object
b.batchLabel = 'erp_trials'
b.saveFolder = '../data/'+b.batchLabel
b.runCfg = {'type': 'mpi_direct', 'mpi_command': 'mpirun', 'script': 'init.py'}
b.run()

'''

###############################################################################
# We can additionally calculate the mean spike rates for each cell class by
# specifying a time window with tstart and tstop.

# in netpyne pop rates are already printed at end of sim
# accessible print(sim.allSimData['popRates'])

###############################################################################
# Now, let us try to make the exogenous driving inputs to the cells
# synchronous and see what happens

##############################################################################
# Next, let's simulate a single trial using the MPI backend. This will
# start the simulation trial across the number of processors (cores)
# specified by n_procs using MPI. The 'mpiexec' launcher is for
# openmpi, which must be installed on the system

cfg.sync_evinput = True
sim.createSimulateAnalyze(simConfig=cfg, netParams=netParams)  

