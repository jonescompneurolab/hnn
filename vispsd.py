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
def extractpsd (dat, fmax=120.0):
  from specfn import MorletSpec
  lpsd = []
  tvec = dat[:,0]
  dt = tvec[1] - tvec[0]
  tstop = tvec[-1]
  prm = {'f_max_spec':fmax,'dt':dt,'tstop':tstop}
  for col in range(1,dat.shape[1],1):
    ms = MorletSpec(tvec,dat[:,col],None,None,prm)
    lpsd.append(mean(ms.TFR,axis=1))
  return ms.f, np.array(lpsd)

def drawpsd (dspec, fig, G, ltextra=''):

  lax = []

  lkF = ['f_L2', 'f_L5', 'f_L2']
  lkS = ['TFR_L2', 'TFR_L5', 'TFR']      

  plt.ion()

  gdx = 311

  ltitle = ['Layer2', 'Layer5', 'Aggregate']

  #white_patch = mpatches.Patch(color='white', label='Average')
  #gray_patch = mpatches.Patch(color='gray', label='Individual')
  #lpatch = []
  #if len(ddat['dpltrials']) > 0: lpatch = [white_patch,gray_patch]

  yl = [1e9,-1e9]

  for i in [0,1,2]:
    ddat['avg'+str(i)] = avg = np.mean(dspec[lkS[i]],axis=1)
    ddat['std'+str(i)] = std = np.std(dspec[lkS[i]],axis=1) / sqrt(dspec[lkS[i]].shape[1])
    yl[0] = min(yl[0],np.amin(avg-std))
    yl[1] = max(yl[1],np.amax(avg+std))
    """
    if len(ddat['dpltrials']) > 0: # plot dipoles from individual trials
      for dpltrial in ddat['dpltrials']:
        yl[0] = min(yl[0],dpltrial[:,i].min())
        yl[1] = max(yl[1],dpltrial[:,i].max())
    """
  yl = tuple(yl)
  xl = (dspec['f_L2'][0],dspec['f_L2'][-1])

  for i,title in zip([0, 1, 2],ltitle):
    ax = fig.add_subplot(gdx)
    lax.append(ax)

    if i == 2: ax.set_xlabel('Frequency (Hz)');

    """
    if len(ddat['dpltrials']) > 0: # plot dipoles from individual trials
      for dpltrial in ddat['dpltrials']:
        ax.plot(dpltrial[:,0],dpltrial[:,i],color='gray',linewidth=2)
    """

    ax.plot(dspec[lkF[i]],np.mean(dspec[lkS[i]],axis=1),color='w',linewidth=4)
    avg = ddat['avg'+str(i)]
    std = ddat['std'+str(i)]
    ax.plot(dspec[lkF[i]],avg-std,color='gray',linewidth=2)
    ax.plot(dspec[lkF[i]],avg+std,color='gray',linewidth=2)

    # ax.plot(ddat['dpl'][:,0],ddat['dpl'][:,i],'w',linewidth=5)
    # ax.set_ylabel(r'(nAm $\times$ '+str(scalefctr)+')')
    ax.set_ylim(yl)
    ax.set_xlim(xl)

    # if i == 2 and len(ddat['dpltrials']) > 0: plt.legend(handles=lpatch)

    ax.set_facecolor('k')
    ax.grid(True)
    ax.set_title(title)

    gdx += 1
  return lax


