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

ntrial = 0; paramf = ''
for i in range(len(sys.argv)):
  if sys.argv[i].endswith('.param'):
    paramf = sys.argv[i]
        
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
  for col in range(1,dat.shape[1],1):
    ms = MorletSpec(tvec,dat[:,col],None,None,prm)
    lspec.append(ms)
  ntrial = len(lspec)
  avgdipole = np.mean(dat[:,1:-1],axis=1)
  avgspec = MorletSpec(tvec,avgdipole,None,None,prm)
  return ms.f, lspec, avgdipole, avgspec

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
      ax.plot(tvec, dat[:,i],linewidth=1,color='gray')
    ax.plot(tvec,avgdipole,linewidth=2,color='black')
  else:
    ax.plot(dat[:,0], dat[:,sdx-1],linewidth=2,color='gray')

  ax.set_xlim(tvec[0],tvec[-1])
  ax.set_ylabel('Dipole (nAm)')

  gdx = 212

  ax = fig.add_subplot(gdx)

  if sdx==0: ms = avgspec
  else: ms = lspec[sdx-1]

  ax.imshow(ms.TFR, extent=[tvec[0], tvec[-1], ms.f[-1], ms.f[0]], aspect='auto', origin='upper',cmap=plt.get_cmap('jet'))

  ax.set_xlim(tvec[0],tvec[-1])
  ax.set_xlabel('Time (ms)')
  ax.set_ylabel('Frequency (Hz)');

  lax.append(ax)

  return lax


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
    if self.index == 0:      
      self.lax = drawspec(self.dat, self.lextspec,self.index, self.avgdipole, self.avgspec, self.figure, self.G, ltextra='All Trials')
    else:
      self.lax=drawspec(self.dat, self.lextspec,self.index, self.avgdipole, self.avgspec, self.figure, self.G, ltextra='Trial '+str(self.index));

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

  def initCanvas (self):
    super(SpecViewGUI,self).initCanvas()
    self.m.lextspec = self.lextspec
    self.m.dat = self.dat
    self.m.avgdipole = self.avgdipole
    self.m.avgspec = self.avgspec

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
    self.dat = dat
    try:
      f, lspec, avgdipole, avgspec = extractspec(dat)
      self.ntrial = len(lspec)
      self.updateCB()
      self.printStat('Extracted ' + str(len(lspec)) + ' spectrograms from ' + extdataf)
      self.lextspec = lspec
      self.lextfiles.append(extdataf)
      self.avgdipole = avgdipole
      self.avgspec = avgspec
      self.lF.append(f)
    except:
      self.printStat('Could not extract Spectrograms from ' + extdataf)

    try:
      if len(self.lextspec) > 0:
        self.printStat('Plotting ext data Spectrograms.')
        self.m.lextspec = self.lextspec
        self.m.dat = self.dat
        self.m.avgspec = self.avgspec
        self.m.avgdipole = self.avgdipole
        self.m.plot()
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
  ex = SpecViewGUI(SpecCanvas,'',ntrial,'HNN Spectrogram Viewer')
  sys.exit(app.exec_())  
  
