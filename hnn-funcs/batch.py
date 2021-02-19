"""
batch.py 

Batch simulation for M1 model using NetPyNE

Contributors: salvadordura@gmail.com
"""

from netpyne.batch import Batch
import numpy as np


def runBatch(b, label, setup='mpi_bulletin'):

    b.batchLabel = label
    b.saveFolder = 'data/'+b.batchLabel
    b.method = 'grid'

    if setup == 'mpi_bulletin':
        b.runCfg = {'type': 'mpi_bulletin', 
                    'script': 'init.py', 
                    'skip': True}
	
    elif setup == 'hpc_slurm_comet':
        b.runCfg = {'type': 'hpc_slurm', 
                    'allocation': 'csd403', 
                    'walltime': '6:00:00',
                    'nodes': 1,
                    'coresPerNode': 24,  
                    'email': 'salvadordura@gmail.com',
                    'folder': '/home/salvadord/netpyne/examples/batchCell',  # startup folder
                    'script': 'init.py', 
                    'mpiCommand': 'ibrun'}  # specific command for Comet
                    
    b.run() # run batch


# set params 
params = {'prng_seedcore_input_prox': [13, 14],
          'prng_seedcore_input_dist': [14, 15]}

# create netpyne Batch object
b = Batch(params=params)

# submit batch
runBatch(b, label='seeds', setup='mpi_bulletin')

