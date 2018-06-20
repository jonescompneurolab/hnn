# paramrw.py - routines for reading the param files
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: removed dependence on cartesian, updated for python3)
# last major: (SL: cleanup of self.p_all)

import re
import fileio as fio
import numpy as np
import itertools as it
# from cartesian import cartesian
from params_default import get_params_default

# get dict of ':' separated params from fn; ignore lines starting with #
def quickreadprm (fn):
  d = {}
  with open(fn,'r') as fp:
    ln = fp.readlines()
    for l in ln:
      s = l.strip()
      if s.startswith('#'): continue
      sp = s.split(':')
      if len(sp) > 1:
        d[sp[0].strip()]=str(sp[1]).strip()
  return d

# get dict of ':' separated params from fn; ignore lines starting with #
def quickgetprm (fn,k,ty):
  d = quickreadprm(fn)
  return ty(d[k])

# check if using ongoing inputs
def usingOngoingInputs (d, lty = ['_prox', '_dist']):
  if type(d)==str: d = quickreadprm(d)
  tstop = float(d['tstop'])
  dpref = {'_prox':'input_prox_A_','_dist':'input_dist_A_'}
  try:
    for postfix in lty:
      if float(d['t0_input'+postfix])<= tstop and \
         float(d['tstop_input'+postfix])>=float(d['t0_input'+postfix]) and \
         float(d['f_input'+postfix])>0.:
        for k in ['weight_L2Pyr_ampa','weight_L2Pyr_nmda',\
                  'weight_L5Pyr_ampa','weight_L5Pyr_nmda',\
                  'weight_inh_ampa','weight_inh_nmda']:
          if float(d[dpref[postfix]+k])>0.:
            #print('usingOngoingInputs:',d[dpref[postfix]+k])
            return True
  except: 
    return False
  return False

# return number of evoked inputs (proximal, distal)
# using dictionary d (or if d is a string, first load the dictionary from filename d)
def countEvokedInputs (d):
  if type(d) == str: d = quickreadprm(d)
  nprox = ndist = 0
  for k,v in d.items():
    if k.startswith('t_'):
      if k.count('evprox') > 0:
        nprox += 1
      elif k.count('evdist') > 0:
        ndist += 1
  return nprox, ndist

# check if using any evoked inputs 
def usingEvokedInputs (d, lsuffty = ['_evprox_', '_evdist_']):
  if type(d) == str: d = quickreadprm(d)
  nprox,ndist = countEvokedInputs(d)
  tstop = float(d['tstop']) 
  lsuff = []
  if '_evprox_' in lsuffty:
    for i in range(1,nprox+1,1): lsuff.append('_evprox_'+str(i))
  if '_evdist_' in lsuffty:
    for i in range(1,ndist+1,1): lsuff.append('_evdist_'+str(i))
  for suff in lsuff:
    k = 't' + suff
    if k not in d: continue
    if float(d[k]) > tstop: continue
    k = 'gbar' + suff
    for k1 in d.keys():
      if k1.startswith(k):
        if float(d[k1]) > 0.0: return True
  return False

# check if using any poisson inputs 
def usingPoissonInputs (d):
  if type(d)==str: d = quickreadprm(d)
  tstop = float(d['tstop'])
  if 't0_pois' in d and 'T_pois' in d:
    t0_pois = float(d['t0_pois'])
    if t0_pois > tstop: return False
    T_pois = float(d['T_pois'])
    if t0_pois > T_pois and T_pois != -1.0:
      return False
  for cty in ['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket']:
    for sy in ['ampa','nmda']:
      k = cty+'_Pois_A_weight_'+sy
      if k in d:
        if float(d[k]) != 0.0: return True
  return False

# check if using any tonic (IClamp) inputs 
def usingTonicInputs (d):
  if type(d)==str: d = quickreadprm(d)
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

