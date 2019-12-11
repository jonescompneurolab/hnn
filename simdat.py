import os
from PyQt5.QtWidgets import QMenu, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
from math import ceil
from conf import dconf
import conf
import spikefn
from paramrw import usingOngoingInputs, usingEvokedInputs, usingPoissonInputs, usingTonicInputs, find_param, quickgetprm, countEvokedInputs, ExpParams
from scipy import signal
from gutils import getscreengeom

# dconf has settings from hnn.cfg
if dconf['fontsize'] > 0: plt.rcParams['font.size'] = dconf['fontsize']
else: plt.rcParams['font.size'] = dconf['fontsize'] = 10

debug = dconf['debug']

ddat = {} # current simulation data
dfile = {} # data file information for current simulation

lsimdat = [] # list of simulation data
lsimidx = 0 # index into lsimdat

initial_ddat = {}
optdat = [] # list of optimization data

def updatelsimdat(paramf,dpl):
  # update lsimdat with paramf and dipole dpl
  # but if the specific sim already run put dipole at that location in list
  global lsimdat,lsimidx
  # while len(lsimdat)>0 and lsimidx!=len(lsimdat)-1: lsimdat.pop() # redos popped
  found = False
  for i,l in enumerate(lsimdat):
    if l[0] == paramf:
      lsimdat[i][1] = dpl
      found = True
      break
  if not found: lsimdat.append([paramf,dpl]) # if not found, append to end of the list
  lsimidx = len(lsimdat) - 1 # current simulation index


def updateoptdat(paramf,dpl):
  global optdat

  optdat.append([paramf,dpl])

def rmse (a1, a2):
  # return root mean squared error between a1, a2; assumes same lengths, sampling rates
  len1,len2 = len(a1),len(a2)
  sz = min(len1,len2)
  if debug: print('len1:',len1,'len2:',len2,'ty1:',type(a1),'ty2:',type(a2))
  return np.sqrt(((a1[0:sz] - a2[0:sz]) ** 2).mean())

def readdpltrials (basedir,ntrial):
  # read dipole data files for individual trials
  if debug: print('in readdpltrials',basedir,ntrial)
  ldpl = []
  for i in range(ntrial):
    fn = os.path.join(basedir,'dpl_'+str(i)+'.txt')
    if not os.path.exists(fn): break
    ldpl.append(readtxt(fn))
    if debug: print('loaded ', fn)

  if len(ldpl) < ntrial and ntrial > 1:
    print("Warning: only read data for %d trials" % len(ldpl))

  return ldpl

def getinputfiles (paramf):
  # get a dictionary of input files based on simulation parameter file paramf
  global dfile,basedir
  dfile = {}
  basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
  # print('basedir:',basedir)
  dfile['dpl'] = os.path.join(basedir,'dpl.txt')
  dfile['spec'] = os.path.join(basedir,'rawspec.npz')
  dfile['spk'] = os.path.join(basedir,'spk.txt')
  dfile['outparam'] = os.path.join(basedir,'param.txt')
  return dfile

def readtxt (fn, silent=False):
  contents = []

  try:
    contents = np.loadtxt(fn)
  except OSError:
    if not silent:
      print('Warning: could not read file:', fn)
  except ValueError:
    if not silent:
      print('Warning: error reading data from:', fn)

  return contents

def updatedat (paramf):
  # update data dictionary (ddat) from the param file

  global basedir
  if debug: print('paramf:',paramf)
  getinputfiles(paramf)

  for k in ['dpl','spk']:
    if k in ddat:
      del ddat[k]
    silent = not os.path.exists(basedir)
    ddat[k] = readtxt(dfile[k], silent)
    if len(ddat[k]) == 0:
      del ddat[k]

  if not 'dpl' in ddat or not 'spk' in ddat:
    raise ValueError

  ddat['dpltrials'] = readdpltrials(basedir,quickgetprm(paramf,'N_trials',int))

  if os.path.isfile(dfile['spec']):
    ddat['spec'] = np.load(dfile['spec'])
  else:
    ddat['spec'] = None

