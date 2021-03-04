"""
network.py

Network-related functions in NetPyNE-based version of HNN

Contributors: salvadordura@gmail.com
"""
import json
import pickle
import numpy as np
from itertools import product
import os

from neuron import h
from netpyne import sim, specs

from .npencoder import NumpyEncoder


def create_network(cfg_params, createNEURONObj=True, addConns=False, xzScaling=100):

    # option to create NEURON objects or just
    if createNEURONObj:
        cfg_params.createNEURONObj = True
        load_custom_mechanisms(cfg_params.model_folder)
    else:
        cfg_params.createNEURONObj = False

    # ensure cell sections are stored so can be plotted
    saveCellSecs_orig = cfg_params.saveCellSecs
    cfg_params.saveCellSecs = True

    # param to fix hnn model horizontal spacing of 1um (hack for visualization)
    xzScaling_orig = cfg_params.xzScaling
    cfg_params.xzScaling = xzScaling

    # create network
    from netParams import netParams as net_params
    sim.initialize(simConfig=cfg_params, netParams=net_params)
    sim.net.createPops()
    sim.net.createCells()
    if addConns:
        sim.cfg.saveCellConns = True
        sim.net.connectCells()
    sim.gatherData()

    # restore original param values
    cfg_params.xzScaling = xzScaling_orig
    cfg_params.saveCellSecs = saveCellSecs_orig


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
        mech_fname = op.join(root+folder, 'nrnmech.dll')
    else:
        mech_fname = op.join(root+folder, 'x86_64',
                             '.libs', 'libnrnmech.so')
    if not op.exists(mech_fname):
        raise FileNotFoundError(f'The file {mech_fname} could not be found')

    h.nrn_load_dll(mech_fname)
    print('Loading custom mechanism files from %s' % mech_fname)
    if not _is_loaded_mechanisms():
        raise ValueError('The custom mechanisms could not be loaded')



def simulate_trials(cfg_params, n_trials, n_cores=1, postproc=True, only_read=False):

    from netpyne import sim
    from netpyne.batch import Batch

    try:
        sim.clearAll()
    except:
        pass

    model_folder = cfg_params.model_folder

    # setup and run netpyne batch with different seeds
    seeds = range(n_trials)

    params = specs.ODict()
    params[('hnn_params','prng_seedcore')] = list(seeds)

    b = Batch(params=params,
             cfgFile=model_folder+'/cfg.py',
             netParamsFile=model_folder+'/netParams.py',
             cfg=cfg_params)

    b.batchLabel = 'trials'
    b.saveFolder = model_folder+'/data/'+b.batchLabel
    b.method = 'grid'
    b.runCfg = {'type': 'mpi_direct',
                'script': model_folder+'/init.py',
                'cores': n_cores,
                'skip': False}

    if not only_read:
        b.run()

    # read data from batch output files
    data = read_trials_data(model_folder+'/data/', b.batchLabel, n_trials)

    # postprocess dipole data
    if postproc:
        from .dipole import Dipole

        for i, trial_data in enumerate(data):

            dpl_data = [np.array(trial_data['simData']['dipole']['L2'])+np.array(trial_data['simData']['dipole']['L5']),
                        np.array(trial_data['simData']['dipole']['L2']),
                        np.array(trial_data['simData']['dipole']['L5'])]
            dpl_trial = Dipole(np.array(trial_data['simData']['t']), np.array(dpl_data).T)
            dpl_trial.post_proc(cfg_params.hnn_params['N_pyr_x'],
                                cfg_params.hnn_params['N_pyr_y'],
                                cfg_params.hnn_params['dipole_smooth_win'] / cfg_params.dt,
                                cfg_params.hnn_params['dipole_scalefctr'])
            trial_data['dpl'] = dpl_trial

    return data



def explore_params(cfg_params, params_explore, n_cores=1, postproc=True, only_read=False):

    from netpyne import sim
    from netpyne.batch import Batch

    try:
        sim.clearAll()
    except:
        pass

    model_folder = cfg_params.model_folder

    # setup and run netpyne batch with different seeds

    params = specs.ODict(params_explore)

    b = Batch(params=params,
             cfgFile=model_folder+'/cfg.py',
             netParamsFile=model_folder+'/netParams.py',
             cfg=cfg_params)

    b.batchLabel = 'explore'
    b.saveFolder = model_folder+'/data/'+b.batchLabel
    b.method = 'grid'
    b.runCfg = {'type': 'mpi_direct',
                'script': model_folder+'/init.py',
                'cores': n_cores,
                'skip': False}

    if not only_read:
        b.run()

    # read data from batch output files
    params, data = read_batch_data(model_folder+'/data/', b.batchLabel)

    # postprocess dipole data
    '''
    if postproc:
        from .dipole import Dipole

        for i, trial_data in enumerate(data):
            trial_data['simData']['dipole']['L2'][0] = 0
            trial_data['simData']['dipole']['L5'][0] = 0

            dpl_data = [np.array(trial_data['simData']['dipole']['L2'])+np.array(trial_data['simData']['dipole']['L5']),
                        np.array(trial_data['simData']['dipole']['L2']),
                        np.array(trial_data['simData']['dipole']['L5'])]
            dpl_trial = Dipole(np.array(trial_data['simData']['t']), np.array(dpl_data).T)
            dpl_trial.post_proc(cfg_params.hnn_params['N_pyr_x'],
                                cfg_params.hnn_params['N_pyr_y'],
                                cfg_params.hnn_params['dipole_smooth_win'] / cfg_params.dt,
                                cfg_params.hnn_params['dipole_scalefctr'])
            dpl_trial.data['L2'][0] = dpl_trial.data['L5'][0] = dpl_trial.data['agg'][0] = 0
            trial_data['dpl'] = dpl_trial
    '''
    return data