class PSDCanvas (FigureCanvas):
  def __init__ (self, paramf, index, parent=None, width=12, height=10, dpi=100, title='PSD Viewer'):
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

  def clearlextdatobj (self):
    if hasattr(self,'lextdatobj'):
      for o in self.lextdatobj:
        try:
          o.set_visible(False)
        except:
          o[0].set_visible(False)
      del self.lextdatobj

  def plotextdat (self): # plot 'external' data (e.g. from experiment/other simulation)
    pass
    """
    try:
      dat = ddat['extdata']
      shp = dat.shape
      ax = self.axdipole

      yl = ax.get_ylim()
      cmap=plt.get_cmap('nipy_spectral')
      csm = plt.cm.ScalarMappable(cmap=cmap);
      csm.set_clim((0,100))

      errtot = 0.0

      # first downsample simulation timeseries to 600 Hz (assumes same time length as data)
      dpldown = signal.resample(ddat['dpl'][:,1], len(dat[:,1]))

      self.lextdatobj = []

      for c in range(1,shp[1],1): 
        clr = csm.to_rgba(int(np.random.RandomState().uniform(0,101,1)))
        self.lextdatobj.append(ax.plot(dat[:,0],dat[:,c],'--',color=clr,linewidth=4))
        yl = ((min(yl[0],min(dat[:,c]))),(max(yl[1],max(dat[:,c]))))

        err0 = rmse(dat[:,c], dpldown)
        errtot += err0
        print('RMSE: ',err0)

        fx = int(shp[0] * float(c) / shp[1])

        tx,ty=dat[fx,0],dat[fx,c]
        txt='RMSE:' + str(round(err0,2))
        self.lextdatobj.append(ax.annotate(txt,xy=(dat[0,0],dat[0,c]),xytext=(tx,ty),color=clr,fontsize=15,fontweight='bold'))
      ax.set_ylim(yl)

      tx,ty=0,0
      errtot /= (shp[1]-1)

      print(txt)
    except:
      print('simdat ERR: could not plotextdat')
      return False
    return True
    """

  def plot (self):
    #self.clearaxes()
    #plt.close(self.figure)
    if self.index == 0:      
      self.lax = drawpsd(ddat['spec'],self.figure, self.G, ltextra='All Trials')
    else:
      specpathtrial = os.path.join('data',paramf.split('.param')[0].split(os.path.sep)[-1],'rawspec_'+str(self.index)+'.npz') 
      if 'spec'+str(self.index) not in ddat:
        ddat['spec'+str(self.index)] = np.load(specpath)
      self.lax=drawpsd(ddat['spec'+str(self.index)],self.figure, self.G, ltextra='Trial '+str(self.index));

    self.draw()

class PSDViewGUI (DataViewGUI):
  def __init__ (self,CanvasType,paramf,ntrial):
    super(PSDViewGUI,self).__init__(CanvasType,paramf,ntrial)
    self.addLoadData()

  def addLoadData(self):
    loadDataFile = QAction(QIcon.fromTheme('open'), 'Load data file.', self)
    loadDataFile.setShortcut('Ctrl+D')
    loadDataFile.setStatusTip('Load data file.')
    loadDataFile.triggered.connect(self.loadDataFileDialog)

    clearDataFileAct = QAction(QIcon.fromTheme('close'), 'Clear data file.', self)
    clearDataFileAct.setShortcut('Ctrl+C')
    clearDataFileAct.setStatusTip('Clear data file.')
    clearDataFileAct.triggered.connect(self.clearDataFile)

    self.fileMenu.addAction(loadDataFile)
    self.fileMenu.addAction(clearDataFileAct)

  def loadDataFileDialog (self):
    fn = QFileDialog.getOpenFileName(self, 'Open file', 'data')
    if fn[0]:
      try:
        self.extdata = np.load(fn[0])
        self.extdataf = fn[0] # data file
        print('Loaded data in ', fn[0])
      except:
        print('Could not load data in ', fn[0])
      """
      try:
        self.m.plotextdat()
        self.m.draw() # make sure new lines show up in plot
      except:
        print('Could not plot data from ', fn[0])
      """

  def clearDataFile (self):
    self.m.clearlextdatobj()
    self.extdata = None
    self.extdataf = None
    self.m.draw()


if __name__ == '__main__':
  app = QApplication(sys.argv)
  ex = PSDViewGUI(PSDCanvas,paramf,ntrial)
  sys.exit(app.exec_())  
  
