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
from specfn import MorletSpec
import simdat
from simdat import readdpltrials
from paramrw import get_output_dir

from hnn_core import read_params

fontsize = plt.rcParams['font.size'] = 10

# assumes column 0 is time, rest of columns are time-series
def extractspec (dat, fmax=40.0):
  global ntrial
  #print('extractspec',dat.shape)
  lspec = []
  tvec = dat[:,0]
  dt = tvec[1] - tvec[0]
  tstop = tvec[-1]

  prm = {'f_max_spec':fmax,'dt':dt,'tstop':tstop}

  if dat.shape[1] > 2:
    for col in range(1,dat.shape[1],1):
      ms = MorletSpec(tvec,dat[:,col],None,p_dict=prm)
      lspec.append(ms)
  else:
    ms = MorletSpec(tvec,dat[:,1],None,p_dict=prm)
    lspec.append(ms)

  ntrial = len(lspec)

  if ntrial > 1:
    avgdipole = np.mean(dat[:,1:-1],axis=1)
  else:
    avgdipole = dat[:,1]

  avgspec = MorletSpec(tvec,avgdipole,None,p_dict=prm) # !!should fix to average of individual spectrograms!!

  ltfr = [ms.TFR for ms in lspec]
  npspec = np.array(ltfr)
  avgspec.TFR = np.mean(npspec,axis=0)#,axis=0)

  return ms.f, lspec, avgdipole, avgspec

def loaddat_txt (fname):
    dat = np.loadtxt(fname)
    print('Loaded data in ' + fname + '. Extracting Spectrograms.')
    return dat

def loaddat (sim_prefix, ntrial):
  basedir = os.path.join(get_output_dir(), 'data', sim_prefix)
  if ntrial > 1:
    ddat = readdpltrials(basedir)
    #print('read dpl trials',ddat[0].shape)
    dout = np.zeros((ddat[0].shape[0],1+ntrial))
    #print('set dout shape',dout.shape)
    dout[:,0] = ddat[0][:,0]
    for i in range(ntrial):
      dout[:,i+1] = ddat[i][:,1]
    return dout
  else:
    ddat = np.loadtxt(os.path.join(basedir,'dpl.txt'))
    #print('ddat.shape:',ddat.shape)
    dout = np.zeros((ddat.shape[0],2))
    #print('dout.shape:',dout.shape)
    dout[:,0] = ddat[:,0]
    dout[:,1] = ddat[:,1]
    return dout
  # except:
  #   print('Could not load data in ' + fname)
  #   return None
  return None

class SpecCanvas (FigureCanvas):
  def __init__ (self, parama, index, parent=None, width=12, height=10, dpi=120, title='Spectrogram Viewer'):

    FigureCanvas.__init__(self, Figure(figsize=(width, height), dpi=dpi))
    self.title = title
    self.setParent(parent)
    self.gui = parent
    self.index = index
    FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
    FigureCanvas.updateGeometry(self)
    self.params = params
    self.invertedhistax = False
    self.G = gridspec.GridSpec(10,1)
    self.dat = []
    self.lextspec = []
    self.lax = []
    self.avgdipole = []
    self.avgspec = []

    if 'spec_cmap' in self.params:
      self.spec_cmap = self.params['spec_cmap']
    else:
      # default to jet, but allow user to change in param file
      self.spec_cmap = 'jet'

    self.plot()

  def clearaxes (self):
    # try:
    for ax in self.lax:
      ax.set_yticks([])
      ax.cla()
    # except:
    #   pass

  def clearlextdatobj (self):
    if hasattr(self,'lextdatobj'):
      for o in self.lextdatobj:
        # try:
        o.set_visible(False)
        # except:
        #   o[0].set_visible(False)
      del self.lextdatobj

  def drawspec (self, dat, lspec, sdx, avgdipole, avgspec, fig, G, ltextra=''):
    if len(lspec) == 0: return

    plt.ion()

    gdx = 211

    ax = fig.add_subplot(gdx)
    lax = [ax]
    tvec = dat[:,0]
    # dt = tvec[1] - tvec[0]
    # tstop = tvec[-1]

    if sdx == 0:
      for i in range(1,dat.shape[1],1):
        #print('sdx is 0',dat.shape,i)
        ax.plot(tvec, dat[:,i],linewidth=self.gui.linewidth,color='gray')
      ax.plot(tvec,avgdipole,linewidth=self.gui.linewidth+1,color='black')
    else:
      ax.plot(dat[:,0], dat[:,sdx],linewidth=self.gui.linewidth+1,color='gray')

    ax.set_xlim(tvec[0],tvec[-1])
    ax.set_ylabel('Dipole (nAm)')

    gdx = 212

    ax = fig.add_subplot(gdx)

    #print('sdx:',sdx,avgspec.TFR.shape)

    if sdx==0: ms = avgspec
    else: ms = lspec[sdx-1]
    #print('ms.TFR.shape:',ms.TFR.shape)

    ax.imshow(ms.TFR, extent=[tvec[0], tvec[-1], ms.f[-1], ms.f[0]], aspect='auto', origin='upper',cmap=plt.get_cmap(self.spec_cmap))

    ax.set_xlim(tvec[0],tvec[-1])
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Frequency (Hz)')

    lax.append(ax)

    return lax
    
  def plot (self):
    ltextra = 'Trial '+str(self.index)
    if self.index == 0: ltextra = 'All Trials'
    self.lax = self.drawspec(self.dat, self.lextspec,self.index, self.avgdipole, self.avgspec, self.figure, self.G, ltextra=ltextra)
    self.figure.subplots_adjust(bottom=0.06, left=0.06, right=0.98, top=0.97, wspace=0.1, hspace=0.09)
    self.draw()

