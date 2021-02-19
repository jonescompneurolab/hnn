"""
===============
Simulate dipole
===============

This example demonstrates how to simulate a dipole for evoked-like
waveforms using HNN-netpyne.
"""


###############################################################################
# Let us import hnn_netpyne

from hnn-funcs import set_model, read_params, simulate_trials
from hnn-funcs.viz import plot_dipole, plot_raster, plot_spike_hist, mean_rates

user_params, net_params = read_params(model_folder='../hnn-models/hnn-neocortex', params_fname='param/default.param')

net = create_network(user_params, net_params)  # this is really just the netParams or mixtude of netParams and non-instantiated net; cell locs and stims

net.plot_cells()

trials_data = simulate_trials(net, n_trials=2)  # this can be done using netpyne batch (via disk) or hnn-core backends (via memory)

plot_dipole(trials_data, options)

plot_raster(trials_data, options)

plot_spike_hist(trials_data, options)

mean_rates(trials_data, options)

user_params.update({'sync_evinput': True}) # alternative: user_params.sync_evinput = True

net_sync = create_network(user_params, net_params)

trials_data_sync = simulate_trials(net, n_trials=1)

plot_dipoles(trials_data_sync, options)


