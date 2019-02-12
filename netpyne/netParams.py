
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


# ----------------------------------------------------------------------------
#
# NETWORK PARAMETERS
#
# ----------------------------------------------------------------------------

netParams = specs.NetParams()  # object of class NetParams to store the network parameters

#------------------------------------------------------------------------------
# General network parameters
#------------------------------------------------------------------------------
netParams.sizeX = (cfg.N_pyr_x * cfg.gridSpacing) - 1  # x-dimension (horizontal length) size in um
netParams.sizeY = cfg.sizeY # y-dimension (vertical height or cortical depth) size in um
netParams.sizeZ = (cfg.N_pyr_y * cfg.gridSpacing) - 1 # z-dimension (horizontal depth) size in um
netParams.shape = 'cuboid' 

# ----------------------------------------------------------------------------
# Cell parameters
# ----------------------------------------------------------------------------
from cellParams import cellParams  # defined in separate module for clarity
netParams.cellParams = cellParams


# ----------------------------------------------------------------------------
# Population parameters
# ----------------------------------------------------------------------------
layersE = {'L5': [0.5*cfg.sizeY, 0.5*cfg.sizeY], 'L2': [0.5*cfg.sizeY, 0.5*cfg.sizeY]}
layersI = {'L5': [0.6*cfg.sizeY, 0.6*cfg.sizeY], 'L2': [1.4*cfg.sizeY, 1.4*cfg.sizeY]}

netParams.popParams['L2Pyr'] = {'cellType': 'L2Pyr',    'cellModel': 'HH_reduced', 'yRange': layersE['L2'], 'gridSpacing': cfg.gridSpacing} 
netParams.popParams['L2Basket'] = {'cellType': 'L2Basket', 'cellModel': 'HH_simple', 'yRange': layersI['L2'], 'gridSpacing': cfg.gridSpacing} 
netParams.popParams['L5Pyr'] = {'cellType': 'L5Pyr',    'cellModel': 'HH_reduced', 'yRange': layersE['L5'], 'gridSpacing': cfg.gridSpacing} 
netParams.popParams['L5Basket'] = {'cellType': 'L5Basket', 'cellModel': 'HH_simple', 'yRange': layersI['L5'], 'gridSpacing': cfg.gridSpacing} 


#------------------------------------------------------------------------------
# Synaptic mechanism parameters
#------------------------------------------------------------------------------

netParams.synMechParams['L2Pyr_AMPA'] = {'mod':'Exp2Syn', 'tau1': cfg.L2Pyr_ampa_tau1, 'tau2': cfg.L2Pyr_ampa_tau2, 'e': cfg.L2Pyr_ampa_e}
netParams.synMechParams['L2Pyr_NMDA'] = {'mod': 'Exp2Syn', 'tau1': cfg.L2Pyr_nmda_tau1, 'tau2': cfg.L2Pyr_nmda_tau2, 'e': cfg.L2Pyr_nmda_e}
netParams.synMechParams['L2Pyr_GABAA'] = {'mod':'Exp2Syn', 'tau1': cfg.L2Pyr_gabaa_tau1, 'tau2': cfg.L2Pyr_gabaa_tau2, 'e': cfg.L2Pyr_gabaa_e}
netParams.synMechParams['L2Pyr_GABAB'] = {'mod':'Exp2Syn', 'tau1': cfg.L2Pyr_gabab_tau1, 'tau2': cfg.L2Pyr_gabab_tau2, 'e': cfg.L2Pyr_gabab_e}

netParams.synMechParams['L5Pyr_AMPA'] = {'mod':'Exp2Syn', 'tau1': cfg.L5Pyr_ampa_tau1, 'tau2': cfg.L5Pyr_ampa_tau2, 'e': cfg.L5Pyr_ampa_e}
netParams.synMechParams['L5Pyr_NMDA'] = {'mod': 'Exp2Syn', 'tau1': cfg.L5Pyr_nmda_tau1, 'tau2': cfg.L5Pyr_nmda_tau2, 'e': cfg.L5Pyr_nmda_e}
netParams.synMechParams['L5Pyr_GABAA'] = {'mod':'Exp2Syn', 'tau1': cfg.L5Pyr_gabaa_tau1, 'tau2': cfg.L5Pyr_gabaa_tau2, 'e': cfg.L5Pyr_gabaa_e}
netParams.synMechParams['L5Pyr_GABAB'] = {'mod':'Exp2Syn', 'tau1': cfg.L5Pyr_gabab_tau1, 'tau2': cfg.L5Pyr_gabab_tau2, 'e': cfg.L5Pyr_gabab_e}

