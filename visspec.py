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
from DataViewGUI import DataViewGUI
from neuron import h
from run import net
import paramrw
from filt import boxfilt, hammfilt
import spikefn
from math import ceil, sqrt
from specfn import MorletSpec

ntrial = 0; specpath = ''; paramf = ''
for i in range(len(sys.argv)):
  if sys.argv[i].endswith('.txt'):
    specpath = sys.argv[i]
  elif sys.argv[i].endswith('.param'):
    paramf = sys.argv[i]
    ntrial = paramrw.quickgetprm(paramf,'N_trials',int)
        
basedir = os.path.join('data',paramf.split(os.path.sep)[-1].split('.param')[0])
print('basedir:',basedir)

ddat = {}
try:
  specpath = os.path.join(basedir,'rawspec.npz')
  print('specpath',specpath)
  ddat['spec'] = np.load(specpath)
except:
  print('Could not load',specpath)
  quit()

# assumes column 0 is time, rest of columns are time-series
def extractspec (dat, fmax=120.0):
  print('extractpsd',dat.shape)
  lspec = []
  tvec = dat[:,0]
  dt = tvec[1] - tvec[0]
  tstop = tvec[-1]
  prm = {'f_max_spec':fmax,'dt':dt,'tstop':tstop}
  for col in range(1,dat.shape[1],1):
    ms = MorletSpec(tvec,dat[:,col],None,None,prm)
    lspec.append(ms)
    # lpsd.append(np.mean(ms.TFR,axis=1))
  return ms.f, lspec

def drawspec (lspec, sdx, fig, G, ltextra=''):

  if len(lspec) == 0: return

  lax = []

  lkF = ['f_L2', 'f_L5', 'f_L2']
  lkS = ['TFR_L2', 'TFR_L5', 'TFR']      

  plt.ion()

  gdx = 311

  ltitle = ['Layer2', 'Layer5', 'Aggregate']

  yl = [1e9,-1e9]

  """
  for i in [0,1,2]:
    ddat['avg'+str(i)] = avg = np.mean(dspec[lkS[i]],axis=1)
    ddat['std'+str(i)] = std = np.std(dspec[lkS[i]],axis=1) / sqrt(dspec[lkS[i]].shape[1])
    yl[0] = min(yl[0],np.amin(avg-std))
    yl[1] = max(yl[1],np.amax(avg+std))
  """

  ms = lspec[sdx]

  yl = tuple(yl)
  xl = (ms.f[0],ms.f[-1])

  #for i,title in zip([0, 1, 2],ltitle):

  gdx = 212

  ax = fig.add_subplot(gdx)

  lspec[sdx].plot_to_ax(ax,1e3/600.0)

  lax.append(ax)

  if i == 2: ax.set_xlabel('Frequency (Hz)');

  """
  ax.plot(dspec[lkF[i]],np.mean(dspec[lkS[i]],axis=1),color='w',linewidth=4)
  avg = ddat['avg'+str(i)]
  std = ddat['std'+str(i)]
  ax.plot(dspec[lkF[i]],avg-std,color='gray',linewidth=2)
  ax.plot(dspec[lkF[i]],avg+std,color='gray',linewidth=2)

  ax.set_ylim(yl)
  ax.set_xlim(xl)

  ax.set_facecolor('k')
  ax.grid(True)
  ax.set_title(title)
  ax.set_ylabel(r'$nAm^2$')
  """

  gdx += 1

  #return lax


