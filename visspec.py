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
from conf import dconf
import simdat
from simdat import readdpltrials
import paramrw
from paramrw import quickgetprm

if dconf['fontsize'] > 0: plt.rcParams['font.size'] = dconf['fontsize']

ntrial = 1; paramf = ''
for i in range(len(sys.argv)):
  if sys.argv[i].endswith('.txt'):
    specpath = sys.argv[i]
  elif sys.argv[i].endswith('.param'):
    paramf = sys.argv[i]
    ntrial = paramrw.quickgetprm(paramf,'N_trials',int)

basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
print('basedir:',basedir,'paramf:',paramf,'ntrial:',ntrial)
        
# assumes column 0 is time, rest of columns are time-series
def extractspec (dat, fmax=120.0):
  global ntrial
  print('extractspec',dat.shape)
  lspec = []
  tvec = dat[:,0]
  dt = tvec[1] - tvec[0]
  tstop = tvec[-1]
  print('tstop is ', tstop)
  prm = {'f_max_spec':fmax,'dt':dt,'tstop':tstop}

  if dat.shape[1] > 2:
    print('gt2')
    for col in range(1,dat.shape[1],1):
      ms = MorletSpec(tvec,dat[:,col],None,None,prm)
      lspec.append(ms)
  else:
    ms = MorletSpec(tvec,dat[:,1],None,None,prm)
    lspec.append(ms)

  ntrial = len(lspec)

  if ntrial > 1:
    avgdipole = np.mean(dat[:,1:-1],axis=1)
  else:
    avgdipole = dat[:,1]

  print('lspec len is ' , len(lspec))

  avgspec = MorletSpec(tvec,avgdipole,None,None,prm) # !!should fix to average of individual spectrograms!!

  ltfr = [ms.TFR for ms in lspec]
  npspec = np.array(ltfr)
  print('got npspec',npspec.shape)
  avgspec.TFR = np.mean(npspec,axis=0)#,axis=0)
  print('got avgspec',avgspec.TFR.shape)

  return ms.f, lspec, avgdipole, avgspec

def loaddat (fname):
  try:
    if fname.endswith('.txt'):
      extdataf = fname # data file
      dat = np.loadtxt(extdataf)
      self.printStat('Loaded data in ' + extdataf + '. Extracting Spectrograms.')
      return dat
    elif fname.endswith('.param'):
      ntrial = paramrw.quickgetprm(paramf,'N_trials',int)
      basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
      print('basedir:',basedir)
      #simdat.updatedat(paramf)
      #return paramf,simdat.ddat
      if ntrial > 1:
        ddat = readdpltrials(basedir,quickgetprm(paramf,'N_trials',int))
        print('read dpl trials',ddat[0].shape)
        dout = np.zeros((ddat[0].shape[0],1+ntrial))
        print('set dout shape',dout.shape)
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
  except:
    print('Could not load data in ' + fname)
    return None
  return None

def drawspec (dat, lspec, sdx, avgdipole, avgspec, fig, G, ltextra=''):
  if len(lspec) == 0: return

  lax = []

  plt.ion()

  gdx = 211

  ax = fig.add_subplot(gdx)
  lax.append(ax)

  tvec = dat[:,0]
  dt = tvec[1] - tvec[0]
  tstop = tvec[-1]

  if sdx == 0:
    for i in range(1,dat.shape[1],1):
      print('sdx is 0',dat.shape,i)
      ax.plot(tvec, dat[:,i],linewidth=1,color='gray')
    ax.plot(tvec,avgdipole,linewidth=2,color='black')
  else:
    ax.plot(dat[:,0], dat[:,sdx],linewidth=2,color='gray')

  ax.set_xlim(tvec[0],tvec[-1])
  ax.set_ylabel('Dipole (nAm)')

  gdx = 212

  ax = fig.add_subplot(gdx)

  print('sdx:',sdx,avgspec.TFR.shape)

  if sdx==0: ms = avgspec
  else: ms = lspec[sdx-1]
  #print('ms.TFR.shape:',ms.TFR.shape)

  ax.imshow(ms.TFR, extent=[tvec[0], tvec[-1], ms.f[-1], ms.f[0]], aspect='auto', origin='upper',cmap=plt.get_cmap('jet'))

  ax.set_xlim(tvec[0],tvec[-1])
  ax.set_xlabel('Time (ms)')
  ax.set_ylabel('Frequency (Hz)');

  lax.append(ax)

  return lax


class SpecCanvas (FigureCanvas):
  def __init__ (self, paramf, index, parent=None, width=12, height=10, dpi=120, title='Spectrogram Viewer'):
    FigureCanvas.__init__(self, Figure(figsize=(width, height), dpi=dpi))
    self.title = title
    self.setParent(parent)
    self.index = index
    FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
    FigureCanvas.updateGeometry(self)
    self.paramf = paramf
    self.invertedhistax = False
    self.G = gridspec.GridSpec(10,1)
    self.dat = []
    self.lextspec = []
    self.lax = []
    self.avgdipole = []
    self.avgspec = []
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
    
  def plot (self):
    ltextra = 'Trial '+str(self.index)
    if self.index == 0: ltextra = 'All Trials'
    self.lax = drawspec(self.dat, self.lextspec,self.index, self.avgdipole, self.avgspec, self.figure, self.G, ltextra=ltextra)
    self.draw()

class SpecViewGUI (DataViewGUI):
  def __init__ (self,CanvasType,paramf,ntrial,title):
    self.lF = [] # frequencies associated with external data spec
    self.lextspec = [] # external data spec
    self.lextfiles = [] # external data files
    self.dat = None
    self.avgdipole = []
    self.avgspec = []
    super(SpecViewGUI,self).__init__(CanvasType,paramf,ntrial,title)
    self.addLoadDataActions()
    print('paramf:',paramf)
    if len(paramf):
      self.loadDisplayData(paramf)

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

  def loadDisplayData (self, fname=None):
    if fname is None:
      fname = QFileDialog.getOpenFileName(self, 'Open .param or .txt file', 'data')
    if not fname: return
    dat = loaddat(fname)
    self.dat = dat
    try:
      f, lspec, avgdipole, avgspec = extractspec(dat)
      self.ntrial = len(lspec)
      self.updateCB()
      self.printStat('Extracted ' + str(len(lspec)) + ' spectrograms from ' + fname)
      self.lextspec = lspec
      self.lextfiles.append(fname)
      self.avgdipole = avgdipole
      self.avgspec = avgspec
      self.lF.append(f)
    except:
      self.printStat('Could not extract Spectrograms from ' + fname)

    try:
      if len(self.lextspec) > 0:
        self.printStat('Plotting Spectrograms.')
        self.m.lextspec = self.lextspec
        self.m.dat = self.dat
        self.m.avgspec = self.avgspec
        self.m.avgdipole = self.avgdipole
        self.m.plot()
        self.m.draw() # make sure new lines show up in plot
        self.printStat('')
    except:
      self.printStat('Could not plot data from ' + fname)    

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
  
