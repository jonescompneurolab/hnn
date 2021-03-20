# paramrw.py - routines for reading the param files
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: removed dependence on cartesian, updated for python3)
# last major: (SL: cleanup of self.p_all)

import os
import numpy as np


def get_output_dir():
    """Return the base directory for storing output files"""

    try:
        base_dir = os.environ["SYSTEM_USER_DIR"]
    except KeyError:
        base_dir = os.path.expanduser('~')

    return os.path.join(base_dir, 'hnn_out')


def get_fname(sim_dir, key, trial=None):
    """Build the file names using the old HNN scheme

    Parameters
    ----------
    sim_dir : str
        The base data directory where simulation result files are stored
    key : str
        A string describing the type of file (HNN specific)
    trial : int | None
        Trial number for which to generate files (separate files per trial).
        If None is given, then will use filename with trial suffix

    Returns
    ----------
    fname : str
        A string with the correct filename
    """

    datatypes = {'rawspk': ('spk', '.txt'),
                 'rawdpl': ('rawdpl', '.txt'),
                 'normdpl': ('dpl', '.txt'),
                 'rawcurrent': ('i', '.txt'),
                 'rawspec': ('rawspec', '.npz'),
                 'rawspeccurrent': ('speci', '.npz'),
                 'avgdpl': ('dplavg', '.txt'),
                 'avgspec': ('specavg', '.npz'),
                 'figavgdpl': ('dplavg', '.png'),
                 'figavgspec': ('specavg', '.png'),
                 'figdpl': ('dpl', '.png'),
                 'figspec': ('rawspec', '.png'),
                 'figspk': ('spk', '.png'),
                 'param': ('param', '.txt'),
                 'vsoma': ('vsoma', '.pkl')}

    if trial is None or key == 'param':
        # param file currently identical for all trials
        fname = os.path.join(sim_dir, datatypes[key][0] + datatypes[key][1])
    else:
        fname = os.path.join(sim_dir, datatypes[key][0] + '_' + str(trial) +
                             datatypes[key][1])

    return fname


def get_inputs(params):
    """ get a dictionary of input types used in simulation
        with distal/proximal specificity for evoked,ongoing inputs
    """

    dinty = {'evoked': usingEvokedInputs(params),
             'ongoing': usingOngoingInputs(params),
             'tonic': usingTonicInputs(params),
             'pois': usingPoissonInputs(params),
             'evdist': usingEvokedInputs(params, lsuffty=['_evdist_']),
             'evprox': usingEvokedInputs(params, lsuffty=['_evprox_']),
             'dist': usingOngoingInputs(params, lty=['_dist']),
             'prox': usingOngoingInputs(params, lty=['_prox'])}

    return dinty

# Cleans input files


def clean_lines(file):
    with open(file) as f_in:
        lines = (line.rstrip() for line in f_in)
        lines = [line for line in lines if line]
    return lines

# check if using ongoing inputs


def usingOngoingInputs(params, lty=['_prox', '_dist']):
    if params is None:
        return False

    try:
        tstop = float(params['tstop'])
    except KeyError:
        return False

    dpref = {'_prox': 'input_prox_A_', '_dist': 'input_dist_A_'}
    for postfix in lty:
        if float(params['t0_input'+postfix]) <= tstop and \
                float(params['tstop_input'+postfix]) >= float(params['t0_input' + postfix]) and float(params['f_input'+postfix]) > 0.:  # noqa: E501
            for k in ['weight_L2Pyr_ampa', 'weight_L2Pyr_nmda',
                      'weight_L5Pyr_ampa', 'weight_L5Pyr_nmda',
                      'weight_inh_ampa', 'weight_inh_nmda']:
                if float(params[dpref[postfix]+k]) > 0.:
                    # print('usingOngoingInputs:',params[dpref[postfix]+k])
                    return True

    return False

# return number of evoked inputs (proximal, distal)
# using dictionary d (or if d is a string, first load the dictionary from
#                     filename d)


def countEvokedInputs(params):
    nprox = ndist = 0
    if params is not None:
        for k, v in params.items():
            if k.startswith('t_'):
                if k.count('evprox') > 0:
                    nprox += 1
                elif k.count('evdist') > 0:
                    ndist += 1
    return nprox, ndist

# check if using any evoked inputs


