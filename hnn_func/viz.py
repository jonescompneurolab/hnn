"""
params.py 

Useful functions for the NetPyNE-based implementation of HNN

Contributors: salvadordura@gmail.com
"""

import os.path as op
from netpyne import sim

# viz file
def plot_cells(pops=['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket'], iv = False):
    sim.analysis.plotShape(includePost=pops, iv=iv)

    # add options to plot from data passed as arguments of from saved file 
