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
from hnn_api.viz import plot_cells, plot_dipole, plot_spike_raster, plot_spike_hist, netpyne_plot, print #, plot_raster, plot_spike_hist, mean_rates


cfg_params = read_params(model_folder='../hnn_models/hnn_neocortex_divergence', params_fname='param/ERPYes1Trial.param') 

hnn_params = cfg_params.hnn_params

hnn_params['div_evdist_1_L2Pyr'] = 5
hnn_params['div_evdist_1_L2Basket'] = 5
hnn_params['div_evdist_1_L5Pyr'] = 5

trials_data = simulate_trials(cfg_params, n_trials=1, n_cores=1) 

plot_dipole(trials_data)
plot_spike_hist(trials_data)
plot_spike_raster(trials_data)

net=create_network(cfg_params, createNEURONObj=False, addConns=1, xzScaling=1)
print("\n Number of evoked distal inputs on a L2 Basket cell:")
print(len([c for c in net.cells[0].conns if 'evokedDistal' in c['label']]))