# class controlling multiple simulation files (.param)
class ExpParams():
    def __init__ (self, f_psim, debug=False):

        self.debug = debug

        self.expmt_group_params = []

        # self.prng_seedcore = {}
        # this list is simply to access these easily
        self.prng_seed_list = []

        # read in params from a file
        p_all_input = self.__read_sim(f_psim)
        self.p_template = dict.fromkeys(self.expmt_group_params)

        # create non-exp params dict from default dict
        self.p_all = self.__create_dict_from_default(p_all_input)

        # pop off fixed known vals and create experimental prefix templates
        self.__pop_known_values()

        # make dict of coupled params
        self.coupled_params = self.__find_coupled_params()

        # create the list of iterated params
        self.list_params = self.__create_paramlist()
        self.N_sims = len(self.list_params[0][1])

    # return pdict based on that one value, PLUS append the p_ext here ... yes, hack-y
    def return_pdict(self, expmt_group, i):
        # p_template was always updated to include the ones from exp and others
        p_sim = dict.fromkeys(self.p_template)

        # go through params in list_params
        for param, val_list in self.list_params:
            if param.startswith('prng_seedcore_'):
                p_sim[param] = int(val_list[i])
            else:
                p_sim[param] = val_list[i]

        # go through the expmt group-based params
        for param, val in self.p_group[expmt_group].items():
            p_sim[param] = val

        # add alpha distributions. A bit hack-y
        for param, val in self.alpha_distributions.items():
            p_sim[param] = val

        # Add coupled params
        for coupled_param, val_param  in self.coupled_params.items():
            p_sim[coupled_param] = p_sim[val_param]

        return p_sim

    # reads .param file and returns p_all_input dict
    def __read_sim(self, f_psim):
        lines = fio.clean_lines(f_psim)

        # ignore comments
        lines = [line for line in lines if line[0] is not '#']
        p = {}

        for line in lines:
            # splits line by ':'
            param, val = line.split(": ")

            # sim_prefix is not a rotated variable
            # not sure why `if param is 'sim_prefix':` does not work here
            if param == 'sim_prefix':
                p[param] = str(val)

            # expmt_groups must be listed before other vals
            elif param == 'expmt_groups':
                # this list will be the preservation of the original order
                self.expmt_groups = [expmt_group for expmt_group in val[1:-1].split(', ')]

                # this dict here for easy access
                # p_group saves each of the changed params per group
                self.p_group = dict.fromkeys(self.expmt_groups)

                # create empty dicts in each
                for group in self.p_group:
                    self.p_group[group] = {}

            elif param.startswith('prng_seedcore_'):
                p[param] = int(val)
                # key = param.split('prng_seedcore_')[-1]
                # self.prng_seedcore[key] = val

                # only add values that will change
                if p[param] == -1:
                    self.prng_seed_list.append(param)

            elif param.startswith('distribution_'):
                p[param] = str(val)

            elif param == 'Run_Date':
                pass

            else:
                # assign group params first
                if val[0] is '{':
                    # check for a linspace as a param!
                    if val[1] is 'L':
                        # in this case, val_range must be as long as the correct expmt_group length
                        # everything beyond that will be truncated by the zip operation below
                        # param passed will strip away the curly braces and just pass the linspace
                        val_range = self.__expand_linspace(val[1:-1])
                    else:
                        val_range = self.__expand_array(val)

                    # add the expmt_group param to the list if it's not already present
                    if param not in self.expmt_group_params:
                        self.expmt_group_params.append(param)

                    # parcel out vals to exp groups with assigned param names
                    for expmt_group, val in zip(self.expmt_groups, val_range):
                        self.p_group[expmt_group][param] = val

                # interpret this as a list of vals
                # type floats to a np array
                elif val[0] is '[':
                    p[param] = self.__expand_array(val)

                # interpret as a linspace
                elif val[0] is 'L':
                    p[param] = self.__expand_linspace(val)

                elif val[0] is 'A':
                    p[param] = self.__expand_arange(val)

                else:
                    try:
                        p[param] = float(val)
                    except ValueError:
                        p[param] = str(val)

        # hack-y. sorry, future
        # tstop_* = 0 is valid now, resets to the actual tstop
        # with the added bonus of saving this time to the indiv params
        for param, val in p.items():
            if param.startswith('tstop_'):
                if isinstance(val, float):
                    if val == 0:
                        p[param] = p['tstop']
                elif isinstance(val, np.ndarray):
                    p[param][p[param] == 0] = p['tstop']

        return p

    # general function to expand a list of values
    def __expand_array(self, str_val):
        val_list = str_val[1:-1].split(', ')
        val_range = np.array([float(item) for item in val_list])

        return val_range

    # general function to expand the arange
    def __expand_arange(self, str_val):
        # strip away the leading character along with the brackets and split the csv values
        val_list = str_val[2:-1].split(', ')

        # use the values in val_list as params for np.linspace
        val_range = np.arange(float(val_list[0]), float(val_list[1]), float(val_list[2]))

        # return the final linspace expanded
        return val_range

    # general function to expand the linspace
    def __expand_linspace(self, str_val):
        # strip away the leading character along with the brackets and split the csv values
        val_list = str_val[2:-1].split(', ')

        # use the values in val_list as params for np.linspace
        val_range = np.linspace(float(val_list[0]), float(val_list[1]), int(val_list[2]))

        # return the final linspace expanded
        return val_range

    # creates dict of params whose values are to be coupled
    def __find_coupled_params(self):
        coupled_params = {}
        # iterates over all key/value pairs to find vals that are strings
        for key, val in self.p_all.items():
            if isinstance(val, str):
                # check that string is another param in p_all
                if val in self.p_all.keys():
                    coupled_params[key] = val
                else:
                    print("Unknown key: %s. Probably going to error." % (val))

        # Pop coupled params
        for key in coupled_params:
            self.p_all.pop(key)

        return coupled_params

    # pop known values & strings off of the params list
    def __pop_known_values(self):
        self.sim_prefix = self.p_all.pop('sim_prefix')

        # create an experimental string prefix template
        self.exp_prefix_str = self.sim_prefix+"-%03d"
        self.trial_prefix_str = self.exp_prefix_str+"-T%02d"

        # self.N_trials = int(self.p_all.pop('N_trials'))
        # self.prng_state = self.p_all.pop('prng_state')[1:-1]

        # Save alpha distribution types in dict for later use
        self.alpha_distributions = {
            'distribution_prox': self.p_all.pop('distribution_prox'),
            'distribution_dist': self.p_all.pop('distribution_dist'),
        }

    # create the dict based on the default param dict
    def __create_dict_from_default (self, p_all_input):
        nprox, ndist = countEvokedInputs(p_all_input)
        # print('found nprox,ndist ev inputs:', nprox, ndist)

        # create a copy of params_default through which to iterate
        p_all = get_params_default(nprox, ndist)

        # now find ONLY the values that are present in the supplied p_all_input
        # based on the default dict
        for key in p_all.keys():
            # automatically expects that keys are either in p_all_input OR will resort
            # to default value
            if key in p_all_input:
                # pop val off so the remaining items in p_all_input are extraneous
                p_all[key] = p_all_input.pop(key)

        # now display extraneous keys, if there were any
        if len(p_all_input):
            if self.debug: print("Invalid keys from param file not found in default params: %s" % str(p_all_input.keys()))

        return p_all

    # creates all combination of non-exp params
    def __create_paramlist (self):
        # p_all is the dict specifying all of the changing params
        plist = []

        # get all key/val pairs from the all dict
        list_sorted = [item for item in self.p_all.items()]

        # sort the list by the key (alpha)
        list_sorted.sort(key=lambda x: x[0])

        # grab just the keys (but now in order)
        self.keys_sorted = [item[0] for item in list_sorted]
        self.p_template.update(dict.fromkeys(self.keys_sorted))

        # grab just the values (but now in order)
        # plist = [item[1] for item in list_sorted]
        for item in list_sorted:
            if isinstance(item[1], np.ndarray):
                plist.append(item[1])
            else:
                plist.append(np.array([item[1]]))

        # print(plist)
        # vals_all = cartesian(plist)
        vals_new = np.array([np.array(val) for val in it.product(*plist)])
        vals_new = vals_new.transpose()

        return [item for item in zip(self.keys_sorted, vals_new)]

    # Find keys that change anytime during simulation
    # (i.e. have more than one associated value)
    def get_key_types(self):
        key_dict = {
            'expmt_keys': [],
            'dynamic_keys': [],
            'static_keys': [],
        }

        # Save exmpt keys
        key_dict['expmt_keys'] = self.expmt_group_params

        # Save expmt keys as dynamic keys
        key_dict['dynamic_keys'] = self.expmt_group_params

        # Find keys that change run to run within experiments
        for key in self.p_all.keys():
            # if key has length associated with it, must change run to run
            try:
                len(self.p_all[key])

                # Before storing key, check to make sure it has not already been stored
                if key not in key_dict['dynamic_keys']:
                    key_dict['dynamic_keys'].append(key)

            except TypeError:
                key_dict['static_keys'].append(key)

        # Check if coupled params are dynamic
        for dep_param, ind_param in self.coupled_params.items():
            if ind_param in key_dict['dynamic_keys']:
                key_dict['dynamic_keys'].append(dep_param)
            else:
                key_dict['static_keys'].append(dep_param)

        return key_dict

