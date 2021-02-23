"""
params.py 

Useful functions for the NetPyNE-based implementation of HNN

Contributors: salvadordura@gmail.com
"""

import os.path as op
import numpy as np
from pprint import pprint as print

from netpyne import sim

# viz file
def plot_cells(pops=['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket'], iv = False):
    sim.analysis.plotShape(includePost=pops, iv=iv)

    # add options to plot from data passed as arguments of from saved file 


def plot_dipole(trials_data, ax=None, layer='agg', show=True, method='hnn-core'):
    """Simple layer-specific plot function.

    Parameters
    ----------
    trials_data : output data from simulating data; contains dipole signal 
        dict with netpyne output data from multiple trials
    ax : instance of matplotlib figure | None
        The matplotlib axis
    layer : str
        The layer to plot. Can be one of
        'agg', 'L2', and 'L5'
    show : bool
        If True, show the figure
    method : which method to use to plot (temporary arg for testing) 
        'hnn-core' or 'netpyne'

    Returns
    -------
    fig : instance of plt.fig
        The matplotlib figure handle.
    """
    import matplotlib.pyplot as plt

    
    if method == 'hnn-core':

        dpls = trials_data.get('dpls', None)

        if dpls:
            # plot dipoles
            if ax is None:
                fig, ax = plt.subplots(1, 1)

            for dpl_trial in dpls:
                if layer in dpl_trial.data.keys():
                    ax.plot(dpl_trial.times, dpl_trial.data[layer])

            ax.set_xlabel('Time (ms)')
            ax.set_title(layer)

            if show:
                plt.show()

    elif method == 'netpyne':
        # sim.analysis.iplotDipole()
        pass

    return ax.get_figure()


def plot_spike_raster(trials_data, **kwargs):
    if len(trials_data) > 0:
        sim.initialize()
        sim.loadNet(None, data=trials_data[0])

        for trial_data in trials_data.values():
            sim.loadSimData(filename=None, data=trial_data)
            try:
                fig, data = sim.analysis.plotRaster()
            except:
                fig, data = -1, {}

    return fig


def plot_spike_hist(trials_data, **kwargs):
    if len(trials_data) > 0:
        sim.initialize()
        sim.loadNet(None, data=trials_data[0])

        for trial_data in trials_data.values():
            sim.loadSimData(filename=None, data=trial_data)
            try:
                fig, data = sim.analysis.plotSpikeHist()
            except:
                fig, data = -1, {}

    return fig


def netpyne_plot(func_name, trials_data, **kwargs):

    if len(trials_data) > 0:
        sim.initialize()
        sim.loadNet(None, data=trials_data[0])

        for trial_data in trials_data.values():
            sim.loadSimData(filename=None, data=trial_data)
            try:
                fig, data = getattr(sim.analysis, 'func_name')(**kwargs)
            except:
                fig, data = -1, {}
    return fig


'''
fig = plt.figure()
f2 = plt.figure()
plt.plot([1,2], [1,2])
f2.axes[0].figure=fig
fig.add_subplot(f2.axes[0])
plt.show()

from ax can get fig
'''