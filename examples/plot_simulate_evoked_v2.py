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


cfg_params, net_params = read_params(model_folder='../hnn_models/hnn_neocortex', params_fname='param/ERPYes100Trials.param') #default.param')

trials_data = simulate_trials(cfg_params, net_params, n_trials=2, n_cores=1) 

# modify params as in tutorial

# plot conn

# voltage traces ?

# stats

# dipole spectrogram

# LFP / CSD

# granger causality

# batch explore params

# modify netParams interactively 
