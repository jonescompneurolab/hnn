"""
===============
Simulate dipole
===============

This example demonstrates how to simulate a dipole for evoked-like
waveforms using HNN-netpyne.

Requires adding the hnn_api package to PYTHONPATH, e.g.:

 - cd ~
 - git clone --single-branch --branch hnn2 https://github.com/jonescompneurolab/hnn.git hnn2
 - export PYTHONPATH=~/hnn2/:$PYTHONPATH

"""

# Let us import hnn_api
from hnn_api import read_params, create_network, simulate_trials, mean_rates
from hnn_api.viz import plot_cells, plot_dipole, plot_spike_raster, plot_spike_hist, plot_LFP, netpyne_plot, print #, plot_raster, plot_spike_hist, mean_rates


cfg_params = read_params(model_folder='../hnn_models/hnn_A1', params_fname='')  

cfg_params.recordDipoles = {'L4': ['ITS4', 'ITP4'], 'L5': ['IT5A', 'IT5B', 'PT5B'], 'L6': ['IT6', 'CT6']}
cfg_params.hnn_params['dipole_scalefctr'] = 3000
cfg_params.hnn_params['dipole_smooth_win'] = 30

trials_data = simulate_trials(cfg_params, n_trials=1, n_cores=4, postproc=False, only_read=0) 

# plot dipole and spike raster
import numpy as np

t=np.arange(0, cfg_params.duration, cfg_params.dt)  # should be available in ['simData']['t'] -- check why empty
netpyne_plot('iplotDipole', trials_data, showFig=True, t=np.arange(0,300, 0.05), dpl=trials_data[0]['simData']['dipole'])

netpyne_plot('plotRaster', trials_data, popRates=True, orderInverse= True, figSize= (10,10), lw=1.0, markerSize=10, marker= '.', dpi= 300)

