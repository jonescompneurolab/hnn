# spikefn.py - dealing with spikes
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: minor)
# last major: (SL: toward python3)

import numpy as np
import scipy.signal as sps
import matplotlib.pyplot as plt
import itertools as it
import os
import paramrw

from hnn_core import read_spikes

# meant as a class for ONE cell type
class Spikes():
  def __init__ (self, s_all, ranges):
    self.r = ranges
    self.spike_list = self.filter(s_all)
    self.N_cells = len(self.r)
    self.N_spikingcells = len(self.spike_list)
    # this is set externally
    self.tick_marks = []

  # returns spike_list, a list of lists of spikes.
  # Each list corresponds to a cell, counted by range
  def filter (self, s_all):
    spike_list = []
    if len(s_all) > 0:
      for ri in self.r:
        srange = s_all[s_all[:, 1] == ri][:, 0]
        srange[srange.argsort()]
        spike_list.append(srange)

    return spike_list

  # simple return of all spikes *or* each spike indexed i in every list
  def collapse_all (self, i=None):
    if i == 'None':
      spk_all = []
      for spk_list in self.spike_list:
        spk_all.extend(spk_list)
    else:
      spk_all = [spk_list[i] for spk_list in self.spike_list if spk_list]
    return spk_all

  # uses self.collapse_all() and returns unique spike times
  def unique_all (self, i=None):
    spk_all = self.collapse_all(i)
    return np.unique(spk_all)

  # plot psth
  def ppsth (self, a):
    # flatten list of spikes
    s_agg = np.array(list(it.chain.from_iterable(self.spike_list)))
    # plot histogram to axis 'a'
    bins = hist_bin_opt(s_agg, 1)
    a.hist(s_agg, bins, normed=True, facecolor='g', alpha=0.75)