def read_trials_data(dataFolder, batchLabel, n_trials):

    from netpyne import specs

    data = []

    # read vars from all files - store in dict
    for i in range(n_trials):
        # read output file
        simLabel = batchLabel+'_'+str(i)

        outFile = dataFolder+'/'+batchLabel+'/'+simLabel
        if os.path.isfile(outFile+'.json'):
            outFile = outFile + '.json'
            with open(outFile, 'rb') as fileObj:
                output = json.load(fileObj, object_pairs_hook=specs.OrderedDict)
        elif os.path.isfile(outFile+'.pkl'):
            outFile = outFile + '.pkl'
            with open(outFile, 'rb') as fileObj:
                output = pickle.load(fileObj)

        try:
            # save output file in data dict
            trial_data = {}

            for key in output.keys():
                if isinstance(key, tuple):
                    container = output
                    for ikey in range(len(key)-1):
                        container = container[key[ikey]]
                    trial_data[key[1]] = container[key[-1]]

                elif isinstance(key, str):
                    trial_data[key] = output[key]

            data.append(trial_data)
        except:
            pass

    return data


def mean_rates(trials_data, mean_type='all'):

    if mean_type == 'all':
        mean_rates_values = np.mean([list(trial_data['simData']['popRates'].values()) for trial_data in trials_data], 0)
        mean_rates = dict(zip(trials_data[0]['simData']['popRates'].keys(), mean_rates_values))

    elif mean_type == 'trial':
        mean_rates = [trial_data['simData']['popRates'] for trial_data in trials_data]

    return mean_rates



def read_batch_data(dataFolder, batchLabel, loadAll=False, saveAll=True, vars=None, maxCombs=None, listCombs=None):

    from netpyne import specs

    # load from previously saved file with all data
    if loadAll:
        print('\nLoading single file with all data...')
        filename = '%s/%s/%s_allData.json' % (dataFolder, batchLabel, batchLabel)
        with open(filename, 'r') as fileObj:
            dataLoad = json.load(fileObj, object_pairs_hook=specs.OrderedDict)
        params = dataLoad['params']
        data = dataLoad['data']
        return params, data

    if isinstance(listCombs, str):
        filename = str(listCombs)
        with open(filename, 'r') as fileObj:
            dataLoad = json.load(fileObj)
        listCombs = dataLoad['paramsMatch']

    # read the batch file and cfg
    batchFile = '%s/%s/%s_batch.json' % (dataFolder, batchLabel, batchLabel)
    with open(batchFile, 'r') as fileObj:
        b = json.load(fileObj)['batch']

    # read params labels and ranges
    params = b['params']

    # reorder so grouped params come first
    preorder = [p for p in params if 'group' in p and p['group']]
    for p in params:
        if p not in preorder: preorder.append(p)
    params = preorder

    # read vars from all files - store in dict
    if b['method'] == 'grid':
        labelList, valuesList = zip(*[(p['label'], p['values']) for p in params])
        valueCombinations = product(*(valuesList))
        indexCombinations = product(*[range(len(x)) for x in valuesList])
        data = {}
        print('Reading data...')
        missing = 0
        for i,(iComb, pComb) in enumerate(zip(indexCombinations, valueCombinations)):
            if (not maxCombs or i<= maxCombs) and (not listCombs or list(pComb) in listCombs):
                print(i, iComb)
                # read output file
                iCombStr = ''.join([''.join('_'+str(i)) for i in iComb])
                simLabel = b['batchLabel']+iCombStr
                outFile = dataFolder+'/'+batchLabel+'/'+simLabel
                if os.path.isfile(outFile+'.json'):
                    outFile = outFile + '.json'
                    with open(outFile, 'rb') as fileObj:
                        output = json.load(fileObj, object_pairs_hook=specs.OrderedDict)
                elif os.path.isfile(outFile+'.pkl'):
                    outFile = outFile + '.pkl'
                    with open(outFile, 'rb') as fileObj:
                        output = pickle.load(fileObj)
                else:
                    print('... file missing')
                    missing = missing + 1
                    output = {}
                    continue

                try:
                    # save output file in data dict
                    data[iCombStr] = {}
                    data[iCombStr]['paramValues'] = pComb  # store param values
                    if not vars: vars = output.keys()

                    for key in vars:
                        if isinstance(key, tuple):
                            container = output
                            for ikey in range(len(key)-1):
                                container = container[key[ikey]]
                            data[iCombStr][key[1]] = container[key[-1]]

                        elif isinstance(key, str):
                            data[iCombStr][key] = output[key]
                except:
                    print('... file missing')
                    missing = missing + 1
                    output = {}

                    #import IPython; IPython.embed()

            else:
                missing = missing + 1

        print('%d files missing' % (missing))

        # save
        if saveAll:
            print('Saving to single file with all data')
            filename = '%s/%s/%s_allData.json' % (dataFolder, batchLabel, batchLabel)
            dataSave = {'params': params, 'data': data}
            with open(filename, 'w') as fileObj:
                json.dump(dataSave, fileObj, cls=NumpyEncoder)

        return params, data
