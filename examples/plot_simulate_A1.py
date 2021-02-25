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

# Let us import hnn_func
from hnn_api import read_params, create_network, simulate_trials, mean_rates
from hnn_api.viz import plot_cells, plot_dipole, plot_spike_raster, plot_spike_hist, plot_LFP, netpyne_plot, print #, plot_raster, plot_spike_hist, mean_rates


cfg_params = read_params(model_folder='../hnn_models/A1', params_fname='')  

trials_data = simulate_trials(cfg_params, n_trials=1, n_cores=4, only_read=0) 

