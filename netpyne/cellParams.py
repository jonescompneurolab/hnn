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
                    'pt3d': [[0.0, 0.0, 0.0, cfg.L2Pyr_soma_diam],
                        [0.0, 0.0+cfg.L2Pyr_soma_L, 0.0, cfg.L2Pyr_soma_diam]]},
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
    
    sec['mechs'] = {
        'dipole': {},
        'hh2': {'el': cfg.L2Pyr_dend_el_hh2, 
                'gkbar': cfg.L2Pyr_dend_gkbar_hh2, 
                'gl': cfg.L2Pyr_dend_gl_hh2, 
                'gnabar': cfg.L2Pyr_dend_gnabar_hh2},
        'km': {'gbar': cfg.L2Pyr_dend_gbar_km}}

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
                'mechs': {
                    'hh2': {'el': -54.3, 
                            'gkbar': 0.036, 
                            'gl': 0.0003, 
                            'gnabar': 0.12}},
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

gbar_ar = {  # values calculated for each segment as: seg.gbar_ar = 1e-6 * np.exp(3e-3 * h.distance(seg.x)) (from orig HNN)
    'apical_trunk': [1.183e-06, 1.31e-06, 1.451e-06],
    'apical_1': [1.651e-06, 1.932e-06, 2.26e-06, 2.644e-06, 3.093e-06, 3.619e-06, 4.233e-06, 4.953e-06, 5.794e-06, 6.779e-06, 7.93e-06, 9.278e-06, 1.085e-05], 'apical_2': [1.27e-05, 1.486e-05, 1.738e-05, 2.033e-05, 2.379e-05, 2.783e-05, 3.256e-05, 3.809e-05, 4.456e-05, 5.213e-05, 6.099e-05, 7.135e-05, 8.347e-05], 'apical_tuft': [9.691e-05, 0.0001117, 0.0001287, 0.0001482, 0.0001708, 0.0001968, 0.0002267, 0.0002613, 0.000301],
    'apical_oblique': [1.648e-06, 1.92e-06, 2.238e-06, 2.608e-06, 3.039e-06],
    'basal_1': [1.136e-06],
    'basal_2': [1.393e-06, 1.623e-06, 1.892e-06, 2.204e-06, 2.569e-06],
    'basal_3': [1.393e-06, 1.623e-06, 1.892e-06, 2.204e-06, 2.569e-06]}

somaL = cellParams['L5Pyr_rule']['secs']['soma']['geom']['L']

for secName, sec in [(secName, sec) for secName, sec in cellParams['L5Pyr_rule']['secs'].items() if secName != 'soma']:
    sec['ions'] = {
        'ca': {'e': 132.4579341637009, 'i': 5e-05, 'o': 2.0},
        'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
        'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}}

    L = sec['geom']['L']
    nseg = sec['geom']['nseg']
    
    sec['mechs'] = {
        # gbar_ar value depends of distance from soma 
        'ar': {'gbar': gbar_ar[secName]}, #[1e-6*np.exp(3e-3 * ((L/nseg)*i+(L/nseg)/2)) for i in range(nseg)]}, 
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
                'mechs': {
                    'hh2': {'el': -54.3, 
                            'gkbar': 0.036, 
                            'gl': 0.0003, 
                            'gnabar': 0.12}},
                'topol': {}
        }}}

## set vinit
for secName,sec in cellParams['L5Basket_rule']['secs'].items():
    sec['vinit'] = -64.9737


