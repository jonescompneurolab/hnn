'''
 cellParams.py - High-level specifications for cells (redefine in netpyne instead of import)
 
 Modified from netpyne-generated JSON resulting from importing original Python cell templates

'''
import numpy as np
from netpyne import specs
from cfg import cfg

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
                    'pt3d': [[-50.0, 765.0, 0.0, cfg.L2Pyr_soma_diam],
                        [-50.0, 765.0+cfg.L2Pyr_soma_L, 0.0, cfg.L2Pyr_soma_diam]]},
                'ions': {
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}
                },
                'mechs': {
                    'dipole': {},
                    'hh2': {'el': cfg.L2Pyr_soma_el_hh2, 
                            'gkbar': cfg.L2Pyr_soma_gkbar_hh2, 
                            'gl': cfg.L2Pyr_soma_gl_hh2, 
                            'gnabar': cfg.L2Pyr_soma_gnabar_hh2},
                    'km': {'gbar': cfg.L2Pyr_soma_gbar_km}},
                'topol': {}
            },
            'apical_1': {
                'geom': {'L': cfg.L2Pyr_apical1_L, 
                        'Ra': cfg.L2Pyr_dend_Ra, 
                        'cm': cfg.L2Pyr_dend_cm, 
                        'diam': cfg.L2Pyr_apical1_diam, 
                        'nseg': 7,
                    'pt3d': [
                        [-50.0, 813.0, 0.0, cfg.L2Pyr_apical1_diam],
                        [-50.0, 813.0+cfg.L2Pyr_apical1_L, 0.0, cfg.L2Pyr_apical1_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_trunk', 'parentX': 1.0}
            },
            'apical_oblique': {
                'geom': {'L': cfg.L2Pyr_apicaloblique_L, 
                        'Ra': cfg.L2Pyr_dend_Ra, 
                        'cm': cfg.L2Pyr_dend_cm, 
                        'diam': cfg.L2Pyr_apicaloblique_diam, 
                        'nseg': 7,
                    'pt3d': [[-50.0, 813.0, 0.0, cfg.L2Pyr_apicaloblique_diam],
                        [-50-cfg.L2Pyr_apicaloblique_L, 813.0, 0.0, cfg.L2Pyr_apicaloblique_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_trunk', 'parentX': 1.0}
            },
            'apical_trunk': {
                'geom': {'L': cfg.L2Pyr_apicaltrunk_L, 
                        'Ra': cfg.L2Pyr_dend_Ra, 
                        'cm': cfg.L2Pyr_dend_cm, 
                        'diam': cfg.L2Pyr_apicaltrunk_diam, 
                        'nseg': 1,
                    'pt3d': [
                        [-50.0, 778.0, 0.0, cfg.L2Pyr_apicaltrunk_diam],
                        [-50.0, 778.0+cfg.L2Pyr_apicaltrunk_L, 0.0, cfg.L2Pyr_apicaltrunk_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'soma', 'parentX': 1.0}
            },
            'apical_tuft': {
                'geom': {'L': cfg.L2Pyr_apicaltuft_L, 
                        'Ra': cfg.L2Pyr_dend_Ra, 
                        'cm': cfg.L2Pyr_dend_cm, 
                        'diam': cfg.L2Pyr_apicaltuft_diam, 
                        'nseg': 5,
                    'pt3d': [[-50.0, 993.0, 0.0, cfg.L2Pyr_apicaltuft_diam],
                        [-50.0, 993.0+cfg.L2Pyr_apicaltuft_L, 0.0, cfg.L2Pyr_apicaltuft_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_1', 'parentX': 1.0}
            },
            'basal_1': {
                'geom': {'L': cfg.L2Pyr_basal1_L, 
                        'Ra': cfg.L2Pyr_dend_Ra, 
                        'cm': cfg.L2Pyr_dend_cm, 
                        'diam': cfg.L2Pyr_basal1_diam, 
                        'nseg': 1,
                    'pt3d': [[-50.0, 765.0, 0.0, cfg.L2Pyr_basal1_diam],
                        [-50.0, 765.0-cfg.L2Pyr_basal1_L, 0.0, cfg.L2Pyr_basal1_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'soma', 'parentX': 0.0}
            },
            'basal_2': {
                'geom': {
                    'L': cfg.L2Pyr_basal2_L, 
                            'Ra': cfg.L2Pyr_dend_Ra, 
                            'cm': cfg.L2Pyr_dend_cm, 
                            'diam': cfg.L2Pyr_basal2_diam, 
                            'nseg': 5,
                    'pt3d': [[-50.0, 715.0, 0.0, cfg.L2Pyr_basal2_diam],
                        [-50-cfg.L2Pyr_basal2_L/np.sqrt(2), 715.0-cfg.L2Pyr_basal2_L/np.sqrt(2), 0.0, cfg.L2Pyr_basal2_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'basal_1', 'parentX': 1.0}
            },
            'basal_3': {
                'geom': {'L': cfg.L2Pyr_basal3_L, 
                        'Ra': cfg.L2Pyr_dend_Ra, 
                        'cm': cfg.L2Pyr_dend_cm, 
                        'diam': cfg.L2Pyr_basal3_diam, 
                        'nseg': 5,
                    'pt3d': [[-50.0, 715.0, 0.0, cfg.L2Pyr_basal3_diam],
                        [-50.0+cfg.L2Pyr_basal3_L/np.sqrt(2), 715.0-cfg.L2Pyr_basal3_L/np.sqrt(2), 0.0, cfg.L2Pyr_basal3_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'basal_1', 'parentX': 1.0}
        }}}

## add biophysics (ions and mechs) to L2Pyr dendrites
somaL = cellParams['L2Pyr_rule']['secs']['soma']['geom']['L']

for sec in [sec for secName, sec in cellParams['L2Pyr_rule']['secs'].items() if secName != 'soma']:
    sec['ions'] = {
        'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
        'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}}
    
    sec['mechs'] = {
        'dipole': {},
        'hh2': {'el': cfg.L2Pyr_dend_el_hh2, 
                'gkbar': cfg.L2Pyr_dend_gkbar_hh2, 
                'gl': cfg.L2Pyr_dend_gl_hh2, 
                'gnabar': cfg.L2Pyr_dend_gnabar_hh2},
        'km': {'gbar': cfg.L2Pyr_dend_gbar_km}}


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
                'mechs': {
                    'hh2': {'el': -54.3, 
                            'gkbar': 0.036, 
                            'gl': 0.0003, 
                            'gnabar': 0.12}},
                'topol': {}
        }}}


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
                        [0.0, 0.0+cfg.L5Pyr_soma_diam, 0.0, cfg.L5Pyr_soma_diam]]},
                'ions': {
                    'ca': {'e': 132.4579341637009, 'i': 5e-05, 'o': 2.0},
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}},
                'mechs': {
                    'ar': {'gbar': cfg.L5Pyr_soma_gbar_ar}, 
                    'ca': {'gbar': cfg.L5Pyr_soma_gbar_ca},
                    'cad': {'taur': cfg.L5Pyr_soma_taur_cad},
                    'cat': {'gbar': cfg.L5Pyr_soma_gbar_cat},
                    'dipole': {},
                    'hh2': {'el': cfg.L5Pyr_soma_el_hh2, 
                            'gkbar': cfg.L5Pyr_soma_gkbar_hh2, 
                            'gl': cfg.L5Pyr_soma_gl_hh2, 
                            'gnabar': cfg.L5Pyr_soma_gnabar_hh2},
                    'kca': {'gbar': cfg.L5Pyr_soma_gbar_kca},
                    'km': {'gbar': cfg.L5Pyr_soma_gbar_km}},
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
somaL = cellParams['L5Pyr_rule']['secs']['soma']['geom']['L']

for sec in [sec for secName, sec in cellParams['L5Pyr_rule']['secs'].items() if secName != 'soma']:
    sec['ions'] = {
        'ca': {'e': 132.4579341637009, 'i': 5e-05, 'o': 2.0},
        'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
        'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}}

    L = sec['geom']['L']
    nseg = sec['geom']['nseg']
    
    sec['mechs'] = {
        # gbar_ar value depends of distance from soma 
        'ar': {'gbar': [1e-6*np.exp(3e-3 * ((L/nseg)*i+(L/nseg)/2)) for i in range(nseg)]}, 
        'ca': {'gbar': cfg.L5Pyr_dend_gbar_ca},
        'cad': {'taur': cfg.L5Pyr_dend_taur_cad},
        'cat': {'gbar': cfg.L5Pyr_dend_gbar_cat},
        'dipole': {},
        'hh2': {'el': cfg.L5Pyr_dend_el_hh2, 
                'gkbar': cfg.L5Pyr_dend_gkbar_hh2, 
                'gl': cfg.L5Pyr_dend_gl_hh2, 
                'gnabar': cfg.L5Pyr_dend_gnabar_hh2},
        'kca': {'gbar': cfg.L5Pyr_dend_gbar_kca},
        'km': {'gbar': cfg.L5Pyr_dend_gbar_km}}


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
                'mechs': {
                    'hh2': {'el': -54.3, 
                            'gkbar': 0.036, 
                            'gl': 0.0003, 
                            'gnabar': 0.12}},
                'topol': {}
        }}}
