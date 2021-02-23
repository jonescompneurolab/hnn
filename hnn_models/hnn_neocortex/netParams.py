
"""
netParams.py 

High-level specifications for HNN network model using NetPyNE

Contributors: salvadordura@gmail.com
"""

from netpyne import specs

try:
  from __main__ import cfg  # import SimConfig object with params from parent module
except:
  from cfg import cfg  # if no simConfig in parent module, import directly from cfg module

import numpy as np
import itertools as it

p = cfg.hnn_params  # quick access to p['hnn_params']


# ----------------------------------------------------------------------------
#
# NETWORK PARAMETERS
#
# ----------------------------------------------------------------------------

netParams = specs.NetParams()  # object of class NetParams to store the network parameters

#------------------------------------------------------------------------------
# General network parameters
#------------------------------------------------------------------------------
netParams.sizeX = ((p['N_pyr_x'] * cfg.gridSpacingPyr) - 1) * cfg.xzScaling  # x-dimension (horizontal length) size in um
netParams.sizeY = cfg.sizeY # y-dimension (vertical height or cortical depth) size in um
netParams.sizeZ = ((p['N_pyr_y'] * cfg.gridSpacingPyr) - 1) * cfg.xzScaling # z-dimension (horizontal depth) size in um
netParams.shape = 'cuboid'


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


netParams.cellParams = cellParams

# ----------------------------------------------------------------------------
# Population parameters
# ----------------------------------------------------------------------------

# layer locations
layersE = {'L2': [0.0*cfg.sizeY, 0.0*cfg.sizeY], 'L5': [0.654*cfg.sizeY, 0.654*cfg.sizeY]} # 0.654 = 1308/2000
layersI = {'L2': [0.0*cfg.sizeY-00.0, 0.0*cfg.sizeY-00.0], 'L5': [0.654*cfg.sizeY-00.0, 0.654*cfg.sizeY-00.0]}

# Create list of locations for Basket cells based on original ad hoc rules 
# define relevant x spacings for basket cells
xzero = np.arange(0, p['N_pyr_x'], 3)
xone = np.arange(1, p['N_pyr_x'], 3)
yeven = np.arange(0, p['N_pyr_y'], 2)
yodd = np.arange(1, p['N_pyr_y'], 2)
coords = [pos for pos in it.product(xzero, yeven)] + [pos for pos in it.product(xone, yodd)]
coords_sorted = sorted(coords, key=lambda pos: pos[1])
L2BasketLocs = [{'x': coord[0]*cfg.xzScaling, 'y': layersI['L2'][0], 'z': coord[1]*cfg.xzScaling} for coord in coords_sorted]
L5BasketLocs = [{'x': coord[0]*cfg.xzScaling, 'y': layersI['L5'][0], 'z': coord[1]*cfg.xzScaling} for coord in coords_sorted]

# create popParams
netParams.popParams['L2Basket'] = {'cellType':  'L2Basket', 'cellModel': 'HH_simple', 'numCells': len(L2BasketLocs), 'cellsList': L2BasketLocs} 
netParams.popParams['L2Pyr'] =    {'cellType':  'L2Pyr',    'cellModel': 'HH_reduced', 'yRange': layersE['L2'],  'gridSpacing': cfg.gridSpacingPyr*cfg.xzScaling} 
netParams.popParams['L5Basket'] = {'cellType':  'L5Basket', 'cellModel': 'HH_simple',  'numCells': len(L5BasketLocs), 'cellsList': L5BasketLocs} 
netParams.popParams['L5Pyr'] =    {'cellType':  'L5Pyr',    'cellModel': 'HH_reduced', 'yRange': layersE['L5'],  'gridSpacing': cfg.gridSpacingPyr*cfg.xzScaling} 

# create variables useful for connectivity
pops = list(netParams.popParams.keys())
cellsPerPop = {}
cellsPerPop['L2Pyr'] = cellsPerPop['L5Pyr'] = int(p['N_pyr_x'] * p['N_pyr_x'])
cellsPerPop['L2Basket'] = cellsPerPop['L5Basket'] = int(np.ceil(p['N_pyr_x'] * p['N_pyr_x'] / cfg.gridSpacingBasket[2]) + 1)


#------------------------------------------------------------------------------
# Synaptic mechanism parameters
#------------------------------------------------------------------------------

netParams.synMechParams['L2Pyr_AMPA'] = {'mod':'Exp2Syn', 'tau1': p['L2Pyr_ampa_tau1'], 'tau2': p['L2Pyr_ampa_tau2'], 'e': p['L2Pyr_ampa_e']}
netParams.synMechParams['L2Pyr_NMDA'] = {'mod': 'Exp2Syn', 'tau1': p['L2Pyr_nmda_tau1'], 'tau2': p['L2Pyr_nmda_tau2'], 'e': p['L2Pyr_nmda_e']}
netParams.synMechParams['L2Pyr_GABAA'] = {'mod':'Exp2Syn', 'tau1': p['L2Pyr_gabaa_tau1'], 'tau2': p['L2Pyr_gabaa_tau2'], 'e': p['L2Pyr_gabaa_e']}
netParams.synMechParams['L2Pyr_GABAB'] = {'mod':'Exp2Syn', 'tau1': p['L2Pyr_gabab_tau1'], 'tau2': p['L2Pyr_gabab_tau2'], 'e': p['L2Pyr_gabab_e']}

