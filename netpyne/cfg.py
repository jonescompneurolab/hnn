"""
cfg.py 

Simulationg configuration for NetPyNE-based HNN network model

Contributors: salvadordura@gmail.com
"""

from netpyne import specs

cfg = specs.SimConfig()  

cfg.checkErrors = False # True # leave as False to avoid extra printouts


# ############################################################################
#
# SIMULATION CONFIGURATION
#
# ############################################################################

# ----------------------------------------------------------------------------
#
# NetPyNE config parameters (not part of original HNN implementation)
#
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Run parameters
# ----------------------------------------------------------------------------
cfg.duration = 250 
cfg.seeds = {'conn': 4321, 'stim': 1234, 'loc': 4321} 
cfg.hParams['v_init'] = -80  
cfg.verbose = 0
cfg.cvode_active = False
cfg.printRunTime = 0.1
cfg.printPopAvgRates = True

# ----------------------------------------------------------------------------
# Recording 
# ----------------------------------------------------------------------------
cfg.recordTraces = {'V_soma': {'sec': 'soma', 'loc': 0.5, 'var': 'v'}}
cfg.recordStims = False  
cfg.recordStep = 0.1 

# ----------------------------------------------------------------------------
# Saving
# ----------------------------------------------------------------------------
cfg.sim_prefix = cfg.simLabel = 'default'

cfg.saveFolder = '.'
cfg.savePickle = False
cfg.saveJson = False
cfg.saveDataInclude = ['simData', 'simConfig'] #, 'netParams', 'net']

# ----------------------------------------------------------------------------
# Analysis and plotting 
# ----------------------------------------------------------------------------
cfg.analysis['plotTraces'] = {'include': [('L2Pyr',0), ('L5Pyr',0),('L2Basket',0), ('L5Basket',0) ], 'oneFigPer': 'trace', 'overlay': True, 'saveFig': False, 
							  'showFig': False, 'figSize': (10, 8), 'timeRange': [0, cfg.duration]}

cfg.analysis['plotRaster'] = {'include': ['all'], 'popRates': True, 'orderInverse': True}

cfg.analysis['plotConn'] = {'includePre': ['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket'], 'includePost': ['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket'],
                            'feature': 'numConns'}
#cfg.analysis['plotDipole'] = True


# ----------------------------------------------------------------------------
# Network parameters
# ----------------------------------------------------------------------------
cfg.gridSpacing = 50 # 50
cfg.sizeY = 1000 
cfg.localConn = True
cfg.rhythmicInputs = True
cfg.evokedInputs = True
cfg.poissonInputs = True
cfg.gaussInputs = True


# ----------------------------------------------------------------------------
#
# HNN original config parameters (adapted to NetPyNE)
#
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Run parameters
# ----------------------------------------------------------------------------
cfg.tstop = cfg.duration 
cfg.dt = 0.025
cfg.celsius = 37.0
cfg.hParams['celsius'] = cfg.celsius = 37 
cfg.threshold = 0.0 # firing threshold (sets netParams.defaultThreshold)


# ----------------------------------------------------------------------------
# Connectivity/synaptic parameters
# ----------------------------------------------------------------------------
# L2 cells
# Soma
cfg.L2Pyr_soma_L = 22.1
cfg.L2Pyr_soma_diam = 23.4
cfg.L2Pyr_soma_cm = 0.6195
cfg.L2Pyr_soma_Ra = 200.

# Dendrites
cfg.L2Pyr_dend_cm = 0.6195
cfg.L2Pyr_dend_Ra = 200.

cfg.L2Pyr_apicaltrunk_L = 59.5
cfg.L2Pyr_apicaltrunk_diam = 4.25

cfg.L2Pyr_apical1_L = 306.
cfg.L2Pyr_apical1_diam = 4.08

cfg.L2Pyr_apicaltuft_L = 238.
cfg.L2Pyr_apicaltuft_diam = 3.4

cfg.L2Pyr_apicaloblique_L = 340.
cfg.L2Pyr_apicaloblique_diam = 3.91

cfg.L2Pyr_basal1_L = 85.
cfg.L2Pyr_basal1_diam = 4.25

cfg.L2Pyr_basal2_L = 255.
cfg.L2Pyr_basal2_diam = 2.72

cfg.L2Pyr_basal3_L = 255.
cfg.L2Pyr_basal3_diam = 2.72

