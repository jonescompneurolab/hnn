"""
params.py 

Useful functions for the NetPyNE-based implementation of HNN

Contributors: salvadordura@gmail.com
"""

import os
import os.path as op
import json
from netpyne import specs, sim


def read_params(model_folder, params_fname):

    """Read param values from a file (.json or .param).

    Parameters
    ----------
    params_fname : str
        Full path to the file (.param)

    Returns
    -------
    cfg_params : an instance of netpyne.specs.SimConfig
        configuration params including hnn-specific params

    net_params : an instance of netpyne.specs.NetParams
        all params required to fully define the network model 

    """

    # Import cfg_params and net_params for target model
    #os.chdir(model_folder)

    import sys
    sys.path.insert(1, model_folder)

    from cfg import cfg as cfg_params
    from netParams import netParams as net_params

    # update cfg_params based on hnn params file
    split_fname = op.splitext(params_fname)
    ext = split_fname[1]

    if ext == '.json':
        cfg_params = _read_json(model_folder+'/'+params_fname, cfg_params)
    elif ext == '.param':
        cfg_params = _read_legacy_params(model_folder+'/'+params_fname, cfg_params) 
    else:
        raise ValueError('Unrecognized extension, expected one of' +
                         ' .json, .param. Got %s' % ext)

    if len(cfg_params.__dict__) == 0:
        raise ValueError("Failed to read parameters from file: %s" %
                         op.normpath(params_fname))

    # save model and params path 
    cfg_params.model_folder = model_folder
    cfg_params.params_fname = params_fname

    return cfg_params, net_params


def _read_json(fname, cfg):
    """Read param values from a .json file and update cfg
    Parameters
    ----------
    fname : str
        Full path to the file (.json)

    Returns
    -------
    params_input : dict
        Dictionary of parameters
    """
    with open(fname) as json_data:
        params_input = json.load(json_data)
    
    cfg.hnn_params = params_input

    return cfg


def _read_legacy_params (params_fname, cfg, exclude = []):
    """Read param values from a .param file and update netpyne SimConfig object  (legacy).
    Parameters
    ----------
    fname : str
        Full path to the file (.param)
    cfg   : an instance of netpyne.specs.SimConfig to update

    Returns
    -------
    cfg : an instance of netpyne.specs.SimConfig
        object of class SimConfig with parameters
    """

    cfg.hnn_params = {}
    d = {}
    with open(params_fname,'r') as fp:
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
            cfg.hnn_params[k] = v
    if 'duration' not in exclude:
        cfg.duration = cfg.hnn_params['tstop']
    return cfg