netParams.synMechParams['L5Pyr_AMPA'] = {'mod':'Exp2Syn', 'tau1': p['L5Pyr_ampa_tau1'], 'tau2': p['L5Pyr_ampa_tau2'], 'e': p['L5Pyr_ampa_e']}
netParams.synMechParams['L5Pyr_NMDA'] = {'mod': 'Exp2Syn', 'tau1': p['L5Pyr_nmda_tau1'], 'tau2': p['L5Pyr_nmda_tau2'], 'e': p['L5Pyr_nmda_e']}
netParams.synMechParams['L5Pyr_GABAA'] = {'mod':'Exp2Syn', 'tau1': p['L5Pyr_gabaa_tau1'], 'tau2': p['L5Pyr_gabaa_tau2'], 'e': p['L5Pyr_gabaa_e']}
netParams.synMechParams['L5Pyr_GABAB'] = {'mod':'Exp2Syn', 'tau1': p['L5Pyr_gabab_tau1'], 'tau2': p['L5Pyr_gabab_tau2'], 'e': p['L5Pyr_gabab_e']}

netParams.synMechParams['AMPA'] = {'mod':'Exp2Syn', 'tau1': 0.5, 'tau2': 5.0, 'e': 0}
netParams.synMechParams['NMDA'] = {'mod': 'Exp2Syn', 'tau1': 1, 'tau2': 20, 'e': 0}
netParams.synMechParams['GABAA'] = {'mod':'Exp2Syn', 'tau1': 0.5, 'tau2': 5, 'e': -80}
netParams.synMechParams['GABAB'] = {'mod':'Exp2Syn', 'tau1': 1, 'tau2': 20, 'e': -80}


#------------------------------------------------------------------------------
# Local connectivity parameters 
#------------------------------------------------------------------------------

# Weight and delay distance-dependent functions (as strings) to use in conn rules
weightDistFunc = '{A_weight} * exp(-(dist_2D**2) / ({lamtha}**2))'
delayDistFunc = '{A_delay} / exp(-(dist_2D**2) / ({lamtha}**2))'

