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
def plot_cells(net, pops=['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket'], iv = False):

    # create list of segement colors based on cell gid  
    try:
        cvals = []
        for cell in net.cells:
            if cell.tags['pop'] in pops:
                for sec in cell.secs.values():
                    cvals.extend([cell.gid] * sec['hObj'].nseg) # [pops.index(cell.tags['pop'])] *sec['hObj'].nseg ) 
    except:
        cvals = None

    # currently using sim.net and assuming already instantiated; make more flexible by using sim.loadNet:
    # sim.loadNet(None, data={'net': {'cells': net.allCells, 'pops': net.allPops}}, instantiate=True)  

    # plot morphology of net cells
    fig, data = sim.analysis.plotShape(includePost=pops, iv=iv, cvals=cvals, elev=125, azim=-115)

    return fig
    

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
        # plot dipoles
        if ax is None:
            fig, ax = plt.subplots(1, 1)
        
        for trial_data in trials_data:
            dpl_trial = trial_data.get('dpl', None)

            if dpl_trial:

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

        if 'include' not in kwargs:
            kwargs['include'] = ['L2Basket', 'L2Pyr', 'L5Basket', 'L5Pyr']

        if 'popColors' not in kwargs:
            kwargs['popColors'] = {'L2Basket': [0.0, 0.0, 0.0], 'L2Pyr': [0.0, 0.6, 0.0], 'L5Basket': [0.0, 0.0, 1.0], 'L5Pyr': [1.0, 0.0, 0.0],
                        'Evoked proximal': [0.0, 1.0, 1.0], 'Evoked distal': [1.0, 1.0, 0.0]}

        if 'markerSize' not in kwargs: 
            kwargs['markerSize'] = 6
        
        if 'orderInverse' not in kwargs:
            kwargs['orderInverse'] = True

        if 'showFig' not in kwargs:
            kwargs['showFig'] = True

        if 'saveFig' not in kwargs:
            kwargs['saveFig'] = False

        if 'timeRange' not in kwargs:
            kwargs['timeRange'] = [0, trials_data[0]['simConfig']['duration']]

        sim.initialize()
        sim.loadNet(None, data=trials_data[0], instantiate=False)
        sim.loadSimCfg(None, data=trials_data[0])

        for trial_data in trials_data:
            sim.loadSimData(filename=None, data=trial_data)
            try:
                fig, data = sim.analysis.iplotRaster(**kwargs)
            except:
                fig, data = -1, {}

    return 1


def plot_spike_hist(trials_data, **kwargs):
    if len(trials_data) > 0:

        if 'include' not in kwargs:
            pops = ['L2Basket', 'L2Pyr', 'L5Basket', 'L5Pyr']
            evprox = ['evokedProximal_1_L2Basket', 'evokedProximal_1_L2Pyr', 'evokedProximal_1_L5Basket', 'evokedProximal_1_L5Pyr',
                    'evokedProximal_2_L2Basket', 'evokedProximal_2_L2Pyr', 'evokedProximal_2_L5Basket', 'evokedProximal_2_L5Pyr']
            evdist = ['evokedDistal_1_L2Basket', 'evokedDistal_1_L2Pyr', 'evokedDistal_1_L5Basket', 'evokedDistal_1_L5Pyr']
            kwargs['include'] = [*pops, evprox, evdist, 'extRhythmicProximal', 'extRhythmicDistal']

        if 'legendLabels' not in kwargs:
            kwargs['legendLabels'] = ['L2Basket', 'L2Pyr', 'L5Basket', 'L5Pyr', 'Evoked proximal', 'Evoked distal', 'Rhythmic proximal', 'Rhythmic distal']

        if 'popColors' not in kwargs:
            kwargs['popColors'] = {'L2Basket': [0.0, 0.0, 0.0], 'L2Pyr': [0.0, 0.6, 0.0], 'L5Basket': [0.0, 0.0, 1.0], 'L5Pyr': [1.0, 0.0, 0.0],
                        'Evoked proximal': [0.0, 1.0, 1.0], 'Evoked distal': [1.0, 1.0, 0.0]}

        if 'yaxis' not in kwargs:
            kwargs['yaxis'] = 'count'

        if 'showFig' not in kwargs:
            kwargs['showFig'] = True

        if 'saveFig' not in kwargs:
            kwargs['saveFig'] = False   

        if 'timeRange' not in kwargs:
            kwargs['timeRange'] = [0, trials_data[0]['simConfig']['duration']]

        sim.initialize()
        sim.loadNet(None, data=trials_data[0], instantiate=False)
        sim.loadSimCfg(None, data=trials_data[0])

        for trial_data in trials_data:
            sim.loadSimData(filename=None, data=trial_data)
            try:
                fig, data = sim.analysis.iplotSpikeHist(**kwargs)
            except:
                fig, data = -1, {}

    return fig


def netpyne_plot(func_name, trials_data, **kwargs):
    if len(trials_data) > 0:

        sim.initialize()
        sim.loadNet(None, data=trials_data[0], instantiate=False)
        sim.loadSimCfg(None, data=trials_data[0])

        for trial_data in trials_data:
            sim.loadSimData(filename=None, data=trial_data)

            try:
                fig, data = getattr(sim.analysis, func_name)(**kwargs)
            except:
                fig, data = -1, {}
    return fig


'''
cfg.analysis['iplotTraces'] = {'include': [('L5Pyr',0) ], 'oneFigPer': 'cell', 'saveFig': False, 
							  'showFig': True, 'timeRange': [0, cfg.duration]}

cfg.analysis['iplotRaster'] = {'include': pops, 'showFig': True, 'popColors': popColors, 'markerSize': 6, 'orderInverse': True}

cfg.analysis['iplotSpikeHist'] = {'include': [*pops, evprox, evdist, 'extRhythmicProximal', 'extRhythmicDistal'], 'legendLabels': pops + ['Evoked proximal', 'Evoked distal', 'Rhythmic proximal', 'Rhythmic distal'], 'popColors': popColors, 'yaxis': 'count', 'showFig': True}

cfg.analysis['iplotDipole'] = {'showFig': True}

cfg.analysis['iplotDipolePSD'] = {'showFig': True, 'maxFreq': 80}  # change freq to 40 for alpha&beta tut

cfg.analysis['iplotDipoleSpectrogram'] = {'showFig': True, 'maxFreq': 80} # change freq to 40 for alpha&beta tut

# cfg.analysis['iplotConn'] = {'includePre': pops, 'includePost': pops, 'feature': 'strength'}

# cfg.analysis['iplotLFP'] = {'showFig': True}

#cfg.analysis['iplotRatePSD'] = {'include': pops, 'showFig': True}
'''