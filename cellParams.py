'''
 cellParams.py - High-level specifications for cells (redefine in netpyne instead of import)
 
 Modified from netpyne-generated JSON resulting from importing original Python cell templates

'''
import numpy as np
from cfg import cfg

# ----------------------------------------------------------------------------
# Cell parameters
# ----------------------------------------------------------------------------

# dictionary to store cellParams (cell property rules)
cellParams = {}

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
                'geom': {'L': cfg.L2Pyr_soma_L, 'Ra': cfg.L2Pyr_soma_Ra, 'cm': cfg.L2Pyr_soma_cm, 'diam': cfg.L2Pyr_soma_diam, 'nseg': 1,
                    'pt3d': [[-50.0, 765.0, 0.0, cfg.L2Pyr_soma_diam],
                        [-50.0, 765.0+cfg.L2Pyr_soma_L, 0.0, cfg.L2Pyr_soma_diam]]},
                'ions': {
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}
                },
                'mechs': {
                    'dipole': {},
                    'hh2': {'el': cfg.L2Pyr_soma_el_hh2, 'gkbar': cfg.L2Pyr_soma_gkbar_hh2, 'gl': cfg.L2Pyr_soma_gl_hh2, 'gnabar': cfg.L2Pyr_soma_gnabar_hh2},
                    'km': {'gbar': cfg.L2Pyr_soma_gbar_km}},
                'topol': {}
            },
            'apical_1': {
                'geom': {'L': cfg.L2Pyr_apical1_L, 'Ra': cfg.L2Pyr_dend_Ra, 'cm': cfg.L2Pyr_dend_cm, 'diam': cfg.L2Pyr_apical1_diam, 'nseg': 7,
                    'pt3d': [
                        [-50.0, 813.0, 0.0, cfg.L2Pyr_apical1_diam],
                        [-50.0, 813.0+cfg.L2Pyr_apical1_L, 0.0, cfg.L2Pyr_apical1_diam]]},
                'ions': {
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}},
                'mechs': {
                    'dipole': {},
                    'hh2': {'el': -65.0, 'gkbar': 0.01, 'gl': 4.26e-05, 'gnabar': 0.15},
                    'km': {'gbar': 250.0}},
                'topol': {'childX': 0.0, 'parentSec': 'apical_trunk', 'parentX': 1.0}
            },
            'apical_oblique': {
                'geom': {'L': cfg.L2Pyr_apicaloblique_L, 'Ra': cfg.L2Pyr_dend_Ra, 'cm': cfg.L2Pyr_dend_cm, 'diam': cfg.L2Pyr_apicaloblique_diam, 'nseg': 7,
                    'pt3d': [[-50.0, 813.0, 0.0, cfg.L2Pyr_apicaloblique_diam],
                        [-50-cfg.L2Pyr_apicaloblique_L, 813.0, 0.0, cfg.L2Pyr_apicaloblique_diam]]},
                'ions': {
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}},
                'mechs': {
                    'dipole': {},
                    'hh2': {'el': -65.0, 'gkbar': 0.01, 'gl': 4.26e-05, 'gnabar': 0.15},
                    'km': {'gbar': 250.0}},
                'topol': {'childX': 0.0, 'parentSec': 'apical_trunk', 'parentX': 1.0}
            },
            'apical_trunk': {
                'geom': {'L': cfg.L2Pyr_apicaltrunk_L, 'Ra': cfg.L2Pyr_dend_Ra, 'cm': cfg.L2Pyr_dend_cm, 'diam': cfg.L2Pyr_apicaltrunk_diam, 'nseg': 1,
                    'pt3d': [
                        [-50.0, 778.0, 0.0, cfg.L2Pyr_apicaltrunk_diam],
                        [-50.0, 778.0+cfg.L2Pyr_apicaltrunk_L, 0.0, cfg.L2Pyr_apicaltrunk_diam]]},
                'ions': {
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': { 'e': 50.0, 'i': 10.0, 'o': 140.0}},
                'mechs': {
                    'dipole': {},
                    'hh2': {'el': -65.0, 'gkbar': 0.01, 'gl': 4.26e-05, 'gnabar': 0.15},
                    'km': {'gbar': 250.0}},
                'topol': {'childX': 0.0, 'parentSec': 'soma', 'parentX': 1.0}
            },
            'apical_tuft': {
                'geom': {'L': cfg.L2Pyr_apicaltuft_L, 'Ra': cfg.L2Pyr_dend_Ra, 'cm': cfg.L2Pyr_dend_cm, 'diam': cfg.L2Pyr_apicaltuft_diam, 'nseg': 5,
                    'pt3d': [[-50.0, 993.0, 0.0, cfg.L2Pyr_apicaltuft_diam],
                        [-50.0, 993.0+cfg.L2Pyr_apicaltuft_L, 0.0, cfg.L2Pyr_apicaltuft_diam]]},
                'ions': {
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}},
                'mechs': {
                    'dipole': {},
                    'hh2': {'el': -65.0, 'gkbar': 0.01, 'gl': 4.26e-05, 'gnabar': 0.15},
                    'km': {'gbar': 250.0}},
                'topol': {'childX': 0.0, 'parentSec': 'apical_1', 'parentX': 1.0}
            },
            'basal_1': {
                'geom': {'L': cfg.L2Pyr_basal1_L, 'Ra': cfg.L2Pyr_dend_Ra, 'cm': cfg.L2Pyr_dend_cm, 'diam': cfg.L2Pyr_basal1_diam, 'nseg': 1,
                    'pt3d': [[-50.0, 765.0, 0.0, cfg.L2Pyr_basal1_diam],
                        [-50.0, 765.0-cfg.L2Pyr_basal1_L, 0.0, cfg.L2Pyr_basal1_diam]]},
                'ions': {
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}},
                'mechs': {
                    'dipole': {},
                    'hh2': {'el': -65.0, 'gkbar': 0.01, 'gl': 4.26e-05, 'gnabar': 0.15},
                    'km': {'gbar': 250.0}},
                'topol': {'childX': 0.0, 'parentSec': 'soma', 'parentX': 0.0}
            },
            'basal_2': {
                'geom': {
                    'L': cfg.L2Pyr_basal2_L, 'Ra': cfg.L2Pyr_dend_Ra, 'cm': cfg.L2Pyr_dend_cm, 'diam': cfg.L2Pyr_basal2_diam, 'nseg': 5,
                    'pt3d': [[-50.0, 715.0, 0.0, cfg.L2Pyr_basal2_diam],
                        [-50-cfg.L2Pyr_basal2_L/np.sqrt(2), 715.0-cfg.L2Pyr_basal2_L/np.sqrt(2), 0.0, cfg.L2Pyr_basal2_diam]]},
                'ions': {
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}},
                'mechs': {
                    'dipole': {},
                    'hh2': {'el': -65.0, 'gkbar': 0.01, 'gl': 4.26e-05, 'gnabar': 0.15},
                    'km': {'gbar': 250.0}},
                'topol': {'childX': 0.0, 'parentSec': 'basal_1', 'parentX': 1.0}
            },
            'basal_3': {
                'geom': {'L': cfg.L2Pyr_basal3_L, 'Ra': cfg.L2Pyr_dend_Ra, 'cm': cfg.L2Pyr_dend_cm, 'diam': cfg.L2Pyr_basal3_diam, 'nseg': 5,
                    'pt3d': [[-50.0, 715.0, 0.0, cfg.L2Pyr_basal3_diam],
                        [-50.0+cfg.L2Pyr_basal3_L/np.sqrt(2), 715.0-cfg.L2Pyr_basal3_L/np.sqrt(2), 0.0, cfg.L2Pyr_basal3_diam]]},
                'topol': {'childX': 0.0, 'parentSec': 'basal_1', 'parentX': 1.0}
        }}}