# reads params from a generated txt file and returns gid dict and p dict 
def read (fparam):
    lines = fio.clean_lines(fparam)
    p = {}
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
        else:
            try:
                p[key] = float(val)
            except ValueError:
                p[key] = str(val)
    return gid_dict, p

# write the params to a filename
def write(fparam, p, gid_list):
  """ now sorting
  """
  # sort the items in the dict by key
  # p_sorted = [item for item in p.items()]
  p_keys = [key for key, val in p.items()]
  p_sorted = [(key, p[key]) for key in p_keys]
  # for some reason this is now crashing in python/mpi
  # specifically, lambda sorting in place?
  # p_sorted = [item for item in p.items()]
  # p_sorted.sort(key=lambda x: x[0])
  # open the file for writing
  with open(fparam, 'w') as f:
    pstring = '%26s: '
    # write the gid info first
    for key in gid_list.keys():
      f.write(pstring % key)
      if len(gid_list[key]):
        f.write('[%4i, %4i] ' % (gid_list[key][0], gid_list[key][-1]))
      else:
        f.write('[]')
      f.write('\n')
    # do the params in p_sorted
    for param in p_sorted:
      key, val = param
      f.write(pstring % key)
      if key.startswith('N_'):
        f.write('%i\n' % val)
      else:
        f.write(str(val)+'\n')