def getscalefctr (paramf):
  # get dipole scaling factor parameter value from paramf file
  try:
    xx = quickgetprm(paramf,'dipole_scalefctr',float)
    if type(xx) == float: return xx
  except:
    pass
  if 'dipole_scalefctr' in dconf:
    return dconf['dipole_scalefctr']
  return 30e3

def drawraster ():
  # draw raster to standalone matplotlib figure - for debugging (not used in main HNN GUI)
  if 'spk' in ddat:
    # print('spk shape:',ddat['spk'].shape)
    plt.ion()
    plt.figure()
    for pair in ddat['spk']:
      plt.plot([pair[0]],[pair[1]],'ko',markersize=10)
    plt.xlabel('Time (ms)',fontsize=dconf['fontsize']); plt.ylabel('ID',fontsize=dconf['fontsize'])

def calcerr (ddat, tstop, tstart=0.0):
  # calculates RMSE error from ddat dictionary
  NSig = errtot = 0.0; lerr = []
  ddat['errtot']=None; ddat['lerr']=None
  for fn,dat in ddat['dextdata'].items():
    shp = dat.shape

    exp_times = dat[:,0]
    sim_times = ddat['dpl'][:,0]

    # do tstart and tstop fall within both datasets?
    # if not, use the closest data point as the new tstop/tstart
    for tseries in [exp_times, sim_times]:
      if tstart <  tseries[0]:
        tstart = tseries[0]
      if tstop >  tseries[-1]:
        tstop = tseries[-1]

    # make sure start and end times are valid for both dipoles
    exp_start_index = (np.abs(exp_times - tstart)).argmin()
    exp_end_index = (np.abs(exp_times - tstop)).argmin()
    exp_length = exp_end_index - exp_start_index

    sim_start_index = (np.abs(sim_times - tstart)).argmin()
    sim_end_index = (np.abs(sim_times - tstop)).argmin()
    sim_length = sim_end_index - sim_start_index

    for c in range(1,shp[1],1):
      dpl1 = ddat['dpl'][sim_start_index:sim_end_index,1]
      dpl2 = dat[exp_start_index:exp_end_index,c]

      if (sim_length > exp_length):
          # downsample simulation timeseries to match exp data
          dpl1 = signal.resample(dpl1, exp_length)
      elif (sim_length < exp_length):
          # downsample exp timeseries to match simulation data
          dpl2 = signal.resample(dpl2, sim_length)
      err0 = np.sqrt(((dpl1 - dpl2) ** 2).mean())
      lerr.append(err0)
      errtot += err0
      #print('RMSE: ',err0)
      NSig += 1
  if not NSig == 0.0:
    errtot /= NSig
  #print('Avg. RMSE:' + str(round(errtot,2)))
  ddat['errtot'] = errtot
  ddat['lerr'] = lerr
  return lerr, errtot

def weighted_rmse(ddat, tstop, weights, tstart=0.0):
  from numpy import sqrt
  from scipy import signal

  # calculates RMSE error from ddat dictionary
  NSig = errtot = 0.0; lerr = []
  ddat['werrtot']=None; ddat['lerr']=None
  for fn,dat in ddat['dextdata'].items():
    shp = dat.shape
    exp_times = dat[:,0]
    sim_times = ddat['dpl'][:,0]

    # do tstart and tstop fall within both datasets?
    # if not, use the closest data point as the new tstop/tstart
    for tseries in [exp_times, sim_times]:
      if tstart <  tseries[0]:
        tstart = tseries[0]
      if tstop >  tseries[-1]:
        tstop = tseries[-1]

    # make sure start and end times are valid for both dipoles
    exp_start_index = (np.abs(exp_times - tstart)).argmin()
    exp_end_index = (np.abs(exp_times - tstop)).argmin()
    exp_length = exp_end_index - exp_start_index

    sim_start_index = (np.abs(sim_times - tstart)).argmin()
    sim_end_index = (np.abs(sim_times - tstop)).argmin()
    sim_length = sim_end_index - sim_start_index

    weight = weights[sim_start_index:sim_end_index]

    for c in range(1,shp[1],1):
      dpl1 = ddat['dpl'][sim_start_index:sim_end_index,1]
      dpl2 = dat[exp_start_index:exp_end_index,c]

      if (sim_length > exp_length):
          # downsample simulation timeseries to match exp data
          dpl1 = signal.resample(dpl1, exp_length)
          weight = signal.resample(weight, exp_length)
          indices = np.where(weight < 1e-4)
          weight[indices] = 0
      elif (sim_length < exp_length):
          # downsample exp timeseries to match simulation data
          dpl2 = signal.resample(dpl2, sim_length)

      err0 = np.sqrt((weight * ((dpl1 - dpl2) ** 2)).sum()/weight.sum())
      lerr.append(err0)
      errtot += err0
      #print('RMSE: ',err0)
      NSig += 1
  errtot /= NSig
  #print('Avg. RMSE:' + str(round(errtot,2)))
  ddat['werrtot'] = errtot
  ddat['wlerr'] = lerr
  return lerr, errtot


