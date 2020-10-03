# paramrw.py - routines for reading the param files
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: removed dependence on cartesian, updated for python3)
# last major: (SL: cleanup of self.p_all)

import re
import numpy as np
import itertools as it

from hnn_core import read_params

# Cleans input files
def clean_lines (file):
  with open(file) as f_in:
    lines = (line.rstrip() for line in f_in)
    lines = [line for line in lines if line]
  return lines

def validate_param_file (fn):
    try:
        fp = open(fn, 'r')
    except OSError:
        print("ERROR: could not open/read file")
        raise ValueError

    d = {}
    with fp:
        try:
            ln = fp.readlines()
        except UnicodeDecodeError:
            print("ERROR: bad file format")
            raise ValueError
        for l in ln:
            s = l.strip()
            if s.startswith('#'): continue
            sp = s.split(':')
            if len(sp) > 1:
                d[sp[0].strip()]=str(sp[1]).strip()
    if not 'tstop' in d:
        print("ERROR: parameter file not valid. Could not find 'tstop'")
        raise ValueError

# check if using ongoing inputs
def usingOngoingInputs (params, lty = ['_prox', '_dist']):
  if params is None:
    return False

  try:
    tstop = float(params['tstop'])
  except KeyError:
    return False

  dpref = {'_prox':'input_prox_A_','_dist':'input_dist_A_'}
  try:
    for postfix in lty:
      if float(params['t0_input'+postfix])<= tstop and \
         float(params['tstop_input'+postfix])>=float(params['t0_input'+postfix]) and \
         float(params['f_input'+postfix])>0.:
        for k in ['weight_L2Pyr_ampa','weight_L2Pyr_nmda',\
                  'weight_L5Pyr_ampa','weight_L5Pyr_nmda',\
                  'weight_inh_ampa','weight_inh_nmda']:
          if float(params[dpref[postfix]+k])>0.:
            # print('usingOngoingInputs:',params[dpref[postfix]+k])
            return True
  except: 
    return False
  return False

# return number of evoked inputs (proximal, distal)
# using dictionary d (or if d is a string, first load the dictionary from filename d)
def countEvokedInputs (params):
  nprox = ndist = 0
  if params is not None:
    for k,v in params.items():
      if k.startswith('t_'):
        if k.count('evprox') > 0:
          nprox += 1
        elif k.count('evdist') > 0:
          ndist += 1
  return nprox, ndist

# check if using any evoked inputs 
def usingEvokedInputs (params, lsuffty = ['_evprox_', '_evdist_']):
  nprox,ndist = countEvokedInputs(params)
  if nprox == 0 and ndist == 0:
    return False

  try:
    tstop = float(params['tstop'])
  except KeyError:
    return False

  lsuff = []
  if '_evprox_' in lsuffty:
    for i in range(1,nprox+1,1): lsuff.append('_evprox_'+str(i))
  if '_evdist_' in lsuffty:
    for i in range(1,ndist+1,1): lsuff.append('_evdist_'+str(i))
  for suff in lsuff:
    k = 't' + suff
    if k not in params: continue
    if float(params[k]) > tstop: continue
    k = 'gbar' + suff
    for k1 in params.keys():
      if k1.startswith(k):
        if float(params[k1]) > 0.0: return True
  return False

# check if using any poisson inputs 
def usingPoissonInputs (params):
  if params is None:
    return False

  try:
    tstop = float(params['tstop'])

    if 't0_pois' in params and 'T_pois' in params:
      t0_pois = float(params['t0_pois'])
      if t0_pois > tstop: return False
      T_pois = float(params['T_pois'])
      if t0_pois > T_pois and T_pois != -1.0:
        return False
  except KeyError:
    return False

  for cty in ['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket']:
    for sy in ['ampa','nmda']:
      k = cty+'_Pois_A_weight_'+sy
      if k in params:
        if float(params[k]) != 0.0:
          return True

  return False

