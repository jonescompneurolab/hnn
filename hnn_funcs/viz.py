"""
params.py 

Useful functions for the NetPyNE-based implementation of HNN

Contributors: salvadordura@gmail.com
"""

import os.path as op


def read_params(params_fname):
    """Read param values from a file (.json or .param).

    Parameters
    ----------
    params_fname : str
        Full path to the file (.param)

    Returns
    -------
    params : an instance of Params
        Params containing paramter values from file
    """

    split_fname = op.splitext(params_fname)
    ext = split_fname[1]

    if ext == '.json':
        params_dict = _read_json(params_fname)
    elif ext == '.param':
        params_dict = _read_legacy_params(params_fname)
    else:
        raise ValueError('Unrecognized extension, expected one of' +
                         ' .json, .param. Got %s' % ext)

    if len(params_dict) == 0:
        raise ValueError("Failed to read parameters from file: %s" %
                         op.normpath(params_fname))

    params = Params(params_dict)


    # Import simConfig and set parameters from file
    cfg, netParams = sim.readCmdLineArgs()
    cfg = setCfgFromFile(cfgFile, cfg)#, exclude = ['prng_seedcore_input_prox', 'prng_seedcore_input_dist']) # exclude parameters modified in batch.py

    from netParams import netParams


    return params

#network file
def create_network():
    sim.initialize(simConfig=cfg, netParams=netParams)  
    sim.net.createPops()
    sim.net.createCells()
    sim.gatherData()

# viz file
def plot_cells():
    if not gatherData: 
        sim.gatherData()
    sim.analysis.plotShape(includePost=['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket'])


# parallel_backends / simulation file
def simulate_trials:
    dpls = []
    for trial in range(n_trials):
        print('Trial %d ...' % (trial))
        cfg.prng_seedcore_input_prox += 1
        sim.createSimulateAnalyze(simConfig=cfg, netParams=netParams)  
        dpls.append(sim.allSimData['dipole'])

# utils 
# Function to set cfg params from .param file
def setCfgFromFile (fn, cfg, exclude = []):
    d = {}
    with open(fn,'r') as fp:
        ln = fp.readlines()
        for l in ln:
            s = l.strip()
            if s.startswith('#'): continue
            sp = s.split(':')
            sp[1] = sp[1].strip()
            if len(sp[1]) > 0:
                if '.' in sp[1] or 'e' in sp[1]:
                    try:
                        value = float(sp[1])
                    except:
                        value = str(sp[1])
                else:
                    try:
                        value = int(sp[1])
                    except:
                        value = str(sp[1])
                d[sp[0].strip()] = value
    for k, v in d.items():
        if k not in exclude:
            setattr(cfg, k, v)
        if 'duration' not in exclude:
            cfg.duration = cfg.tstop
    return cfg