# Synapses
cfg.L2Pyr_ampa_e = 0.
cfg.L2Pyr_ampa_tau1 = 0.5
cfg.L2Pyr_ampa_tau2 = 5.

cfg.L2Pyr_nmda_e = 0.
cfg.L2Pyr_nmda_tau1 = 1.
cfg.L2Pyr_nmda_tau2 = 20.

cfg.L2Pyr_gabaa_e = -80.
cfg.L2Pyr_gabaa_tau1 = 0.5
cfg.L2Pyr_gabaa_tau2 = 5.

cfg.L2Pyr_gabab_e = -80.
cfg.L2Pyr_gabab_tau1 = 1.
cfg.L2Pyr_gabab_tau2 = 20.

# Biophysics soma
cfg.L2Pyr_soma_gkbar_hh2 = 0.01
cfg.L2Pyr_soma_gnabar_hh2 = 0.18
cfg.L2Pyr_soma_el_hh2 = -65.
cfg.L2Pyr_soma_gl_hh2 = 4.26e-5
cfg.L2Pyr_soma_gbar_km = 250.

# Biophysics dends
cfg.L2Pyr_dend_gkbar_hh2 = 0.01
cfg.L2Pyr_dend_gnabar_hh2 = 0.15
cfg.L2Pyr_dend_el_hh2 = -65.
cfg.L2Pyr_dend_gl_hh2 = 4.26e-5
cfg.L2Pyr_dend_gbar_km = 250.


# L5 cells
# Soma
cfg.L5Pyr_soma_L = 39.
cfg.L5Pyr_soma_diam = 28.9
cfg.L5Pyr_soma_cm = 0.85
cfg.L5Pyr_soma_Ra = 200.

# Dendrites
cfg.L5Pyr_dend_cm = 0.85
cfg.L5Pyr_dend_Ra = 200.

cfg.L5Pyr_apicaltrunk_L = 102.
cfg.L5Pyr_apicaltrunk_diam = 10.2

cfg.L5Pyr_apical1_L = 680.
cfg.L5Pyr_apical1_diam = 7.48

cfg.L5Pyr_apical2_L = 680.
cfg.L5Pyr_apical2_diam = 4.93

cfg.L5Pyr_apicaltuft_L = 425.
cfg.L5Pyr_apicaltuft_diam = 3.4

cfg.L5Pyr_apicaloblique_L = 255.
cfg.L5Pyr_apicaloblique_diam = 5.1

cfg.L5Pyr_basal1_L = 85.
cfg.L5Pyr_basal1_diam = 6.8

cfg.L5Pyr_basal2_L = 255.
cfg.L5Pyr_basal2_diam = 8.5

cfg.L5Pyr_basal3_L = 255.
cfg.L5Pyr_basal3_diam = 8.5

# Synapses
cfg.L5Pyr_ampa_e = 0.
cfg.L5Pyr_ampa_tau1 = 0.5
cfg.L5Pyr_ampa_tau2 = 5.

cfg.L5Pyr_nmda_e = 0.
cfg.L5Pyr_nmda_tau1 = 1.
cfg.L5Pyr_nmda_tau2 = 20.

cfg.L5Pyr_gabaa_e = -80.
cfg.L5Pyr_gabaa_tau1 = 0.5
cfg.L5Pyr_gabaa_tau2 = 5.

cfg.L5Pyr_gabab_e = -80.
cfg.L5Pyr_gabab_tau1 = 1.
cfg.L5Pyr_gabab_tau2 = 20.

# Biophysics soma
cfg.L5Pyr_soma_gkbar_hh2 = 0.01
cfg.L5Pyr_soma_gnabar_hh2 = 0.16
cfg.L5Pyr_soma_el_hh2 = -65.
cfg.L5Pyr_soma_gl_hh2 = 4.26e-5
cfg.L5Pyr_soma_gbar_ca = 60.
cfg.L5Pyr_soma_taur_cad = 20.
cfg.L5Pyr_soma_gbar_kca = 2e-4
cfg.L5Pyr_soma_gbar_km = 200.
cfg.L5Pyr_soma_gbar_cat = 2e-4
cfg.L5Pyr_soma_gbar_ar = 1e-6