# Searches f_param for any match of p
def find_param(fparam, param_key):
    _, p = read(fparam)

    try:
        return p[param_key]

    except KeyError:
        return "There is no key by the name %s" % param_key

# reads the simgroup name from fparam
def read_sim_prefix(fparam):
    lines = fio.clean_lines(fparam)
    param_list = [line for line in lines if line.split(': ')[0].startswith('sim_prefix')]

    # Assume we found something ...
    if param_list:
        return param_list[0].split(" ")[1]
    else:
        print("No sim_prefix found")
        return 0

# Finds the experiments list from the simulation param file (.param)
def read_expmt_groups(fparam):
    lines = fio.clean_lines(fparam)
    lines = [line for line in lines if line.split(': ')[0] == 'expmt_groups']

    try:
        return lines[0].split(': ')[1][1:-1].split(', ')
    except:
        print("Couldn't get a handle on expmts")
        return 0

# qnd function to add feeds if they are sensible
def feed_validate(p_ext, d, tstop):
    """ whips into shape ones that are not
        could be properly made into a meaningful class.
    """
    # only append if t0 is less than simulation tstop
    if tstop > d['t0']:
        # # reset tstop if the specified tstop exceeds the
        # # simulation runtime
        # if d['tstop'] == 0:
        #     d['tstop'] = tstop

        if d['tstop'] > tstop:
            d['tstop'] = tstop

        # if stdev is zero, increase synaptic weights 5 fold to make
        # single input equivalent to 5 simultaneous input to prevent spiking    <<---- SN: WHAT IS THIS RULE!?!?!?
        if not d['stdev'] and d['distribution'] != 'uniform':
            for key in d.keys():
                if key.endswith('Pyr'):
                    d[key] = (d[key][0] * 5., d[key][1])
                elif key.endswith('Basket'):
                    d[key] = (d[key][0] * 5., d[key][1])

        # if L5 delay is -1, use same delays as L2 unless L2 delay is 0.1 in which case use 1. <<---- SN: WHAT IS THIS RULE!?!?!?
        if d['L5Pyr_ampa'][1] == -1:                                  
            for key in d.keys():
                if key.startswith('L5'):
                    if d['L2Pyr'][1] != 0.1:
                        d[key] = (d[key][0], d['L2Pyr'][1])
                    else:
                        d[key] = (d[key][0], 1.)

        p_ext.append(d)

    return p_ext

