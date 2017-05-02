import os
from PyQt5.QtWidgets import QMenu, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from math import ceil
from conf import dconf
import spikefn

simf = dconf['simf']
paramf = dconf['paramf']

ddat = {}
dfile = {}

def getinputfiles (paramf):
  global dfile,basedir
  dfile = {}
  basedir = os.path.join('data',paramf.split(os.path.sep)[-1].split('.param')[0])
  dfile['dpl'] = os.path.join(basedir,'dpl.txt')
  dfile['spec'] = os.path.join(basedir,'rawspec.npz')
  dfile['spk'] = os.path.join(basedir,'spk.txt')
  dfile['outparam'] = os.path.join(basedir,'param.txt')
  return dfile

try:
  getinputfiles(paramf)
  ddat['dpl'] = np.loadtxt(dfile['dpl']);
  ddat['spec'] = np.load(dfile['spec']); 
  ddat['spk'] = np.loadtxt(dfile['spk']); 
except:
  print('exception in getting input files')

# based on https://pythonspot.com/en/pyqt5-matplotlib/
class SIMCanvas (FigureCanvas): 

  def __init__ (self, parent=None, width=5, height=4, dpi=100, title='Simulation Viewer'):
    FigureCanvas.__init__(self, Figure(figsize=(width, height), dpi=dpi))
    self.title = title
    self.setParent(parent)
    FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
    FigureCanvas.updateGeometry(self)
    self.invertedhistax = False
    self.G = gridspec.GridSpec(10,1)
    self.plot()

  def plotinputhist (self,xl): # plot input histograms
    xlim_new = (ddat['dpl'][0,0],ddat['dpl'][-1,0])
    # set number of bins (150 bins per 1000ms)
    bins = ceil(150. * (xlim_new[1] - xlim_new[0]) / 1000.) # bins needs to be an int
    extinputs = None
    try:
      # print('dfilespk:',dfile['spk'],'dfileoutparam',dfile['outparam'])
      extinputs = spikefn.ExtInputs(dfile['spk'], dfile['outparam'])
      extinputs.add_delay_times()
      if len(extinputs.inputs['dist']) <= 0 and len(extinputs.inputs['prox']) <= 0:
        return False
    except:
      print('problem with extinputs')
    self.hist = hist = {}
    self.axdist = axdist = self.figure.add_subplot(self.G[0,0]); # distal inputs
    self.axprox = axprox = self.figure.add_subplot(self.G[1,0]); # proximal inputs
    if extinputs is not None: # only valid param.txt file after sim was run
      hist['feed_dist'] = extinputs.plot_hist(axdist,'dist',ddat['dpl'][:,0],bins,xlim_new,color='r')
      hist['feed_prox'] = extinputs.plot_hist(axprox,'prox',ddat['dpl'][:,0],bins,xlim_new,color='g')
      if hist['feed_dist'] is None and hist['feed_prox'] is None:
        self.invertedhistax = False
        return False
      else:
        if not self.invertedhistax:# only need to invert axis 1X
          axdist.invert_yaxis()
          self.invertedhistax = True
        for ax in [axdist,axprox]:
          ax.set_xlim(xl)
          ax.legend()          
        return True

  def clearaxes (self):
    try:
      self.axdist.cla()
      self.axprox.cla()
      self.axdipole.cla()
      self.axspec.cla()
    except:
      pass

  def plotsimdat (self):
    self.clearaxes()
    plt.close(self.figure); # self.figure.clear(); 
    #print(dir(self.figure))
    #print(dir(self.figure.canvas))
    if len(ddat.keys()) == 0: return
    try:
      ds = ddat['spec'] # spectrogram
      xl = (ds['time'][0],ds['time'][-1]) # use specgram time limits
      gRow = 0
      if self.plotinputhist(xl): gRow = 2
      self.axdipole = ax = self.figure.add_subplot(self.G[gRow:5,0]); # dipole
      ax.plot(ddat['dpl'][:,0],ddat['dpl'][:,1],'b')
      ax.set_ylabel('dipole (nA m)')
      ax.set_xlim(xl)
      ax.set_ylim(np.amin(ddat['dpl'][1:,1]),np.amax(ddat['dpl'][1:,1])) # fix ylim
      # print('ylim is : ', np.amin(ddat['dpl'][:,1]),np.amax(ddat['dpl'][:,1]))
      gRow = 6
      self.axspec = ax = self.figure.add_subplot(self.G[gRow:10,0]); # specgram
      cax = ax.imshow(ds['TFR'],extent=(ds['time'][0],ds['time'][-1],ds['freq'][-1],ds['freq'][0]),aspect='auto',origin='upper',cmap=plt.get_cmap('jet'))
      ax.set_ylabel('Frequency (Hz)')
      ax.set_xlabel('Time (ms)')
      ax.set_xlim(xl)
      ax.set_ylim(ds['freq'][-1],ds['freq'][0])
      cbaxes = self.figure.add_axes([0.6, 0.49, 0.3, 0.005]) 
      cb = plt.colorbar(cax, cax = cbaxes, orientation='horizontal') # horizontal to save space
    except:
      print('ERR: in plotsimdat')
    self.figure.subplots_adjust(left=0.1,right=1.0-0.02,bottom=0.08,top=0.99) # reduce padding

  def plot (self):
    self.plotsimdat()
    self.draw()
