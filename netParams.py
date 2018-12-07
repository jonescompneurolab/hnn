# netParams.py - High-level specifications for network model using NetPyNE

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

netParams = specs.NetParams()   # object of class NetParams to store the network parameters
#------------------------------------------------------------------------------
# General network parameters
#------------------------------------------------------------------------------
netParams.sizeX = cfg.N_pyr_x * cfg.gridSpacing # x-dimension (horizontal length) size in um
netParams.sizeY = cfg.sizeY # y-dimension (vertical height or cortical depth) size in um
netParams.sizeZ = cfg.N_pyr_y * cfg.gridSpacing # z-dimension (horizontal depth) size in um
netParams.shape = 'cuboid' 


# ----------------------------------------------------------------------------
# Cell parameters
# ----------------------------------------------------------------------------

# L2Pyr params
netParams.importCellParams(label='L2Pyr_rule', conds={'cellType': 'L2Pyr'}, fileName='L2_pyramidal.py', cellName='L2Pyr')

# L2Bas params
netParams.importCellParams(label='L2Basket_rule', conds={'cellType': 'L2Basket'}, fileName='L2_basket.py', cellName='L2Basket')

# L5Pyr params
netParams.importCellParams(label='L5Pyr_rule', conds={'cellType':'L5Pyr'}, fileName='L5_pyramidal.py', cellName='L5Pyr')

# L5Bas params
netParams.importCellParams(label='L5Basket_rule', conds={'cellType':'L5Basket'}, fileName='L5_basket.py',cellName='L5Basket')

# simplify section names and add section lists
cellLabels = ['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket']
secListLabels = ['basal', 'apical']

for cellLabel in cellLabels:
    cellRule = cellLabel+'_rule'

    # remove cell name from section name
    secs = list(netParams.cellParams[cellRule]['secs'].keys())
    for secName in secs:
        netParams.renameCellParamsSec(cellRule, secName, secName.replace(cellLabel+'_', '')) 

    # create basal and apical sec lists (new list of secs with shorter names)
    secs = list(netParams.cellParams[cellRule]['secs'].keys())
    for secListLabel in secListLabels:
        netParams.cellParams[cellRule]['secLists'][secListLabel] = [sec for sec in secs if secListLabel in sec]


# ----------------------------------------------------------------------------
# Population parameters
# ----------------------------------------------------------------------------
layers = {'L2': [0.1*cfg.sizeY, 0.15*cfg.sizeY], 'L5': [0.5*cfg.sizeY, 0.55*cfg.sizeY]}

netParams.popParams['L2Pyr'] = {'cellType': 'L2Pyr',    'cellModel': 'HH_reduced', 'yRange': layers['L2'], 'gridSpacing': cfg.gridSpacing} # 'numCells': numCellsE}
netParams.popParams['L2Bas'] = {'cellType': 'L2Basket', 'cellModel': 'HH_simple', 'yRange': layers['L2'], 'gridSpacing': cfg.gridSpacing} # 'numCells': numCellsI}
netParams.popParams['L5Pyr'] = {'cellType': 'L5Pyr',    'cellModel': 'HH_reduced', 'yRange': layers['L5'], 'gridSpacing': cfg.gridSpacing} #  'numCells': numCellsE}
netParams.popParams['L5Bas'] = {'cellType': 'L5Basket', 'cellModel': 'HH_simple', 'yRange': layers['L5'], 'gridSpacing': cfg.gridSpacing} #  'numCells': numCellsI}


#------------------------------------------------------------------------------
# Synaptic mechanism parameters
#------------------------------------------------------------------------------
netParams.synMechParams['AMPA'] = {'mod':'Exp2Syn', 'tau1': 0.5, 'tau2': 5.0, 'e': 0}
netParams.synMechParams['NMDA'] = {'mod': 'Exp2Syn', 'tau1': 1, 'tau2': 20, 'e': 0}
netParams.synMechParams['GABAA'] = {'mod':'Exp2Syn', 'tau1': 0.5, 'tau2': 5, 'e': -80}
netParams.synMechParams['GABAB'] = {'mod':'Exp2Syn', 'tau1': 1, 'tau2': 20, 'e': -80}


#------------------------------------------------------------------------------
# Connectivity parameters
#------------------------------------------------------------------------------

connMetaParams = {}

# L2 Pyr -> L2 Pyr
connMetaParams['L2Pyr->L2Pyr'] = {} 
connMetaParams['L2Pyr->L2Pyr']['AMPA'] = {'A_weight': cfg.gbar_L2Pyr_L2Pyr_ampa, 'A_delay': 1., 'lamtha': 3, 'secs': ['apical_oblique', 'basal_2', 'basal_3']}
connMetaParams['L2Pyr->L2Pyr']['NMDA'] = {'A_weight': cfg.gbar_L2Pyr_L2Pyr_nmda, 'A_delay': 1., 'lamtha': 3, 'secs': ['apical_oblique', 'basal_2', 'basal_3']}

# L2 Pyr -> L2 Pyr
connMetaParams['L2Basket->L2Pyr'] = {} 
connMetaParams['L2Basket->L2Pyr']['AMPA'] = {'A_weight': cfg.gbar_L2Basket_L2Pyr_ampa, 'A_delay': 1., 'lamtha': 50, 'secs': ['soma']}
connMetaParams['L2Basket->L2Pyr']['NMDA'] = {'A_weight': cfg.gbar_L2Basket_L2Pyr_nmda, 'A_delay': 1., 'lamtha': 50, 'secs': ['soma']}


for rule, ruleParams in connMetaParams.items():
    for syn, synParams in ruleParams.items():
        netParams.connParams[rule] = { 
            'preConds': {'cellType': rule.split('->')[0]}, 
            'postConds': {'cellType': rule.split('->')[1]},
            'synMech': syn,
            'weight': '{A_weight} * exp(-(dist_2D**2) / ({lamtha}**2))'.format(**synParams),
            'delay': '{A_weight} / exp(-(dist_2D**2) / ({lamtha}**2))'.format(**synParams),
            'synsPerConn': len(synParams['secs']),
            'sec': synParams['secs']}
                

"""
# ----------------------------------------------------------------------------
# Current inputs (IClamp)
# ----------------------------------------------------------------------------
if cfg.addIClamp:   
    for iclabel in [k for k in dir(cfg) if k.startswith('IClamp')]:
        ic = getattr(cfg, iclabel, None)  # get dict with params

        # add stim source
        netParams.stimSourceParams[iclabel] = {'type': 'IClamp', 'delay': ic['start'], 'dur': ic['dur'], 'amp': ic['amp']}
        
        # connect stim source to target
        netParams.stimTargetParams[iclabel+'_'+ic['pop']] = \
            {'source': iclabel, 'conds': {'pop': ic['pop']}, 'sec': ic['sec'], 'loc': ic['loc']}


# ----------------------------------------------------------------------------
# NetStim inputs
# ----------------------------------------------------------------------------
if cfg.addNetStim:
    for nslabel in [k for k in dir(cfg) if k.startswith('NetStim')]:
        ns = getattr(cfg, nslabel, None)

        # add stim source
        netParams.stimSourceParams[nslabel] = {'type': 'NetStim', 'start': ns['start'], 'interval': ns['interval'], 
                                               'noise': ns['noise'], 'number': ns['number']}

        # connect stim source to target
        netParams.stimTargetParams[nslabel+'_'+ns['pop']] = \
            {'source': nslabel, 'conds': {'pop': ns['pop']}, 'sec': ns['sec'], 'loc': ns['loc'],
             'synMech': ns['synMech'], 'weight': ns['weight'], 'delay': ns['delay']}
"""