class SIMCanvas (FigureCanvas):
  # matplotlib/pyqt-compatible canvas for drawing simulation & external data
  # based on https://pythonspot.com/en/pyqt5-matplotlib/

  def __init__ (self, paramf, parent=None, width=5, height=4, dpi=40, optMode=False, title='Simulation Viewer'):
    FigureCanvas.__init__(self, Figure(figsize=(width, height), dpi=dpi))

    self.title = title
    self.lextdatobj = [] # external data object
    self.clridx = 5 # index for next color for drawing external data
    self.lpatch = [mpatches.Patch(color='black', label='Sim.')] # legend for dipole signals
    self.setParent(parent)
    self.gui = parent
    FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
    FigureCanvas.updateGeometry(self)
    self.paramf = paramf
    self.initaxes()
    self.G = gridspec.GridSpec(10,1)

    global initial_ddat, optdat
    self.optMode = optMode
    if not optMode:
      initial_ddat = {}
      optdat = []
    self.plot()

  def initaxes (self):
    # initialize the axes
    self.axdist = self.axprox = self.axdipole = self.axspec = self.axpois = None

  def plotinputhist (self, xl, dinty):
    """ plot input histograms
        xl = x axis limits
        dinty = dict of input types used, determines how many/which axes created/displayed
    """

    extinputs = None
    plot_distribs = False

    sim_tstop = quickgetprm(self.paramf,'tstop',float)
    sim_dt = quickgetprm(self.paramf,'dt',float)
    num_step = ceil(sim_tstop / sim_dt) + 1
    times = np.linspace(0, sim_tstop, num_step)

    try:
      extinputs = spikefn.ExtInputs(dfile['spk'], dfile['outparam'])
      extinputs.add_delay_times()
      dinput = extinputs.inputs
    except ValueError:
      dinput = self.getInputDistrib()
      plot_distribs = True

    if len(dinput['dist']) <= 0 and len(dinput['prox']) <= 0 and \
        len(dinput['evdist']) <= 0 and len(dinput['evprox']) <= 0 and \
        len(dinput['pois']) <= 0:
      if debug: print('all hists 0!')
      return False

    self.hist=hist={x:None for x in ['feed_dist','feed_prox','feed_evdist','feed_evprox','feed_pois']}

    hasPois = len(dinput['pois']) > 0 and dinty['Poisson'] # this ensures synaptic weight > 0

    gRow = 0
    self.axdist = self.axprox = self.axpois = None # axis objects

    # check poisson inputs, create subplot
    if hasPois:
      self.axpois = self.figure.add_subplot(self.G[gRow,0])
      gRow += 1

    # check distal inputs, create subplot
    if (len(dinput['dist']) > 0 and dinty['OngoingDist']) or \
       (len(dinput['evdist']) > 0 and dinty['EvokedDist']):
      self.axdist = self.figure.add_subplot(self.G[gRow,0])
      gRow+=1

    # check proximal inputs, create subplot
    if (len(dinput['prox']) > 0 and dinty['OngoingProx']) or \
       (len(dinput['evprox']) > 0 and dinty['EvokedProx']):
      self.axprox = self.figure.add_subplot(self.G[gRow,0])
      gRow+=1


    # check input types provided in simulation
    if extinputs is not None and self.hassimdata(): # only valid param.txt file after sim was run
      if debug:
        print(len(dinput['dist']),len(dinput['prox']),len(dinput['evdist']),len(dinput['evprox']),len(dinput['pois']))

      if hasPois: # any Poisson inputs?
        extinputs.plot_hist(self.axpois,'pois',times,'auto',xl,color='k',hty='step',lw=self.gui.linewidth+1)

      if len(dinput['dist']) > 0 and dinty['OngoingDist']: # dinty condition ensures synaptic weight > 0
        extinputs.plot_hist(self.axdist,'dist',times,'auto',xl,color='g',lw=self.gui.linewidth+1)

      if len(dinput['prox']) > 0 and dinty['OngoingProx']: # dinty condition ensures synaptic weight > 0
        extinputs.plot_hist(self.axprox,'prox',times,'auto',xl,color='r',lw=self.gui.linewidth+1)

      if len(dinput['evdist']) > 0 and dinty['EvokedDist']: # dinty condition ensures synaptic weight > 0
        extinputs.plot_hist(self.axdist,'evdist',times,'auto',xl,color='g',hty='step',lw=self.gui.linewidth+1)

      if len(dinput['evprox']) > 0 and dinty['EvokedProx']: # dinty condition ensures synaptic weight > 0
        extinputs.plot_hist(self.axprox,'evprox',times,'auto',xl,color='r',hty='step',lw=self.gui.linewidth+1)
    elif plot_distribs:
      if len(dinput['evprox']) > 0 and dinty['EvokedProx']: # dinty condition ensures synaptic weight > 0
        prox_tot = np.zeros(len(dinput['evprox'][0][0]))
        for prox in dinput['evprox']:
          prox_tot += prox[1]
        plot = self.axprox.plot(dinput['evprox'][0][0],prox_tot,color='r',lw=self.gui.linewidth,label='evprox distribution')
        self.axprox.set_xlim(dinput['evprox'][0][0][0],dinput['evprox'][0][0][-1])
      if len(dinput['evdist']) > 0 and dinty['EvokedDist']: # dinty condition ensures synaptic weight > 0
        dist_tot = np.zeros(len(dinput['evdist'][0][0]))
        for dist in dinput['evdist']:
          dist_tot += dist[1]
        plot = self.axdist.plot(dinput['evdist'][0][0],dist_tot,color='g',lw=self.gui.linewidth,label='evdist distribution')
        self.axprox.set_xlim(dinput['evdist'][0][0][0],dinput['evdist'][0][0][-1])

    ymax = 0
    for ax in [self.axpois, self.axdist, self.axprox]:
      if not ax is None:
        if ax.get_ylim()[1] > ymax:
          ymax = ax.get_ylim()[1]

    if ymax == 0:
      if debug: print('all hists None!')
      return False
    else:
      for ax in [self.axpois, self.axdist, self.axprox]:
        if not ax is None:
          ax.set_ylim(0,ymax)
      if self.axdist:
        self.axdist.invert_yaxis()
      for ax in [self.axpois,self.axdist,self.axprox]:
        if ax:
          ax.set_xlim(xl)
          ax.legend(loc=1)  # legend in upper right
      return True,gRow

  def clearaxes (self):
    # clear the figures axes
    for ax in self.figure.get_axes():
      if ax:
        ax.cla()


  def getNTrials (self):
    # get the number of trials
    N_trials = 1
    try:
      xx = quickgetprm(self.paramf,'N_trials',int)
      if type(xx) == int: N_trials = xx
    except:
      pass
    return N_trials

  def getNPyr (self):
    # get the number of pyramidal neurons used in the simulation
    try:
      x = quickgetprm(self.paramf,'N_pyr_x',int)
      y = quickgetprm(self.paramf,'N_pyr_y',int)
      if type(x)==int and type(y)==int:
        return int(x * y * 2)
    except:
      return 0

  def getInputDistrib (self):
    import scipy.stats as stats

    dinput = {'evprox': [], 'evdist': [], 'prox': [], 'dist': [], 'pois': []}
    try:
      sim_tstop = quickgetprm(self.paramf,'tstop',float)
      sim_dt = quickgetprm(self.paramf,'dt',float)
    except FileNotFoundError:
      return dinput

    num_step = ceil(sim_tstop / sim_dt) + 1
    times = np.linspace(0, sim_tstop, num_step)
    ltprox, ltdist = self.getEVInputTimes()
    for prox in ltprox:
      pdf = stats.norm.pdf(times, prox[0], prox[1])
      dinput['evprox'].append((times,pdf))
    for dist in ltdist:
      pdf = stats.norm.pdf(times, dist[0], dist[1])
      dinput['evdist'].append((times,pdf))
    return dinput

  def getEVInputTimes (self):
    # get the evoked input times
    nprox, ndist = countEvokedInputs(self.paramf)
    ltprox, ltdist = [], []
    for i in range(nprox):
      input_mu = quickgetprm(self.paramf,'t_evprox_' + str(i+1), float)
      input_sigma = quickgetprm(self.paramf,'sigma_t_evprox_' + str(i+1), float)
      ltprox.append((input_mu, input_sigma))
    for i in range(ndist):
      input_mu = quickgetprm(self.paramf,'t_evdist_' + str(i+1), float)
      input_sigma = quickgetprm(self.paramf,'sigma_t_evdist_' + str(i+1), float)
      ltdist.append((input_mu, input_sigma))
    return ltprox, ltdist

  def drawEVInputTimes (self, ax, yl, h=0.1, hw=15, hl=15):
    # draw the evoked input times using arrows
    ltprox, ltdist = self.getEVInputTimes()
    yrange = abs(yl[1] - yl[0])
    #print('drawEVInputTimes:',yl,yrange,h,hw,hl,h*yrange,-h*yrange,yl[0]+h*yrange,yl[1]-h*yrange)
    for tt in ltprox: ax.arrow(tt[0],yl[0],0,h*yrange,fc='r',ec='r', head_width=hw,head_length=hl)#head_length=w,head_width=1.)#w/4)#length_includes_head=True,
    for tt in ltdist: ax.arrow(tt[0],yl[1],0,-h*yrange,fc='g',ec='g',head_width=hw,head_length=hl)#head_length=w,head_width=1.)#w/4)

  def getInputs (self):
    """ get a dictionary of input types used in simulation
        with distal/proximal specificity for evoked,ongoing inputs
    """

    dinty = {'Evoked':False,'Ongoing':False,'Poisson':False,'Tonic':False,'EvokedDist':False,\
             'EvokedProx':False,'OngoingDist':False,'OngoingProx':False}

    try:
      dinty['Evoked'] = usingEvokedInputs(self.paramf)
      dinty['EvokedDist'] = usingEvokedInputs(self.paramf, lsuffty = ['_evdist_'])
      dinty['EvokedProx'] = usingEvokedInputs(self.paramf, lsuffty = ['_evprox_'])
      dinty['Ongoing'] = usingOngoingInputs(self.paramf)
      dinty['OngoingDist'] = usingOngoingInputs(self.paramf, lty = ['_dist'])
      dinty['OngoingProx'] = usingOngoingInputs(self.paramf, lty = ['_prox'])
      dinty['Poisson'] = usingPoissonInputs(self.paramf)
      dinty['Tonic'] = usingTonicInputs(self.paramf)
    except FileNotFoundError:
      pass

    return dinty

  def getnextcolor (self):
    # get next color for external data (colors selected in order)
    self.clridx += 5
    if self.clridx > 100: self.clridx = 5
    return self.clridx

  def plotextdat (self, recalcErr=True):
    if not 'dextdata' in ddat or len(ddat['dextdata']) == 0:
      return

    lerr = None
    errtot = None
    initial_err = None
    # plot 'external' data (e.g. from experiment/other simulation)
    hassimdata = self.hassimdata() # has the simulation been run yet?
    if hassimdata:
      if recalcErr:
        calcerr(ddat, ddat['dpl'][-1,0]) # recalculate/save the error?

      try:
        lerr, errtot = ddat['lerr'], ddat['errtot']

        if self.optMode:
          initial_err = initial_ddat['errtot']
      except KeyError:
        pass


    if self.axdipole is None:
      self.axdipole = self.figure.add_subplot(self.G[0:-1,0]) # dipole
      xl = (0.0,1.0)
      yl = (-0.001,0.001)
    else:
      xl = self.axdipole.get_xlim()
      yl = self.axdipole.get_ylim()

    cmap=plt.get_cmap('nipy_spectral')
    csm = plt.cm.ScalarMappable(cmap=cmap);
    csm.set_clim((0,100))

    self.clearlextdatobj() # clear annotation objects

    ddx = 0
    for fn,dat in ddat['dextdata'].items():
      shp = dat.shape
      clr = csm.to_rgba(self.getnextcolor())
      c = min(shp[1],1)
      self.lextdatobj.append(self.axdipole.plot(dat[:,0],dat[:,c],color=clr,linewidth=self.gui.linewidth+1))
      xl = ((min(xl[0],min(dat[:,0]))),(max(xl[1],max(dat[:,0]))))
      yl = ((min(yl[0],min(dat[:,c]))),(max(yl[1],max(dat[:,c]))))
      fx = int(shp[0] * float(c) / shp[1])
      if lerr:
        tx,ty=dat[fx,0],dat[fx,c]
        txt='RMSE: %.2f' % round(lerr[ddx],2)
        if not self.optMode:
          self.lextdatobj.append(self.axdipole.annotate(txt,xy=(dat[0,0],dat[0,c]),xytext=(tx,ty),color=clr,fontweight='bold'))
      self.lpatch.append(mpatches.Patch(color=clr, label=fn.split(os.path.sep)[-1].split('.txt')[0]))
      ddx+=1

    self.axdipole.set_xlim(xl)
    self.axdipole.set_ylim(yl)

    if self.lextdatobj and self.lpatch:
      self.lextdatobj.append(self.axdipole.legend(handles=self.lpatch, loc=2))

    if errtot:
      tx,ty=0,0
      if self.optMode and initial_err:
        clr = 'black'
        txt='RMSE: %.2f' % round(initial_err,2)
        self.annot_avg = self.axdipole.annotate(txt,xy=(0,0),xytext=(0.005,0.005),textcoords='axes fraction',color=clr,fontweight='bold')
        clr = 'gray'
        txt='RMSE: %.2f' % round(errtot,2)
        self.annot_avg = self.axdipole.annotate(txt,xy=(0,0),xytext=(0.86,0.005),textcoords='axes fraction',color=clr,fontweight='bold')
      else:
        clr = 'black'
        txt='Avg. RMSE: %.2f' % round(errtot,2)
        self.annot_avg = self.axdipole.annotate(txt,xy=(0,0),xytext=(0.005,0.005),textcoords='axes fraction',color=clr,fontweight='bold')

    if not hassimdata: # need axis labels
      self.axdipole.set_xlabel('Time (ms)',fontsize=dconf['fontsize'])
      self.axdipole.set_ylabel('Dipole (nAm)',fontsize=dconf['fontsize'])
      myxl = self.axdipole.get_xlim()
      if myxl[0] < 0.0: self.axdipole.set_xlim((0.0,myxl[1]+myxl[0]))

  def hassimdata (self):
    # check if any simulation data available in ddat dictionary
    return 'dpl' in ddat

  def hasinitoptdata (self):
    # check if any simulation data available in ddat dictionary
    return 'dpl' in initial_ddat

  def clearlextdatobj (self):
    # clear list of external data objects
    for o in self.lextdatobj:
      try:
        o.set_visible(False)
      except:
        o[0].set_visible(False)
    del self.lextdatobj
    self.lextdatobj = [] # reset list of external data objects
    self.lpatch = [] # reset legend
    self.clridx = 5 # reset index for next color for drawing external data

    if self.optMode:
      self.lpatch.append(mpatches.Patch(color='grey', label='Optimization'))
      self.lpatch.append(mpatches.Patch(color='black', label='Initial'))
    elif self.hassimdata():
      self.lpatch.append(mpatches.Patch(color='black', label='Simulation'))
    if hasattr(self,'annot_avg'):
      self.annot_avg.set_visible(False)
      del self.annot_avg

  def plotsimdat (self):
    # plot the simulation data

    self.gRow = 0
    bottom = 0.0

    only_create_axes = False
    if not os.path.isfile(self.paramf):
      only_create_axes = True
      DrawSpec = False
      xl = (0.0, 1.0)
    else:
      # setup the figure axis for drawing the dipole signal
      dinty = self.getInputs()

      # try loading data. ignore failures
      try:
        updatedat(self.paramf)
        loaded_dat = True
      except ValueError:
        loaded_dat = False
        pass

      xl = (0.0, quickgetprm(self.paramf,'tstop',float))
      if dinty['Ongoing'] or dinty['Evoked'] or dinty['Poisson']:
        xo = self.plotinputhist(xl, dinty)
        if xo:
          self.gRow = xo[1]

      # whether to draw the specgram - should draw if user saved it or have ongoing, poisson, or tonic inputs
      DrawSpec = loaded_dat and \
                'spec' in ddat and \
                (find_param(dfile['outparam'],'save_spec_data') or dinty['Ongoing'] or dinty['Poisson'] or dinty['Tonic'])

    if DrawSpec: # dipole axis takes fewer rows if also drawing specgram
      self.axdipole = self.figure.add_subplot(self.G[self.gRow:5,0]) # dipole
      bottom = 0.08
    else:
      self.axdipole = self.figure.add_subplot(self.G[self.gRow:-1,0]) # dipole

    yl = (-0.001,0.001)
    self.axdipole.set_ylim(yl)
    self.axdipole.set_xlim(xl)

    left = 0.08
    w,h=getscreengeom()
    if w < 2800: left = 0.1
    self.figure.subplots_adjust(left=left,right=0.99,bottom=bottom,top=0.99,hspace=0.1,wspace=0.1) # reduce padding

    if only_create_axes:
      return

    try:
      updatedat(self.paramf)
    except ValueError:
      if 'dpl' not in ddat:
        # failed to load dipole data, nothing more to plot
        return

    ds = None
    xl = (0,ddat['dpl'][-1,0])
    dt = ddat['dpl'][1,0] - ddat['dpl'][0,0]

    # get spectrogram if it exists, then adjust axis limits but only if drawing spectrogram
    if DrawSpec:
      if ddat['spec'] is not None:
        ds = ddat['spec'] # spectrogram
        xl = (ds['time'][0],ds['time'][-1]) # use specgram time limits
      else:
        DrawSpec = False

    sampr = 1e3/dt # dipole sampling rate
    sidx, eidx = int(sampr*xl[0]/1e3), int(sampr*xl[1]/1e3) # use these indices to find dipole min,max

    N_trials = self.getNTrials()
    if debug: print('simdat: N_trials:',N_trials)

    yl = [0,0]
    yl[0] = min(yl[0],np.amin(ddat['dpl'][sidx:eidx,1]))
    yl[1] = max(yl[1],np.amax(ddat['dpl'][sidx:eidx,1]))

    if not self.optMode:
      # skip for optimization
      for lsim in lsimdat: # plot average dipoles from prior simulations
        olddpl = lsim[1]
        if debug: print('olddpl has shape ',olddpl.shape,len(olddpl[:,0]),len(olddpl[:,1]))
        self.axdipole.plot(olddpl[:,0],olddpl[:,1],'--',color='black',linewidth=self.gui.linewidth)

      if N_trials>1 and dconf['drawindivdpl'] and len(ddat['dpltrials']) > 0: # plot dipoles from individual trials
        for dpltrial in ddat['dpltrials']:
          self.axdipole.plot(dpltrial[:,0],dpltrial[:,1],color='gray',linewidth=self.gui.linewidth)
          yl[0] = min(yl[0],dpltrial[sidx:eidx,1].min())
          yl[1] = max(yl[1],dpltrial[sidx:eidx,1].max())

      if conf.dconf['drawavgdpl'] or N_trials <= 1:
        # this is the average dipole (across trials)
        # it's also the ONLY dipole when running a single trial
        self.axdipole.plot(ddat['dpl'][:,0],ddat['dpl'][:,1],'k',linewidth=self.gui.linewidth+1)
        yl[0] = min(yl[0],ddat['dpl'][sidx:eidx,1].min())
        yl[1] = max(yl[1],ddat['dpl'][sidx:eidx,1].max())
    else:
      for idx, opt in enumerate(optdat):
        optdpl = opt[1]
        if idx == len(optdat) - 1:
          # only show the last optimization
          self.axdipole.plot(optdpl[:,0],optdpl[:,1],'k',color='gray',linewidth=self.gui.linewidth+1)
          yl[0] = min(yl[0],optdpl[sidx:eidx,1].min())
          yl[1] = max(yl[1],optdpl[sidx:eidx,1].max())

      if self.hasinitoptdata():
        # show initial dipole in dotted black line
        self.axdipole.plot(initial_ddat['dpl'][:,0],initial_ddat['dpl'][:,1],'--',color='black',linewidth=self.gui.linewidth)
        yl[0] = min(yl[0],initial_ddat['dpl'][sidx:eidx,1].min())
        yl[1] = max(yl[1],initial_ddat['dpl'][sidx:eidx,1].max())

    scalefctr = getscalefctr(self.paramf)
    NEstPyr = int(self.getNPyr() * scalefctr)

    if NEstPyr > 0:
      self.axdipole.set_ylabel(r'Dipole (nAm $\times$ '+str(scalefctr)+')\nFrom Estimated '+str(NEstPyr)+' Cells',fontsize=dconf['fontsize'])
    else:
      self.axdipole.set_ylabel(r'Dipole (nAm $\times$ '+str(scalefctr)+')\n',fontsize=dconf['fontsize'])
    self.axdipole.set_xlim(xl); self.axdipole.set_ylim(yl)

    if DrawSpec: #
      if debug: print('ylim is : ', np.amin(ddat['dpl'][sidx:eidx,1]),np.amax(ddat['dpl'][sidx:eidx,1]))

      p_exp = ExpParams(self.paramf, debug=debug)
      if len(p_exp.expmt_groups) > 0:
        expmt_group = p_exp.expmt_groups[0]
      else:
        expmt_group = None
      p = p_exp.return_pdict(expmt_group, 0)

      gRow = 6
      self.axspec = self.figure.add_subplot(self.G[gRow:10,0]); # specgram
      cax = self.axspec.imshow(ds['TFR'],extent=(ds['time'][0],ds['time'][-1],ds['freq'][-1],ds['freq'][0]),aspect='auto',origin='upper',cmap=plt.get_cmap(p['spec_cmap']))
      self.axspec.set_ylabel('Frequency (Hz)',fontsize=dconf['fontsize'])
      self.axspec.set_xlabel('Time (ms)',fontsize=dconf['fontsize'])
      self.axspec.set_xlim(xl)
      self.axspec.set_ylim(ds['freq'][-1],ds['freq'][0])
      cbaxes = self.figure.add_axes([0.6, 0.49, 0.3, 0.005])
      cb = plt.colorbar(cax, cax = cbaxes, orientation='horizontal') # horizontal to save space
    else:
      self.axdipole.set_xlabel('Time (ms)',fontsize=dconf['fontsize'])

  def plotarrows (self):
    # run after scales have been updated
    xl = self.axdipole.get_xlim()
    yl = self.axdipole.get_ylim()

    dinty = self.getInputs()
    if dinty['Evoked']:
      self.drawEVInputTimes(self.axdipole,yl,0.1,(xl[1]-xl[0])*.02,(yl[1]-yl[0])*.02)#15.0)

  def plot (self, recalcErr=True):
    self.clearaxes()
    plt.close(self.figure)
    self.figure.clf()
    self.axdipole = None

    self.plotsimdat()  # creates self.axdipole
    self.plotextdat(recalcErr)
    self.plotarrows()

    self.draw()