if cfg.localConn:

    # L2 Pyr -> L2 Pyr
    synParamsList = [{'synMech': 'L2Pyr_AMPA',
                'A_weight': cfg.EEgain * p['gbar_L2Pyr_L2Pyr_ampa'],
                'A_delay': 1.,
                'lamtha': 3.},

                {'synMech': 'L2Pyr_NMDA',
                'A_weight': cfg.EEgain * p['gbar_L2Pyr_L2Pyr_nmda'],
                'A_delay': 1.,
                'lamtha': 3.}]

    for i,synParams in enumerate(synParamsList):
        netParams.connParams['L2Pyr->L2Pyr_%d'%(i)] = { 
            'preConds': {'pop': 'L2Pyr'}, 
            'postConds': {'pop': 'L2Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams), # equivalent to weightDistFunc.format(A_weight=p['gbar_L2Pyr_L2Pyr_ampa'], lamtha=1.)
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 3,
            'sec': ['basal_2', 'basal_3','apical_oblique', ]}
                    

    # L2 Basket -> L2 Pyr
    synParamsList = [{'synMech': 'L2Pyr_GABAA',
                'A_weight': cfg.IEgain * p['gbar_L2Basket_L2Pyr_gabaa'],
                'A_delay': 1.,
                'lamtha': 50.},

                {'synMech': 'L2Pyr_GABAB',
                'A_weight': cfg.IEgain * p['gbar_L2Basket_L2Pyr_gabab'],
                'A_delay': 1.,
                'lamtha': 50.}]

    for i,synParams in enumerate(synParamsList):
        netParams.connParams['L2Basket->L2Pyr_%d'%(i)] = { 
            'preConds': {'pop': 'L2Basket'}, 
            'postConds': {'pop': 'L2Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 1,
            'sec': ['soma']}


    # L2 Pyr -> L2 Basket 
    synParams = {'synMech': 'AMPA',
                'A_weight': cfg.EIgain * p['gbar_L2Pyr_L2Basket'],
                'A_delay': 1.,
                'lamtha': 3.}

    netParams.connParams['L2Pyr->L2Basket_%s'%(synParams['synMech'])] = { 
        'preConds': {'pop': 'L2Pyr'}, 
        'postConds': {'pop': 'L2Basket'},
        'synMech': synParams['synMech'],
        'weight': weightDistFunc.format(**synParams),
        'delay': delayDistFunc.format(**synParams),
        'synsPerConn': 1,
        'sec': ['soma']}


    # L2 Basket -> L2 Basket 
    synParams = {'synMech': 'GABAA',
                'A_weight': cfg.IIgain * p['gbar_L2Basket_L2Basket'],
                'A_delay': 1.,
                'lamtha': 20.}

    netParams.connParams['L2Basket->L2Basket'] = { 
        'preConds': {'pop': 'L2Basket'}, 
        'postConds': {'pop': 'L2Basket'},
        'synMech': synParams['synMech'],
        'weight': weightDistFunc.format(**synParams),
        'delay': delayDistFunc.format(**synParams),
        'synsPerConn': 1,
        'sec': ['soma']}


    # L5 Pyr -> L5 Pyr
    synParamsList = [{'synMech': 'L5Pyr_AMPA',
                'A_weight': cfg.EEgain * p['gbar_L5Pyr_L5Pyr_ampa'],
                'A_delay': 1.,
                'lamtha': 3.},

                {'synMech': 'L5Pyr_NMDA',
                'A_weight': cfg.EEgain * p['gbar_L5Pyr_L5Pyr_nmda'],
                'A_delay': 1.,
                'lamtha': 3.}]

    for i,synParams in enumerate(synParamsList):
        netParams.connParams['L5Pyr->L5Pyr_%d'%(i)] = { 
            'preConds': {'pop': 'L5Pyr'}, 
            'postConds': {'pop': 'L5Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 3,
            'sec': ['basal_2', 'basal_3', 'apical_oblique']}
                

    # L5 Basket -> L5 Pyr
    synParamsList = [{'synMech': 'L5Pyr_GABAA',
                'A_weight': cfg.IEgain * p['gbar_L5Basket_L5Pyr_gabaa'],
                'A_delay': 1.,
                'lamtha': 70.},

                {'synMech': 'L5Pyr_GABAB',
                'A_weight': cfg.IEgain * p['gbar_L5Basket_L5Pyr_gabab'],
                'A_delay': 1.,
                'lamtha': 70.}]

    for i,synParams in enumerate(synParamsList):
        netParams.connParams['L5Basket->L5Pyr_%d'%(i)] = { 
            'preConds': {'pop': 'L5Basket'}, 
            'postConds': {'pop': 'L5Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 1,
            'sec': ['soma']}


    # L2 Pyr -> L5 Pyr
    synParams = {'synMech': 'L5Pyr_AMPA',
                'A_weight': cfg.EEgain * p['gbar_L2Pyr_L5Pyr'],
                'A_delay': 1.,
                'lamtha': 3.}

    netParams.connParams['L2Pyr->L5Pyr'] = { 
        'preConds': {'pop': 'L2Pyr'}, 
        'postConds': {'pop': 'L5Pyr'},
        'synMech': synParams['synMech'],
        'weight': weightDistFunc.format(**synParams),
        'delay': delayDistFunc.format(**synParams),
        'synsPerConn': 4,
        'sec': ['basal_2', 'basal_3', 'apical_tuft', 'apical_oblique']}
                

    # L2 Basket -> L5 Pyr
    synParams = {'synMech': 'L5Pyr_GABAA',
                'A_weight': cfg.IEgain * p['gbar_L2Basket_L5Pyr'],
                'A_delay': 1.,
                'lamtha': 50.}

    netParams.connParams['L2Basket->L5Pyr'] = { 
        'preConds': {'pop': 'L2Basket'}, 
        'postConds': {'pop': 'L5Pyr'},
        'synMech': synParams['synMech'],
        'weight': weightDistFunc.format(**synParams),
        'delay': delayDistFunc.format(**synParams),
        'synsPerConn': 1,
        'sec': ['apical_tuft']}
        

    # L5 Pyr -> L5 Basket 
    synParams = {'synMech': 'AMPA',
                'A_weight': cfg.EIgain * p['gbar_L5Pyr_L5Basket'],
                'A_delay': 1.,
                'lamtha': 3.}

    netParams.connParams['L5Pyr->L5Basket'] = { 
        'preConds': {'pop': 'L5Pyr'}, 
        'postConds': {'pop': 'L5Basket'},
        'synMech': synParams['synMech'],
        'weight': weightDistFunc.format(**synParams),
        'delay': delayDistFunc.format(**synParams),
        'synsPerConn': 1,
        'sec': ['soma']}


    # L2 Pyr -> L5 Basket 
    synParams = {'synMech': 'AMPA',
                'A_weight': cfg.EIgain * p['gbar_L2Pyr_L5Basket'],
                'A_delay': 1.,
                'lamtha': 3.}

    netParams.connParams['L2Pyr->L5Basket'] = { 
        'preConds': {'pop': 'L2Pyr'}, 
        'postConds': {'pop': 'L5Basket'},
        'synMech': synParams['synMech'],
        'weight': weightDistFunc.format(**synParams),
        'delay': delayDistFunc.format(**synParams),
        'synsPerConn': 1,
        'sec': ['soma']}


    # L5 Basket -> L5 Basket 
    synParams = {'synMech': 'GABAA',
                'A_weight': cfg.IIgain * p['gbar_L5Basket_L5Basket'],
                'A_delay': 1.,
                'lamtha': 20.}

    netParams.connParams['L5Basket->L5Basket'] = { 
        'preConds': {'pop': 'L5Basket'}, 
        'postConds': {'pop': 'L5Basket'},
        'synMech': synParams['synMech'],
        'weight': weightDistFunc.format(**synParams),
        'delay': delayDistFunc.format(**synParams),
        'synsPerConn': 1,
        'sec': ['soma']}


#------------------------------------------------------------------------------
# Rhythmic proximal and distal inputs parameters 
#------------------------------------------------------------------------------

# Location of external inputs
xrange = np.arange(p['N_pyr_x'])
extLocX = xrange[int((len(xrange) - 1) // 2)]
zrange = np.arange(p['N_pyr_y'])
extLocZ = xrange[int((len(zrange) - 1) // 2)]
extLocY = 650 # positive depth of L5 relative to L2; doesn't affect weight/delay calculations

conn1to1Pyr = np.array([range(0,cellsPerPop['L2Pyr']), range(0,cellsPerPop['L2Pyr'])]).T
conn1to1Basket = np.array([range(0,cellsPerPop['L2Basket']), range(0,cellsPerPop['L2Basket'])]).T

if cfg.rhythmicInputs:

    # Ad hoc rules copied from original code (need to improve!! -- maybe add to .param files?)

    ## "if stdev is zero, increase synaptic weights 5 fold to make"
    ## "single input equivalent to 5 simultaneous input to prevent spiking <<---- SN: WHAT IS THIS RULE!?!?!?"
    if p['f_stdev_prox'] == 0.0 and p['distribution_prox'] != 'uniform':
        for key in [k for k in cfg.__dict__ if k.startswith('input_prox_A_weight')]:
            cfg.__dict__[key] *= 5.0

    if p['f_stdev_dist'] == 0.0 and p['distribution_dist'] != 'uniform':
        for key in [k for k in cfg.__dict__ if k.startswith('input_dist_A_weight')]:
            cfg.__dict__[key] *= 5.0

    ## "if L5 delay is -1, use same delays as L2 unless L2 delay is 0.1 in which case use 1. <<---- SN: WHAT IS THIS RULE!?!?!?"
    if p['input_prox_A_delay_L5'] == -1:
        if p['input_prox_A_delay_L2'] != 0.1:
            p['input_prox_A_delay_L5'] = p['input_prox_A_delay_L2']
        else:
            p['input_prox_A_delay_L5'] = 1.0

    if p['input_dist_A_delay_L5'] == -1:
        if p['input_dist_A_delay_L2'] != 0.1:
            p['input_dist_A_delay_L5'] = p['input_dist_A_delay_L2']
        else:
            p['input_dist_A_delay_L5'] = 1.0
            
    # External Rhythmic proximal inputs (1 VecStim per cell for each cell population)
    netParams.popParams['extRhythmicProximal'] = {
        'cellModel': 'VecStim',
        'numCells': 1,
        'xRange': [extLocX, extLocX],
        'yRange': [extLocY, extLocY],
        'zRange': [extLocZ, extLocZ],
        'seed': int(p['prng_seedcore']),
        'spikePattern': {
                'type': 'rhythmic',
                'start': p['t0_input_prox'],
                'startStd': p['t0_input_stdev_prox'],
                'stop': p['tstop_input_prox'],
                'freq': p['f_input_prox'],
                'freqStd': p['f_stdev_prox'],
                'eventsPerCycle': p['events_per_cycle_prox'],
                'distribution': p['distribution_prox'],
                'repeats': p['repeats_prox']}}


    # External Rhythmic distal inputs (population of 1 VecStim)
    netParams.popParams['extRhythmicDistal'] = {
        'cellModel': 'VecStim',
        'numCells': 1,
        'xRange': [extLocX, extLocX],
        'yRange': [extLocY, extLocY],
        'zRange': [extLocZ, extLocZ],
        'seed': int(p['prng_seedcore_input_dist']),
        'spikePattern': {
                'type': 'rhythmic',
                'start': p['t0_input_dist'],
                'startStd': p['t0_input_stdev_dist'],
                'stop': p['tstop_input_dist'],
                'freq': p['f_input_dist'],
                'freqStd': p['f_stdev_dist'],
                'eventsPerCycle': p['events_per_cycle_dist'],
                'distribution': p['distribution_dist'],
                'repeats': p['repeats_dist']}}


    # Rhytmic proximal -> L2 Pyr
    synParamsList = [{'synMech': 'L2Pyr_AMPA',
                'A_weight': p['input_prox_A_weight_L2Pyr_ampa'],
                'A_delay': p['input_prox_A_delay_L2'],
                'lamtha': 100.},

                {'synMech': 'L2Pyr_NMDA',
                'A_weight': p['input_prox_A_weight_L2Pyr_nmda'],
                'A_delay': p['input_prox_A_delay_L2'],
                'lamtha': 100.}]

    for i,synParams in enumerate(synParamsList):
        netParams.connParams['extRhythmicProx->L2Pyr_%d'%(i)] = { 
            'preConds': {'pop': 'extRhythmicProximal'}, 
            'postConds': {'pop': 'L2Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 3,
            'sec': ['basal_2', 'basal_3','apical_oblique']}


    # Rhythmic distal -> L2 Pyr
    synParamsList = [{'synMech': 'L2Pyr_AMPA',
                'A_weight': p['input_dist_A_weight_L2Pyr_ampa'],
                'A_delay': p['input_dist_A_delay_L2'],
                'lamtha': 100.},

                {'synMech': 'L2Pyr_NMDA',
                'A_weight': p['input_dist_A_weight_L2Pyr_nmda'],
                'A_delay': p['input_dist_A_delay_L2'],
                'lamtha': 100.}]

    for i,synParams in enumerate(synParamsList):
        netParams.connParams['extRhythmicDistal->L2Pyr_%d'%(i)] = { 
            'preConds': {'pop': 'extRhythmicDistal'}, 
            'postConds': {'pop': 'L2Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 1,
            'sec': ['apical_tuft']}


    # Rhythmic proximal -> L5 Pyr
    synParamsList = [{'synMech': 'L5Pyr_AMPA',
                'A_weight': p['input_prox_A_weight_L5Pyr_ampa'],
                'A_delay': p['input_prox_A_delay_L5'],
                'lamtha': 100.},

                {'synMech': 'L5Pyr_NMDA',
                'A_weight': p['input_prox_A_weight_L5Pyr_nmda'],
                'A_delay': p['input_prox_A_delay_L5'],
                'lamtha': 100.}]

    for i,synParams in enumerate(synParamsList):
        netParams.connParams['extRhythmicProx->L5Pyr_%d'%(i)] = { 
            'preConds': {'pop': 'extRhythmicProximal'}, 
            'postConds': {'pop': 'L5Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 3,
            'sec': ['basal_2', 'basal_3','apical_oblique']}


    # Rhythmic distal -> L5 Pyr
    synParamsList = [{'synMech': 'L5Pyr_AMPA',
                'A_weight': p['input_dist_A_weight_L5Pyr_ampa'],
                'A_delay': p['input_dist_A_delay_L5'],
                'lamtha': 100.},

                {'synMech': 'L5Pyr_NMDA',
                'A_weight': p['input_dist_A_weight_L5Pyr_nmda'],
                'A_delay': p['input_dist_A_delay_L5'],
                'lamtha': 100.}]

    for i,synParams in enumerate(synParamsList):
        netParams.connParams['extRhythmicDistal->L5Pyr_%d'%(i)] = { 
            'preConds': {'pop': 'extRhythmicDistal'}, 
            'postConds': {'pop': 'L5Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 1,
            'sec': ['apical_tuft']}


    # Rhytmic proximal -> L2 Basket
    synParamsList = [{'synMech': 'AMPA',
                'A_weight': p['input_prox_A_weight_L2Basket_ampa'],
                'A_delay': p['input_prox_A_delay_L2'],
                'lamtha': 100.},

                {'synMech': 'NMDA',
                'A_weight': p['input_prox_A_weight_L2Basket_nmda'],
                'A_delay': p['input_prox_A_delay_L2'],
                'lamtha': 100.}]

    for i,synParams in enumerate(synParamsList):
        netParams.connParams['extRhythmicProx->L2Basket_%d'%(i)] = { 
            'preConds': {'pop': 'extRhythmicProximal'}, 
            'postConds': {'pop': 'L2Basket'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 1,
            'sec': 'soma'}


    # Rhytmic proximal -> L5 Basket
    synParamsList = [{'synMech': 'AMPA',
                'A_weight': p['input_prox_A_weight_L5Basket_ampa'],
                'A_delay': p['input_prox_A_delay_L5'],
                'lamtha': 100.},

                {'synMech': 'NMDA',
                'A_weight': p['input_prox_A_weight_L5Basket_nmda'],
                'A_delay': p['input_prox_A_delay_L5'],
                'lamtha': 100.}]

    for i,synParams in enumerate(synParamsList):
        netParams.connParams['extRhythmicProx->L5Basket_%d'%(i)] = { 
            'preConds': {'pop': 'extRhythmicProximal'}, 
            'postConds': {'pop': 'L5Basket'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 1,
            'sec': 'soma'}


#------------------------------------------------------------------------------
# Evoked proximal and distal inputs parameters 
#------------------------------------------------------------------------------

if cfg.evokedInputs:

    # Evoked proximal inputs (population of 1 VecStim)
    nprox = len([k for k in cfg.hnn_params if k.startswith('t_evprox')])
    ndist = len([k for k in cfg.hnn_params if k.startswith('t_evdist')])

    # Evoked proximal inputs (population of 1 VecStim)
    for iprox in range(nprox):
        for pop in pops:
            skey = 'evprox_%d'%(iprox+1)
            netParams.popParams['evokedProximal_%d_%s'%(iprox+1, pop)] = {
                'cellModel': 'VecStim',
                'numCells': cellsPerPop[pop],
                'xRange': [extLocX, extLocX],
                'yRange': [extLocY, extLocY],
                'zRange': [extLocZ, extLocZ],
                'seed': int(p['prng_seedcore']),
                'spikePattern': {
                        'type': 'evoked',
                        'start': p['t_' + skey],
                        'startStd': p['sigma_t_' + skey],
                        'numspikes': p['numspikes_' + skey],
                        'sync': p['sync_evinput']}}


        # Evoked proximal -> L2 Pyr
        synParamsList = [{'synMech': 'L2Pyr_AMPA',
                    'A_weight': p['gbar_'+skey+'_L2Pyr_ampa'],
                    'A_delay': 0.1,
                    'lamtha': 3.},

                    {'synMech': 'L2Pyr_NMDA',
                    'A_weight': p['gbar_'+skey+'_L2Pyr_nmda'],
                    'A_delay': 0.1,
                    'lamtha': 3.}]

        for i,synParams in enumerate(synParamsList):
            netParams.connParams['evokedProx_%d->L2Pyr_%d'%(iprox+1, i)] = { 
                'preConds': {'pop': 'evokedProximal_%d_L2Pyr'%(iprox+1)}, 
                'postConds': {'pop': 'L2Pyr'},
                'synMech': synParams['synMech'],
                'weight': weightDistFunc.format(**synParams),
                'delay': delayDistFunc.format(**synParams),
                'connList': conn1to1Pyr,
                'synsPerConn': 3,
                'sec': ['basal_2', 'basal_3','apical_oblique']}

        # Evoked proximal -> L5 Pyr
        synParamsList = [{'synMech': 'L5Pyr_AMPA',
                    'A_weight': p['gbar_'+skey+'_L5Pyr_ampa'],
                    'A_delay': 1.0,
                    'lamtha': 3.},

                    {'synMech': 'L5Pyr_NMDA',
                    'A_weight': p['gbar_'+skey+'_L5Pyr_nmda'],
                    'A_delay': 1.0,
                    'lamtha': 3.}]

        for i,synParams in enumerate(synParamsList):
            netParams.connParams['evokedProx_%d->L5Pyr_%d'%(iprox+1, i)] = { 
                'preConds': {'pop': 'evokedProximal_%d_L5Pyr'%(iprox+1)}, 
                'postConds': {'pop': 'L5Pyr'},
                'synMech': synParams['synMech'],
                'weight': weightDistFunc.format(**synParams),
                'delay': delayDistFunc.format(**synParams),
                'connList': conn1to1Pyr,
                'synsPerConn': 3,
                'sec': ['basal_2', 'basal_3','apical_oblique']}

        # Evoked proximal -> L2 Basket
        synParamsList = [{'synMech': 'AMPA',
                    'A_weight': p['gbar_'+skey+'_L2Basket_ampa'],
                    'A_delay': 0.1,
                    'lamtha': 3.},

                    {'synMech': 'NMDA',
                    'A_weight': p['gbar_'+skey+'_L2Basket_nmda'],
                    'A_delay': 0.1,
                    'lamtha': 3.}]

        for i,synParams in enumerate(synParamsList):
            netParams.connParams['evokedProx_%d->L2Basket_%d'%(iprox+1, i)] = { 
                'preConds': {'pop': 'evokedProximal_%d_L2Basket'%(iprox+1)}, 
                'postConds': {'pop': 'L2Basket'},
                'synMech': synParams['synMech'],
                'weight': weightDistFunc.format(**synParams),
                'delay': delayDistFunc.format(**synParams),
                'connList': conn1to1Basket,
                'synsPerConn': 1,
                'sec': 'soma'}

        # Evoked proximal -> L5 Basket
        synParamsList = [{'synMech': 'AMPA',
                    'A_weight': p['gbar_'+skey+'_L5Basket_ampa'],
                    'A_delay': 1.0,
                    'lamtha': 3.},

                    {'synMech': 'NMDA',
                    'A_weight': p['gbar_'+skey+'_L5Basket_nmda'],
                    'A_delay': 1.0,
                    'lamtha': 3.}]

        for i,synParams in enumerate(synParamsList):
            netParams.connParams['evokedProx_%d->L5Basket_%d'%(iprox+1, i)] = { 
                'preConds': {'pop': 'evokedProximal_%d_L5Basket'%(iprox+1)}, 
                'postConds': {'pop': 'L5Basket'},
                'synMech': synParams['synMech'],
                'weight': weightDistFunc.format(**synParams),
                'delay': delayDistFunc.format(**synParams),
                'connList': conn1to1Basket,
                'synsPerConn': 1,
                'sec': 'soma'}


    # Evoked distal inputs (population of 1 VecStim)
    for idist in range(ndist):
        for pop in pops:
            skey = 'evdist_%d'%(idist+1)
            netParams.popParams['evokedDistal_%d_%s'%(idist+1, pop)] = {
            'cellModel': 'VecStim',
            'numCells': cellsPerPop[pop],
            'xRange': [extLocX, extLocX],
            'yRange': [extLocY, extLocY],
            'zRange': [extLocZ, extLocZ],
            'seed': int(p['prng_seedcore']),
            'spikePattern': {
                    'type': 'evoked',
                    'start': p['t_' + skey],
                    'startStd': p['sigma_t_' + skey],
                    'numspikes': p['numspikes_' + skey],
                    'sync': p['sync_evinput']}}


        # Evoked Distal -> L2 Pyr
        synParamsList = [{'synMech': 'L2Pyr_AMPA',
                    'A_weight': p['gbar_'+skey+'_L2Pyr_ampa'],
                    'A_delay': 0.1,
                    'lamtha': 3.},

                    {'synMech': 'L2Pyr_NMDA',
                    'A_weight': p['gbar_'+skey+'_L2Pyr_nmda'],
                    'A_delay': 0.1,
                    'lamtha': 3.}]

        for i,synParams in enumerate(synParamsList):
            netParams.connParams['evokedDistal_%d->L2Pyr_%d'%(idist+1, i)] = { 
                'preConds': {'pop': 'evokedDistal_%d_L2Pyr'%(idist+1)}, 
                'postConds': {'pop': 'L2Pyr'},
                'synMech': synParams['synMech'],
                'weight': weightDistFunc.format(**synParams),
                'delay': delayDistFunc.format(**synParams),
                'connList': conn1to1Pyr,
                'synsPerConn': 1,
                'sec': 'apical_tuft'}

        # Evoked Distal -> L5 Pyr
        synParamsList = [{'synMech': 'L5Pyr_AMPA',
                    'A_weight': p['gbar_'+skey+'_L5Pyr_ampa'],
                    'A_delay': 0.1,
                    'lamtha': 3.},

                    {'synMech': 'L5Pyr_NMDA',
                    'A_weight': p['gbar_'+skey+'_L5Pyr_nmda'],
                    'A_delay': 0.1,
                    'lamtha': 3.}]

        for i,synParams in enumerate(synParamsList):
            netParams.connParams['evokedDistal_%d->L5Pyr_%d'%(idist+1, i)] = { 
                'preConds': {'pop': 'evokedDistal_%d_L5Pyr'%(idist+1)}, 
                'postConds': {'pop': 'L5Pyr'},
                'synMech': synParams['synMech'],
                'weight': weightDistFunc.format(**synParams),
                'delay': delayDistFunc.format(**synParams),
                'connList': conn1to1Pyr,
                'synsPerConn': 1,
                'sec': 'apical_tuft'}

        # Evoked Distal -> L2 Basket
        synParamsList = [{'synMech': 'AMPA',
                    'A_weight': p['gbar_'+skey+'_L2Basket_ampa'],
                    'A_delay': 0.1,
                    'lamtha': 3.},

                    {'synMech': 'NMDA',
                    'A_weight': p['gbar_'+skey+'_L2Basket_nmda'],
                    'A_delay': 0.1,
                    'lamtha': 3.}]

        for i,synParams in enumerate(synParamsList):
            netParams.connParams['evokedDistal_%d->L2Basket_%d'%(idist+1, i)] = { 
                'preConds': {'pop': 'evokedDistal_%d_L2Basket'%(idist+1)}, 
                'postConds': {'pop': 'L2Basket'},
                'synMech': synParams['synMech'],
                'weight': weightDistFunc.format(**synParams),
                'delay': delayDistFunc.format(**synParams),
                'connList': conn1to1Basket,
                'synsPerConn': 1,
                'sec': 'soma'}


#------------------------------------------------------------------------------
# Tonic input parameters 
#------------------------------------------------------------------------------

if cfg.tonicInputs:

    # Tonic inputs (IClamp) -> L2Pyr
    if p['Itonic_T_L2Pyr_soma'] == -1:
        t_dur = cfg.duration - p['Itonic_t0_L2Pyr_soma']
    else:
        t_dur = p['Itonic_T_L2Pyr_soma'] - p['Itonic_t0_L2Pyr_soma']

    netParams.stimSourceParams['ITonic_L2Pyr'] = {'type': 'IClamp', 'del': p['Itonic_t0_L2Pyr_soma'], 'dur': t_dur, 'amp': p['Itonic_A_L2Pyr_soma']}
    netParams.stimTargetParams['ITonic->L2Pyr'] = {'source': 'ITonic_L2Pyr', 'sec':'soma', 'loc': 0.5, 'conds': {'pop': 'L2Pyr'}}


    # Tonic inputs (IClamp) -> L5Pyr
    if p['Itonic_T_L5Pyr_soma'] == -1:
        t_dur = cfg.duration - p['Itonic_t0_L5Pyr_soma']
    else:
        t_dur = p['Itonic_T_L5Pyr_soma'] - p['Itonic_t0_L5Pyr_soma']

    netParams.stimSourceParams['ITonic_L5Pyr'] = {'type': 'IClamp', 'del': p['Itonic_t0_L5Pyr_soma'], 'dur': t_dur, 'amp': p['Itonic_A_L5Pyr_soma']}
    netParams.stimTargetParams['ITonic->L5Pyr'] = {'source': 'ITonic_L5Pyr', 'sec':'soma', 'loc': 0.5, 'conds': {'pop': 'L5Pyr'}}


    # Tonic inputs (IClamp) -> L2Basket
    if p['Itonic_T_L2Basket'] == -1:
        t_dur = cfg.duration - p['Itonic_t0_L2Basket']
    else:
        t_dur = p['Itonic_T_L2Basket'] - p['Itonic_t0_L2Basket']

    netParams.stimSourceParams['ITonic_L2Basket'] = {'type': 'IClamp', 'del': p['Itonic_t0_L2Basket'], 'dur': t_dur, 'amp': p['Itonic_A_L2Basket']}
    netParams.stimTargetParams['ITonic->L2Basket'] = {'source': 'ITonic_L2Basket', 'sec':'soma', 'loc': 0.5, 'conds': {'pop': 'L2Basket'}}


    # Tonic inputs (IClamp) -> L5Basket
    if p['Itonic_T_L5Basket'] == -1:
        t_dur = cfg.duration - p['Itonic_t0_L5Basket']
    else:
        t_dur = p['Itonic_T_L5Basket'] - p['Itonic_t0_L5Basket']

    netParams.stimSourceParams['ITonic_L5Basket'] = {'type': 'IClamp', 'del': p['Itonic_t0_L5Basket'], 'dur': t_dur, 'amp': p['Itonic_A_L5Basket']}
    netParams.stimTargetParams['ITonic->L5Basket'] = {'source': 'ITonic_L5Basket', 'sec':'soma', 'loc': 0.5, 'conds': {'pop': 'L5Basket'}}


#------------------------------------------------------------------------------
# Poisson-distributed input parameters 
#------------------------------------------------------------------------------

if cfg.poissonInputs:

    # Poisson inputs -> L2 Pyr
    netParams.popParams['extPoisson_L2Pyr'] = {
        'cellModel': 'VecStim',
        'numCells': cellsPerPop['L2Pyr'],
        'xRange': [extLocX, extLocX],
        'yRange': [extLocY, extLocY],
        'zRange': [extLocZ, extLocZ],
        'seed': int(cfg.hnn_params.get('prng_seedcore')),
        'spikePattern': {
                'type': 'poisson',
                'start': p['t0_pois'],
                'stop': p['T_pois'],
                'frequency': p['L2Pyr_Pois_lamtha']}}

    synParamsList = [{'synMech': 'L2Pyr_AMPA',
                'A_weight': p['L2Pyr_Pois_A_weight_ampa'],
                'A_delay': 0.1,
                'lamtha': 100.},

                {'synMech': 'L2Pyr_NMDA',
                'A_weight': p['L2Pyr_Pois_A_weight_nmda'],
                'A_delay': 0.1,
                'lamtha': 100.}]

    for i,synParams in enumerate(synParamsList):
        netParams.connParams['extPoisson->L2Pyr_%d'%(i)] = { 
            'preConds': {'pop': 'extPoisson_L2Pyr'}, 
            'postConds': {'pop': 'L2Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'connList': conn1to1Pyr,
            'synsPerConn': 3,
            'sec': ['basal_2', 'basal_3','apical_oblique']}


    # Poisson inputs -> L5 Pyr
    netParams.popParams['extPoisson_L5Pyr'] = {
        'cellModel': 'VecStim',
        'numCells': cellsPerPop['L5Pyr'],
        'xRange': [extLocX, extLocX],
        'yRange': [extLocY, extLocY],
        'zRange': [extLocZ, extLocZ],
        'seed': int(p['prng_seedcore']),
        'spikePattern': {
                'type': 'poisson',
                'start': p['t0_pois'],
                'stop': p['T_pois'],
                'frequency': p['L5Pyr_Pois_lamtha']}}

    synParamsList = [{'synMech': 'L5Pyr_AMPA',
                'A_weight': p['L5Pyr_Pois_A_weight_ampa'],
                'A_delay': 0.1,
                'lamtha': 100.},

                {'synMech': 'L5Pyr_NMDA',
                'A_weight': p['L5Pyr_Pois_A_weight_nmda'],
                'A_delay': 0.1,
                'lamtha': 100.}]

    for i,synParams in enumerate(synParamsList):
        netParams.connParams['extPoisson->L5Pyr_%d'%(i)] = { 
            'preConds': {'pop': 'extPoisson_L5Pyr'}, 
            'postConds': {'pop': 'L5Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'connList': conn1to1Pyr,
            'synsPerConn': 3,
            'sec': ['basal_2', 'basal_3','apical_oblique']}


    # Poisson inputs -> L2 Basket
    netParams.popParams['extPoisson_L2Basket'] = {
        'cellModel': 'VecStim',
        'numCells': cellsPerPop['L2Basket'],
        'xRange': [extLocX, extLocX],
        'yRange': [extLocY, extLocY],
        'zRange': [extLocZ, extLocZ],
        'seed': int(p['prng_seedcore']),
        'spikePattern': {
                'type': 'poisson',
                'start': p['t0_pois'],
                'stop': p['T_pois'],
                'frequency': p['L2Basket_Pois_lamtha']}}

    synParamsList = [{'synMech': 'AMPA',
                'A_weight': p['L2Basket_Pois_A_weight_ampa'],
                'A_delay': 1.0,
                'lamtha': 100.},

                {'synMech': 'NMDA',
                'A_weight': p['L2Basket_Pois_A_weight_nmda'],
                'A_delay': 1.0,
                'lamtha': 100.}]

    for i,synParams in enumerate(synParamsList):
        netParams.connParams['extPoisson->L2Basket_%d'%(i)] = { 
            'preConds': {'pop': 'extPoisson_L2Basket'}, 
            'postConds': {'pop': 'L2Basket'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'connList': conn1to1Basket,
            'synsPerConn': 1,
            'sec': ['soma']}


    # Poisson inputs -> L5 Basket
    netParams.popParams['extPoisson_L5Basket'] = {
        'cellModel': 'VecStim',
        'numCells': cellsPerPop['L5Basket'],
        'xRange': [extLocX, extLocX],
        'yRange': [extLocY, extLocY],
        'zRange': [extLocZ, extLocZ],
        'seed': int(p['prng_seedcore']),
        'spikePattern': {
                'type': 'poisson',
                'start': p['t0_pois'],
                'stop': p['T_pois'],
                'frequency': p['L5Basket_Pois_lamtha']}}

    synParamsList = [{'synMech': 'AMPA',
                'A_weight': p['L5Basket_Pois_A_weight_ampa'],
                'A_delay': 1.0,
                'lamtha': 100.},

                {'synMech': 'NMDA',
                'A_weight': p['L5Basket_Pois_A_weight_nmda'],
                'A_delay': 1.0,
                'lamtha': 100.}]

    for i,synParams in enumerate(synParamsList):
        netParams.connParams['extPoisson->L5Basket_%d'%(i)] = { 
            'preConds': {'pop': 'extPoisson_L5Basket'}, 
            'postConds': {'pop': 'L5Basket'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'connList': conn1to1Basket,
            'synsPerConn': 1,
            'sec': ['soma']}


#------------------------------------------------------------------------------
# Gaussian-distributed inputs parameters 
#------------------------------------------------------------------------------

if cfg.gaussInputs:

    # Gaussian inputs -> L2 Pyr
    netParams.popParams['extGauss_L2Pyr'] = {
        'cellModel': 'VecStim',
        'numCells': 1,
        'xRange': [extLocX, extLocX],
        'yRange': [extLocY, extLocY],
        'zRange': [extLocZ, extLocZ],
        'seed': int(p['prng_seedcore']),
        'spikePattern': {
                'type': 'gauss',
                'mu': p['L2Pyr_Gauss_mu'],
                'sigma': p['L2Pyr_Gauss_sigma']}}

    synParams = {'synMech': 'L2Pyr_AMPA',
                'A_weight': p['L2Pyr_Gauss_A_weight'],
                'A_delay': 0.1,
                'lamtha': 100.}

    netParams.connParams['extGauss->L2Pyr'] = { 
        'preConds': {'pop': 'extGauss_L2Pyr'}, 
        'postConds': {'pop': 'L2Pyr'},
        'synMech': synParams['synMech'],
        'weight': weightDistFunc.format(**synParams),
        'delay': delayDistFunc.format(**synParams),
        'synsPerConn': 3,
        'sec': ['basal_2', 'basal_3','apical_oblique']}


    # Gaussian inputs -> L5 Pyr
    netParams.popParams['extGauss_L5Pyr'] = {
        'cellModel': 'VecStim',
        'numCells': 1,
        'xRange': [extLocX, extLocX],
        'yRange': [extLocY, extLocY],
        'zRange': [extLocZ, extLocZ],
        'seed': int(p['prng_seedcore']),
        'spikePattern': {
                'type': 'gauss',
                'mu': p['L5Pyr_Gauss_mu'],
                'sigma': p['L5Pyr_Gauss_sigma']}}

    synParams = {'synMech': 'L5Pyr_AMPA',
                'A_weight': p['L5Pyr_Gauss_A_weight'],
                'A_delay': 0.1,
                'lamtha': 100.}

    netParams.connParams['extGauss->L5Pyr'] = { 
        'preConds': {'pop': 'extGauss_L5Pyr'}, 
        'postConds': {'pop': 'L5Pyr'},
        'synMech': synParams['synMech'],
        'weight': weightDistFunc.format(**synParams),
        'delay': delayDistFunc.format(**synParams),
        'synsPerConn': 3,
        'sec': ['basal_2', 'basal_3','apical_oblique']}