netParams.synMechParams['AMPA'] = {'mod':'Exp2Syn', 'tau1': 0.5, 'tau2': 5.0, 'e': 0}
netParams.synMechParams['NMDA'] = {'mod': 'Exp2Syn', 'tau1': 1, 'tau2': 20, 'e': 0}
netParams.synMechParams['GABAA'] = {'mod':'Exp2Syn', 'tau1': 0.5, 'tau2': 5, 'e': -80}
netParams.synMechParams['GABAB'] = {'mod':'Exp2Syn', 'tau1': 1, 'tau2': 20, 'e': -80}


#------------------------------------------------------------------------------
# Local connectivity parameters 
#------------------------------------------------------------------------------

# Weight and delay distance-dependent functions (as strings) to use in conn rules
weightDistFunc = '{A_weight} * exp(-(dist_2D**2) / ({lamtha}**2))'
delayDistFunc = '{A_weight} / exp(-(dist_2D**2) / ({lamtha}**2))'

if cfg.localConn:

    # L2 Pyr -> L2 Pyr
    synParamsList = [{'synMech': 'L2Pyr_AMPA',
                'A_weight': cfg.gbar_L2Pyr_L2Pyr_ampa,
                'A_delay': 1.,
                'lamtha': 3.},

                {'synMech': 'L2Pyr_NMDA',
                'A_weight': cfg.gbar_L2Pyr_L2Pyr_nmda,
                'A_delay': 1.,
                'lamtha': 3.}]

    for synParams in synParamsList:
        netParams.connParams['L2Pyr->L2Pyr'] = { 
            'preConds': {'pop': 'L2Pyr'}, 
            'postConds': {'pop': 'L2Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 3,
            'sec': ['basal_2', 'basal_3','apical_oblique', ]}
                    

    # L2 Basket -> L2 Pyr
    synParamsList = [{'synMech': 'L2Pyr_GABAA',
                'A_weight': cfg.gbar_L2Basket_L2Pyr_gabaa,
                'A_delay': 1.,
                'lamtha': 50.},

                {'synMech': 'L2Pyr_GABAB',
                'A_weight': cfg.gbar_L2Basket_L2Pyr_gabab,
                'A_delay': 1.,
                'lamtha': 50.}]

    for synParams in synParamsList:
        netParams.connParams['L2Basket->L2Pyr'] = { 
            'preConds': {'pop': 'L2Basket'}, 
            'postConds': {'pop': 'L2Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 1,
            'sec': ['soma']}


    # L2 Pyr -> L2 Basket 
    synParams = {'synMech': 'AMPA',
                'A_weight': cfg.gbar_L2Pyr_L2Basket,
                'A_delay': 1.,
                'lamtha': 3.}

    netParams.connParams['L2Pyr->L2Basket'] = { 
        'preConds': {'pop': 'L2Pyr'}, 
        'postConds': {'pop': 'L2Basket'},
        'synMech': synParams['synMech'],
        'weight': weightDistFunc.format(**synParams),
        'delay': delayDistFunc.format(**synParams),
        'synsPerConn': 1,
        'sec': ['soma']}


    # L2 Basket -> L2 Basket 
    synParams = {'synMech': 'GABAA',
                'A_weight': cfg.gbar_L2Basket_L2Basket,
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
                'A_weight': cfg.gbar_L5Pyr_L5Pyr_ampa,
                'A_delay': 1.,
                'lamtha': 3.},

                {'synMech': 'L5Pyr_NMDA',
                'A_weight': cfg.gbar_L5Pyr_L5Pyr_nmda,
                'A_delay': 1.,
                'lamtha': 3.}]

    for synParams in synParamsList:
        netParams.connParams['L5Pyr->L5Pyr'] = { 
            'preConds': {'pop': 'L5Pyr'}, 
            'postConds': {'pop': 'L5Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 3,
            'sec': ['basal_2', 'basal_3', 'apical_oblique']}
                

    # L5 Basket -> L5 Pyr
    synParamsList = [{'synMech': 'L5Pyr_GABAA',
                'A_weight': cfg.gbar_L5Basket_L5Pyr_gabaa,
                'A_delay': 1.,
                'lamtha': 70.},

                {'synMech': 'L5Pyr_GABAB',
                'A_weight': cfg.gbar_L5Basket_L5Pyr_gabab,
                'A_delay': 1.,
                'lamtha': 70.}]

    for synParams in synParamsList:
        netParams.connParams['L5Basket->L5Pyr'] = { 
            'preConds': {'pop': 'L5Basket'}, 
            'postConds': {'pop': 'L5Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 1,
            'sec': ['soma']}


    # L2 Pyr -> L5 Pyr
    synParams = {'synMech': 'L5Pyr_AMPA',
                'A_weight': cfg.gbar_L2Pyr_L5Pyr,
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
                'A_weight': cfg.gbar_L2Basket_L5Pyr,
                'A_delay': 1.,
                'lamtha': 50.}

    netParams.connParams['L2Basket->L5Pyr'] = { 
        'preConds': {'pop': 'L2Basket'}, 
        'postConds': {'pop': 'L5Pyr'},
        'synMech': synParams['synMech'],
        'weight': weightDistFunc.format(**synParams),
        'delay': delayDistFunc.format(**synParams),
        'synsPerConn': 4,
        'sec': ['apical_tuft']}
        

    # L5 Pyr -> L5 Basket 
    synParams = {'synMech': 'AMPA',
                'A_weight': cfg.gbar_L5Pyr_L5Basket,
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
                'A_weight': cfg.gbar_L2Pyr_L5Basket,
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
                'A_weight': cfg.gbar_L5Basket_L5Basket,
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

if cfg.rhythmicInputs:

    # Location of external inputs
    xrange = np.arange(cfg.N_pyr_x)
    extLocX = xrange[int((len(xrange) - 1) // 2)]
    zrange = np.arange(cfg.N_pyr_y)
    extLocZ = xrange[int((len(zrange) - 1) // 2)]
    extLocY = 1307.4  # positive depth of L5 relative to L2; doesn't affect weight/delay calculations


    # External Rhythmic proximal inputs (population of 1 VecStim)
    netParams.popParams['extRhythmicProximal'] = {
        'cellModel': 'VecStim',
        'numCells': 1,
        'xRange': [extLocX, extLocX],
        'yRange': [extLocY, extLocY],
        'zRange': [extLocZ, extLocZ],
        'seed': int(cfg.prng_seedcore_input_prox),
        'spikePattern': {
                'type': 'rhythmic',
                'start': cfg.t0_input_prox,
                'startStd': cfg.t0_input_stdev_prox,
                'stop': cfg.tstop_input_prox,
                'freq': cfg.f_input_prox,
                'freqStd': cfg.f_stdev_prox,
                'eventsPerCycle': cfg.events_per_cycle_prox,
                'distribution': cfg.distribution_prox,
                'repeats': cfg.repeats_prox}}


    # External Rhythmic distal inputs (population of 1 VecStim)
    netParams.popParams['extRhythmicDistal'] = {
        'cellModel': 'VecStim',
        'numCells': 1,
        'xRange': [extLocX, extLocX],
        'yRange': [extLocY, extLocY],
        'zRange': [extLocZ, extLocZ],
        'seed': int(cfg.prng_seedcore_input_dist),
        'spikePattern': {
                'type': 'rhythmic',
                'start': cfg.t0_input_dist,
                'startStd': cfg.t0_input_stdev_dist,
                'stop': cfg.tstop_input_dist,
                'freq': cfg.f_input_dist,
                'freqStd': cfg.f_stdev_dist,
                'eventsPerCycle': cfg.events_per_cycle_dist,
                'distribution': cfg.distribution_dist,
                'repeats': cfg.repeats_dist}}


    # Rhytmic proximal -> L2 Pyr
    synParamsList = [{'synMech': 'L2Pyr_AMPA',
                'A_weight': cfg.input_prox_A_weight_L2Pyr_ampa,
                'A_delay': cfg.input_prox_A_delay_L2,
                'lamtha': 100.},

                {'synMech': 'L2Pyr_NMDA',
                'A_weight': cfg.input_prox_A_weight_L2Pyr_nmda,
                'A_delay': cfg.input_prox_A_delay_L2,
                'lamtha': 100.}]

    for synParams in synParamsList:
        netParams.connParams['extRhythmicProx->L2Pyr'] = { 
            'preConds': {'pop': 'extRhythmicProximal'}, 
            'postConds': {'pop': 'L2Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 3,
            'sec': ['basal_2', 'basal_3','apical_oblique']}


    # Rhythmic distal -> L2 Pyr
    synParamsList = [{'synMech': 'L2Pyr_AMPA',
                'A_weight': cfg.input_dist_A_weight_L2Pyr_ampa,
                'A_delay': cfg.input_dist_A_delay_L2,
                'lamtha': 100.},

                {'synMech': 'L2Pyr_NMDA',
                'A_weight': cfg.input_dist_A_weight_L2Pyr_nmda,
                'A_delay': cfg.input_dist_A_delay_L2,
                'lamtha': 100.}]

    for synParams in synParamsList:
        netParams.connParams['extRhythmicDistal->L2Pyr'] = { 
            'preConds': {'pop': 'extRhythmicDistal'}, 
            'postConds': {'pop': 'L2Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 3,
            'sec': ['apical_tuft']}


    # Rhythmic proximal -> L5 Pyr
    synParamsList = [{'synMech': 'L5Pyr_AMPA',
                'A_weight': cfg.input_prox_A_weight_L5Pyr_ampa,
                'A_delay': cfg.input_prox_A_delay_L5,
                'lamtha': 100.},

                {'synMech': 'L5Pyr_NMDA',
                'A_weight': cfg.input_prox_A_weight_L5Pyr_nmda,
                'A_delay': cfg.input_prox_A_delay_L5,
                'lamtha': 100.}]

    for synParams in synParamsList:
        netParams.connParams['extRhythmicProx->L5Pyr'] = { 
            'preConds': {'pop': 'extRhythmicProximal'}, 
            'postConds': {'pop': 'L5Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 3,
            'sec': ['basal_2', 'basal_3','apical_oblique']}


    # Rhythmic distal -> L5 Pyr
    synParamsList = [{'synMech': 'L5Pyr_AMPA',
                'A_weight': cfg.input_dist_A_weight_L5Pyr_ampa,
                'A_delay': cfg.input_dist_A_delay_L5,
                'lamtha': 100.},

                {'synMech': 'L5Pyr_NMDA',
                'A_weight': cfg.input_dist_A_weight_L5Pyr_nmda,
                'A_delay': cfg.input_dist_A_delay_L5,
                'lamtha': 100.}]

    for synParams in synParamsList:
        netParams.connParams['extRhythmicDistal->L5Pyr'] = { 
            'preConds': {'pop': 'extRhythmicDistal'}, 
            'postConds': {'pop': 'L5Pyr'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 3,
            'sec': ['apical_tuft']}


    # Rhytmic proximal -> L2 Basket
    synParamsList = [{'synMech': 'AMPA',
                'A_weight': cfg.input_prox_A_weight_L2Basket_ampa,
                'A_delay': cfg.input_prox_A_delay_L2,
                'lamtha': 100.},

                {'synMech': 'NMDA',
                'A_weight': cfg.input_prox_A_weight_L2Basket_nmda,
                'A_delay': cfg.input_prox_A_delay_L2,
                'lamtha': 100.}]

    for synParams in synParamsList:
        netParams.connParams['extRhythmicProx->L2Basket'] = { 
            'preConds': {'pop': 'extRhythmicProximal'}, 
            'postConds': {'pop': 'L2Basket'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 3,
            'sec': 'soma'}


    # Rhytmic proximal -> L5 Basket
    synParamsList = [{'synMech': 'AMPA',
                'A_weight': cfg.input_prox_A_weight_L5Basket_ampa,
                'A_delay': cfg.input_prox_A_delay_L5,
                'lamtha': 100.},

                {'synMech': 'NMDA',
                'A_weight': cfg.input_prox_A_weight_L5Basket_nmda,
                'A_delay': cfg.input_prox_A_delay_L5,
                'lamtha': 100.}]

    for synParams in synParamsList:
        netParams.connParams['extRhythmicProx->L5Basket'] = { 
            'preConds': {'pop': 'extRhythmicProximal'}, 
            'postConds': {'pop': 'L5Basket'},
            'synMech': synParams['synMech'],
            'weight': weightDistFunc.format(**synParams),
            'delay': delayDistFunc.format(**synParams),
            'synsPerConn': 3,
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
        skey = 'evprox_' + str(iprox+1)
        netParams.popParams['evokedProximal_%s'%(str(iprox+1))] = {
            'cellModel': 'VecStim',
            'numCells': 1,
            'xRange': [extLocX, extLocX],
            'yRange': [extLocY, extLocY],
            'zRange': [extLocZ, extLocZ],
            'seed': int(getattr(cfg, 'prng_seedcore_' + skey)),
            'spikePattern': {
                    'type': 'evoked',
                    'start': getattr(cfg, 't_' + skey),
                    'startStd': getattr(cfg, 'sigma_t_' + skey),
                    'numspikes': getattr(cfg, 'numspikes_' + skey),
                    'sync': getattr(cfg, 'sync_evinput')}}


        # Evoked proximal -> L2 Pyr
        synParamsList = [{'synMech': 'L2Pyr_AMPA',
                    'A_weight': getattr(cfg, 'gbar_'+skey+'_L2Pyr_ampa'),
                    'A_delay': 0.1,
                    'lamtha': 3.},

                    {'synMech': 'L2Pyr_NMDA',
                    'A_weight': getattr(cfg, 'gbar_'+skey+'_L2Pyr_nmda'),
                    'A_delay': 0.1,
                    'lamtha': 3.}]

        for synParams in synParamsList:
            netParams.connParams['evokedProx_%s->L2Pyr'%(str(iprox+1))] = { 
                'preConds': {'pop': 'evokedProximal_%s'%(str(iprox+1))}, 
                'postConds': {'pop': 'L2Pyr'},
                'synMech': synParams['synMech'],
                'weight': weightDistFunc.format(**synParams),
                'delay': delayDistFunc.format(**synParams),
                'synsPerConn': 3,
                'sec': ['basal_2', 'basal_3','apical_oblique']}

        # Evoked proximal -> L5 Pyr
        synParamsList = [{'synMech': 'L5Pyr_AMPA',
                    'A_weight': getattr(cfg, 'gbar_'+skey+'_L5Pyr_ampa'),
                    'A_delay': 1.0,
                    'lamtha': 3.},

                    {'synMech': 'L5Pyr_NMDA',
                    'A_weight': getattr(cfg, 'gbar_'+skey+'_L5Pyr_nmda'),
                    'A_delay': 1.0,
                    'lamtha': 3.}]

        for synParams in synParamsList:
            netParams.connParams['evokedProx_%s->L5Pyr'%(str(iprox+1))] = { 
                'preConds': {'pop': 'evokedProximal_%s'%(str(iprox+1))}, 
                'postConds': {'pop': 'L5Pyr'},
                'synMech': synParams['synMech'],
                'weight': weightDistFunc.format(**synParams),
                'delay': delayDistFunc.format(**synParams),
                'synsPerConn': 3,
                'sec': ['basal_2', 'basal_3','apical_oblique']}

        # Evoked proximal -> L2 Basket
        synParamsList = [{'synMech': 'AMPA',
                    'A_weight': getattr(cfg, 'gbar_'+skey+'_L2Basket_ampa'),
                    'A_delay': 0.1,
                    'lamtha': 3.},

                    {'synMech': 'NMDA',
                    'A_weight': getattr(cfg, 'gbar_'+skey+'_L2Basket_nmda'),
                    'A_delay': 0.1,
                    'lamtha': 3.}]

        for synParams in synParamsList:
            netParams.connParams['evokedProx_%s->L2Basket'%(str(iprox+1))] = { 
                'preConds': {'pop': 'evokedProximal_%s'%(str(iprox+1))}, 
                'postConds': {'pop': 'L2Basket'},
                'synMech': synParams['synMech'],
                'weight': weightDistFunc.format(**synParams),
                'delay': delayDistFunc.format(**synParams),
                'synsPerConn': 1,
                'sec': 'soma'}

        # Evoked proximal -> L5 Basket
        synParamsList = [{'synMech': 'AMPA',
                    'A_weight': getattr(cfg, 'gbar_'+skey+'_L5Basket_ampa'),
                    'A_delay': 1.0,
                    'lamtha': 3.},

                    {'synMech': 'NMDA',
                    'A_weight': getattr(cfg, 'gbar_'+skey+'_L5Basket_nmda'),
                    'A_delay': 1.0,
                    'lamtha': 3.}]

        for synParams in synParamsList:
            netParams.connParams['evokedProx_%s->L5Basket'%(str(iprox+1))] = { 
                'preConds': {'pop': 'evokedProximal_%s'%(str(iprox+1))}, 
                'postConds': {'pop': 'L5Basket'},
                'synMech': synParams['synMech'],
                'weight': weightDistFunc.format(**synParams),
                'delay': delayDistFunc.format(**synParams),
                'synsPerConn': 1,
                'sec': 'soma'}


    # Evoked distal inputs (population of 1 VecStim)
    for idist in range(ndist):
        skey = 'evdist_' + str(idist+1)
        netParams.popParams['evokedDistal_%s'%(str(idist+1))] = {
            'cellModel': 'VecStim',
            'numCells': 1,
            'xRange': [extLocX, extLocX],
            'yRange': [extLocY, extLocY],
            'zRange': [extLocZ, extLocZ],
            'seed': int(getattr(cfg, 'prng_seedcore_' + skey)),
            'spikePattern': {
                    'type': 'evoked',
                    'start': getattr(cfg, 't_' + skey),
                    'startStd': getattr(cfg, 'sigma_t_' + skey),
                    'numspikes': getattr(cfg, 'numspikes_' + skey),
                    'sync': getattr(cfg, 'sync_evinput')}}


        # Evoked Distal -> L2 Pyr
        synParamsList = [{'synMech': 'L2Pyr_AMPA',
                    'A_weight': getattr(cfg, 'gbar_'+skey+'_L2Pyr_ampa'),
                    'A_delay': 0.1,
                    'lamtha': 3.},

                    {'synMech': 'L2Pyr_NMDA',
                    'A_weight': getattr(cfg, 'gbar_'+skey+'_L2Pyr_nmda'),
                    'A_delay': 0.1,
                    'lamtha': 3.}]

        for synParams in synParamsList:
            netParams.connParams['evokedDistal_%s->L2Pyr'%(str(idist+1))] = { 
                'preConds': {'pop': 'evokedDistal'}, 
                'postConds': {'pop': 'L2Pyr'},
                'synMech': synParams['synMech'],
                'weight': weightDistFunc.format(**synParams),
                'delay': delayDistFunc.format(**synParams),
                'synsPerConn': 3,
                'sec': 'apical_tuft'}

        # Evoked Distal -> L5 Pyr
        synParamsList = [{'synMech': 'L5Pyr_AMPA',
                    'A_weight': getattr(cfg, 'gbar_'+skey+'_L5Pyr_ampa'),
                    'A_delay': 0.1,
                    'lamtha': 3.},

                    {'synMech': 'L5Pyr_NMDA',
                    'A_weight': getattr(cfg, 'gbar_'+skey+'_L5Pyr_nmda'),
                    'A_delay': 0.1,
                    'lamtha': 3.}]

        for synParams in synParamsList:
            netParams.connParams['evokedDistal_%s->L5Pyr'%(str(idist+1))] = { 
                'preConds': {'pop': 'evokedDistal_%s'%(str(idist+1))}, 
                'postConds': {'pop': 'L5Pyr'},
                'synMech': synParams['synMech'],
                'weight': weightDistFunc.format(**synParams),
                'delay': delayDistFunc.format(**synParams),
                'synsPerConn': 3,
                'sec': 'apical_tuft'}

        # Evoked Distal -> L2 Basket
        synParamsList = [{'synMech': 'AMPA',
                    'A_weight': getattr(cfg, 'gbar_'+skey+'_L2Basket_ampa'),
                    'A_delay': 0.1,
                    'lamtha': 3.},

                    {'synMech': 'NMDA',
                    'A_weight': getattr(cfg, 'gbar_'+skey+'_L2Basket_nmda'),
                    'A_delay': 0.1,
                    'lamtha': 3.}]

        for synParams in synParamsList:
            netParams.connParams['evokedDistal_%s->L2Basket'%(str(idist+1))] = { 
                'preConds': {'pop': 'evokedDistal_%s'%(str(idist+1))}, 
                'postConds': {'pop': 'L2Basket'},
                'synMech': synParams['synMech'],
                'weight': weightDistFunc.format(**synParams),
                'delay': delayDistFunc.format(**synParams),
                'synsPerConn': 1,
                'sec': 'soma'}


#------------------------------------------------------------------------------
# Poisson-distributed input sparameters 
#------------------------------------------------------------------------------

if cfg.poissonInputs:
    pass
''''
    # define T_pois as 0 or -1 to reset automatically to tstop
    if p['T_pois'] in (0, -1): p['T_pois'] = tstop

    # Poisson distributed inputs to proximal
    p_unique['extpois'] = {# NEW: setting up AMPA and NMDA for Poisson inputs; why delays differ?
        'stim': 'poisson',
        'L2_basket': (p['L2Basket_Pois_A_weight_ampa'],p['L2Basket_Pois_A_weight_nmda'],1.,p['L2Basket_Pois_lamtha']),
        'L2_pyramidal': (p['L2Pyr_Pois_A_weight_ampa'],p['L2Pyr_Pois_A_weight_nmda'], 0.1,p['L2Pyr_Pois_lamtha']),
        'L5_basket': (p['L5Basket_Pois_A_weight_ampa'],p['L5Basket_Pois_A_weight_nmda'],1.,p['L5Basket_Pois_lamtha']),
        'L5_pyramidal': (p['L5Pyr_Pois_A_weight_ampa'],p['L5Pyr_Pois_A_weight_nmda'],1.,p['L5Pyr_Pois_lamtha']),
        'lamtha_space': 100.,
        'prng_seedcore': int(p['prng_seedcore_extpois']),
        't_interval': (p['t0_pois'], p['T_pois']),
        'loc': 'proximal',
        'threshold': p['threshold']
    }

- - - - - - - -

    def parreceive_ext (self, type, gid, gid_dict, pos_dict, p_ext):
        if type.startswith(('evprox', 'evdist')):
            if self.celltype in p_ext.keys():
                gid_ev = gid + gid_dict[type][0]

                # separate dictionaries for ampa and nmda evoked inputs
                nc_dict_ampa = {
                    'pos_src': pos_dict[type][gid],
                    'A_weight': p_ext[self.celltype][0], # index 0 for ampa weight
                    'A_delay': p_ext[self.celltype][2], # index 2 for delay
                    'lamtha': p_ext['lamtha_space'],
                    'threshold': p_ext['threshold'],
                    'type_src': type
                }

                nc_dict_nmda = {
                    'pos_src': pos_dict[type][gid],
                    'A_weight': p_ext[self.celltype][1], # index 1 for nmda weight
                    'A_delay': p_ext[self.celltype][2], # index 2 for delay
                    'lamtha': p_ext['lamtha_space'],
                    'threshold': p_ext['threshold'],
                    'type_src': type
                }

                if p_ext['loc'] is 'proximal':
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_ampa, self.basal2_ampa))
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_ampa, self.basal3_ampa))
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_ampa, self.apicaloblique_ampa))

                    # NEW: note that default/original is 0 nmda weight for these proximal dends
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_nmda, self.basal2_nmda))
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_nmda, self.basal3_nmda))
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_nmda, self.apicaloblique_nmda))

                elif p_ext['loc'] is 'distal':
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_ampa, self.apicaltuft_ampa))
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_nmda, self.apicaltuft_nmda))


'''

#------------------------------------------------------------------------------
# Gaussian-distributed inputs parameters 
#------------------------------------------------------------------------------

if cfg.gaussInputs:
    pass