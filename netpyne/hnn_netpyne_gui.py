
"""
netParams.py 

High-level specifications for HNN network model using NetPyNE

Contributors: salvadordura@gmail.com
"""

from netpyne import specs
import numpy as np
import itertools as it


"""
cfg.py 

Simulationg configuration for NetPyNE-based HNN network model

Contributors: salvadordura@gmail.com
"""


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
cfg.hParams['v_init'] = -65  
cfg.verbose = 0
cfg.cvode_active = False
cfg.printRunTime = 0.1
cfg.printPopAvgRates = True
cfg.distributeSynsUniformly = False  # one syn per section in list of sections
cfg.allowSelfConns = False  # allow connections from a cell to itself
cfg.allowConnsWithWeight0 = False # do not allow conns with weight 0 (faster)

# ----------------------------------------------------------------------------
# Recording 
# ----------------------------------------------------------------------------
cfg.recordTraces = {'V_soma': {'sec': 'soma', 'loc': 0.5, 'var': 'v'}}
cfg.recordCells = [('L2Basket',0), ('L2Pyr',0), ('L5Basket',0), ('L5Pyr',0)]  
cfg.recordStims = False  
cfg.recordStep = 0.025

# cfg.recordLFP = [[50, 50, 50], [50, 1300, 50]]

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
# ----------------------------------------------------------------------------
# Network parameters
# ----------------------------------------------------------------------------
cfg.gridSpacingPyr = 1  # 50
cfg.gridSpacingBasket = [1, 1, 3]  
cfg.xzScaling = 100
cfg.sizeY = 2000 

cfg.localConn = True
cfg.rhythmicInputs = True
cfg.evokedInputs = True
cfg.tonicInputs = True
cfg.poissonInputs = True
cfg.gaussInputs = True


# ----------------------------------------------------------------------------
#
# HNN parameters in original GUI but not in config files (adapted to NetPyNE)
#
# ----------------------------------------------------------------------------

cfg.EEgain = 1.0
cfg.EIgain = 1.0
cfg.IEgain = 1.0
cfg.IIgain = 1.0


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
# Cell parameters
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
cfg.dipole_scalefctr = 30e3 # scale factor for dipole - default at 30e
#based on scaling needed to match model ongoing rhythms from jones 2009 - for ERPs can use 300
# for ongoing rhythms + ERPs ... use ... ?
cfg.dipole_smooth_win = 15.0 # window for smoothing (box filter) - 15 ms from jones 2009; shorte
# in case want to look at higher frequency activity
cfg.save_figs = 0
cfg.save_vsoma = 0 # whether to record/save somatic voltag

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





# ----------------------------------------------------------------------------
# Cell parameters
# ----------------------------------------------------------------------------

# dictionary to store cellParams (cell property rules)
cellParams = specs.CellParams()