# Biophysics dends
cfg.L5Pyr_dend_gkbar_hh2 = 0.01
cfg.L5Pyr_dend_gnabar_hh2 = 0.14
cfg.L5Pyr_dend_el_hh2 = -71.
cfg.L5Pyr_dend_gl_hh2 = 4.26e-5
cfg.L5Pyr_dend_gbar_ca = 60.
cfg.L5Pyr_dend_taur_cad = 20.
cfg.L5Pyr_dend_gbar_kca = 2e-4
cfg.L5Pyr_dend_gbar_km = 200.
cfg.L5Pyr_dend_gbar_cat = 2e-4
cfg.L5Pyr_dend_gbar_ar = 1e-6



# ----------------------------------------------------------------------------
# Network size parameters
# ----------------------------------------------------------------------------
# numbers of cells making up the pyramidal grids
cfg.N_pyr_x = 10
cfg.N_pyr_y = 10


# ----------------------------------------------------------------------------
# Connectivity/synaptic parameters
# ----------------------------------------------------------------------------
# maximal conductances for all synapses
# max conductances TO L2Pyrs
cfg.gbar_L2Pyr_L2Pyr_ampa = 0.
cfg.gbar_L2Pyr_L2Pyr_nmda = 0.
cfg.gbar_L2Basket_L2Pyr_gabaa = 0.
cfg.gbar_L2Basket_L2Pyr_gabab = 0.

# max conductances TO L2Baskets
cfg.gbar_L2Pyr_L2Basket = 0.
cfg.gbar_L2Basket_L2Basket = 0.

# max conductances TO L5Pyr
cfg.gbar_L5Pyr_L5Pyr_ampa = 0.
cfg.gbar_L5Pyr_L5Pyr_nmda = 0.
cfg.gbar_L2Pyr_L5Pyr = 0.
cfg.gbar_L2Basket_L5Pyr = 0.
cfg.gbar_L5Basket_L5Pyr_gabaa = 0.
cfg.gbar_L5Basket_L5Pyr_gabab = 0.

# max conductances TO L5Baskets
cfg.gbar_L5Basket_L5Basket = 0.
cfg.gbar_L5Pyr_L5Basket = 0.
cfg.gbar_L2Pyr_L5Basket = 0.

# ----------------------------------------------------------------------------
# Random Inputs parameters
# ----------------------------------------------------------------------------
# amplitudes of individual Gaussian random inputs to L2Pyr and L5Pyr
# L2 Basket params
cfg.L2Basket_Gauss_A_weight = 0.
cfg.L2Basket_Gauss_mu = 2000.
cfg.L2Basket_Gauss_sigma = 3.6
cfg.L2Basket_Pois_A_weight_ampa = 0.
cfg.L2Basket_Pois_A_weight_nmda = 0.
cfg.L2Basket_Pois_lamtha = 0.

# L2 Pyr params
cfg.L2Pyr_Gauss_A_weight = 0.
cfg.L2Pyr_Gauss_mu = 2000.
cfg.L2Pyr_Gauss_sigma = 3.6
cfg.L2Pyr_Pois_A_weight_ampa = 0.
cfg.L2Pyr_Pois_A_weight_nmda = 0.
cfg.L2Pyr_Pois_lamtha = 0.

# L5 Pyr params
cfg.L5Pyr_Gauss_A_weight = 0.
cfg.L5Pyr_Gauss_mu = 2000.
cfg.L5Pyr_Gauss_sigma = 4.8
cfg.L5Pyr_Pois_A_weight_ampa = 0.
cfg.L5Pyr_Pois_A_weight_nmda = 0.
cfg.L5Pyr_Pois_lamtha = 0.

# L5 Basket params
cfg.L5Basket_Gauss_A_weight = 0.
cfg.L5Basket_Gauss_mu = 2000.
cfg.L5Basket_Gauss_sigma = 2.
cfg.L5Basket_Pois_A_weight_ampa = 0.
cfg.L5Basket_Pois_A_weight_nmda = 0.
cfg.L5Basket_Pois_lamtha = 0.

# default end time for pois inputs
cfg.t0_pois = 0.
cfg.T_pois = -1


# ----------------------------------------------------------------------------
# Rhythmic inputs parameters
# ----------------------------------------------------------------------------
# Ongoing proximal alpha rhythm
cfg.distribution_prox = 'normal'
cfg.t0_input_prox = 1000.
cfg.tstop_input_prox = 250.
cfg.f_input_prox = 10.
cfg.f_stdev_prox = 20.
cfg.events_per_cycle_prox = 2
cfg.repeats_prox = 10
cfg.t0_input_stdev_prox = 0.0