# Class to handle extinput event times
class ExtInputs (Spikes):
  # class for external inputs - extracts gids and times
  def __init__ (self, fspk, fgids, params, evoked=False):

    self.p_dict = params
    try:
      self.gid_dict = paramrw.read_gids_param(fgids)
    except FileNotFoundError:
      raise ValueError

    if 'common' in self.gid_dict:
      extinput_key = 'common'
    else:
      extinput_key = 'extinput'

    self.evoked = evoked

    # parse evoked prox and dist input gids from gid_dict
    self.gid_evprox, self.gid_evdist = self.__get_evokedinput_gids()

    # parse ongoing prox and dist input gids from gid_dict
    self.gid_prox, self.gid_dist = self.__get_extinput_gids(extinput_key)
    # poisson input gids
    #print('getting pois input gids')
    self.gid_pois = self.__get_poisinput_gids()
    # self.inputs is dict of input times with keys 'prox' and 'dist'
    self.inputs = self.__get_extinput_times(fspk)

  def __get_extinput_gids (self, extinput_key):
    # Determine if both feeds exist in this sim
    # If they do, self.gid_dict['extinput'] has length 2
    # If so, first gid is guaraneteed to be prox feed, second to be dist feed
    if len(self.gid_dict[extinput_key]) == 2:
      return self.gid_dict[extinput_key]
    # Otherwise, only one feed exists in this sim
    # Must use param file to figure out which one...
    elif len(self.gid_dict[extinput_key]) > 0:
      if self.p_dict['t0_input_prox'] < self.p_dict['tstop']:
        return self.gid_dict[extinput_key][0], None
      elif self.p_dict['t0_input_dist'] < self.p_dict['tstop']:
        return None, self.gid_dict[extinput_key][0]
    else:
      return None, None

  def __get_poisinput_gids (self):
    # get Poisson input gids
    gids = []
    if len(self.gid_dict['extpois']) > 0:
      if self.p_dict['t0_pois'] < self.p_dict['tstop']:
        gids = np.array(self.gid_dict['extpois'])
        self.pois_gid_range = (min(gids),max(gids))
    return gids

  def countevinputs (self, ty):
    # count number of evoked inputs
    n = 0
    for k in self.gid_dict.keys():
      if k.startswith(ty) and len(self.gid_dict[k]) > 0: n += 1
    return n

  def countevprox (self): return self.countevinputs('evprox')
  def countevdist (self): return self.countevinputs('evdist')

  def __get_evokedinput_gids (self):
    gid_prox,gid_dist=None,None
    nprox,ndist = self.countevprox(), self.countevdist()
    #print('__get_evokedinput_gids keys:',self.gid_dict.keys(),'nprox:',nprox,'ndist:',ndist)
    if nprox > 0:
      gid_prox = []
      for i in range(nprox):
        if len(self.gid_dict['evprox'+str(i+1)]) > 0:
          l = list(self.gid_dict['evprox'+str(i+1)])
          for x in l: gid_prox.append(x)
      gid_prox = np.array(gid_prox)
      self.evprox_gid_range = (min(gid_prox),max(gid_prox))
    if ndist > 0:
      gid_dist = []
      for i in range(ndist):
        if len(self.gid_dict['evdist'+str(i+1)]) > 0:
          l = list(self.gid_dict['evdist'+str(i+1)])
          for x in l: gid_dist.append(x)
      gid_dist = np.array(gid_dist)
      self.evdist_gid_range = (min(gid_dist),max(gid_dist))
    return gid_prox, gid_dist

  def unique_times (self,s_all,lidx):
    self.r = [x for x in lidx]
    lfilttime = self.filter(s_all); ltime = []
    for arr in lfilttime:
      for time in arr:
        ltime.append(time)
    return np.array(list(set(ltime)))

  def get_times (self, gid, s_all):
    # self.filter() inherited from Spikes()
    # self.r weirdness is necessary to use self.filter()
    # i.e. self.r must exist and be a list to execute self.filter()
    self.r = [gid]
    return self.filter(s_all)[0]

  def __get_extinput_times (self, fspk):
    # load all spike times from file
    s_all = []
    try:
      spikes = read_spikes(fspk)
      s_all = np.r_[spikes.times, spikes.gids].T
    except ValueError:
      s_all = np.loadtxt(open(fspk, 'rb'))
    except OSError:
      print('Warning: could not read file:', fspk)

    if len(s_all) == 0:
      # couldn't read spike times
      raise ValueError

    inputs = {k:np.array([]) for k in ['prox','dist','evprox','evdist','pois']}
    if self.gid_prox is not None: inputs['prox'] = self.get_times(self.gid_prox,s_all)
    if self.gid_dist is not None: inputs['dist'] = self.get_times(self.gid_dist,s_all)
    if self.gid_evprox is not None: inputs['evprox'] = self.unique_times(s_all, self.gid_evprox)
    if self.gid_evdist is not None: inputs['evdist'] = self.unique_times(s_all, self.gid_evdist)
    if self.gid_pois is not None:  inputs['pois'] = self.unique_times(s_all, self.gid_pois)
    return inputs

  # gid associated with evoked input
  def is_evoked_gid (self,gid):
    if len(self.inputs['evprox']) > 0:
      if self.evprox_gid_range[0] <= gid <= self.evprox_gid_range[1]:
        return True
    if len(self.inputs['evdist']) > 0:
      if self.evdist_gid_range[0] <= gid <= self.evdist_gid_range[1]:
        return True
    return False

  # check if gid is associated with a proximal input
  def is_prox_gid (self, gid):
    if gid == self.gid_prox: return True
    if len(self.inputs['evprox']) > 0:
      return self.evprox_gid_range[0] <= gid <= self.evprox_gid_range[1]
    return False

  # check if gid is associated with a distal input
  def is_dist_gid (self, gid):
    if gid == self.gid_dist: return True
    if len(self.inputs['evdist']) > 0:
      return self.evdist_gid_range[0] <= gid <= self.evdist_gid_range[1]
    return False

  # check if gid is associated with a Poisson input
  def is_pois_gid (self, gid):
    try:
      if len(self.inputs['pois']) > 0:
        return self.pois_gid_range[0] <= gid <= self.pois_gid_range[1]
    except:
      pass
    return False

  def truncate_ext (self, dtype, t_int):
    if dtype == 'prox' or dtype == 'dist':
      tmask = (self.inputs[dtype] >= t_int[0]) & (self.inputs[dtype] <= t_int[1])
      return self.inputs[dtype][tmask]
    if dtype == 'env':
      tmask = (self.inputs['t'] >= t_int[0]) & (self.inputs['t'] <= t_int[1])
      return [self.inputs[dtype][tmask], self.inputs['t'][tmask]]

  def add_delay_times (self):
    # if prox delay to both layers is the same, add it to the prox input times
    if self.p_dict['input_prox_A_delay_L2'] == self.p_dict['input_prox_A_delay_L5']:
      self.inputs['prox'] += self.p_dict['input_prox_A_delay_L2']
    # if dist delay to both layers is the same, add it to the dist input times
    if self.p_dict['input_dist_A_delay_L2'] == self.p_dict['input_dist_A_delay_L5']:
      self.inputs['dist'] += self.p_dict['input_dist_A_delay_L2']

  # extinput is either 'dist' or 'prox'
  def plot_hist (self, ax, extinput, tvec, bins='auto', xlim=None, color='green', hty='bar',lw=4):
    if bins is 'auto':
        bins = hist_bin_opt(self.inputs[extinput], 1)
    if not xlim:
      xlim = (0., self.p_dict['tstop'])
    if len(self.inputs[extinput]):
      #print("plot_hist bins:",bins,type(bins))
      hist = ax.hist(self.inputs[extinput], bins, range=xlim, color=color, label=extinput, histtype=hty,linewidth=lw)
      ax.set_xticklabels([])
      ax.tick_params(bottom=False, left=False)
    else:
      hist = None
    return hist

