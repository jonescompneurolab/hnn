# feed.py - establishes FeedExt(), ParFeedAll()
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: updated for python3)
# last major: (SL: toward python3)

import numpy as np
import itertools as it # this used?
from neuron import h

class ParFeedAll ():
  # p_ext has a different structure for the extinput
  # usually, p_ext is a dict of cell types
  def __init__ (self, ty, celltype, p_ext, gid):
    #print("ParFeedAll __init__")
    # VecStim setup
    self.eventvec = h.Vector()
    self.vs = h.VecStim()
    # self.p_unique = p_unique[type]
    self.p_ext = p_ext
    self.celltype = celltype
    self.ty = ty # feed type
    self.gid = gid
    self.set_prng() # sets seeds for random num generator
    self.set_event_times() # sets event times into self.eventvec and plays into self.vs (VecStim)

  # inc random number generator seeds
  def inc_prng (self, inc):
    self.seed += inc
    self.prng = np.random.RandomState(self.seed)
    if hasattr(self,'seed2'):
      self.seed2 += inc
      self.prng2 = np.random.RandomState(self.seed2)

  def set_prng (self, seed = None):
    if seed is None: # no seed specified then use p_ext to determine seed
      # random generator for this instance
      # qnd hack to make the seeds the same across all gids
      # for just evoked
      if self.ty.startswith(('evprox', 'evdist')):
        if self.p_ext['sync_evinput']:
          self.seed = self.p_ext['prng_seedcore']
        else:
          self.seed = self.p_ext['prng_seedcore'] + self.gid
      elif self.ty.startswith('extinput'):
        self.seed = self.p_ext['prng_seedcore'] + self.gid # seed for events assuming a given start time
        self.seed2  = self.p_ext['prng_seedcore'] # separate seed for start times
      else:
        self.seed = self.p_ext['prng_seedcore'] + self.gid
    else: # if seed explicitly specified use it
      self.seed = seed
      if hasattr(self,'seed2'): self.seed2 = seed
    self.prng = np.random.RandomState(self.seed)
    if hasattr(self,'seed2'): self.prng2 = np.random.RandomState(self.seed2)
    #print('ty,seed:',self.ty,self.seed)

  def set_event_times (self, inc_evinput = 0.0):
    # print('self.p_ext:',self.p_ext)
    # each of these methods creates self.eventvec for playback
    if self.ty == 'extpois':
      self.__create_extpois()
    elif self.ty.startswith(('evprox', 'evdist')):
      self.__create_evoked(inc_evinput)
    elif self.ty == 'extgauss':
      self.__create_extgauss()
    elif self.ty == 'extinput':
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
    if self.p_ext[self.celltype][0] <= 0.0 and \
       self.p_ext[self.celltype][1] <= 0.0: return False # 0 ampa and 0 nmda weight
    # check the t interval
    t0 = self.p_ext['t_interval'][0]
    T = self.p_ext['t_interval'][1]
    lamtha = self.p_ext[self.celltype][3] # index 3 is frequency (lamtha)
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
    # if len(val_pois)>0: print('val_pois:',val_pois)
    self.eventvec.from_python(val_pois)
    return self.eventvec.size() > 0

  # mu and sigma vals come from p
  def __create_evoked (self, inc=0.0):
    #print("__create_evoked", self.p_ext)
    if self.celltype in self.p_ext.keys():
      # assign the params
      mu = self.p_ext['t0'] + inc
      sigma = self.p_ext[self.celltype][3] # index 3 is sigma_t_ (stdev)
      numspikes = int(self.p_ext['numspikes'])
      # print('mu:',mu,'sigma:',sigma,'inc:',inc)
      # if a non-zero sigma is specified
      if sigma:
        val_evoked = self.prng.normal(mu, sigma, numspikes)
      else:
        # if sigma is specified at 0
        val_evoked = np.array([mu] * numspikes)
      val_evoked = val_evoked[val_evoked > 0]
      # vals must be sorted
      val_evoked.sort()
      # print('__create_evoked val_evoked:',val_evoked)
      self.eventvec.from_python(val_evoked)
    else:
      # return an empty eventvec list
      self.eventvec.from_python([])
    return self.eventvec.size() > 0

  def __create_extgauss (self):
    # print("__create_extgauss")
    # assign the params
    if self.p_ext[self.celltype][0] <= 0.0 and \
       self.p_ext[self.celltype][1] <= 0.0: return False # 0 ampa and 0 nmda weight
    # print('gauss params:',self.p_ext[self.celltype])
    mu = self.p_ext[self.celltype][3]
    sigma = self.p_ext[self.celltype][4]
    # mu and sigma values come from p
    # one single value from Gaussian dist.
    # values MUST be sorted for VecStim()!
    val_gauss = self.prng.normal(mu, sigma, 50)
    # val_gauss = np.random.normal(mu, sigma, 50)
    # remove non-zero values brute force-ly
    val_gauss = val_gauss[val_gauss > 0]
    # sort values - critical for nrn
    val_gauss.sort()
    # if len(val_gauss)>0: print('val_gauss:',val_gauss)
    # Convert array into nrn vector
    self.eventvec.from_python(val_gauss)
    return self.eventvec.size() > 0

  def __create_extinput (self): # creates the ongoing external inputs (rhythmic)
    #print("__create_extinput")
    # store f_input as self variable for later use if it exists in p
    # t0 is always defined
    t0 = self.p_ext['t0']
    # If t0 is -1, randomize start time of inputs
    if t0 == -1:
      t0 = self.prng.uniform(25., 125.)
      #print(self.ty,'t0 was -1; now', t0,'seed:',self.seed)
    elif self.p_ext['t0_stdev'] > 0.0: # randomize start time based on t0_stdev
      t0 = self.prng2.normal(t0, self.p_ext['t0_stdev']) # start time uses different prng
      #print(self.ty,'t0 is', t0, 'seed:',self.seed,'seed2:',self.seed2)
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
        t_array = self.prng.normal(np.repeat(isi_array, self.p_ext['repeats']), stdev)        
      else:
        t_array = isi_array
      if events_per_cycle == 2: # spikes/burst in GUI
        # Two arrays store doublet times
        t_array_low = t_array - 5
        t_array_high = t_array + 5
        # Array with ALL stimulus times for input
        # np.append concatenates two np arrays
        t_input = np.append(t_array_low, t_array_high)
      elif events_per_cycle == 1:
        t_input = t_array
      # brute force remove zero times. Might result in fewer vals than desired
      t_input = t_input[t_input > 0]
      t_input.sort()
    # Uniform Distribution
    elif distribution == 'uniform':
      n_inputs = self.p_ext['repeats'] * f_input * (self.p_ext['tstop'] - t0) / 1000.
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
    return self.eventvec.size() > 0

  # for parallel, maybe be that postsyn for this is just nil (None)
  def connect_to_target (self, threshold):
    #print("connect_to_target")
    nc = h.NetCon(self.vs, None) # why is target always nil??
    nc.threshold = threshold
    return nc
