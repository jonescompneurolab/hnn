"""
====================
Simulate alpha waves
====================

This example demonstrates how to simulate alpha waves using
HNN-core.
"""


# Let us import hnn_api
from hnn_api import read_params, create_network, simulate_trials, mean_rates
from hnn_api.viz import plot_cells, plot_dipole, plot_spike_raster, plot_spike_hist, netpyne_plot, print 


cfg_params = read_params(model_folder='../hnn_models/hnn_neocortex', params_fname='param/ERPYes1Trial.param') 

hnn_params = cfg_params.hnn_params

# Remove all evoked proximal feed parameters
for key in [k for k in hnn_params if 'evprox' in k]:
    del hnn_params[key]

# Remove all evoked distal feed parameters
for key in [k for k in hnn_params if 'evdist' in k]:
    del hnn_params[key]

# Now, we update a few rhythmic feed parameters
hnn_params.update({
    'dipole_scalefctr': 150000.0,
    'dipole_smooth_win': 0,
    'tstop': 310.0,
    't0_input_dist': 50.0,
    'tstop_input_dist': 1001.0,
    'input_dist_A_weight_L2Pyr_ampa': 5.4e-5,
    'input_dist_A_weight_L5Pyr_ampa': 5.4e-5,
    'sync_evinput': 1,
    "prng_seedcore_input_dist": 3
})

###############################################################################
# Now let's simulate the dipole and plot it
trials_data = simulate_trials(cfg_params, n_trials=1, n_cores=2)
plot_dipole(trials_data)

###############################################################################
# We can confirm that what we simulate is indeed 10 Hz activity.
import matplotlib.pyplot as plt
from scipy.signal import spectrogram
import numpy as np
sfreq = 1000. / hnn_params['dt']
n_fft = 1024 * 8
dpl = trials_data[0]['dpl']
freqs, _, psds = spectrogram(
    dpl.data['agg'], sfreq, window='hamming', nfft=n_fft,
    nperseg=n_fft, noverlap=0)
plt.figure()
plt.plot(freqs, np.mean(psds, axis=-1))
plt.xlim((0, 40))
plt.xlabel('Frequency (Hz)')
plt.ylabel('PSD')
plt.show()

