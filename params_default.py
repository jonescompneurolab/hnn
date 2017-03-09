# params_default.py - master list of changeable params. most set to default val of inactive
#
# v 1.9.01
# rev 2015-12-08 (RL: added t0_pois)
# last major: (SL: Added default params for L2Basket and L5Basket cells)

# returns default params - see note
def get_params_default():
    """ Note that nearly all start times are set BEYOND tstop for this file
        Most values here are set to whatever default value inactivates them, such as 0 for conductance
        prng seed values are also set to 0 (non-random)
        flat file of default values
        will most often be overwritten
    """
    # set default params
    p = {
        'sim_prefix': 'default',

        # simulation end time (ms)
        'tstop': 250.,

        # numbers of cells making up the pyramidal grids
        'N_pyr_x': 1,
        'N_pyr_y': 1,

        # amplitudes of individual Gaussian random inputs to L2Pyr and L5Pyr
        # L2 Basket params
        'L2Basket_Gauss_A_weight': 0.,
        'L2Basket_Gauss_mu': 2000.,
        'L2Basket_Gauss_sigma': 3.6,
        'L2Basket_Pois_A_weight': 0.,
        'L2Basket_Pois_lamtha': 0.,

        # L2 Pyr params
        'L2Pyr_Gauss_A_weight': 0.,
        'L2Pyr_Gauss_mu': 2000.,
        'L2Pyr_Gauss_sigma': 3.6,
        'L2Pyr_Pois_A_weight': 0.,
        'L2Pyr_Pois_lamtha': 0.,

        # L5 Pyr params
        'L5Pyr_Gauss_A_weight': 0.,
        'L5Pyr_Gauss_mu': 2000.,
        'L5Pyr_Gauss_sigma': 4.8,
        'L5Pyr_Pois_A_weight': 0.,
        'L5Pyr_Pois_lamtha': 0.,

        # L5 Basket params
        'L5Basket_Gauss_A_weight': 0.,
        'L5Basket_Gauss_mu': 2000.,
        'L5Basket_Gauss_sigma': 2.,
        'L5Basket_Pois_A_weight': 0.,
        'L5Basket_Pois_lamtha': 0.,

        # maximal conductances for all synapses
        # max conductances TO L2Pyrs
        'gbar_L2Pyr_L2Pyr_ampa': 0.,
        'gbar_L2Pyr_L2Pyr_nmda': 0.,
        'gbar_L2Basket_L2Pyr_gabaa': 0.,
        'gbar_L2Basket_L2Pyr_gabab': 0.,

        # max conductances TO L2Baskets
        'gbar_L2Pyr_L2Basket': 0.,
        'gbar_L2Basket_L2Basket': 0.,

        # max conductances TO L5Pyr
        'gbar_L5Pyr_L5Pyr_ampa': 0.,
        'gbar_L5Pyr_L5Pyr_nmda': 0.,
        'gbar_L2Pyr_L5Pyr': 0.,
        'gbar_L2Basket_L5Pyr': 0.,
        'gbar_L5Basket_L5Pyr_gabaa': 0.,
        'gbar_L5Basket_L5Pyr_gabab': 0.,

        # max conductances TO L5Baskets
        'gbar_L5Basket_L5Basket': 0.,
        'gbar_L5Pyr_L5Basket': 0.,
        'gbar_L2Pyr_L5Basket': 0.,

        # Ongoing proximal alpha rhythm
        'distribution_prox': 'normal',
        't0_input_prox': 1000.,
        'tstop_input_prox': 250.,
        'f_input_prox': 10.,
        'f_stdev_prox': 20.,
        'events_per_cycle_prox': 2,

        # Ongoing distal alpha rhythm
        'distribution_dist': 'normal',
        't0_input_dist': 1000.,
        'tstop_input_dist': 250.,
        'f_input_dist': 10.,
        'f_stdev_dist': 20.,
        'events_per_cycle_dist': 2,

        # thalamic input amplitudes abd delays
        'input_prox_A_weight_L2Pyr_ampa': 0.,
        'input_prox_A_weight_L2Pyr_nmda': 0.,
        'input_prox_A_weight_L5Pyr_ampa': 0.,
        'input_prox_A_weight_L5Pyr_nmda': 0.,
        'input_prox_A_weight_inh_ampa': 0.,
        'input_prox_A_weight_inh_nmda': 0.,
        'input_prox_A_delay_L2': 0.1,
        'input_prox_A_delay_L5': 1.0,

        # current values, not sure where these distal values come from, need to check
        'input_dist_A_weight_L2Pyr_ampa': 0.,
        'input_dist_A_weight_L2Pyr_nmda': 0.,
        'input_dist_A_weight_L5Pyr_ampa': 0.,
        'input_dist_A_weight_L5Pyr_nmda': 0.,
        'input_dist_A_weight_inh_ampa': 0.,
        'input_dist_A_weight_inh_nmda': 0.,
        'input_dist_A_delay_L2': 5.,
        'input_dist_A_delay_L5': 5.,

        # evprox (early) feed strength
        'gbar_evprox_early_L2Pyr': 0.,
        'gbar_evprox_early_L5Pyr': 0.,
        'gbar_evprox_early_L2Basket': 0.,
        'gbar_evprox_early_L5Basket': 0.,

        # evprox (late) feed strength
        'gbar_evprox_late_L2Pyr': 0.,
        'gbar_evprox_late_L5Pyr': 0.,
        'gbar_evprox_late_L2Basket': 0.,
        'gbar_evprox_late_L5Basket': 0.,

        # evdist feed strengths
        'gbar_evdist_L2Pyr': 0.,
        'gbar_evdist_L5Pyr': 0.,
        'gbar_evdist_L2Basket': 0.,

        # times and stdevs for evoked responses
        't_evprox_early': 2000.,
        'sigma_t_evprox_early': 2.5,

        'dt_evprox0_evdist': -1,
        't_evdist': 2000.,
        'sigma_t_evdist': 6.,

        'dt_evprox0_evprox1': -1,
        't_evprox_late': 2000.,
        'sigma_t_evprox_late': 7.,

        # analysis
        'save_spec_data': 0,
        'f_max_spec': 40.,

        # IClamp params for L2Pyr
        'Itonic_A_L2Pyr_soma': 0.,
        'Itonic_t0_L2Pyr_soma': 0.,
        'Itonic_T_L2Pyr_soma': -1.,

        # IClamp param for L2Basket
        'Itonic_A_L2Basket': 0.,
        'Itonic_t0_L2Basket': 0.,
        'Itonic_T_L2Basket': -1.,

        # IClamp params for L5Pyr
        'Itonic_A_L5Pyr_soma': 0.,
        'Itonic_t0_L5Pyr_soma': 0.,
        'Itonic_T_L5Pyr_soma': -1.,

        # IClamp param for L5Basket
        'Itonic_A_L5Basket': 0.,
        'Itonic_t0_L5Basket': 0.,
        'Itonic_T_L5Basket': -1.,

        # numerics
        # N_trials of 0 means that seed is set by rank, will still run 1 trial (obviously)
        'N_trials': 0,

        # prng_state is a string for a filename containing the random state one wants to use
        # prng seed cores are the base integer seed for the specific
        # prng object for a specific random number stream
        # 'prng_state': None,
        'prng_seedcore_input_prox': 0,
        'prng_seedcore_input_dist': 0,
        'prng_seedcore_extpois': 0,
        'prng_seedcore_extgauss': 0,
        'prng_seedcore_evprox_early': 0,
        'prng_seedcore_evdist': 0,
        'prng_seedcore_evprox_late': 0,

        # default end time for pois inputs
        't0_pois': 0.,
        'T_pois': -1,
        'dt': 0.025,
    }

    # grab cell-specific params and update p accordingly
    p_L2Pyr = get_L2Pyr_params_default()
    p_L5Pyr = get_L5Pyr_params_default()
    p.update(p_L2Pyr)
    p.update(p_L5Pyr)

    return p