# ------------------------------------------------------------------------------------
# L2 Pyr cell rule
# ------------------------------------------------------------------------------------
cellParams['L2Pyr_rule'] = {
        'conds': {'cellType': 'L2Pyr'},
        'secLists': {
            'apical': ['apical_trunk', 'apical_1', 'apical_tuft', 'apical_oblique'],
            'basal': ['basal_1', 'basal_2', 'basal_3']},
        'secs': {
            'soma': {
                'geom': {'L': cfg.L2Pyr_soma_L, 
                        'Ra': cfg.L2Pyr_soma_Ra, 
                        'cm': cfg.L2Pyr_soma_cm, 
                        'diam': cfg.L2Pyr_soma_diam, 
                        'nseg': 1,
                    'pt3d': [[0.0, 0.0, 0.0, cfg.L2Pyr_soma_diam],
                        [0.0, 0.0+cfg.L2Pyr_soma_L, 0.0, cfg.L2Pyr_soma_diam]]},
                'ions': {
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}
                },
                'mechs': {},
                'topol': {}
            },
            'apical_1': {
                'geom': {'L': cfg.L2Pyr_apical1_L, 
                        'Ra': cfg.L2Pyr_dend_Ra, 
                        'cm': cfg.L2Pyr_dend_cm, 
                        'diam': cfg.L2Pyr_apical1_diam, 
                        'nseg': 7,
                    'pt3d': [
                        [0.0, 48.0, 0.0, cfg.L2Pyr_apical1_diam],
                        [0.0, 48.0+cfg.L2Pyr_apical1_L, 0.0, cfg.L2Pyr_apical1_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_trunk', 'parentX': 1.0}
            },
            'apical_oblique': {
                'geom': {'L': cfg.L2Pyr_apicaloblique_L, 
                        'Ra': cfg.L2Pyr_dend_Ra, 
                        'cm': cfg.L2Pyr_dend_cm, 
                        'diam': cfg.L2Pyr_apicaloblique_diam, 
                        'nseg': 7,
                    'pt3d': [[0.0, 48.0, 0.0, cfg.L2Pyr_apicaloblique_diam],
                        [0.0-cfg.L2Pyr_apicaloblique_L, 48.0, 0.0, cfg.L2Pyr_apicaloblique_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_trunk', 'parentX': 1.0}
            },
            'apical_trunk': {
                'geom': {'L': cfg.L2Pyr_apicaltrunk_L, 
                        'Ra': cfg.L2Pyr_dend_Ra, 
                        'cm': cfg.L2Pyr_dend_cm, 
                        'diam': cfg.L2Pyr_apicaltrunk_diam, 
                        'nseg': 1,
                    'pt3d': [
                        [0.0, 13.0, 0.0, cfg.L2Pyr_apicaltrunk_diam],
                        [0.0, 13.0+cfg.L2Pyr_apicaltrunk_L, 0.0, cfg.L2Pyr_apicaltrunk_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'soma', 'parentX': 1.0}
            },
            'apical_tuft': {
                'geom': {'L': cfg.L2Pyr_apicaltuft_L, 
                        'Ra': cfg.L2Pyr_dend_Ra, 
                        'cm': cfg.L2Pyr_dend_cm, 
                        'diam': cfg.L2Pyr_apicaltuft_diam, 
                        'nseg': 5,
                    'pt3d': [[0.0, 228.0, 0.0, cfg.L2Pyr_apicaltuft_diam],
                        [0.0, 228.0+cfg.L2Pyr_apicaltuft_L, 0.0, cfg.L2Pyr_apicaltuft_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_1', 'parentX': 1.0}
            },
            'basal_1': {
                'geom': {'L': cfg.L2Pyr_basal1_L, 
                        'Ra': cfg.L2Pyr_dend_Ra, 
                        'cm': cfg.L2Pyr_dend_cm, 
                        'diam': cfg.L2Pyr_basal1_diam, 
                        'nseg': 1,
                    'pt3d': [[0.0, 0.0, 0.0, cfg.L2Pyr_basal1_diam],
                        [0.0, 0.0-cfg.L2Pyr_basal1_L, 0.0, cfg.L2Pyr_basal1_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'soma', 'parentX': 0.0}
            },
            'basal_2': {
                'geom': {
                    'L': cfg.L2Pyr_basal2_L, 
                            'Ra': cfg.L2Pyr_dend_Ra, 
                            'cm': cfg.L2Pyr_dend_cm, 
                            'diam': cfg.L2Pyr_basal2_diam, 
                            'nseg': 5,
                    'pt3d': [[0.0, -50.0, 0.0, cfg.L2Pyr_basal2_diam],
                        [0.0-cfg.L2Pyr_basal2_L/np.sqrt(2), -50.0-cfg.L2Pyr_basal2_L/np.sqrt(2), 0.0, cfg.L2Pyr_basal2_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'basal_1', 'parentX': 1.0}
            },
            'basal_3': {
                'geom': {'L': cfg.L2Pyr_basal3_L, 
                        'Ra': cfg.L2Pyr_dend_Ra, 
                        'cm': cfg.L2Pyr_dend_cm, 
                        'diam': cfg.L2Pyr_basal3_diam, 
                        'nseg': 5,
                    'pt3d': [[0.0, -50.0, 0.0, cfg.L2Pyr_basal3_diam],
                        [0.0+cfg.L2Pyr_basal3_L/np.sqrt(2), -50.0-cfg.L2Pyr_basal3_L/np.sqrt(2), 0.0, cfg.L2Pyr_basal3_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'basal_1', 'parentX': 1.0}
        }}}

## add biophysics (ions and mechs) to L2Pyr dendrites
somaL = cellParams['L2Pyr_rule']['secs']['soma']['geom']['L']

for sec in [sec for secName, sec in cellParams['L2Pyr_rule']['secs'].items() if secName != 'soma']:
    sec['ions'] = {
        'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
        'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}}
    
    sec['mechs'] = {}

## set vinit
for sec in cellParams['L2Pyr_rule']['secs'].values():
    sec['vinit'] = -71.46


# ------------------------------------------------------------------------------------
# L2 Basket cell rule
# ------------------------------------------------------------------------------------
cellParams['L2Basket_rule'] = {
        'conds': {'cellType': 'L2Basket'},
        'secs': {
            'soma': {
                'geom': {'L': 39.0, 
                        'Ra': 200.0, 
                        'cm': 0.85, 
                        'diam': 20.0, 
                        'nseg': 1},
                'ions': {
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0,'o': 140.0}},
                'mechs': {},
                'topol': {}
        }}}

## set vinit
for secName,sec in cellParams['L2Basket_rule']['secs'].items():
    sec['vinit'] = -64.9737

# ------------------------------------------------------------------------------------
# L5 Pyramidal cell rule
# ------------------------------------------------------------------------------------

cellParams['L5Pyr_rule'] = {
        'conds': {'cellType': 'L5Pyr'},
        'secLists': {
            'apical': ['apical_trunk', 'apical_1', 'apical_2', 'apical_tuft', 'apical_oblique'],
            'basal': ['basal_1', 'basal_2', 'basal_3']},
        'secs': {
            'soma': {
                'geom': {'L': cfg.L5Pyr_soma_L, 
                        'Ra': cfg.L5Pyr_soma_Ra, 
                        'cm': cfg.L5Pyr_soma_cm, 
                        'diam': cfg.L5Pyr_soma_diam, 
                        'nseg': 1,
                    'pt3d': [[0.0, 0.0, 0.0, cfg.L5Pyr_soma_diam],
                        [0.0, 0.0+cfg.L5Pyr_soma_L, 0.0, cfg.L5Pyr_soma_diam]]},
                'ions': {
                    'ca': {'e': 132.4579341637009, 'i': 5e-05, 'o': 2.0},
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}},
                'mechs': {},
                'topol': {}
            },
            'apical_1': {
                'geom': {'L': cfg.L5Pyr_apical1_L, 
                        'Ra': cfg.L5Pyr_dend_Ra, 
                        'cm': cfg.L5Pyr_dend_cm, 
                        'diam': cfg.L5Pyr_apical1_diam, 
                        'nseg': 13,
                    'pt3d': [[0.0, 83.0, 0.0, cfg.L5Pyr_apical1_diam],
                        [0.0, 83.0+cfg.L5Pyr_apical1_L, 0.0, cfg.L5Pyr_apical1_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_trunk','parentX': 1.0}
            },
            'apical_2': {
                'geom': {'L': cfg.L5Pyr_apical2_L, 
                        'Ra': cfg.L5Pyr_dend_Ra, 
                        'cm': cfg.L5Pyr_dend_cm, 
                        'diam': cfg.L5Pyr_apical2_diam, 
                        'nseg': 13,
                    'pt3d': [[0.0, 483.0, 0.0, cfg.L5Pyr_apical2_diam],
                        [0.0, 483.0+cfg.L5Pyr_apical2_L, 0.0, cfg.L5Pyr_apical2_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_1', 'parentX': 1.0}
            },
            'apical_oblique': {
                'geom': {'L': cfg.L5Pyr_apicaloblique_L, 
                        'Ra': cfg.L5Pyr_dend_Ra, 
                        'cm': cfg.L5Pyr_dend_cm, 
                        'diam': cfg.L5Pyr_apicaloblique_diam, 
                        'nseg': 5,
                    'pt3d': [[0.0, 83.0, 0.0, cfg.L5Pyr_apicaloblique_diam],
                        [0.0-cfg.L5Pyr_apicaloblique_L, 83.0, 0.0, cfg.L5Pyr_apicaloblique_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_trunk', 'parentX': 1.0}
            },
            'apical_trunk': {
                'geom': {'L': cfg.L5Pyr_apicaltrunk_L, 
                        'Ra': cfg.L5Pyr_dend_Ra, 
                        'cm': cfg.L5Pyr_dend_cm, 
                        'diam': cfg.L5Pyr_apicaltrunk_diam, 
                        'nseg': 3,
                    'pt3d': [[0.0, 23.0, 0.0, cfg.L5Pyr_apicaltrunk_diam ],
                        [0.0, 23.0+cfg.L5Pyr_apicaltrunk_L, 0.0, cfg.L5Pyr_apicaltrunk_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'soma', 'parentX': 1.0}
            },
            'apical_tuft': {
                'geom': {'L': cfg.L5Pyr_apicaltuft_L, 
                        'Ra': cfg.L5Pyr_dend_Ra, 
                        'cm': cfg.L5Pyr_dend_cm, 
                        'diam': cfg.L5Pyr_apicaltuft_diam, 
                        'nseg': 9,
                    'pt3d': [[0.0, 883.0, 0.0, cfg.L5Pyr_apicaltuft_diam],
                        [0.0, 883.0+cfg.L5Pyr_apicaltuft_L, 0.0, cfg.L5Pyr_apicaltuft_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_2', 'parentX': 1.0}
            },
            'basal_1': {
                'geom': {'L': cfg.L5Pyr_basal1_L, 
                        'Ra': cfg.L5Pyr_dend_Ra, 
                        'cm': cfg.L5Pyr_dend_cm, 
                        'diam': cfg.L5Pyr_basal1_diam, 
                        'nseg': 1,
                    'pt3d': [[0.0, 0.0, 0.0, cfg.L5Pyr_basal1_diam],
                        [0.0, 0.0-cfg.L5Pyr_basal1_L, 0.0, cfg.L5Pyr_basal1_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'soma', 'parentX': 0.0}
            },
            'basal_2': {
                'geom': {'L': cfg.L5Pyr_basal2_L, 
                        'Ra': cfg.L5Pyr_dend_Ra, 
                        'cm': cfg.L5Pyr_dend_cm, 
                        'diam': cfg.L5Pyr_basal2_diam, 
                        'nseg': 5,
                    'pt3d': [[0.0, -50.0, 0.0, cfg.L5Pyr_basal2_diam],
                        [0.0-cfg.L5Pyr_basal2_L/np.sqrt(2), -50-cfg.L5Pyr_basal2_L/np.sqrt(2), 0.0, cfg.L5Pyr_basal2_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'basal_1', 'parentX': 1.0}
            },
            'basal_3': {
                'geom': {'L': cfg.L5Pyr_basal3_L, 
                        'Ra': cfg.L5Pyr_dend_Ra, 
                        'cm': cfg.L5Pyr_dend_cm, 
                        'diam': cfg.L5Pyr_basal3_diam, 
                        'nseg': 5,
                    'pt3d': [[0.0, -50.0, 0.0, cfg.L5Pyr_basal3_diam],
                        [0.0+cfg.L5Pyr_basal2_L/np.sqrt(2), -50-cfg.L5Pyr_basal2_L/np.sqrt(2), 0.0, cfg.L5Pyr_basal3_diam]]},
                'topol': {
                    'childX': 0.0,
                    'parentSec': 'basal_1',
                    'parentX': 1.0}
        }}}

## add biophysics (ions and mechs) to L5Pyr dendrites

gbar_ar = {  # values calculated for each segment as: seg.gbar_ar = 1e-6 * np.exp(3e-3 * h.distance(seg.x)) (from orig HNN)
    'apical_trunk': [1.1829366e-06, 1.3099645e-06, 1.450633e-06],
    'apical_1': [1.6511327e-06, 1.9316694e-06, 2.2598709e-06, 2.6438357e-06, 3.0930382e-06, 3.6185628e-06, 4.2333769e-06, 4.9526514e-06, 5.7941347e-06, 6.7785908e-06, 7.9303114e-06, 9.2777159e-06, 1.0854052e-05],
    'apical_2': [1.2698216e-05, 1.4855715e-05, 1.7379784e-05, 2.0332707e-05, 2.3787348e-05, 2.7828952e-05, 3.2557247e-05, 3.8088907e-05, 4.4560426e-05, 5.2131493e-05, 6.0988926e-05, 7.1351287e-05, 8.3474272e-05],
    'apical_tuft': [9.6914906e-05, 0.00011166463, 0.00012865915, 0.00014824011, 0.00017080115, 0.0001967958, 0.00022674665, 0.0002612558, 0.00030101698], 'apical_oblique': [1.6478971e-06, 1.9203357e-06, 2.2378151e-06, 2.6077819e-06, 3.0389133e-06],
    'basal_1': [1.1359849e-06],
    'basal_2': [1.3930561e-06, 1.6233631e-06, 1.8917456e-06, 2.2044984e-06, 2.5689571e-06],
    'basal_3': [1.3930561e-06, 1.6233631e-06, 1.8917456e-06, 2.2044984e-06, 2.5689571e-06]}

somaL = cellParams['L5Pyr_rule']['secs']['soma']['geom']['L']

for secName, sec in [(secName, sec) for secName, sec in cellParams['L5Pyr_rule']['secs'].items() if secName != 'soma']:
    sec['ions'] = {
        'ca': {'e': 132.4579341637009, 'i': 5e-05, 'o': 2.0},
        'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
        'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}}

    L = sec['geom']['L']
    nseg = sec['geom']['nseg']
    
    sec['mechs'] = {}

## set vinit
for secName,sec in cellParams['L5Pyr_rule']['secs'].items():
    if secName == 'apical_1':
        sec['vinit'] = -71.32
    elif secName == 'apical_2':
        sec['vinit'] = -69.08
    elif secName == 'apical_tuft':
        sec['vinit'] = -67.30
    else:
        sec['vinit'] = -72.


# ------------------------------------------------------------------------------------
# L5 Basket cell rule
# ------------------------------------------------------------------------------------
cellParams['L5Basket_rule'] = {
        'conds': {'cellType': 'L5Basket'},
        'secs': {
            'soma': {
                'geom': {'L': 39.0, 
                        'Ra': 200.0, 
                        'cm': 0.85, 
                        'diam': 20.0, 
                        'nseg': 1},
                'ions': {
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0,'o': 140.0}},
                'mechs': {},
                'topol': {}
        }}}

## set vinit
for secName,sec in cellParams['L5Basket_rule']['secs'].items():
    sec['vinit'] = -64.9737





# ----------------------------------------------------------------------------
#
# NETWORK PARAMETERS
#
# ----------------------------------------------------------------------------

netParams = specs.NetParams()  # object of class NetParams to store the network parameters

#------------------------------------------------------------------------------
# General network parameters
#------------------------------------------------------------------------------
netParams.sizeX = ((cfg.N_pyr_x * cfg.gridSpacingPyr) - 1) * cfg.xzScaling  # x-dimension (horizontal length) size in um
netParams.sizeY = cfg.sizeY # y-dimension (vertical height or cortical depth) size in um
netParams.sizeZ = ((cfg.N_pyr_y * cfg.gridSpacingPyr) - 1) * cfg.xzScaling # z-dimension (horizontal depth) size in um
netParams.shape = 'cuboid'


# ----------------------------------------------------------------------------
# Cell parameters
# ----------------------------------------------------------------------------
netParams.cellParams = cellParams


# ----------------------------------------------------------------------------
# Population parameters
# ----------------------------------------------------------------------------

# layer locations
layersE = {'L2': [0.0*cfg.sizeY, 0.0*cfg.sizeY], 'L5': [0.654*cfg.sizeY, 0.654*cfg.sizeY]} # 0.654 = 1308/2000
layersI = {'L2': [0.0*cfg.sizeY-100.0, 0.0*cfg.sizeY-100.0], 'L5': [0.654*cfg.sizeY-100.0, 0.654*cfg.sizeY-100.0]}

# Create list of locations for Basket cells based on original ad hoc rules 
# define relevant x spacings for basket cells
xzero = np.arange(0, cfg.N_pyr_x, 3)
xone = np.arange(1, cfg.N_pyr_x, 3)
yeven = np.arange(0, cfg.N_pyr_y, 2)
yodd = np.arange(1, cfg.N_pyr_y, 2)
coords = [pos for pos in it.product(xzero, yeven)] + [pos for pos in it.product(xone, yodd)]
coords_sorted = sorted(coords, key=lambda pos: pos[1])
L2BasketLocs = [{'x': int(coord[0]*cfg.xzScaling), 'y': layersI['L2'][0], 'z': int(coord[1]*cfg.xzScaling)} for coord in coords_sorted]
L5BasketLocs = [{'x': int(coord[0]*cfg.xzScaling), 'y': layersI['L5'][0], 'z': int(coord[1]*cfg.xzScaling)} for coord in coords_sorted]

# create popParams
netParams.popParams['L2Basket'] = {'cellType':  'L2Basket', 'cellModel': 'HH_simple', 'numCells': len(L2BasketLocs), 'cellsList': L2BasketLocs} 
netParams.popParams['L2Pyr'] =    {'cellType':  'L2Pyr',    'cellModel': 'HH_reduced', 'yRange': layersE['L2'],  'gridSpacing': cfg.gridSpacingPyr*cfg.xzScaling} 
netParams.popParams['L5Basket'] = {'cellType':  'L5Basket', 'cellModel': 'HH_simple',  'numCells': len(L5BasketLocs), 'cellsList': L5BasketLocs} 
netParams.popParams['L5Pyr'] =    {'cellType':  'L5Pyr',    'cellModel': 'HH_reduced', 'yRange': layersE['L5'],  'gridSpacing': cfg.gridSpacingPyr*cfg.xzScaling} 

# update gui variables
netpyne_geppetto.cfg = cfg
netpyne_geppetto.netParams = netParams