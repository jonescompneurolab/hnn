# netParams.py - High-level specifications for network model using NetPyNE
from netpyne import specs

try:
  from __main__ import cfg  # import SimConfig object with params from parent module
except:
  from cfg import cfg  # if no simConfig in parent module, import directly from cfg module

###############################################################################
#
# NETWORK PARAMETERS
#
###############################################################################

netParams = specs.NetParams()   # object of class NetParams to store the network parameters

###############################################################################
# Cell parameters
###############################################################################

# L2Pyr params
cellRule = netParams.importCellParams(label='L2Pyr',conds={'cellType':'L2Pyr','cellModel':'HH_reduced'},
                                      fileName='L2_pyramidal.py',cellName='L2Pyr')

cellRule['secLists']['alldend'] = []
cellRule['secLists']['apicdend'] = []
cellRule['secLists']['basaldend'] = []


# # L2Bas params
# cellRule = netParams.importCellParams(label='L2Bas',conds={'cellType':'L2Bas','cellModel':'HH_simple'},
#                                       fileName='L2_basket.py',cellName='L2Basket')



# # L5Pyr params
# cellRule = netParams.importCellParams(label='L5Pyr',conds={'cellType':'L5Pyr','cellModel':'HH_reduced'},
#                                       fileName='L5_pyramidal.py',cellName='L5Pyr')


# # L5Bas params
# cellRule = netParams.importCellParams(label='L5Bas',conds={'cellType':'L5Bas','cellModel':'HH_simple'},
#                                       fileName='L5_basket.py',cellName='L5Basket')


"""
# PT cell params (6-comp)
cellRule = netParams.importCellParams(label='PT_6comp', conds={'cellType': 'PT', 'cellModel': 'HH_reduced'},
  fileName='cells/SPI6.py', cellName='SPI6')

cellRule['secLists']['alldend'] = ['Bdend', 'Adend1', 'Adend2', 'Adend3']  # define section lists
cellRule['secLists']['apicdend'] = ['Adend1', 'Adend2', 'Adend3']

for secName,sec in cellRule['secs'].iteritems(): 
	sec['vinit'] = -75.0413649414  # set vinit for all secs
	if secName in cellRule['secLists']['alldend']:  
		sec['mechs']['nax']['gbar'] = cfg.dendNa  # set dend Na gmax for all dends
"""

###############################################################################
# Population parameters
###############################################################################
#netParams.popParams['PT5B'] =	{'cellModel': 'HH_reduced', 'cellType': 'PT', 'numCells': 1}

num = {
  'E': 100,
  'I': 35
}

p = 1.0 

netParams.popParams['L2Bas'] = {'cellModel': 'HH_simple', 'cellType': 'L2Bas', 'numCells': int(p*num['E'])}
netParams.popParams['L2Pyr'] = {'cellModel': 'HH_reduced', 'cellType': 'L2Pyr', 'numCells': int(p*num['I'])}
netParams.popParams['L5Bas'] = {'cellModel': 'HH_simple', 'cellType': 'L5Bas', 'numCells': int(p*num['E'])}
netParams.popParams['L5Pyr'] = {'cellModel': 'HH_reduced', 'cellType': 'L5Pyr', 'numCells': int(p*num['I'])}



###############################################################################
# Synaptic mechanism parameters
###############################################################################
# netParams.synMechParams['NMDA'] = {'mod': 'MyExp2SynNMDABB', 'tau1NMDA': cfg.tau1NMDA, 'tau2NMDA': 150, 'e': 0}

#------------------------------------------------------------------------------
# Synaptic mechanism parameters
#------------------------------------------------------------------------------
netParams.synMechParams['NMDA'] = {'mod': 'NMDA'} #, 'tau1NMDA': 15, 'tau2NMDA': 150, 'e': 0}
netParams.synMechParams['AMPA'] = {'mod':'AMPA'}#, 'tau1': 0.05, 'tau2': 5.3, 'e': 0}
netParams.synMechParams['GABAA'] = {'mod':'GABAA'}#, 'tau1': 0.07, 'tau2': 18.2, 'e': -80}

ESynMech = ['AMPA','NMDA']



"""
###############################################################################
# Current inputs (IClamp)
###############################################################################
if cfg.addIClamp:	
 	for iclabel in [k for k in dir(cfg) if k.startswith('IClamp')]:
 		ic = getattr(cfg, iclabel, None)  # get dict with params

		# add stim source
		netParams.stimSourceParams[iclabel] = {'type': 'IClamp', 'delay': ic['start'], 'dur': ic['dur'], 'amp': ic['amp']}
		
		# connect stim source to target
		netParams.stimTargetParams[iclabel+'_'+ic['pop']] = \
			{'source': iclabel, 'conds': {'pop': ic['pop']}, 'sec': ic['sec'], 'loc': ic['loc']}


###############################################################################
# NetStim inputs
###############################################################################
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