# weird bin counting function
def bin_count(bins_per_second, tinterval): return bins_per_second * tinterval / 1000.

# splits ext random feeds (of type exttype) by supplied cell type
def split_extrand(s, gid_dict, celltype, exttype):
  gid_cell = gid_dict[celltype]
  gid_exttype_start = gid_dict[exttype][0]
  gid_exttype_cell = [gid + gid_exttype_start for gid in gid_dict[celltype]]
  return Spikes(s, gid_exttype_cell)

# histogram bin optimization
def hist_bin_opt(x, N_trials):
  """ Shimazaki and Shinomoto, Neural Comput, 2007
  """
  bin_checks = np.arange(80, 300, 10)
  # bin_checks = np.linspace(150, 300, 16)
  costs = np.zeros(len(bin_checks))
  i = 0
  # this might be vectorizable in np
  for n_bins in bin_checks:
    # use np.histogram to do the numerical minimization
    pdf, bin_edges = np.histogram(x, n_bins)
    # calculate bin width
    # some discrepancy here but should be fine
    w_bin = np.unique(np.diff(bin_edges))
    if len(w_bin) > 1: w_bin = w_bin[0]
    # calc mean and var
    kbar = np.mean(pdf)
    kvar = np.var(pdf)
    # calc cost
    costs[i] = (2.*kbar - kvar) / (N_trials * w_bin)**2.
    i += 1
  # find the bin size corresponding to a minimization of the costs
  bin_opt_list = bin_checks[costs.min() == costs]
  bin_opt = bin_opt_list[0]
  return bin_opt

# from the supplied key name, return a marker style
def get_markerstyle(key):
  markerstyle = ''
  # ext now same color, not ideal yet
  # if 'L2' in key:
  #     markerstyle += 'k'
  # elif 'L5' in key:
  #     markerstyle += 'b'
  # short circuit this by putting extgauss first ... cheap.
  if 'extgauss' in key:
    markerstyle += 'k.'
  elif 'extpois' in key:
    markerstyle += 'k.'
  elif 'pyramidal' in key:
    markerstyle += 'k.'
  elif 'basket' in key:
    markerstyle += 'r|'
  return markerstyle