# returns default params for L2 pyramidal cell
def get_L2Pyr_params_default():
    return {
        # Soma
        'L2Pyr_soma_L': 22.1,
        'L2Pyr_soma_diam': 23.4,
        'L2Pyr_soma_cm': 0.6195,
        'L2Pyr_soma_Ra': 200.,

        # Dendrites
        'L2Pyr_dend_cm': 0.6195,
        'L2Pyr_dend_Ra': 200.,

        'L2Pyr_apicaltrunk_L': 59.5,
        'L2Pyr_apicaltrunk_diam': 4.25,

        'L2Pyr_apical1_L': 306.,
        'L2Pyr_apical1_diam': 4.08,

        'L2Pyr_apicaltuft_L': 238.,
        'L2Pyr_apicaltuft_diam': 3.4,

        'L2Pyr_apicaloblique_L': 340.,
        'L2Pyr_apicaloblique_diam': 3.91,

        'L2Pyr_basal1_L': 85.,
        'L2Pyr_basal1_diam': 4.25,

        'L2Pyr_basal2_L': 255.,
        'L2Pyr_basal2_diam': 2.72,

        'L2Pyr_basal3_L': 255.,
        'L2Pyr_basal3_diam': 2.72,

        # Synapses
        'L2Pyr_ampa_e': 0.,
        'L2Pyr_ampa_tau1': 0.5,
        'L2Pyr_ampa_tau2': 5.,

        'L2Pyr_nmda_e': 0.,
        'L2Pyr_nmda_tau1': 1.,
        'L2Pyr_nmda_tau2': 20.,

        'L2Pyr_gabaa_e': -80.,
        'L2Pyr_gabaa_tau1': 0.5,
        'L2Pyr_gabaa_tau2': 5.,

        'L2Pyr_gabab_e': -80.,
        'L2Pyr_gabab_tau1': 1.,
        'L2Pyr_gabab_tau2': 20.,

        # Biophysics soma
        'L2Pyr_soma_gkbar_hh': 0.01,
        'L2Pyr_soma_gnabar_hh': 0.18,
        'L2Pyr_soma_el_hh': -65.,
        'L2Pyr_soma_gl_hh': 4.26e-5,
        'L2Pyr_soma_gbar_km': 250.,

        # Biophysics dends
        'L2Pyr_dend_gkbar_hh': 0.01,
        'L2Pyr_dend_gnabar_hh': 0.15,
        'L2Pyr_dend_el_hh': -65.,
        'L2Pyr_dend_gl_hh': 4.26e-5,
        'L2Pyr_dend_gbar_km': 250.,
    }

