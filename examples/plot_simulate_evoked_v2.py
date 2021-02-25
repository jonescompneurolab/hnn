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
from hnn_api import read_params, create_network, simulate_trials, mean_rates
from hnn_api.viz import plot_cells, plot_dipole, plot_spike_raster, plot_spike_hist, plot_LFP, netpyne_plot, print #, plot_raster, plot_spike_hist, mean_rates


cfg_params = read_params(model_folder='../hnn_models/hnn_neocortex', params_fname='param/ERPYes1Trial.param') 

cfg_params.saveCellSecs = True
cfg_params.saveCellConns = True
cfg_params.recordLFP = [[1, y, 1] for y in range(0, 1400, 100)]

trials_data = simulate_trials(cfg_params, n_trials=1, n_cores=4, only_read=0) 

# # plot connectivity matrix
pops = ['L2Basket', 'L2Pyr', 'L5Basket', 'L5Pyr']
# netpyne_plot('plotConn', trials_data, includePre=pops, includePost=pops, groupBy='pop', feature='strength', graphType='matrix')
# netpyne_plot('plotConn', trials_data, includePre=pops, includePost=pops, groupBy='cell', feature='weight', graphType='matrix')
# netpyne_plot('plotConn', trials_data, includePre=pops, includePost=pops, feature='numConns', graphType='bar')

# # plot voltage traces
# netpyne_plot('iplotTraces', trials_data, include=[('L2Basket',0), ('L2Pyr',0), ('L5Basket',0), ('L5Pyr',0)], oneFigPer='trace', overlay=1)

# stats
# netpyne_plot('plotSpikeStats', trials_data, stats=['rate', 'sync', 'pairsync'], include=pops)

# dipole spectrogram
#netpyne_plot('iplotDipoleSpectrogram', trials_data, dpl={'L2': trials_data[0]['dpl'].data['L2'], 'L5': trials_data[0]['dpl'].data['L5']}, showFig=1)

# LFP / CSD
plot_LFP(trials_data, showFig = True)

# granger causality
#netpyne_plot('plotGranger', trials_data, showFig= True)


# batch explore params

# modify netParams interactively 
