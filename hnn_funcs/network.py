"""
network.py 

Network-related functions in NetPyNE-based version of HNN

Contributors: salvadordura@gmail.com
"""

from neuron import h
from netpyne import sim


def create_network(cfg_params, net_params, createNEURONObj=True):

    if createNEURONObj:
        cfg_params.createNEURONObj = True
        load_custom_mechanisms(cfg_params.model_folder)
    else:
        cfg_params.createNEURONObj = False

    sim.initialize(simConfig=cfg_params, netParams=net_params)  
    sim.net.createPops()
    sim.net.createCells()
    sim.net.addStims()
    sim.gatherData()

    return sim.net


def _is_loaded_mechanisms():
    # copied from:
    # https://www.neuron.yale.edu/neuron/static/py_doc/modelspec/programmatic/mechtype.html
    mt = h.MechanismType(0)
    mname = h.ref('')
    mnames = list()
    for i in range(mt.count()):
        mt.select(i)
        mt.selected(mname)
        mnames.append(mname[0])

    # note this check only works for the original hnn model
    # need to generalize for any model
    
    if 'hh2' not in mnames:  
        return False
    else:
        return True


def load_custom_mechanisms(folder=''):
    import platform
    import os.path as op

    root = op.dirname(__file__) + '/'

    if _is_loaded_mechanisms():
        return

    if platform.system() == 'Windows':
        mech_fname = op.join(root+folder, 'mod', 'nrnmech.dll')
    else:
        mech_fname = op.join(root+folder, 'mod', 'x86_64',
                             '.libs', 'libnrnmech.so')
    if not op.exists(mech_fname):
        raise FileNotFoundError(f'The file {mech_fname} could not be found')

    h.nrn_load_dll(mech_fname)
    print('Loading custom mechanism files from %s' % mech_fname)
    if not _is_loaded_mechanisms():
        raise ValueError('The custom mechanisms could not be loaded')



def simulate_trials(cfg_params, net_params, n_trials):

    from netpyne.batch import Batch

    model_folder = cfg_params.model_folder

    # create netpyne Batch object
    seeds = range(n_trials)

    params = {'prng_seedcore_input_prox': list(seeds),
              'prng_seedcore_input_dist': list(seeds),
              'prng_seedcore_extpois': list(seeds),
              'prng_seedcore_extgauss': list(seeds)}

    groupedParams = {'prng_seedcore_input_prox', 'prng_seedcore_input_dist', 'prng_seedcore_extpois', 'prng_seedcore_extgauss'}

    b = Batch(params=params, 
             groupedParams=groupedParams,
             cfgFile=model_folder+'/cfg.py', 
             netParamsFile=model_folder+'/netParams.py', 
             cfg=None)
             
    b.batchLabel = 'trials'
    b.saveFolder = model_folder+'/data/'+b.batchLabel
    b.method = 'grid'
    b.runCfg = {'type': 'mpi_direct', 
                'script': model_folder+'/init.py',
                'cores': 1, 
                'skip': False}

    b.run() # run batch

    # load data
    
    # return data



