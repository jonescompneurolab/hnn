# feed.py - establishes FeedExt(), ParFeedAll()
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: updated for python3)
# last major: (SL: toward python3)

import numpy as np
import itertools as it
from neuron import h

create_evoked_call = 0

class ParFeedAll ():
  # p_ext has a different structure for the extinput
  # usually, p_ext is a dict of cell types
  def __init__ (self, type, celltype, p_ext, gid):
    #print("ParFeedAll __init__")
    # VecStim setup
    self.eventvec = h.Vector()
    self.vs = h.VecStim()
    # self.p_unique = p_unique[type]
    self.p_ext = p_ext
    self.celltype = celltype
    self.set_prng(type) # sets seeds for random num generator
    self.set_event_times(type) # sets event times into self.eventvec and plays into self.vs (VecStim)

  def set_prng (self, type, seed = None):
    if seed is None: # no seed specified then use p_ext to determine seed
      # random generator for this instance
      # qnd hack to make the seeds the same across all gids
      # for just evoked
      if type.startswith(('evprox', 'evdist')):
        self.seed = self.p_ext['prng_seedcore']
        self.prng = np.random.RandomState(self.seed)
        print('type,seed:',type,self.seed)
      else:
        self.seed = self.p_ext['prng_seedcore'] + gid
        self.prng = np.random.RandomState(self.seed)    
        print('type,seed:',type,self.seed)
      # print('self.p_ext:',self.p_ext)
    else: # if seed explicitly specified use it
      self.seed = seed
      self.prng = np.random.RandomState(self.seed)

  def set_event_times (self,type):
    # print('self.p_ext:',self.p_ext)
    # each of these methods creates self.eventvec for playback
    if type == 'extpois':
      self.__create_extpois()
    elif type.startswith(('evprox', 'evdist')):
      self.__create_evoked()
    elif type == 'extgauss':
      self.__create_extgauss()
    elif type == 'extinput':
      self.__create_extinput()
    # load eventvec into VecStim object
    self.vs.play(self.eventvec)

  # based on cdf for exp wait time distribution from unif [0, 1)
  # returns in ms based on lamtha in Hz
  def __t_wait (self, lamtha):
    return -1000. * np.log(1. - self.prng.rand()) / lamtha

  # new external pois designation
  def __create_extpois (self):
    #print("__create_extpois")
    # check the t interval
    t0 = self.p_ext['t_interval'][0]
    T = self.p_ext['t_interval'][1]
    lamtha = self.p_ext[self.celltype][2]
    # values MUST be sorted for VecStim()!
    # start the initial value
    if lamtha > 0.:
      t_gen = t0 + self.__t_wait(lamtha)
      val_pois = np.array([])
      if t_gen < T: np.append(val_pois, t_gen)
      # vals are guaranteed to be monotonically increasing, no need to sort
      while t_gen < T:
        # so as to not clobber confusingly base off of t_gen ...
        t_gen += self.__t_wait(lamtha)
        if t_gen < T: val_pois = np.append(val_pois, t_gen)
    else:
      val_pois = np.array([])
    # checks the distribution stats
    # if len(val_pois):
    #     xdiff = np.diff(val_pois/1000)
    #     print(lamtha, np.mean(xdiff), np.var(xdiff), 1/lamtha**2)
    # Convert array into nrn vector
    self.eventvec.from_python(val_pois)

  # mu and sigma vals come from p
  def __create_evoked (self):
    global create_evoked_call
    # print("__create_evoked",create_evoked_call)
    create_evoked_call += 1
    if self.celltype in self.p_ext.keys():
      # assign the params
      mu = self.p_ext['t0']
      sigma = self.p_ext[self.celltype][2]
      # if a non-zero sigma is specified
      if sigma:
        val_evoked = self.prng.normal(mu, sigma, 1)
      else:
        # if sigma is specified at 0
        val_evoked = np.array([mu])
      val_evoked = val_evoked[val_evoked > 0]
      # vals must be sorted
      val_evoked.sort()
      print("__create_evoked",create_evoked_call,'val_evoked:',val_evoked)
      self.eventvec.from_python(val_evoked)
    else:
      # return an empty eventvec list
      self.eventvec.from_python([])

  def __create_extgauss (self):
    # print("__create_extgauss")
    # assign the params
    mu = self.p_ext[self.celltype][2]
    sigma = self.p_ext[self.celltype][3]
    # mu and sigma values come from p
    # one single value from Gaussian dist.
    # values MUST be sorted for VecStim()!
    val_gauss = self.prng.normal(mu, sigma, 50)
    # val_gauss = np.random.normal(mu, sigma, 50)
    # remove non-zero values brute force-ly
    val_gauss = val_gauss[val_gauss > 0]
    # sort values - critical for nrn
    val_gauss.sort()
    # print('val_gauss:',val_gauss)
    # Convert array into nrn vector
    self.eventvec.from_python(val_gauss)

  def __create_extinput (self):
    #print("__create_extinput")
    # store f_input as self variable for later use if it exists in p
    # t0 is always defined
    t0 = self.p_ext['t0']
    # If t0 is -1, randomize start time of inputs
    if t0 == -1: t0 = self.prng.uniform(25., 125.)
    f_input = self.p_ext['f_input']
    stdev = self.p_ext['stdev']
    events_per_cycle = self.p_ext['events_per_cycle']
    distribution = self.p_ext['distribution']
    # events_per_cycle = 1
    if events_per_cycle > 2 or events_per_cycle <= 0:
      print("events_per_cycle should be either 1 or 2, trying 2")
      events_per_cycle = 2
    # If frequency is 0, create empty vector if input times
    if not f_input:
      t_input = []
    elif distribution == 'normal':
      # array of mean stimulus times, starts at t0
      isi_array = np.arange(t0, self.p_ext['tstop'], 1000. / f_input)
      # array of single stimulus times -- no doublets
      if stdev:
        t_array = self.prng.normal(np.repeat(isi_array, 10), stdev)
      else:
        t_array = isi_array
      if events_per_cycle == 2:
        # Two arrays store doublet times
        t_array_low = t_array - 5
        t_array_high = t_array + 5
        # Array with ALL stimulus times for input
        # np.append concatenates two np arrays
        t_input = np.append(t_array_low, t_array_high)
      elif events_per_cycle == 1:
        t_input = t_array
      # brute force remove non-zero times. Might result in fewer vals than desired
      t_input = t_input[t_input > 0]
      t_input.sort()
    # Uniform Distribution
    elif distribution == 'uniform':
      n_inputs = 10. * f_input * (self.p_ext['tstop'] - t0) / 1000.
      t_array = self.prng.uniform(t0, self.p_ext['tstop'], n_inputs)
      if events_per_cycle == 2:
        # Two arrays store doublet times
        t_input_low = t_array - 5
        t_input_high = t_array + 5
        # Array with ALL stimulus times for input
        # np.append concatenates two np arrays
        t_input = np.append(t_input_low, t_input_high)
      elif events_per_cycle == 1:
        t_input = t_array
      # brute force remove non-zero times. Might result in fewer vals than desired
      t_input = t_input[t_input > 0]
      t_input.sort()
    else:
      print("Indicated distribution not recognized. Not making any alpha feeds.")
      t_input = []
    # Convert array into nrn vector
    self.eventvec.from_python(t_input)

  # for parallel, maybe be that postsyn for this is just nil (None)
  def connect_to_target (self):
    #print("connect_to_target")
    nc = h.NetCon(self.vs, None) # why is target always nil??
    nc.threshold = 0
    return nc