class SpecCanvas (FigureCanvas):
  def __init__ (self, paramf, index, parent=None, width=12, height=10, dpi=100, title='Spectrogram Viewer'):
    FigureCanvas.__init__(self, Figure(figsize=(width, height), dpi=dpi))
    self.title = title
    self.setParent(parent)
    self.index = index
    FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
    FigureCanvas.updateGeometry(self)
    self.paramf = paramf
    self.invertedhistax = False
    self.G = gridspec.GridSpec(10,1)
    self.lextspec = []
    self.plot()

  def clearaxes (self):
    try:
      for ax in self.lax:
        ax.set_yticks([])
        ax.cla()
    except:
      pass

  def clearlextdatobj (self):
    if hasattr(self,'lextdatobj'):
      for o in self.lextdatobj:
        try:
          o.set_visible(False)
        except:
          o[0].set_visible(False)
      del self.lextdatobj

  def plotextdat (self, lF, lextspec, lextfiles): # plot 'external' data (e.g. from experiment/other simulation)

    print('len(lax)',len(self.lax))

    self.lextdatobj = []
    white_patch = mpatches.Patch(color='white', label='Simulation')
    self.lpatch = [white_patch]

    ax = self.lax[2] # plot on agg

    yl = ax.get_ylim()

    cmap=plt.get_cmap('nipy_spectral')
    csm = plt.cm.ScalarMappable(cmap=cmap);
    csm.set_clim((0,100))

    for f,lspec,fname in zip(lF,lextspec,lextfiles):
      print(fname,len(f),lspec.shape)
      clr = csm.to_rgba(int(np.random.RandomState().uniform(5,101,1)))
      avg = np.mean(lspec,axis=0)
      std = np.std(lspec,axis=0) / sqrt(lspec.shape[1])
      self.lextdatobj.append(ax.plot(f,avg,color=clr,linewidth=2))
      self.lextdatobj.append(ax.plot(f,avg-std,'--',color=clr,linewidth=1))
      self.lextdatobj.append(ax.plot(f,avg+std,'--',color=clr,linewidth=1))
      yl = ((min(yl[0],min(avg))),(max(yl[1],max(avg))))
      new_patch = mpatches.Patch(color=clr, label=fname.split(os.path.sep)[-1].split('.txt')[0])
      self.lpatch.append(new_patch)

    ax.set_ylim(yl)
    self.lextdatobj.append(ax.legend(handles=self.lpatch))

  def plot (self):
    #self.clearaxes()
    #plt.close(self.figure)
    if self.index == 0:      
      self.lax = drawspec(self.lextspec,self.index, self.figure, self.G, ltextra='All Trials')
    else:
      specpathtrial = os.path.join('data',paramf.split('.param')[0].split(os.path.sep)[-1],'rawspec_'+str(self.index)+'.npz') 
      if 'spec'+str(self.index) not in ddat:
        ddat['spec'+str(self.index)] = np.load(specpath)
      self.lax=drawspec(self.lextspec,self.index, self.figure, self.G, ltextra='Trial '+str(self.index));

    self.draw()

class SpecViewGUI (DataViewGUI):
  def __init__ (self,CanvasType,paramf,ntrial,title):
    super(SpecViewGUI,self).__init__(CanvasType,paramf,ntrial,title)
    self.addLoadDataActions()
    self.lF = [] # frequencies associated with external data spec
    self.lextspec = [] # external data spec
    self.lextfiles = [] # external data files

  def addLoadDataActions (self):
    loadDataFile = QAction(QIcon.fromTheme('open'), 'Load data file.', self)
    loadDataFile.setShortcut('Ctrl+D')
    loadDataFile.setStatusTip('Load data file.')
    loadDataFile.triggered.connect(self.loadDisplayData)

    clearDataFileAct = QAction(QIcon.fromTheme('close'), 'Clear data file.', self)
    clearDataFileAct.setShortcut('Ctrl+C')
    clearDataFileAct.setStatusTip('Clear data file.')
    clearDataFileAct.triggered.connect(self.clearDataFile)

    self.fileMenu.addAction(loadDataFile)
    self.fileMenu.addAction(clearDataFileAct)

  def loadDisplayData (self):
    extdataf,dat = self.loadDataFileDialog()    
    if not extdataf: return
    try:
      f, lspec = extractspec(dat)
      self.printStat('Extracted Spectrograms from ' + extdataf)
      self.lextspec.append(lspec)
      self.lextfiles.append(extdataf)
      self.lF.append(f)
    except:
      self.printStat('Could not extract Spectrograms from ' + extdataf)

    try:
      if len(self.lextspec) > 0:
        self.printStat('Plotting ext data Spectrograms.')
        self.m.plotextdat(self.lF,self.lextspec,self.lextfiles)
        self.m.draw() # make sure new lines show up in plot
        self.printStat('')
    except:
      self.printStat('Could not plot data from ' + extdataf)    

  def loadDataFileDialog (self):
    fn = QFileDialog.getOpenFileName(self, 'Open file', 'data')
    if fn[0]:
      try:
        extdataf = fn[0] # data file
        dat = np.loadtxt(extdataf)
        self.printStat('Loaded data in ' + extdataf + '. Extracting Spectrograms.')
        return extdataf,dat
      except:
        self.printStat('Could not load data in ' + fn[0])
        return None,None
    return None,None

  def clearDataFile (self):
    self.m.clearlextdatobj()
    self.lextspec = []
    self.lextfiles = []
    self.lF = []
    self.m.draw()


if __name__ == '__main__':
  app = QApplication(sys.argv)
  ex = SpecViewGUI(SpecCanvas,paramf,ntrial,'HNN Spectrogram Viewer')
  sys.exit(app.exec_())  
  
