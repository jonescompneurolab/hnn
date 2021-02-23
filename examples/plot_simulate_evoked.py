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
from hnn_func import read_params, create_network, simulate_trials
from hnn_func.viz import plot_cells, plot_dipole, plot_spike_raster, plot_spike_hist, netpyne_plot, print #, plot_raster, plot_spike_hist, mean_rates


cfg_params, net_params = read_params(model_folder='../hnn_models/hnn_neocortex', params_fname='param/ERPYes100Trials.param') #default.param')

print(cfg_params.hnn_params)

# net = create_network(cfg_params, net_params)  # this is really just the netParams or mixtude of netParams and non-instantiated net; cell locs and stims

# plot_cells()

trials_data = simulate_trials(cfg_params, net_params, n_trials=2, n_cores=1)  # this can be done using netpyne batch (via disk) or hnn-core backends (via memory)

plot_dipole(trials_data)

plot_spike_hist(trials_data)

plot_spike_raster(trials_data)

# mean_rates(trials_data, options)

# user_params.update({'sync_evinput': True}) # alternative: user_params.sync_evinput = True

# net_sync = create_network(user_params, net_params)

# trials_data_sync = simulate_trials(net, n_trials=1)

# plot_dipoles(trials_data_sync, options)