# check if using any tonic (IClamp) inputs 
def usingTonicInputs (d):
  if d is None:
    return False

  tstop = float(d['tstop'])
  for cty in ['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket']:
    k = 'Itonic_A_' + cty + '_soma'
    if k in d:
      amp = float(d[k])
      if amp != 0.0:
        print(k,'amp != 0.0',amp)
        k = 'Itonic_t0_' + cty
        t0,t1 = 0.0,-1.0
        if k in d: t0 = float(d[k])
        k = 'Itonic_T_' + cty
        if k in d: t1 = float(d[k])
        if t0 > tstop: continue
        #print('t0:',t0,'t1:',t1)
        if t0 < t1 or t1 == -1.0: return True
  return False

def read_gids_param (fparam):
    lines = clean_lines(fparam)
    gid_dict = {}
    for line in lines:
        if line.startswith('#'): continue
        keystring, val = line.split(": ")
        key = keystring.strip()
        if val[0] is '[':
            val_range = val[1:-1].split(', ')
            if len(val_range) is 2:
                ind_start = int(val_range[0])
                ind_end = int(val_range[1]) + 1
                gid_dict[key] = np.arange(ind_start, ind_end)
            else:
                gid_dict[key] = np.array([])

    return gid_dict

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

def consolidate_chunks(input_dict):
    # MOVE to hnn-core
    # get a list of sorted chunks
    sorted_inputs = sorted(input_dict.items(), key=lambda x: x[1]['user_start'])

    consolidated_chunks = []
    for one_input in sorted_inputs:
        if not 'opt_start' in one_input[1]:
            continue

        # extract info from sorted list
        input_dict = {'inputs': [one_input[0]],
                      'chunk_start': one_input[1]['user_start'],
                      'chunk_end': one_input[1]['user_end'],
                      'opt_start': one_input[1]['opt_start'],
                      'opt_end': one_input[1]['opt_end'],
                      'weights': one_input[1]['weights'],
                      }

        if (len(consolidated_chunks) > 0) and \
            (input_dict['chunk_start'] <= consolidated_chunks[-1]['chunk_end']):
            # update previous chunk
            consolidated_chunks[-1]['inputs'].extend(input_dict['inputs'])
            consolidated_chunks[-1]['chunk_end'] = input_dict['chunk_end']
            consolidated_chunks[-1]['opt_end'] = max(consolidated_chunks[-1]['opt_end'], input_dict['opt_end'])
            # average the weights
            consolidated_chunks[-1]['weights'] = (consolidated_chunks[-1]['weights'] + one_input[1]['weights'])/2
        else:
            # new chunk
            consolidated_chunks.append(input_dict)

    return consolidated_chunks

def combine_chunks(input_chunks):
    # MOVE to hnn-core
    # Used for creating the opt params of the last step with all inputs

    final_chunk = {'inputs': [],
                   'opt_start': 0.0,
                   'opt_end': 0.0,
                   'chunk_start': 0.0,
                   'chunk_end': 0.0}

    for evinput in input_chunks:
        final_chunk['inputs'].extend(evinput['inputs'])
        if evinput['opt_end'] > final_chunk['opt_end']:
            final_chunk['opt_end'] = evinput['opt_end']
        if evinput['chunk_end'] > final_chunk['chunk_end']:
            final_chunk['chunk_end'] = evinput['chunk_end']

    # wRMSE with weights of 1's is the same as regular RMSE.
    final_chunk['weights'] = np.ones(len(input_chunks[-1]['weights']))
    return final_chunk