#
def checkevokedsynkeys (p, nprox, ndist):
  # make sure ampa,nmda gbar values are in the param dict for evoked inputs(for backwards compatibility)
  lctprox = ['L2Pyr','L5Pyr','L2Basket','L5Basket'] # evoked distal target cell types
  lctdist = ['L2Pyr','L5Pyr','L2Basket'] # evoked proximal target cell types
  lsy = ['ampa','nmda'] # synapse types used in evoked inputs
  for nev,pref,lct in zip([nprox,ndist],['evprox_','evdist_'],[lctprox,lctdist]):
    for i in range(nev):
      skey = pref + str(i+1)
      for sy in lsy:
        for ct in lct:
          k = 'gbar_'+skey+'_'+ct+'_'+sy
          # if the synapse-specific gbar not present, use the existing weight for both ampa,nmda
          if k not in p: 
            p[k] = p['gbar_'+skey+'_'+ct]

#
def checkpoissynkeys (p):
  # make sure ampa,nmda gbar values are in the param dict for Poisson inputs (for backwards compatibility)
  lct = ['L2Pyr','L5Pyr','L2Basket','L5Basket'] # target cell types
  lsy = ['ampa','nmda'] # synapse types used in Poisson inputs
  for ct in lct:
    for sy in lsy:
      k = ct + '_Pois_A_weight_' + sy
      # if the synapse-specific weight not present, set it to 0 in p
      if k not in p: 
        p[k] = 0.0 

