import sys, os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QToolTip, QPushButton, QFormLayout
from PyQt5.QtWidgets import QMenu, QSizePolicy, QMessageBox, QWidget, QFileDialog, QComboBox, QTabWidget
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QDialog, QGridLayout, QLineEdit, QLabel
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal, QObject, pyqtSlot
from PyQt5 import QtCore
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import pylab as plt
import matplotlib.gridspec as gridspec
from neuron import h
from run import net
import paramrw
from filt import boxfilt
import spikefn
from math import ceil

# colors for the different cell types
dclr = {'L2_pyramidal' : 'g',
        'L5_pyramidal' : 'r',
        'L2_basket' : 'w', 
        'L5_basket' : 'b'}

ntrial = 0; tstop = -1; outparamf = spkpath = paramf = ''; EvokedInputs = OngoingInputs = False; 

for i in range(len(sys.argv)):
  if sys.argv[i].endswith('.txt'):
    spkpath = sys.argv[i]
  elif sys.argv[i].endswith('.param'):
    paramf = sys.argv[i]
    tstop = paramrw.quickgetprm(paramf,'tstop',float)
    ntrial = paramrw.quickgetprm(paramf,'N_trials',int)
    EvokedInputs = paramrw.usingEvokedInputs(paramf)
    OngoingInputs = paramrw.usingOngoingInputs(paramf)
    outparamf = os.path.join('data',paramf.split('.param')[0].split(os.path.sep)[-1],'param.txt')

extinputs = spikefn.ExtInputs(spkpath, outparamf)
extinputs.add_delay_times()

alldat = {}
alldat[0] = (extinputs)

ncell = len(net.cells)

binsz = 5.0
smoothsz = 0 # no smoothing

def getEVInputTimes ():
  t_evprox_early,t_evdist,t_evprox_late=-1,-1,-1
  try:
    xx = paramrw.quickgetprm(paramf,'t_evprox_early',float)
    if type(xx)==float: t_evprox_early=xx
    xx = paramrw.quickgetprm(paramf,'t_evprox_late',float)
    if type(xx)==float: t_evprox_late = xx
    xx = paramrw.quickgetprm(paramf,'t_evdist',float)
    if type(xx)==float: t_evdist = xx
  except:
    print('except in getEVInputTimes')
    pass
  return t_evprox_early,t_evdist,t_evprox_late

def drawProxEVInputTimes (ax, h=0.55, w=15):
  t_evprox_early,t_evdist,t_evprox_late = getEVInputTimes()
  yl = ax.get_ylim(); yrange = yl[1] - yl[0]
  ax.plot([t_evprox_early,t_evprox_early],[yl[0],yl[1]],'r--',linewidth=8)
  ax.plot([t_evprox_late,t_evprox_late],[yl[0],yl[1]],'r--',linewidth=8)

def drawDistEVInputTimes (ax, h=0.55, w=15):
  t_evprox_early,t_evdist,t_evprox_late = getEVInputTimes()
  yl = ax.get_ylim(); yrange = yl[1] - yl[0]
  ax.plot([t_evdist,t_evdist],[yl[0],yl[1]],'g--',linewidth=8)

# adjust input gids for display purposes
def adjustinputgid (extinputs, gid):
  if gid == extinputs.gid_prox:
    return 0
  elif gid == extinputs.gid_dist:
    return 1
  elif extinputs.is_prox_gid(gid):
    return 2
  elif extinputs.is_dist_gid(gid):
    return 3
  return gid

def getdspk (fn):
  ddat = {}
  try:
    ddat['spk'] = np.loadtxt(fn)
  except:
    print('Could not load',fn)
    quit()
  dspk = {'Cell':([],[],[]),'Input':([],[],[])}
  dhist = {}
  for ty in dclr.keys(): dhist[ty] = []
  haveinputs = False
  for (t,gid) in ddat['spk']:
    ty = net.gid_to_type(gid)
    if ty in dclr:
      dspk['Cell'][0].append(t)
      dspk['Cell'][1].append(gid)
      dspk['Cell'][2].append(dclr[ty])
      dhist[ty].append(t)
    else:
      dspk['Input'][0].append(t)
      dspk['Input'][1].append(adjustinputgid(extinputs, gid))
      if extinputs.is_prox_gid(gid):
        dspk['Input'][2].append('r')
      elif extinputs.is_dist_gid(gid):
        dspk['Input'][2].append('g')
      else:
        dspk['Input'][2].append('w')
      haveinputs = True
  for ty in dhist.keys():
    dhist[ty] = np.histogram(dhist[ty],range=(0,tstop),bins=int(tstop/binsz))
    if smoothsz > 0:
      dhist[ty] = boxfilt(dhist[ty][0],smoothsz)
    else:
      dhist[ty] = dhist[ty][0]
  return dspk,haveinputs,dhist

def drawhist (dhist,ax):
  ax2 = ax.twinx()
  fctr = 1.0
  if ntrial > 1:
    fctr = 1.0 / ntrial
  for ty in dhist.keys():
    ax2.plot(np.arange(binsz/2,tstop+binsz/2,binsz),dhist[ty]*fctr,dclr[ty],linewidth=3,linestyle='--')
  ax2.set_xlim((0,tstop))
  ax2.set_ylabel('Cell Spikes')
  return ax2

invertedax = False