def chunk_evinputs(opt_params, sim_tstop, sim_dt):
    # MOVE to hnn-core
    """
    Take dictionary (opt_params) sorted by input and
    return a sorted list of dictionaries describing
    chunks with inputs consolidated as determined the
    range between 'user_start' and 'user_end'.

    The keys of the chunks in chunk_list dictionary
    returned are:
    'weights'
    'chunk_start'
    'chunk_end'
    'opt_start'
    'opt_end'
    """

    import re
    import scipy.stats as stats
    from math import ceil, floor

    num_step = ceil(sim_tstop / sim_dt) + 1
    times = np.linspace(0, sim_tstop, num_step)

    # input_dict will be passed to consolidate_chunks, so it has
    # keys 'user_start' and 'user_end' instead of chunk_start and
    # 'chunk_start' that will be returned in the dicts returned
    # in chunk_list
    input_dict = {}
    cdfs = {}


    for input_name in opt_params.keys():
        if opt_params[input_name]['user_start'] > sim_tstop or \
           opt_params[input_name]['user_end'] < 0:
            # can't optimize over this input
            continue

        # calculate cdf using start time (minival of optimization range)
        cdf = stats.norm.cdf(times, opt_params[input_name]['user_start'],
                             opt_params[input_name]['sigma'])
        cdfs[input_name] = cdf.copy()

    for input_name in opt_params.keys():
        if opt_params[input_name]['user_start'] > sim_tstop or \
           opt_params[input_name]['user_end'] < 0:
            # can't optimize over this input
            continue
        input_dict[input_name] = {'weights': cdfs[input_name].copy(),
                                  'user_start': opt_params[input_name]['user_start'],
                                  'user_end': opt_params[input_name]['user_end']}

        for other_input in opt_params:
            if opt_params[other_input]['user_start'] > sim_tstop or \
               opt_params[other_input]['user_end'] < 0:
                # not optimizing over that input
                continue
            if input_name == other_input:
                # don't subtract our own cdf(s)
                continue
            if opt_params[other_input]['mean'] < \
               opt_params[input_name]['mean']:
                # check ordering to only use inputs after us
                continue
            else:
                decay_factor = opt_params[input_name]['decay_multiplier']*(opt_params[other_input]['mean'] - \
                                  opt_params[input_name]['mean']) / \
                                  sim_tstop
                input_dict[input_name]['weights'] -= cdfs[other_input] * decay_factor

        # weights should not drop below 0
        input_dict[input_name]['weights'] = np.clip(input_dict[input_name]['weights'], a_min=0, a_max=None)

        # start and stop optimization where the weights are insignificant
        good_indices = np.where( input_dict[input_name]['weights'] > 0.01)
        if len(good_indices[0]) > 0:
            input_dict[input_name]['opt_start'] = min(opt_params[input_name]['user_start'], times[good_indices][0])
            input_dict[input_name]['opt_end'] = max(opt_params[input_name]['user_end'], times[good_indices][-1])
        else:
            input_dict[input_name]['opt_start'] = opt_params[other_input]['user_start']
            input_dict[input_name]['opt_end']  = opt_params[other_input]['user_end']

        # convert to multiples of dt
        input_dict[input_name]['opt_start'] = floor(input_dict[input_name]['opt_start']/sim_dt)*sim_dt
        input_dict[input_name]['opt_end'] = ceil(input_dict[input_name]['opt_end']/sim_dt)*sim_dt

    # combined chunks that have overlapping ranges
    # opt_params is a dict, turn into a list
    chunk_list = consolidate_chunks(input_dict)

    # add one last chunk to the end
    if len(chunk_list) > 1:
        chunk_list.append(combine_chunks(chunk_list))

    return chunk_list

def get_inputs (params):
    # MOVE
    import re
    input_list = []

    # first pass through all params to get mu and sigma for each
    for k in params.keys():
        input_mu = re.match('^t_ev(prox|dist)_([0-9]+)', k)
        if input_mu:
            id_str = 'ev' + input_mu.group(1) + '_' + input_mu.group(2)
            input_list.append(id_str)

    return input_list

def trans_input (input_var):
    # MOVE
    import re

    input_str = input_var
    input_match = re.match('^ev(prox|dist)_([0-9]+)', input_var)
    if input_match:
        if input_match.group(1) == "prox":
            input_str = 'Proximal ' + input_match.group(2)
        if input_match.group(1) == "dist":
            input_str = 'Distal ' + input_match.group(2)

    return input_str