# creates the external feed params based on individual simulation params p
def create_pext (p, tstop):
    # indexable py list of param dicts for parallel
    # turn off individual feeds by commenting out relevant line here.
    # always valid, no matter the length
    p_ext = []

    # p_unique is a dict of input param types that end up going to each cell uniquely
    p_unique = {}

    # default params for proximal rhythmic inputs
    feed_prox = {
        'f_input': p['f_input_prox'],
        't0': p['t0_input_prox'],
        'tstop': p['tstop_input_prox'],
        'stdev': p['f_stdev_prox'],
        'L2Pyr_ampa': (p['input_prox_A_weight_L2Pyr_ampa'], p['input_prox_A_delay_L2']),
        'L2Pyr_nmda': (p['input_prox_A_weight_L2Pyr_nmda'], p['input_prox_A_delay_L2']),
        'L5Pyr_ampa': (p['input_prox_A_weight_L5Pyr_ampa'], p['input_prox_A_delay_L5']),
        'L5Pyr_nmda': (p['input_prox_A_weight_L5Pyr_nmda'], p['input_prox_A_delay_L5']),
        'L2Basket_ampa': (p['input_prox_A_weight_L2Basket_ampa'], p['input_prox_A_delay_L2']),
        'L2Basket_nmda': (p['input_prox_A_weight_L2Basket_nmda'], p['input_prox_A_delay_L2']),
        'L5Basket_ampa': (p['input_prox_A_weight_L5Basket_ampa'], p['input_prox_A_delay_L5']),
        'L5Basket_nmda': (p['input_prox_A_weight_L5Basket_nmda'], p['input_prox_A_delay_L5']),
        'events_per_cycle': p['events_per_cycle_prox'],
        'prng_seedcore': int(p['prng_seedcore_input_prox']),
        'distribution': p['distribution_prox'],
        'lamtha': 100.,
        'loc': 'proximal',
        'repeats': p['repeats_prox'],
        't0_stdev': p['t0_input_stdev_prox'],
        'threshold': p['threshold']
    }

    # ensures time interval makes sense
    p_ext = feed_validate(p_ext, feed_prox, tstop)

    # default params for distal rhythmic inputs
    feed_dist = {
        'f_input': p['f_input_dist'],
        't0': p['t0_input_dist'],
        'tstop': p['tstop_input_dist'],
        'stdev': p['f_stdev_dist'],
        'L2Pyr_ampa': (p['input_dist_A_weight_L2Pyr_ampa'], p['input_dist_A_delay_L2']),
        'L2Pyr_nmda': (p['input_dist_A_weight_L2Pyr_nmda'], p['input_dist_A_delay_L2']),
        'L5Pyr_ampa': (p['input_dist_A_weight_L5Pyr_ampa'], p['input_dist_A_delay_L5']),
        'L5Pyr_nmda': (p['input_dist_A_weight_L5Pyr_nmda'], p['input_dist_A_delay_L5']),
        'L2Basket_ampa': (p['input_dist_A_weight_L2Basket_ampa'], p['input_dist_A_delay_L2']),
        'L2Basket_nmda': (p['input_dist_A_weight_L2Basket_nmda'], p['input_dist_A_delay_L2']),
        'events_per_cycle': p['events_per_cycle_dist'],
        'prng_seedcore': int(p['prng_seedcore_input_dist']),
        'distribution': p['distribution_dist'],
        'lamtha': 100.,
        'loc': 'distal',
        'repeats': p['repeats_dist'],
        't0_stdev': p['t0_input_stdev_dist'],
        'threshold': p['threshold']
    }

    p_ext = feed_validate(p_ext, feed_dist, tstop)

    nprox, ndist = countEvokedInputs(p)
    # print('nprox,ndist evoked inputs:', nprox, ndist)

    # NEW: make sure all evoked synaptic weights present (for backwards compatibility)
    # could cause differences between output of param files since some nmda weights should
    # be 0 while others > 0
    checkevokedsynkeys(p,nprox,ndist) 

    # Create proximal evoked response parameters
    # f_input needs to be defined as 0
    for i in range(nprox):
      skey = 'evprox_' + str(i+1)
      p_unique['evprox' + str(i+1)] = {
          't0': p['t_' + skey],
          'L2_pyramidal':(p['gbar_'+skey+'_L2Pyr_ampa'],p['gbar_'+skey+'_L2Pyr_nmda'],0.1,p['sigma_t_'+skey]),
          'L2_basket':(p['gbar_'+skey+'_L2Basket_ampa'],p['gbar_'+skey+'_L2Basket_nmda'],0.1,p['sigma_t_'+skey]),
          'L5_pyramidal':(p['gbar_'+skey+'_L5Pyr_ampa'],p['gbar_'+skey+'_L5Pyr_nmda'],1.,p['sigma_t_'+skey]),
          'L5_basket':(p['gbar_'+skey+'_L5Basket_ampa'],p['gbar_'+skey+'_L5Basket_nmda'],1.,p['sigma_t_'+skey]),
          'prng_seedcore': int(p['prng_seedcore_' + skey]),
          'lamtha_space': 3.,
          'loc': 'proximal',
          'sync_evinput': p['sync_evinput'],
          'threshold': p['threshold'],
          'numspikes': p['numspikes_' + skey]
      }

    # Create distal evoked response parameters
    # f_input needs to be defined as 0
    for i in range(ndist):
      skey = 'evdist_' + str(i+1)
      p_unique['evdist' + str(i+1)] = {
          't0': p['t_' + skey],
          'L2_pyramidal':(p['gbar_'+skey+'_L2Pyr_ampa'],p['gbar_'+skey+'_L2Pyr_nmda'],0.1,p['sigma_t_'+skey]),
          'L5_pyramidal':(p['gbar_'+skey+'_L5Pyr_ampa'],p['gbar_'+skey+'_L5Pyr_nmda'],0.1,p['sigma_t_'+skey]),
          'L2_basket':(p['gbar_'+skey+'_L2Basket_ampa'],p['gbar_'+skey+'_L2Basket_nmda'],0.1,p['sigma_t_' + skey]),
          'prng_seedcore': int(p['prng_seedcore_' + skey]),
          'lamtha_space': 3.,
          'loc': 'distal',
          'sync_evinput': p['sync_evinput'],
          'threshold': p['threshold'],
          'numspikes': p['numspikes_' + skey]
      }

    # this needs to create many feeds
    # (amplitude, delay, mu, sigma). ordered this way to preserve compatibility
    p_unique['extgauss'] = { # NEW: note double weight specification since only use ampa for gauss inputs
        'stim': 'gaussian',
        'L2_basket':(p['L2Basket_Gauss_A_weight'],p['L2Basket_Gauss_A_weight'],1.,p['L2Basket_Gauss_mu'],p['L2Basket_Gauss_sigma']),
        'L2_pyramidal':(p['L2Pyr_Gauss_A_weight'],p['L2Pyr_Gauss_A_weight'],0.1,p['L2Pyr_Gauss_mu'],p['L2Pyr_Gauss_sigma']),
        'L5_basket':(p['L5Basket_Gauss_A_weight'],p['L5Basket_Gauss_A_weight'],1.,p['L5Basket_Gauss_mu'],p['L5Basket_Gauss_sigma']),
        'L5_pyramidal':(p['L5Pyr_Gauss_A_weight'],p['L5Pyr_Gauss_A_weight'],1.,p['L5Pyr_Gauss_mu'],p['L5Pyr_Gauss_sigma']),
        'lamtha': 100.,
        'prng_seedcore': int(p['prng_seedcore_extgauss']),
        'loc': 'proximal',
        'threshold': p['threshold']
    }

    checkpoissynkeys(p)

    # define T_pois as 0 or -1 to reset automatically to tstop
    if p['T_pois'] in (0, -1): p['T_pois'] = tstop

    # Poisson distributed inputs to proximal
    p_unique['extpois'] = {# NEW: setting up AMPA and NMDA for Poisson inputs; why delays differ?
        'stim': 'poisson',
        'L2_basket': (p['L2Basket_Pois_A_weight_ampa'],p['L2Basket_Pois_A_weight_nmda'],1.,p['L2Basket_Pois_lamtha']),
        'L2_pyramidal': (p['L2Pyr_Pois_A_weight_ampa'],p['L2Pyr_Pois_A_weight_nmda'], 0.1,p['L2Pyr_Pois_lamtha']),
        'L5_basket': (p['L5Basket_Pois_A_weight_ampa'],p['L5Basket_Pois_A_weight_nmda'],1.,p['L5Basket_Pois_lamtha']),
        'L5_pyramidal': (p['L5Pyr_Pois_A_weight_ampa'],p['L5Pyr_Pois_A_weight_nmda'],1.,p['L5Pyr_Pois_lamtha']),
        'lamtha_space': 100.,
        'prng_seedcore': int(p['prng_seedcore_extpois']),
        't_interval': (p['t0_pois'], p['T_pois']),
        'loc': 'proximal',
        'threshold': p['threshold']
    }

    return p_ext, p_unique

