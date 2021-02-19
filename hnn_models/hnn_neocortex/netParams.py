
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
from cellParams import cellParams  # defined in separate module for clarity
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
        'seed': int(p['prng_seedcore_input_prox']),
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
    nprox = len([k for k in cfg.__dict__ if k.startswith('t_evprox')])
    ndist = len([k for k in cfg.__dict__ if k.startswith('t_evdist')])

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
                'seed': int(p['prng_seedcore_' + skey]),
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
            'seed': int(p['prng_seedcore_' + skey]),
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
        'seed': int(cfg.hnn_params.get('prng_seedcore_extpois')),
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
        'seed': int(p['prng_seedcore_extpois']),
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
        'seed': int(p['prng_seedcore_extpois']),
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
        'seed': int(p['prng_seedcore_extpois']),
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
        'seed': int(p['prng_seedcore_extgauss']),
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
        'seed': int(p['prng_seedcore_extgauss']),
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

