# netParams.py - High-level specifications for network model using NetPyNE

from netpyne import specs

try:
  from __main__ import cfg  # import SimConfig object with params from parent module
except:
  from cfg import cfg  # if no simConfig in parent module, import directly from cfg module

# ----------------------------------------------------------------------------
#
# NETWORK PARAMETERS
#
# ----------------------------------------------------------------------------

netParams = specs.NetParams()   # object of class NetParams to store the network parameters

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
netParams.importCellParams(label='L5Basket_rule',conds={'cellType':'L5Basket'}, fileName='L5_basket.py',cellName='L5Basket')


# remove cell name from section name
cellLabels = ['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket']
for cellLabel in cellLabels:
	for secName in list(netParams.cellParams[cellLabel+'_rule']['secs'].keys()):
		netParams.renameCellParamsSec(cellLabel+'_rule', secName, secName.replace(cellLabel+'_', '')) 


# ----------------------------------------------------------------------------
# Population parameters
# ----------------------------------------------------------------------------

numCellsE = int(cfg.netScale * cfg.numCells['E'])
numCellsI = int(cfg.netScale * cfg.numCells['I'])

netParams.popParams['L2Pyr'] = {'cellType': 'L2Pyr', 	'cellModel': 'HH_reduced', 'numCells': numCellsE}
netParams.popParams['L2Bas'] = {'cellType': 'L2Basket', 'cellModel': 'HH_simple', 'numCells': numCellsI}
netParams.popParams['L5Pyr'] = {'cellType': 'L5Pyr', 	'cellModel': 'HH_reduced',  'numCells': numCellsE}
netParams.popParams['L5Bas'] = {'cellType': 'L5Basket', 'cellModel': 'HH_simple',  'numCells': numCellsI}


#------------------------------------------------------------------------------
# Synaptic mechanism parameters
#------------------------------------------------------------------------------
netParams.synMechParams['AMPA'] = {'mod':'Exp2Syn', 'tau1': 0.5, 'tau2': 5.0, 'e': 0}
netParams.synMechParams['NMDA'] = {'mod': 'Exp2Syn', 'tau1': 1, 'tau2': 20, 'e': 0}
netParams.synMechParams['GABAA'] = {'mod':'Exp2Syn', 'tau1': 0.5, 'tau2': 5, 'e': -80}
netParams.synMechParams['GABAB'] = {'mod':'Exp2Syn', 'tau1': 1, 'tau2': 20, 'e': -80}


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