# Finds the changed variables
# sort of inefficient, probably should be part of something else
# not worried about all that right now, as it appears to work
# brittle in that the match string needs to be correct to find all the changed params
# is redundant with(?) get_key_types() dynamic keys information
def changed_vars(fparam):
    # Strip empty lines and comments
    lines = fio.clean_lines(fparam)
    lines = [line for line in lines if line[0] != '#']

    # grab the keys and vals in a list of lists
    # each item of keyvals is a pair [key, val]
    keyvals = [line.split(": ") for line in lines]

    # match the list for changed items starting with "AKL[(" on the 1st char of the val
    var_list = [line for line in keyvals if re.match('[AKL[\(]', line[1][0])]

    # additional default info to add always
    list_meta = [
        'N_trials',
        'N_sims',
        'Run_Date'
    ]

    # list concatenate these lists
    var_list += [line for line in keyvals if line[0] in list_meta]

    # return the list of "changed" or "default" vars
    return var_list

# Takes two dictionaries (d1 and d2) and compares the keys in d1 to those in d2
# if any match, updates the (key, value) pair of d1 to match that of d2
# not real happy with variable names, but will have to do for now
def compare_dictionaries(d1, d2):
    # iterate over intersection of key sets (i.e. any common keys)
    for key in d1.keys() and d2.keys():
        # update d1 to have same (key, value) pair as d2
        d1[key] = d2[key]

    return d1

# get diff on 2 dictionaries
def diffdict (d1, d2, verbose=True):
  print('d1,d2 num keys - ', len(d1.keys()), len(d2.keys()))
  for k in d1.keys():
    if not k in d2:
      if verbose: print(k, ' in d1, not in d2')
  for k in d2.keys():  
    if not k in d1:
      if verbose: print(k, ' in d2, not in d1')
  for k in d1.keys():
    if k in d2:
      if d1[k] != d2[k]:
        print('d1[',k,']=',d1[k],' d2[',k,']=',d2[k])

# debug test function
if __name__ == '__main__':
  fparam = 'param/debug.param'
  p = ExpParams(fparam,debug=True)
  # print(find_param(fparam, 'WhoDat')) # ?

