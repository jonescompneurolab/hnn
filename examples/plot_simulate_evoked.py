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
from hnn_api.viz import plot_cells, plot_dipole, plot_spike_raster, plot_spike_hist, netpyne_plot, print 

# Then we read the parameters file
cfg_params = read_params(model_folder='../hnn_models/hnn_neocortex', params_fname='param/ERPYes1Trial.param') 

print(cfg_params.hnn_params)

# Let us first create our network from the params file and visualize the cells inside it.
net = create_network(cfg_params) 
plot_cells(net)
    
# let's simulate the dipole, running 2 trials 
trials_data = simulate_trials(cfg_params, n_trials=2, n_cores=4) 

# and then plot it
plot_dipole(trials_data)
plot_spike_hist(trials_data)
plot_spike_raster(trials_data)

# We can additionally calculate the mean spike rates 
all_rates = mean_rates(trials_data, mean_type='all')
print('Mean spike rates across trials: ') 
print(all_rates)

trial_rates = mean_rates(trials_data, mean_type='trial')
print('Mean spike rates for individual trials: ')
print(trial_rates)

# Now, let us try to make the exogenous driving inputs to the cells synchronous and see what happens
cfg_params.hnn_params['sync_evinput'] = True  # alternatively can use dict.update()
trials_data_sync = simulate_trials(cfg_params, n_trials=1, n_cores=4)

plot_dipole(trials_data_sync)
plot_spike_hist(trials_data_sync)
plot_spike_raster(trials_data_sync)