class SpecViewGUI (DataViewGUI):
  def __init__ (self,CanvasType,params,title):
    self.lF = [] # frequencies associated with external data spec
    self.lextspec = [] # external data spec
    # self.lextfiles = [] # external data files
    self.dat = None
    self.avgdipole = []
    self.avgspec = []
    self.params = params
    super(SpecViewGUI,self).__init__(CanvasType,self.params,title)
    self.addLoadDataActions()
    self.loadDisplayData(params)

    if "TRAVIS_TESTING" in os.environ and os.environ["TRAVIS_TESTING"] == "1":
      print("Exiting gracefully with TRAVIS_TESTING=1")
      qApp.quit()
      exit(0)

  def initCanvas (self):
    super(SpecViewGUI,self).initCanvas()
    self.m.lextspec = self.lextspec
    self.m.dat = self.dat
    self.m.avgdipole = self.avgdipole
    self.m.avgspec = self.avgspec

  def addLoadDataActions (self):
    loadDataFile = QAction(QIcon.fromTheme('open'), 'Load data.', self)
    loadDataFile.setShortcut('Ctrl+D')
    loadDataFile.setStatusTip('Load experimental (.txt) / simulation (.param) data.')
    loadDataFile.triggered.connect(self.loadDisplayData)

    clearDataFileAct = QAction(QIcon.fromTheme('close'), 'Clear data.', self)
    clearDataFileAct.setShortcut('Ctrl+C')
    clearDataFileAct.setStatusTip('Clear data.')
    clearDataFileAct.triggered.connect(self.clearDataFile)

    self.fileMenu.addAction(loadDataFile)
    self.fileMenu.addAction(clearDataFileAct)

  def loadDisplayData (self, params=None):
    if params is None or params is False:
      fname = QFileDialog.getOpenFileName(self, 'Open .param or .txt file', 'data')
      fname = os.path.abspath(fname[0])
      dat = loaddat_txt(fname)
    else:
      dat = loaddat(self.params['sim_prefix'], self.params['N_trials'])
    self.dat = dat

    fmax = self.params['f_max_spec']

    f, lspec, avgdipole, avgspec = extractspec(dat,fmax=fmax)
    self.ntrial = len(lspec)
    self.updateCB()
    self.printStat('Extracted ' + str(len(lspec)) + ' spectrograms for ' + self.params['sim_prefix'])
    self.lextspec = lspec
    # self.lextfiles.append(fname)
    self.avgdipole = avgdipole
    self.avgspec = avgspec
    self.lF.append(f)

    if len(self.lextspec) > 0:
      self.printStat('Plotting Spectrograms.')
      self.m.lextspec = self.lextspec
      self.m.dat = self.dat
      self.m.avgspec = self.avgspec
      self.m.avgdipole = self.avgdipole
      self.m.plot()
      self.m.draw() # make sure new lines show up in plot
      self.printStat('')

  def clearDataFile (self):
    self.m.clearlextdatobj()
    self.lextspec = []
    self.lF = []
    self.m.draw()


if __name__ == '__main__':
  for i in range(len(sys.argv)):
    if sys.argv[i].endswith('.param'):
      paramf = sys.argv[i]
      params = read_params(paramf)

  app = QApplication(sys.argv)
  ex = SpecViewGUI(SpecCanvas,params,'Spectrogram Viewer')
  sys.exit(app.exec_())  
  
