"""
===============
Simulate dipole
===============

This example demonstrates how to simulate a dipole for evoked-like
waveforms using HNN-netpyne.

Requires adding the hnn_func package to PYTHONPATH, e.g.:

 - cd ~
 - git clone --single-branch --branch hnn2 https://github.com/jonescompneurolab/hnn.git hnn2
 - export PYTHONPATH=~/hnn2/:$PYTHONPATH

"""

# Let us import hnn_func
from hnn_func import read_params, create_network, simulate_trials, mean_rates
from hnn_func.viz import plot_cells, plot_dipole, plot_spike_raster, plot_spike_hist, netpyne_plot, print #, plot_raster, plot_spike_hist, mean_rates


cfg_params = read_params(model_folder='../hnn_models/hnn_neocortex', params_fname='param/ERPYes1Trial.param') 

cfg_params.saveCellSecs = True
cfg_params.saveCellConns = True
trials_data = simulate_trials(cfg_params, n_trials=1, n_cores=1, only_read=1) 

# # plot connectivity matrix
# pops = ['L2Basket', 'L2Pyr', 'L5Basket', 'L5Pyr']
# netpyne_plot('plotConn', trials_data, includePre=pops, includePost=pops, groupBy='pop', feature='strength', graphType='matrix')
# netpyne_plot('plotConn', trials_data, includePre=pops, includePost=pops, groupBy='cell', feature='weight', graphType='matrix')
# netpyne_plot('plotConn', trials_data, includePre=pops, includePost=pops, feature='numConns', graphType='bar')

# plot voltage traces
netpyne_plot('iplotTraces', 
            trials_data, 
            include=[('L2Basket',0), ('L2Pyr',0), ('L5Basket',0), ('L5Pyr',0)], 
            oneFigPer='trace', 
            overlay=1,
            showFig=True)


# stats

# dipole spectrogram

# LFP / CSD

# granger causality

# batch explore params

# modify netParams interactively 