# returns default params for L5 pyramidal cell
def get_L5Pyr_params_default():
    return {
        # Soma
        'L5Pyr_soma_L': 39.,
        'L5Pyr_soma_diam': 28.9,
        'L5Pyr_soma_cm': 0.85,
        'L5Pyr_soma_Ra': 200.,

        # Dendrites
        'L5Pyr_dend_cm': 0.85,
        'L5Pyr_dend_Ra': 200.,

        'L5Pyr_apicaltrunk_L': 102.,
        'L5Pyr_apicaltrunk_diam': 10.2,

        'L5Pyr_apical1_L': 680.,
        'L5Pyr_apical1_diam': 7.48,

        'L5Pyr_apical2_L': 680.,
        'L5Pyr_apical2_diam': 4.93,

        'L5Pyr_apicaltuft_L': 425.,
        'L5Pyr_apicaltuft_diam': 3.4,

        'L5Pyr_apicaloblique_L': 255.,
        'L5Pyr_apicaloblique_diam': 5.1,

        'L5Pyr_basal1_L': 85.,
        'L5Pyr_basal1_diam': 6.8,

        'L5Pyr_basal2_L': 255.,
        'L5Pyr_basal2_diam': 8.5,

        'L5Pyr_basal3_L': 255.,
        'L5Pyr_basal3_diam': 8.5,

        # Synapses
        'L5Pyr_ampa_e': 0.,
        'L5Pyr_ampa_tau1': 0.5,
        'L5Pyr_ampa_tau2': 5.,

        'L5Pyr_nmda_e': 0.,
        'L5Pyr_nmda_tau1': 1.,
        'L5Pyr_nmda_tau2': 20.,

        'L5Pyr_gabaa_e': -80.,
        'L5Pyr_gabaa_tau1': 0.5,
        'L5Pyr_gabaa_tau2': 5.,

        'L5Pyr_gabab_e': -80.,
        'L5Pyr_gabab_tau1': 1.,
        'L5Pyr_gabab_tau2': 20.,

        # Biophysics soma
        'L5Pyr_soma_gkbar_hh': 0.01,
        'L5Pyr_soma_gnabar_hh': 0.16,
        'L5Pyr_soma_el_hh': -65.,
        'L5Pyr_soma_gl_hh': 4.26e-5,
        'L5Pyr_soma_gbar_ca': 60.,
        'L5Pyr_soma_taur_cad': 20.,
        'L5Pyr_soma_gbar_kca': 2e-4,
        'L5Pyr_soma_gbar_km': 200.,
        'L5Pyr_soma_gbar_cat': 2e-4,
        'L5Pyr_soma_gbar_ar': 1e-6,

        # Biophysics dends
        'L5Pyr_dend_gkbar_hh': 0.01,
        'L5Pyr_dend_gnabar_hh': 0.14,
        'L5Pyr_dend_el_hh': -71.,
        'L5Pyr_dend_gl_hh': 4.26e-5,
        'L5Pyr_dend_gbar_ca': 60.,
        'L5Pyr_dend_taur_cad': 20.,
        'L5Pyr_dend_gbar_kca': 2e-4,
        'L5Pyr_dend_gbar_km': 200.,
        'L5Pyr_dend_gbar_cat': 2e-4,
        'L5Pyr_dend_gbar_ar': 1e-6,
    }
