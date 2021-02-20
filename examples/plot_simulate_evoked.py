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


###############################################################################
# Let us import hnn_netpyne

from hnn_funcs import read_params, create_network, simulate_trials
from hnn_funcs.viz import plot_cells  #plot_dipole, plot_raster, plot_spike_hist, mean_rates

cfg_params, net_params = read_params(model_folder='../hnn_models/hnn_neocortex', params_fname='param/default.param')

# hnn_params = cfg_params.hnn_params

# net = create_network(cfg_params, net_params)  # this is really just the netParams or mixtude of netParams and non-instantiated net; cell locs and stims

# plot_cells()


trials_data = simulate_trials(cfg_params, net_params, n_trials=2)  # this can be done using netpyne batch (via disk) or hnn-core backends (via memory)

# plot_dipole(trials_data, options)

# plot_raster(trials_data, options)

# plot_spike_hist(trials_data, options)

# mean_rates(trials_data, options)

# user_params.update({'sync_evinput': True}) # alternative: user_params.sync_evinput = True

# net_sync = create_network(user_params, net_params)

# trials_data_sync = simulate_trials(net, n_trials=1)

# plot_dipoles(trials_data_sync, options)


