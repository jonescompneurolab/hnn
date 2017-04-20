import os
from PyQt5.QtWidgets import QMenu, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from math import ceil
from conf import readconf, setfcfg, fcfg, dconf
import spikefn
import params_default
from paramrw import quickreadprm

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

invertedhistax = False

def plotsimdat (figure,G,fig):
  global invertedhistax
  if len(ddat.keys()) == 0: return
  try:
    fig,ax = plt.subplots(); ax.cla()
    xlim_new = (ddat['dpl'][0,0],ddat['dpl'][-1,0])

    # set number of bins (150 bins per 1000ms)
    bins = ceil(150. * (xlim_new[1] - xlim_new[0]) / 1000.) # bins needs to be an int

    # plot histograms of inputs
    print(dfile['spk'],dfile['outparam'])
    extinputs = None

    try:
      extinputs = spikefn.ExtInputs(dfile['spk'], dfile['outparam'])
      extinputs.add_delay_times()
    except:
      print('problem with extinputs')

    gRow = 0

    hist = {}
    axdist = figure.add_subplot(G[gRow,0]); axdist.cla(); gRow+=1 # distal inputs
    axprox = figure.add_subplot(G[gRow,0]); axprox.cla(); gRow+=1 # proximal inputs
    if extinputs is not None: # only valid param.txt file after sim was run
      hist['feed_dist'] = extinputs.plot_hist(axdist,'dist',ddat['dpl'][:,0],bins,xlim_new,color='r')
      hist['feed_prox'] = extinputs.plot_hist(axprox,'prox',ddat['dpl'][:,0],bins,xlim_new,color='g')
      if not invertedhistax:# only need to invert axis 1X
        axdist.invert_yaxis()
        invertedhistax = True
      for ax in [axdist,axprox]:
        ax.set_xlim(xlim_new)
        ax.legend()          

    ds = ddat['spec'] # spectrogram

    ax = figure.add_subplot(G[gRow:5,0]); ax.cla() # dipole
    ax.plot(ddat['dpl'][:,0],ddat['dpl'][:,1],'b')
    ax.set_ylabel('dipole (nA m)')
    # ax.set_xlim(ddat['dpl'][0,0],ddat['dpl'][-1,0])
    ax.set_xlim(ds['time'][0],ds['time'][-1])
    ax.set_ylim(np.amin(ddat['dpl'][1:,1]),np.amax(ddat['dpl'][1:,1])) # right ylim??
    # print('ylim is : ', np.amin(ddat['dpl'][:,1]),np.amax(ddat['dpl'][:,1]))
    # truncate tvec and dpl data using logical indexing
    #t_range = dpl.t[(dpl.t >= xmin) & (dpl.t <= xmax)]
    #dpl_range = dpl.dpl['agg'][(dpl.t >= xmin) & (dpl.t <= xmax)]

    gRow = 6

    ax = figure.add_subplot(G[gRow:10,0]); ax.cla() # specgram
    cax = ax.imshow(ds['TFR'],extent=(ds['time'][0],ds['time'][-1],ds['freq'][-1],ds['freq'][0]),aspect='auto',origin='upper',cmap=plt.get_cmap('jet'))
    ax.set_ylabel('Frequency (Hz)')
    ax.set_xlabel('Time (ms)')
    ax.set_xlim(ds['time'][0],ds['time'][-1])
    ax.set_ylim(ds['freq'][-1],ds['freq'][0])
    cbaxes = figure.add_axes([0.915, 0.125, 0.03, 0.2]) 
    cb = plt.colorbar(cax, cax = cbaxes)  

    # print(ds['time'][0],ds['time'][-1],ddat['dpl'][0,0],ddat['dpl'][-1,0])
  except:
    print('ERR: in plot')

# based on https://pythonspot.com/en/pyqt5-matplotlib/
class SIMCanvas (FigureCanvas): 
  def __init__ (self, parent=None, width=5, height=4, dpi=100, title='Simulation Viewer'):
    self.fig = fig = Figure(figsize=(width, height), dpi=dpi)
    self.title = title
    FigureCanvas.__init__(self, fig)
    self.setParent(parent)
    FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
    FigureCanvas.updateGeometry(self)
    self.G = gridspec.GridSpec(10,1)
    self.plot()
  def plot (self):
    plotsimdat(self.figure,self.G,self.fig)
    self.draw()
