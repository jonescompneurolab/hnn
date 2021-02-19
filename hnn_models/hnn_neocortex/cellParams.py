'''
 cellParams.py - High-level specifications for cells (redefine in netpyne instead of import)
 
 Modified from netpyne-generated JSON resulting from importing original Python cell templates

'''

import numpy as np
from netpyne import specs
from cfg import cfg

p = cfg.hnn_params  # quick access to cfg.hnn_params

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
                'geom': {'L': p['L2Pyr_soma_L'], 
                        'Ra': p['L2Pyr_soma_Ra'], 
                        'cm': p['L2Pyr_soma_cm'], 
                        'diam': p['L2Pyr_soma_diam'], 
                        'nseg': 1,
                    'pt3d': [[0.0, 0.0, 0.0, p['L2Pyr_soma_diam']],
                        [0.0, 0.0+p['L2Pyr_soma_L'], 0.0, p['L2Pyr_soma_diam']]]},
                'ions': {
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}
                },
                'mechs': {
                    'dipole': {},
                    'hh2': {'el': p['L2Pyr_soma_el_hh2'], 
                            'gkbar': p['L2Pyr_soma_gkbar_hh2'], 
                            'gl': p['L2Pyr_soma_gl_hh2'], 
                            'gnabar': p['L2Pyr_soma_gnabar_hh2']},
                    'km': {'gbar': p['L2Pyr_soma_gbar_km']}},
                'topol': {}
            },
            'apical_1': {
                'geom': {'L': p['L2Pyr_apical1_L'], 
                        'Ra': p['L2Pyr_dend_Ra'], 
                        'cm': p['L2Pyr_dend_cm'], 
                        'diam': p['L2Pyr_apical1_diam'], 
                        'nseg': 7,
                    'pt3d': [
                        [0.0, 48.0, 0.0, p['L2Pyr_apical1_diam']],
                        [0.0, 48.0+p['L2Pyr_apical1_L'], 0.0, p['L2Pyr_apical1_diam']]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_trunk', 'parentX': 1.0}
            },
            'apical_oblique': {
                'geom': {'L': p['L2Pyr_apicaloblique_L'], 
                        'Ra': p['L2Pyr_dend_Ra'], 
                        'cm': p['L2Pyr_dend_cm'], 
                        'diam': p['L2Pyr_apicaloblique_diam'], 
                        'nseg': 7,
                    'pt3d': [[0.0, 48.0, 0.0, p['L2Pyr_apicaloblique_diam']],
                        [0.0-p['L2Pyr_apicaloblique_L'], 48.0, 0.0, p['L2Pyr_apicaloblique_diam']]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_trunk', 'parentX': 1.0}
            },
            'apical_trunk': {
                'geom': {'L': p['L2Pyr_apicaltrunk_L'], 
                        'Ra': p['L2Pyr_dend_Ra'], 
                        'cm': p['L2Pyr_dend_cm'], 
                        'diam': p['L2Pyr_apicaltrunk_diam'], 
                        'nseg': 1,
                    'pt3d': [
                        [0.0, 13.0, 0.0, p['L2Pyr_apicaltrunk_diam']],
                        [0.0, 13.0+p['L2Pyr_apicaltrunk_L'], 0.0, p['L2Pyr_apicaltrunk_diam']]]},
                'topol': {'childX': 0.0, 'parentSec': 'soma', 'parentX': 1.0}
            },
            'apical_tuft': {
                'geom': {'L': p['L2Pyr_apicaltuft_L'], 
                        'Ra': p['L2Pyr_dend_Ra'], 
                        'cm': p['L2Pyr_dend_cm'], 
                        'diam': p['L2Pyr_apicaltuft_diam'], 
                        'nseg': 5,
                    'pt3d': [[0.0, 228.0, 0.0, p['L2Pyr_apicaltuft_diam']],
                        [0.0, 228.0+p['L2Pyr_apicaltuft_L'], 0.0, p['L2Pyr_apicaltuft_diam']]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_1', 'parentX': 1.0}
            },
            'basal_1': {
                'geom': {'L': p['L2Pyr_basal1_L'], 
                        'Ra': p['L2Pyr_dend_Ra'], 
                        'cm': p['L2Pyr_dend_cm'], 
                        'diam': p['L2Pyr_basal1_diam'], 
                        'nseg': 1,
                    'pt3d': [[0.0, 0.0, 0.0, p['L2Pyr_basal1_diam']],
                        [0.0, 0.0-p['L2Pyr_basal1_L'], 0.0, p['L2Pyr_basal1_diam']]]},
                'topol': {'childX': 0.0, 'parentSec': 'soma', 'parentX': 0.0}
            },
            'basal_2': {
                'geom': {
                    'L': p['L2Pyr_basal2_L'], 
                            'Ra': p['L2Pyr_dend_Ra'], 
                            'cm': p['L2Pyr_dend_cm'], 
                            'diam': p['L2Pyr_basal2_diam'], 
                            'nseg': 5,
                    'pt3d': [[0.0, -50.0, 0.0, p['L2Pyr_basal2_diam']],
                        [0.0-p['L2Pyr_basal2_L']/np.sqrt(2), -50.0-p['L2Pyr_basal2_L']/np.sqrt(2), 0.0, p['L2Pyr_basal2_diam']]]},
                'topol': {'childX': 0.0, 'parentSec': 'basal_1', 'parentX': 1.0}
            },
            'basal_3': {
                'geom': {'L': p['L2Pyr_basal3_L'], 
                        'Ra': p['L2Pyr_dend_Ra'], 
                        'cm': p['L2Pyr_dend_cm'], 
                        'diam': p['L2Pyr_basal3_diam'], 
                        'nseg': 5,
                    'pt3d': [[0.0, -50.0, 0.0, p['L2Pyr_basal3_diam']],
                        [0.0+p['L2Pyr_basal3_L']/np.sqrt(2), -50.0-p['L2Pyr_basal3_L']/np.sqrt(2), 0.0, p['L2Pyr_basal3_diam']]]},
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
        'hh2': {'el': p['L2Pyr_dend_el_hh2'], 
                'gkbar': p['L2Pyr_dend_gkbar_hh2'], 
                'gl': p['L2Pyr_dend_gl_hh2'], 
                'gnabar': p['L2Pyr_dend_gnabar_hh2']},
        'km': {'gbar': p['L2Pyr_dend_gbar_km']}}

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
                'geom': {'L': p['L5Pyr_soma_L'], 
                        'Ra': p['L5Pyr_soma_Ra'], 
                        'cm': p['L5Pyr_soma_cm'], 
                        'diam': p['L5Pyr_soma_diam'], 
                        'nseg': 1,
                    'pt3d': [[0.0, 0.0, 0.0, p['L5Pyr_soma_diam']],
                        [0.0, 0.0+p['L5Pyr_soma_L'], 0.0, p['L5Pyr_soma_diam']]]},
                'ions': {
                    'ca': {'e': 132.4579341637009, 'i': 5e-05, 'o': 2.0},
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}},
                'mechs': {
                    'ar': {'gbar': p['L5Pyr_soma_gbar_ar']}, 
                    'ca': {'gbar': p['L5Pyr_soma_gbar_ca']},
                    'cad': {'taur': p['L5Pyr_soma_taur_cad']},
                    'cat': {'gbar': p['L5Pyr_soma_gbar_cat']},
                    'dipole': {},
                    'hh2': {'el': p['L5Pyr_soma_el_hh2'], 
                            'gkbar': p['L5Pyr_soma_gkbar_hh2'], 
                            'gl': p['L5Pyr_soma_gl_hh2'], 
                            'gnabar': p['L5Pyr_soma_gnabar_hh2']},
                    'kca': {'gbar': p['L5Pyr_soma_gbar_kca']},
                    'km': {'gbar': p['L5Pyr_soma_gbar_km']}},
                'topol': {}
            },
            'apical_1': {
                'geom': {'L': p['L5Pyr_apical1_L'], 
                        'Ra': p['L5Pyr_dend_Ra'], 
                        'cm': p['L5Pyr_dend_cm'], 
                        'diam': p['L5Pyr_apical1_diam'], 
                        'nseg': 13,
                    'pt3d': [[0.0, 83.0, 0.0, p['L5Pyr_apical1_diam']],
                        [0.0, 83.0+p['L5Pyr_apical1_L'], 0.0, p['L5Pyr_apical1_diam']]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_trunk','parentX': 1.0}
            },
            'apical_2': {
                'geom': {'L': p['L5Pyr_apical2_L'], 
                        'Ra': p['L5Pyr_dend_Ra'], 
                        'cm': p['L5Pyr_dend_cm'], 
                        'diam': p['L5Pyr_apical2_diam'], 
                        'nseg': 13,
                    'pt3d': [[0.0, 483.0, 0.0, p['L5Pyr_apical2_diam']],
                        [0.0, 483.0+p['L5Pyr_apical2_L'], 0.0, p['L5Pyr_apical2_diam']]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_1', 'parentX': 1.0}
            },
            'apical_oblique': {
                'geom': {'L': p['L5Pyr_apicaloblique_L'], 
                        'Ra': p['L5Pyr_dend_Ra'], 
                        'cm': p['L5Pyr_dend_cm'], 
                        'diam': p['L5Pyr_apicaloblique_diam'], 
                        'nseg': 5,
                    'pt3d': [[0.0, 83.0, 0.0, p['L5Pyr_apicaloblique_diam']],
                        [0.0-p['L5Pyr_apicaloblique_L'], 83.0, 0.0, p['L5Pyr_apicaloblique_diam']]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_trunk', 'parentX': 1.0}
            },
            'apical_trunk': {
                'geom': {'L': p['L5Pyr_apicaltrunk_L'], 
                        'Ra': p['L5Pyr_dend_Ra'], 
                        'cm': p['L5Pyr_dend_cm'], 
                        'diam': p['L5Pyr_apicaltrunk_diam'], 
                        'nseg': 3,
                    'pt3d': [[0.0, 23.0, 0.0, p['L5Pyr_apicaltrunk_diam'] ],
                        [0.0, 23.0+p['L5Pyr_apicaltrunk_L'], 0.0, p['L5Pyr_apicaltrunk_diam']]]},
                'topol': {'childX': 0.0, 'parentSec': 'soma', 'parentX': 1.0}
            },
            'apical_tuft': {
                'geom': {'L': p['L5Pyr_apicaltuft_L'], 
                        'Ra': p['L5Pyr_dend_Ra'], 
                        'cm': p['L5Pyr_dend_cm'], 
                        'diam': p['L5Pyr_apicaltuft_diam'], 
                        'nseg': 9,
                    'pt3d': [[0.0, 883.0, 0.0, p['L5Pyr_apicaltuft_diam']],
                        [0.0, 883.0+p['L5Pyr_apicaltuft_L'], 0.0, p['L5Pyr_apicaltuft_diam']]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_2', 'parentX': 1.0}
            },
            'basal_1': {
                'geom': {'L': p['L5Pyr_basal1_L'], 
                        'Ra': p['L5Pyr_dend_Ra'], 
                        'cm': p['L5Pyr_dend_cm'], 
                        'diam': p['L5Pyr_basal1_diam'], 
                        'nseg': 1,
                    'pt3d': [[0.0, 0.0, 0.0, p['L5Pyr_basal1_diam']],
                        [0.0, 0.0-p['L5Pyr_basal1_L'], 0.0, p['L5Pyr_basal1_diam']]]},
                'topol': {'childX': 0.0, 'parentSec': 'soma', 'parentX': 0.0}
            },
            'basal_2': {
                'geom': {'L': p['L5Pyr_basal2_L'], 
                        'Ra': p['L5Pyr_dend_Ra'], 
                        'cm': p['L5Pyr_dend_cm'], 
                        'diam': p['L5Pyr_basal2_diam'], 
                        'nseg': 5,
                    'pt3d': [[0.0, -50.0, 0.0, p['L5Pyr_basal2_diam']],
                        [0.0-p['L5Pyr_basal2_L']/np.sqrt(2), -50-p['L5Pyr_basal2_L']/np.sqrt(2), 0.0, p['L5Pyr_basal2_diam']]]},
                'topol': {'childX': 0.0, 'parentSec': 'basal_1', 'parentX': 1.0}
            },
            'basal_3': {
                'geom': {'L': p['L5Pyr_basal3_L'], 
                        'Ra': p['L5Pyr_dend_Ra'], 
                        'cm': p['L5Pyr_dend_cm'], 
                        'diam': p['L5Pyr_basal3_diam'], 
                        'nseg': 5,
                    'pt3d': [[0.0, -50.0, 0.0, p['L5Pyr_basal3_diam']],
                        [0.0+p['L5Pyr_basal2_L']/np.sqrt(2), -50-p['L5Pyr_basal2_L']/np.sqrt(2), 0.0, p['L5Pyr_basal3_diam']]]},
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
    
    sec['mechs'] = {
        # gbar_ar value depends of distance from soma 
        'ar': {'gbar': gbar_ar[secName]}, #[1e-6*np.exp(3e-3 * ((L/nseg)*i+(L/nseg)/2)) for i in range(nseg)]}, 
        'ca': {'gbar': p['L5Pyr_dend_gbar_ca']},
        'cad': {'taur': p['L5Pyr_dend_taur_cad']},
        'cat': {'gbar': p['L5Pyr_dend_gbar_cat']},
        'dipole': {},
        'hh2': {'el': p['L5Pyr_dend_el_hh2'], 
                'gkbar': p['L5Pyr_dend_gkbar_hh2'], 
                'gl': p['L5Pyr_dend_gl_hh2'], 
                'gnabar': p['L5Pyr_dend_gnabar_hh2']},
        'kca': {'gbar': p['L5Pyr_dend_gbar_kca']},
        'km': {'gbar': p['L5Pyr_dend_gbar_km']}}

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