def usingEvokedInputs(params, lsuffty=['_evprox_', '_evdist_']):
    nprox, ndist = countEvokedInputs(params)
    if nprox == 0 and ndist == 0:
        return False

    try:
        tstop = float(params['tstop'])
    except KeyError:
        return False

    lsuff = []
    if '_evprox_' in lsuffty:
        for i in range(1, nprox+1, 1):
            lsuff.append('_evprox_'+str(i))
    if '_evdist_' in lsuffty:
        for i in range(1, ndist+1, 1):
            lsuff.append('_evdist_'+str(i))
    for suff in lsuff:
        k = 't' + suff
        if k not in params:
            continue
        if float(params[k]) > tstop:
            continue
        k = 'gbar' + suff
        for k1 in params.keys():
            if k1.startswith(k):
                if float(params[k1]) > 0.0:
                    return True
    return False

# check if using any poisson inputs


def usingPoissonInputs(params):
    if params is None:
        return False

    try:
        tstop = float(params['tstop'])

        if 't0_pois' in params and 'T_pois' in params:
            t0_pois = float(params['t0_pois'])
            if t0_pois > tstop:
                return False
            T_pois = float(params['T_pois'])
            if t0_pois > T_pois and T_pois != -1.0:
                return False
    except KeyError:
        return False

    for cty in ['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket']:
        for sy in ['ampa', 'nmda']:
            k = cty+'_Pois_A_weight_'+sy
            if k in params:
                if float(params[k]) != 0.0:
                    return True

    return False

# check if using any tonic (IClamp) inputs


def usingTonicInputs(d):
    if d is None:
        return False

    tstop = float(d['tstop'])
    for cty in ['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket']:
        k = 'Itonic_A_' + cty + '_soma'
        if k in d:
            amp = float(d[k])
            if amp != 0.0:
                print(k, 'amp != 0.0', amp)
                k = 'Itonic_t0_' + cty
                t0, t1 = 0.0, -1.0
                if k in d:
                    t0 = float(d[k])
                k = 'Itonic_T_' + cty
                if k in d:
                    t1 = float(d[k])
                if t0 > tstop:
                    continue
                # print('t0:',t0,'t1:',t1)
                if t0 < t1 or t1 == -1.0:
                    return True
    return False


def read_gids_param(fparam):
    lines = clean_lines(fparam)
    gid_dict = {}
    for line in lines:
        if line.startswith('#'):
            continue
        keystring, val = line.split(": ")
        key = keystring.strip()
        if val[0] == '[':
            val_range = val[1:-1].split(', ')
            if len(val_range) == 2:
                ind_start = int(val_range[0])
                ind_end = int(val_range[1]) + 1
                gid_dict[key] = np.arange(ind_start, ind_end)
            else:
                gid_dict[key] = np.array([])

    return gid_dict


def legacy_param_str_to_dict(param_str):
    boolean_params = ['sync_evinput', 'record_vsoma', 'save_spec_data',
                      'save_figs']

    param_dict = {}
    for line in param_str.splitlines():
        keystring, val = line.split(': ')
        key = keystring.strip()
        if key == 'expmt_groups':
            continue
        elif key == 'sim_prefix' or key == 'spec_cmap':
            param_dict[key] = val
        elif key.startswith('N_') or key.startswith('numspikes_') or \
                key.startswith('events_per_cycle_') or \
                key.startswith('repeats_') or \
                key.startswith('prng_seedcore_'):
            param_dict[key] = int(val)
        elif key in boolean_params:
            param_dict[key] = int(val)
        else:
            param_dict[key] = float(val)

    return param_dict


# write the params to a filename
def write_legacy_paramf(fparam, p):
    """ now sorting
    """

    p_keys = [key for key, val in p.items()]
    p_sorted = [(key, p[key]) for key in p_keys]
    with open(fparam, 'w') as f:
        pstring = '%26s: '
        # do the params in p_sorted
        for param in p_sorted:
            key, val = param
            f.write(pstring % key)
            if key.startswith('N_'):
                f.write('%i\n' % val)
            else:
                f.write(str(val)+'\n')


def write_gids_param(fparam, gid_list):
    with open(fparam, 'w') as f:
        pstring = '%26s: '
        # write the gid info
        for key in gid_list.keys():
            f.write(pstring % key)
            if len(gid_list[key]):
                f.write('[%4i, %4i] ' % (gid_list[key][0], gid_list[key][-1]))
            else:
                f.write('[]')
            f.write('\n')