# Add synaptic delays to alpha input times if applicable:
def add_delay_times(s_dict, p_dict):
  # Only add delays if delay is same for L2 and L5
  # Proximal feed
  # if L5 delay is -1, has same delays as L2
  # if p_dict['input_prox_A_delay_L5'] == -1:
  #     s_dict['alpha_feed_prox'].spike_list = [num+p_dict['input_prox_A_delay_L2'] for num in s_dict['alpha_feed_prox'].spike_list]
  # else, check to see if delays are the same anyway
  # else:
  if s_dict['alpha_feed_prox'].spike_list and p_dict['input_prox_A_delay_L2'] == p_dict['input_prox_A_delay_L5']:
    s_dict['alpha_feed_prox'].spike_list = [num+p_dict['input_prox_A_delay_L2'] for num in s_dict['alpha_feed_prox'].spike_list]
  # Distal
  # if L5 delay is -1, has same delays as L2
  # if p_dict['input_dist_A_delay_L5'] == -1:
  #     s_dict['alpha_feed_dist'].spike_list = [num+p_dict['input_dist_A_delay_L2'] for num in s_dict['alpha_feed_dist'].spike_list]
  # else, check to see if delays are the same anyway
  # else:
  if s_dict['alpha_feed_dist'].spike_list and p_dict['input_dist_A_delay_L2'] == p_dict['input_dist_A_delay_L5']:
    s_dict['alpha_feed_dist'].spike_list = [num+p_dict['input_dist_A_delay_L2'] for num in s_dict['alpha_feed_dist'].spike_list]
  return s_dict

# Checks for existance of alpha feed keys in s_dict.
def alpha_feed_verify(s_dict, p_dict):
  """ If they do not exist, then simulation used one or no feeds. Creates keys accordingly
  """
  # check for existance of keys. If exist, do nothing
  if 'alpha_feed_prox' and 'alpha_feed_dist' in s_dict.keys():
    pass
  # if they do not exist, create them and add proper data
  else:
    # if proximal feed's t0 < tstop, it exists and data is stored in s_dict['extinputs'].
    # distal feed does not exist and gets empty list
    if p_dict['t0_input_prox'] < p_dict['tstop']:
      s_dict['alpha_feed_prox'] = s_dict['extinput']
      # make object on the fly with attribute 'spike_list'
      # A little hack-y
      s_dict['alpha_feed_dist'] = type('emptyspike', (object,), {'spike_list': np.array([])})
    # if distal feed's t0 < tstop, it exists and data is stored in s_dict['extinputs'].
    # Proximal feed does not exist and gets empty list
    elif p_dict['t0_input_dist'] < p_dict['tstop']:
      s_dict['alpha_feed_prox'] = type('emptyspike', (object,), {'spike_list': np.array([])})
      s_dict['alpha_feed_dist'] = s_dict['extinput']
    # if neither had t0 < tstop, neither exists and both get empty list
    else:
      s_dict['alpha_feed_prox'] = type('emptyspike', (object,), {'spike_list': np.array([])})
      s_dict['alpha_feed_dist'] = type('emptyspike', (object,), {'spike_list': np.array([])})
  return s_dict

# input histogram on 2 axes
def pinput_hist(a0, a1, s_list0, s_list1, n_bins, xlim):
  hists = {
    'prox': a0.hist(s_list0, n_bins, color='red', label='Proximal input', alpha=0.75),
    'dist': a1.hist(s_list1, n_bins, color='green', label='Distal input', alpha=0.75),
  }
  # assumes these axes are inverted and figure it out
  ylim_max = 2*np.max([a0.get_ylim()[1], a1.get_ylim()[1]]) + 1
  # set the ylims here
  a0.set_ylim((0, ylim_max))
  a1.set_ylim((0, ylim_max))
  a0.set_xlim(xlim)
  a1.set_xlim(xlim)
  a1.invert_yaxis()
  return hists

def pinput_hist_onesided(a0, s_list, n_bins):
  hists = {
    'prox': a0.hist(s_list, n_bins, color='k', label='Proximal input', alpha=0.75),
  }
  return hists

if __name__ == '__main__':
  pass