def drawrast (dspk, fig, G, sz=8, ltextra=''):
  global invertedax
  lax = []
  lk = ['Cell']
  row = 0
  if haveinputs:
    lk.append('Input')
    lk.reverse()
  for i,k in enumerate(lk):
    if k == 'Input':

      ax = fig.add_subplot(G[row:row+2,:])
      lax.append(ax)

      bins = ceil(150. * tstop / 1000.) # bins needs to be an int

      extinputs.plot_hist(ax,'dist',0,bins,(0,tstop),color='g')
      extinputs.plot_hist(ax,'evdist',0,bins,(0,tstop),color='g')
      #if not invertedax: 
      ax.invert_yaxis()
      #invertedax = True
      if EvokedInputs: drawDistEVInputTimes(ax)
      ax.set_ylabel('Distal Input')

      row += 2

      ax2 = fig.add_subplot(G[row:row+2,:])
      lax.append(ax)
      row += 2
      lax.append(ax2)
      extinputs.plot_hist(ax2,'prox',0,bins,(0,tstop),color='r')
      extinputs.plot_hist(ax2,'evprox',0,bins,(0,tstop),color='r')
      ax2.set_facecolor('k')
      ax2.grid(True)
      if tstop != -1: ax2.set_xlim((0,tstop))
      if EvokedInputs: drawProxEVInputTimes(ax2)
      ax2.set_ylabel('Proximal Input')
    else:

      ax = fig.add_subplot(G[row:-1,:])
      lax.append(ax)

      ax.scatter(dspk[k][0],dspk[k][1],c=dspk[k][2],s=sz**2) 
      ax.set_ylabel(k + ' ID')
      white_patch = mpatches.Patch(color='white', label='L2Basket')
      green_patch = mpatches.Patch(color='green', label='L2Pyr')
      red_patch = mpatches.Patch(color='red', label='L5Pyr')
      blue_patch = mpatches.Patch(color='blue', label='L5Basket')
      ax.legend(handles=[white_patch,green_patch,blue_patch,red_patch])
      ax.set_ylim((-1,ncell+1))
      ax.invert_yaxis()
    ax.set_facecolor('k')
    ax.grid(True)
    if tstop != -1: ax.set_xlim((0,tstop))
    if i ==0: ax.set_title(ltextra)
  ax.set_xlabel('Time (ms)');
  return lax

class SpikeCanvas (FigureCanvas):
  def __init__ (self, paramf, index, parent=None, width=12, height=10, dpi=100, title='Simulation Viewer'):
    FigureCanvas.__init__(self, Figure(figsize=(width, height), dpi=dpi))
    self.title = title
    self.setParent(parent)
    self.index = index
    FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
    FigureCanvas.updateGeometry(self)
    self.paramf = paramf
    self.invertedhistax = False
    self.G = gridspec.GridSpec(10,1)
    self.plot()

  def clearaxes (self):
    try:
      for ax in self.lax:
        ax.set_yticks([])
        ax.cla()
    except:
      pass

  def plot (self):
    global haveinputs,extinputs
    #self.clearaxes()
    #plt.close(self.figure)
    if self.index == 0:      
      extinputs = spikefn.ExtInputs(spkpath, outparamf)
      extinputs.add_delay_times()
      dspk,haveinputs,dhist = getdspk(spkpath)
      self.lax = drawrast(dspk,self.figure, self.G, 5, ltextra='All Trials')
      self.lax.append(drawhist(dhist,self.lax[-1]))
    else:
      spkpathtrial = os.path.join('data',paramf.split('.param')[0].split(os.path.sep)[-1],'spk_'+str(self.index)+'.txt') 
      dspktrial,haveinputs,dhisttrial = getdspk(spkpathtrial) # show spikes from first trial
      extinputs = spikefn.ExtInputs(spkpathtrial, outparamf)
      extinputs.add_delay_times()
      self.lax=drawrast(dspktrial,self.figure, self.G, 5, ltextra='Trial '+str(self.index));
      self.lax.append(drawhist(dhisttrial,self.lax[-1]))

    self.draw()

class SpikeGUI (QMainWindow):
  def __init__ (self):
    global dfile, ddat, paramf
    super().__init__()        
    self.initUI()

  def initCanvas (self):
    try: # to avoid memory leaks remove any pre-existing widgets before adding new ones
      self.grid.removeWidget(self.m)
      self.grid.removeWidget(self.toolbar)
      self.m.setParent(None)
      self.toolbar.setParent(None)
      self.m = self.toolbar = None
    except:
      pass
    self.m = SpikeCanvas(paramf, self.index, parent = self, width=12, height=10)
    # this is the Navigation widget
    # it takes the Canvas widget and a parent
    self.toolbar = NavigationToolbar(self.m, self)
    self.grid.addWidget(self.toolbar, 0, 0, 1, 4); 
    self.grid.addWidget(self.m, 1, 0, 1, 4);     

  def initUI (self):
    self.setGeometry(300, 300, 1300, 1100)
    self.setWindowTitle('HNN Spike Viewer')
    self.grid = grid = QGridLayout()
    self.index = 0
    self.initCanvas()
    self.cb = QComboBox(self)
    self.grid.addWidget(self.cb,2,0,1,4)

    if ntrial > 0:
      self.cb.addItem('Show All Trials')
      for i in range(ntrial):
        self.cb.addItem('Show Trial ' + str(i+1))
    else:
      self.cb.addItem('All Trials')
    self.cb.activated[int].connect(self.onActivated) 

    # need a separate widget to put grid on
    widget = QWidget(self)
    widget.setLayout(grid)
    self.setCentralWidget(widget);

    self.show()

  def onActivated(self, idx):
    self.index = idx
    self.m.index = self.index
    self.initCanvas()
    self.m.plot()

if __name__ == '__main__':

  app = QApplication(sys.argv)
  ex = SpikeGUI()
  sys.exit(app.exec_())  
  