# Ongoing distal alpha rhythm
cfg.distribution_dist = 'normal'
cfg.t0_input_dist = 1000.
cfg.tstop_input_dist = 250.
cfg.f_input_dist = 10.
cfg.f_stdev_dist = 20.
cfg.events_per_cycle_dist = 2
cfg.repeats_dist = 10
cfg.t0_input_stdev_dist = 0.0

# ----------------------------------------------------------------------------
# Thalamic inputs parameters
# ----------------------------------------------------------------------------
# thalamic input amplitudes and delays
cfg.input_prox_A_weight_L2Pyr_ampa = 0.
cfg.input_prox_A_weight_L2Pyr_nmda = 0.
cfg.input_prox_A_weight_L5Pyr_ampa = 0.
cfg.input_prox_A_weight_L5Pyr_nmda = 0.
cfg.input_prox_A_weight_L2Basket_ampa = 0.
cfg.input_prox_A_weight_L2Basket_nmda = 0.
cfg.input_prox_A_weight_L5Basket_ampa = 0.
cfg.input_prox_A_weight_L5Basket_nmda = 0.
cfg.input_prox_A_delay_L2 = 0.1
cfg.input_prox_A_delay_L5 = 1.0

# current values, not sure where these distal values come from, need to check
cfg.input_dist_A_weight_L2Pyr_ampa = 0.
cfg.input_dist_A_weight_L2Pyr_nmda = 0.
cfg.input_dist_A_weight_L5Pyr_ampa = 0.
cfg.input_dist_A_weight_L5Pyr_nmda = 0.
cfg.input_dist_A_weight_L2Basket_ampa = 0.
cfg.input_dist_A_weight_L2Basket_nmda = 0.
cfg.input_dist_A_delay_L2 = 5.
cfg.input_dist_A_delay_L5 = 5.

# ----------------------------------------------------------------------------
# Evoked responses parameters
# ----------------------------------------------------------------------------
# times and stdevs for evoked responses
cfg.dt_evprox0_evdist = -1, # not used in GU
cfg.dt_evprox0_evprox1 = -1, # not used in GU
cfg.sync_evinput = 1, # whether evoked inputs arrive at same time to all cell
cfg.inc_evinput = 0.0, # increment (ms) for avg evoked input start (for trial n, avg start time is n * evinputin

# ----------------------------------------------------------------------------
# Current clamp parameters
# ----------------------------------------------------------------------------
# IClamp params for L2Pyr
cfg.Itonic_A_L2Pyr_soma = 0.
cfg.Itonic_t0_L2Pyr_soma = 0.
cfg.Itonic_T_L2Pyr_soma = -1.

# IClamp param for L2Basket
cfg.Itonic_A_L2Basket = 0.
cfg.Itonic_t0_L2Basket = 0.
cfg.Itonic_T_L2Basket = -1.

# IClamp params for L5Pyr
cfg.Itonic_A_L5Pyr_soma = 0.
cfg.Itonic_t0_L5Pyr_soma = 0.
cfg.Itonic_T_L5Pyr_soma = -1.

# IClamp param for L5Basket
cfg.Itonic_A_L5Basket = 0.
cfg.Itonic_t0_L5Basket = 0.
cfg.Itonic_T_L5Basket = -1.

# ----------------------------------------------------------------------------
# Analysis parameters
# ----------------------------------------------------------------------------
cfg.save_spec_data = 0
cfg.f_max_spec = 40.
cfg.dipole_scalefctr = 30e3, # scale factor for dipole - default at 30e
#based on scaling needed to match model ongoing rhythms from jones 2009 - for ERPs can use 300
# for ongoing rhythms + ERPs ... use ... ?
cfg.dipole_smooth_win = 15.0, # window for smoothing (box filter) - 15 ms from jones 2009; shorte
# in case want to look at higher frequency activity
cfg.save_figs = 0
cfg.save_vsoma = 0, # whether to record/save somatic voltag

# ----------------------------------------------------------------------------
# Trials/seeding parameters
# ----------------------------------------------------------------------------
# numerics
# N_trials of 1 means that seed is set by rank
cfg.N_trials = 1

# prng_state is a string for a filename containing the random state one wants to use
# prng seed cores are the base integer seed for the specific
# prng object for a specific random number stream
cfg.prng_state = None
cfg.prng_seedcore_input_prox = 0
cfg.prng_seedcore_input_dist = 0
cfg.prng_seedcore_extpois = 0
cfg.prng_seedcore_extgauss = 0