## add biophysics (ions and mechs) to L2Pyr dendrites
somaL = cellParams['L5Pyr_rule'].secs['soma']['geom']['L']

for sec in [sec for secName, sec in cellParams['L2Pyr_rule'].secs.items() if secName != 'soma']:
    sec['ions'] = {
        'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
        'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}},
    
    sec['mechs'] = {
        'dipole': {},
        'hh2': {'el': cfg.L2Pyr_dend_el_hh2, 'gkbar': cfg.L2Pyr_dend_gkbar_hh2, 'gl': cfg.L2Pyr_dend_gl_hh2, 'gnabar': cfg.L2Pyr_dend_gnabar_hh2},
        'km': {'gbar': cfg.L2Pyr_dend_gbar_km}},


# ------------------------------------------------------------------------------------
# L2 Basket cell rule
# ------------------------------------------------------------------------------------
cellParams['L2Basket_rule'] = {
        'conds': {'cellType': 'L2Basket'},
        'secs': {
            'soma': {
                'geom': {'L': 39.0, 'Ra': 200.0, 'cm': 0.85, 'diam': 20.0, 'nseg': 1},
                'ions': {
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0,'o': 140.0}},
                'mechs': {
                    'hh2': {'el': -54.3, 'gkbar': 0.036, 'gl': 0.0003, 'gnabar': 0.12}},
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
                'geom': {'L': 39.0, 'Ra': 200.0, 'cm': 0.85, 'diam': 28.899999618530273, 'nseg': 1,
                    'pt3d': [[0.0, 0.0, 0.0, 28.899999618530273],
                        [0.0, 39.0, 0.0, 28.899999618530273]]},
                'ions': {
                    'ca': {'e': 132.4579341637009, 'i': 5e-05, 'o': 2.0},
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}},
                'mechs': {
                    'ar': {'gbar': 1e-06}, 
                    'ca': {'gbar': 60.0},
                    'cad': {'taur': 20.0},
                    'cat': {'gbar': 0.0002},
                    'dipole': {},
                    'hh2': {'el': -65.0, 'gkbar': 0.01, 'gl': 4.26e-05, 'gnabar': 0.16},
                    'kca': {'gbar': 0.0002},
                    'km': {'gbar': 200.0}},
                'topol': {}
            },
            'apical_1': {
                'geom': {'L': 680.0, 'Ra': 200.0, 'cm': 0.85, 'diam': 7.48000001907348, 'nseg': 13,
                    'pt3d': [[0.0, 83.0, 0.0, 7.480000019073486],
                        [0.0, 763.0, 0.0, 7.480000019073486]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_trunk','parentX': 1.0}
            },
            'apical_2': {
                'geom': {'L': 680.0, 'Ra': 200.0, 'cm': 0.85, 'diam': 4.929999828338619, 'nseg': 13,
                    'pt3d': [[0.0, 483.0, 0.0, 4.929999828338623],
                        [0.0, 1163.0, 0.0, 4.929999828338623]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_1', 'parentX': 1.0}
            },
            'apical_oblique': {
                'geom': {'L': 255.0, 'Ra': 200.0, 'cm': 0.85, 'diam': 5.099999904632568, 'nseg': 5,
                    'pt3d': [[0.0, 83.0, 0.0, 5.099999904632568],
                        [-255.0, 83.0, 0.0, 5.099999904632568]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_trunk', 'parentX': 1.0}
            },
            'apical_trunk': {
                'geom': {'L': 102.0, 'Ra': 200.0, 'cm': 0.85, 'diam': 10.199999809265137, 'nseg': 3,
                    'pt3d': [[0.0, 23.0, 0.0, 10.199999809265137 ],
                        [0.0, 125.0, 0.0, 10.199999809265137]]},
                'topol': {'childX': 0.0, 'parentSec': 'soma', 'parentX': 1.0}
            },
            'apical_tuft': {
                'geom': {'L': 425.0, 'Ra': 200.0, 'cm': 0.85, 'diam': 3.400000095367432, 'nseg': 9,
                    'pt3d': [[0.0, 883.0, 0.0, 3.4000000953674316],
                        [0.0, 1308.0, 0.0, 3.4000000953674316]]},
                'topol': {'childX': 0.0, 'parentSec': 'apical_2', 'parentX': 1.0}
            },
            'basal_1': {
                'geom': {'L': 85.0, 'Ra': 200.0, 'cm': 0.85, 'diam': 6.800000190734863, 'nseg': 1,
                    'pt3d': [[0.0, 0.0, 0.0, 6.800000190734863],
                        [0.0, -85.0, 0.0, 6.800000190734863]]},
                'topol': {'childX': 0.0, 'parentSec': 'soma', 'parentX': 0.0}
            },
            'basal_2': {
                'geom': {'L': 255.0, 'Ra': 200.0, 'cm': 0.85, 'diam': 8.5, 'nseg': 5,
                    'pt3d': [[0.0, -50.0, 0.0, 8.5],
                        [-180.31222534179688, -230.31222534179688, 0.0, 8.5]]},
                'topol': {'childX': 0.0, 'parentSec': 'basal_1', 'parentX': 1.0}
            },
            'basal_3': {
                'geom': {'L': 255.0, 'Ra': 200.0, 'cm': 0.85, 'diam': 8.5, 'nseg': 5,
                    'pt3d': [[0.0, -50.0, 0.0, 8.5],
                        [180.31222534179688, -230.31222534179688, 0.0, 8.5]]},
                'topol': {
                    'childX': 0.0,
                    'parentSec': 'basal_1',
                    'parentX': 1.0}
        }}}

## add biophysics (ions and mechs) to L5Pyr dendrites
somaL = cellParams['L5Pyr_rule'].secs['soma']['geom']['L']

for sec in [sec for secName, sec in cellParams['L5Pyr_rule'].secs.items() if secName != 'soma']:
    sec['ions'] = {
        'ca': {'e': 132.4579341637009, 'i': 5e-05, 'o': 2.0},
        'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
        'na': {'e': 50.0, 'i': 10.0, 'o': 140.0}}

    L = sec['geom']['L']
    nseg = sec['geom']['nseg']
    
    sec['mechs'] = {
        # gbar_ar value depends of distance from soma 
        'ar': {'gbar': [1e-6*np.exp(3e-3 * ((L/nseg)*i+(L/nseg)/2)) for i in range(nseg)]},
        'ca': {'gbar': 60.0},
        'cad': {'taur': 20.0},
        'cat': {'gbar': 0.0002},
        'dipole': {},
        'hh2': {'el': -71.0, 'gkbar': 0.01, 'gl': 4.26e-05, 'gnabar': 0.14},
        'kca': {'gbar': 0.0002},
        'km': {'gbar': 200.0}}


# ------------------------------------------------------------------------------------
# L5 Basket cell rule
# ------------------------------------------------------------------------------------
cellParams['L5Basket_rule'] = {
        'conds': {'cellType': 'L5Basket'},
        'secs': {
            'soma': {
                'geom': {'L': 39.0, 'Ra': 200.0, 'cm': 0.85, 'diam': 20.0, 'nseg': 1},
                'ions': {
                    'k': {'e': -77.0, 'i': 54.4, 'o': 2.5},
                    'na': {'e': 50.0, 'i': 10.0,'o': 140.0}},
                'mechs': {
                    'hh2': {'el': -54.3, 'gkbar': 0.036, 'gl': 0.0003, 'gnabar': 0.12}},
                'topol': {}
        }}}
