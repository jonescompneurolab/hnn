"""
params.py 

Useful functions for the NetPyNE-based implementation of HNN

Contributors: salvadordura@gmail.com
"""

from netpyne import sim

#network file
def create_network(cfg_params, net_params):

    # dynamically compile mod folder (check if doesn't exist)
    # store folder name in cfg 
    
    #cfg_params.createNEURONObj = False
    sim.initialize(simConfig=cfg_params, netParams=net_params)  
    sim.net.createPops()
    sim.net.createCells()
    sim.gatherData()

    return sim.net

