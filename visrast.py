import sys, os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QToolTip, QPushButton, QFormLayout
from PyQt5.QtWidgets import QMenu, QSizePolicy, QMessageBox, QWidget, QFileDialog, QComboBox, QTabWidget
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QDialog, QGridLayout, QLineEdit, QLabel
from PyQt5.QtWidgets import QCheckBox, QInputDialog
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
from filt import boxfilt, hammfilt
import spikefn
from math import ceil
from conf import dconf
from gutils import getmplDPI

#plt.rcParams['lines.markersize'] = 15
plt.rcParams['lines.linewidth'] = 1
rastmarksz = 5 # raster dot size
if dconf['fontsize'] > 0: plt.rcParams['font.size'] = dconf['fontsize']
else: plt.rcParams['font.size'] = dconf['fontsize'] = 10

# colors for the different cell types
dclr = {'L2_pyramidal' : 'g',
        'L5_pyramidal' : 'r',
        'L2_basket' : 'w', 
        'L5_basket' : 'b'}

ntrial = 1; tstop = -1; outparamf = spkpath = paramf = ''; EvokedInputs = OngoingInputs = PoissonInputs = False; 

for i in range(len(sys.argv)):
  if sys.argv[i].endswith('.txt'):
    spkpath = sys.argv[i]
  elif sys.argv[i].endswith('.param'):
    paramf = sys.argv[i]
    tstop = paramrw.quickgetprm(paramf,'tstop',float)
    ntrial = paramrw.quickgetprm(paramf,'N_trials',int)
    EvokedInputs = paramrw.usingEvokedInputs(paramf)
    OngoingInputs = paramrw.usingOngoingInputs(paramf)
    PoissonInputs = paramrw.usingPoissonInputs(paramf)
    outparamf = os.path.join(dconf['datdir'],paramf.split('.param')[0].split(os.path.sep)[-1],'param.txt')

try:
  extinputs = spikefn.ExtInputs(spkpath, outparamf)
except ValueError:
  print("Error: could not load spike timings from %s" % spkpath)

extinputs.add_delay_times()

alldat = {}

ncell = len(net.cells)

binsz = 5.0
smoothsz = 0 # no smoothing

bDrawHist = True # whether to draw histograms (spike counts per time)

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
        dspk['Input'][2].append('orange')
      haveinputs = True
  for ty in dhist.keys():
    dhist[ty] = np.histogram(dhist[ty],range=(0,tstop),bins=int(tstop/binsz))
    if smoothsz > 0:
      #dhist[ty] = boxfilt(dhist[ty][0],smoothsz)
      dhist[ty] = hammfilt(dhist[ty][0],smoothsz)
    else:
      dhist[ty] = dhist[ty][0]
  return dspk,haveinputs,dhist

def drawhist (dhist,fig,G):
  ax = fig.add_subplot(G[-4:-1,:])
  fctr = 1.0
  if ntrial > 0: fctr = 1.0 / ntrial
  for ty in dhist.keys():
    ax.plot(np.arange(binsz/2,tstop+binsz/2,binsz),dhist[ty]*fctr,dclr[ty],linestyle='--')
  ax.set_xlim((0,tstop))
  ax.set_ylabel('Cell Spikes')
  return ax

invertedax = False

def drawrast (dspk, fig, G, sz=8):
  global invertedax
  lax = []
  lk = ['Cell']
  row = 0

  if haveinputs:
    lk.append('Input')
    lk.reverse()

  dinput = extinputs.inputs

  for i,k in enumerate(lk):
    if k == 'Input': # input spiking

      bins = ceil(150. * tstop / 1000.) # bins needs to be an int

      haveEvokedDist = (EvokedInputs and len(dinput['evdist'])>0)
      haveOngoingDist = (OngoingInputs and len(dinput['dist'])>0)
      haveEvokedProx = (EvokedInputs and len(dinput['evprox'])>0)
      haveOngoingProx = (OngoingInputs and len(dinput['prox'])>0)

      if haveEvokedDist or haveOngoingDist:
        ax = fig.add_subplot(G[row:row+2,:]); row += 2
        lax.append(ax)
        if haveEvokedDist: extinputs.plot_hist(ax,'evdist',0,bins,(0,tstop),color='g',hty='step')
        if haveOngoingDist: extinputs.plot_hist(ax,'dist',0,bins,(0,tstop),color='g')
        ax.invert_yaxis()
        ax.set_ylabel('Distal Input')

      if haveEvokedProx or haveOngoingProx:
        ax2 = fig.add_subplot(G[row:row+2,:]); row += 2
        lax.append(ax2)
        if haveEvokedProx: extinputs.plot_hist(ax2,'evprox',0,bins,(0,tstop),color='r',hty='step')
        if haveOngoingProx: extinputs.plot_hist(ax2,'prox',0,bins,(0,tstop),color='r')
        ax2.set_ylabel('Proximal Input')

      if PoissonInputs and len(dinput['pois']):
        axp = fig.add_subplot(G[row:row+2,:]); row += 2
        lax.append(axp)
        extinputs.plot_hist(axp,'pois',0,bins,(0,tstop),color='orange')
        axp.set_ylabel('Poisson Input')

    else: # local circuit neuron spiking

      endrow = -1
      if bDrawHist: endrow = -4

      ax = fig.add_subplot(G[row:endrow,:])
      lax.append(ax)

      ax.scatter(dspk[k][0],dspk[k][1],c=dspk[k][2],s=sz**2) 
      ax.set_ylabel(k + ' ID')
      white_patch = mpatches.Patch(color='white', label='L2/3 Basket')
      green_patch = mpatches.Patch(color='green', label='L2/3 Pyr')
      red_patch = mpatches.Patch(color='red', label='L5 Pyr')
      blue_patch = mpatches.Patch(color='blue', label='L5 Basket')
      ax.legend(handles=[white_patch,green_patch,blue_patch,red_patch],loc='best')
      ax.set_ylim((-1,ncell+1))
      ax.invert_yaxis()

  return lax

class SpikeCanvas (FigureCanvas):
  def __init__ (self, paramf, index, parent=None, width=12, height=10, dpi=120, title='Spike Viewer'):
    FigureCanvas.__init__(self, Figure(figsize=(width, height), dpi=dpi))
    self.title = title
    self.setParent(parent)
    self.index = index
    FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
    FigureCanvas.updateGeometry(self)
    self.paramf = paramf
    self.invertedhistax = False
    self.G = gridspec.GridSpec(16,1)
    self.plot()

  def clearaxes (self):
    try:
      for ax in self.lax:
        ax.set_yticks([])
        ax.cla()
    except:
      pass

  def loadspk (self,idx):
    global haveinputs,extinputs
    if idx in alldat: return
    alldat[idx] = {}
    if idx == 0:
      try:
        extinputs = spikefn.ExtInputs(spkpath, outparamf)
      except ValueError:
        print("Error: could not load spike timings from %s" % spkpath)
        return
      extinputs.add_delay_times()
      dspk,haveinputs,dhist = getdspk(spkpath)
      alldat[idx]['dspk'] = dspk
      alldat[idx]['haveinputs'] = haveinputs
      alldat[idx]['dhist'] = dhist
      alldat[idx]['extinputs'] = extinputs
    else:
      spkpathtrial = os.path.join(dconf['datdir'],paramf.split('.param')[0].split(os.path.sep)[-1],'spk_'+str(self.index-1)+'.txt') 
      dspktrial,haveinputs,dhisttrial = getdspk(spkpathtrial) # show spikes from first trial
      try:
        extinputs = spikefn.ExtInputs(spkpathtrial, outparamf)
      except ValueError:
        print("Error: could not load spike timings from %s" % spkpath)
        return
      extinputs.add_delay_times()
      alldat[idx]['dspk'] = dspktrial
      alldat[idx]['haveinputs'] = haveinputs
      alldat[idx]['dhist'] = dhisttrial
      alldat[idx]['extinputs'] = extinputs

  def plot (self):
    global haveinputs,extinputs

    self.loadspk(self.index)

    idx = self.index
    dspk = alldat[idx]['dspk']
    haveinputs = alldat[idx]['haveinputs']
    dhist = alldat[idx]['dhist']
    extinputs = alldat[idx]['extinputs']

    self.lax = drawrast(dspk,self.figure, self.G, rastmarksz)

    if bDrawHist: self.lax.append(drawhist(dhist,self.figure,self.G))

    for ax in self.lax: 
      ax.set_facecolor('k')
      ax.grid(True)
      if tstop != -1: ax.set_xlim((0,tstop))

    if idx == 0: self.lax[0].set_title('All Trials')
    else: self.lax[0].set_title('Trial '+str(self.index))

    self.lax[-1].set_xlabel('Time (ms)');

    self.figure.subplots_adjust(bottom=0.0, left=0.06, right=1.0, top=0.97, wspace=0.1, hspace=0.09)

    self.draw()

class SpikeGUI (QMainWindow):
  def __init__ (self):
    global dfile, ddat, paramf
    super().__init__()        
    self.initUI()

    if "TRAVIS_TESTING" in os.environ and os.environ["TRAVIS_TESTING"] == "1":
      print("Exiting gracefully with TRAVIS_TESTING=1")
      qApp.quit()
      exit(0)

  def initMenu (self):
    exitAction = QAction(QIcon.fromTheme('exit'), 'Exit', self)        
    exitAction.setShortcut('Ctrl+Q')
    exitAction.setStatusTip('Exit HNN Spike Viewer.')
    exitAction.triggered.connect(qApp.quit)

    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')
    menubar.setNativeMenuBar(False)
    fileMenu.addAction(exitAction)

    viewMenu = menubar.addMenu('&View')
    drawHistAction = QAction('Toggle Histograms',self)
    drawHistAction.setStatusTip('Toggle Histogram Drawing.')
    drawHistAction.triggered.connect(self.toggleHist)
    viewMenu.addAction(drawHistAction)
    changeFontSizeAction = QAction('Change Font Size',self)
    changeFontSizeAction.setStatusTip('Change Font Size.')
    changeFontSizeAction.triggered.connect(self.changeFontSize)
    viewMenu.addAction(changeFontSizeAction)
    changeLineWidthAction = QAction('Change Line Width',self)
    changeLineWidthAction.setStatusTip('Change Line Width.')
    changeLineWidthAction.triggered.connect(self.changeLineWidth)
    viewMenu.addAction(changeLineWidthAction)
    changeMarkerSizeAction = QAction('Change Marker Size',self)
    changeMarkerSizeAction.setStatusTip('Change Marker Size.')
    changeMarkerSizeAction.triggered.connect(self.changeMarkerSize)
    viewMenu.addAction(changeMarkerSizeAction)


  def toggleHist (self):
    global bDrawHist
    bDrawHist = not bDrawHist
    self.initCanvas()
    self.m.plot()

  def changeFontSize (self):
    i, okPressed = QInputDialog.getInt(self, "Set Font Size","Font Size:", plt.rcParams['font.size'], 1, 100, 1)
    if okPressed:
      plt.rcParams['font.size'] = dconf['fontsize'] = i
      self.initCanvas()
      self.m.plot()

  def changeLineWidth (self):
    i, okPressed = QInputDialog.getInt(self, "Set Line Width","Line Width:", plt.rcParams['lines.linewidth'], 1, 20, 1)
    if okPressed:
      plt.rcParams['lines.linewidth'] = i
      self.initCanvas()
      self.m.plot()

  def changeMarkerSize (self):
    global rastmarksz
    i, okPressed = QInputDialog.getInt(self, "Set Marker Size","Font Size:", rastmarksz, 1, 100, 1)
    if okPressed:
      rastmarksz = i
      self.initCanvas()
      self.m.plot()

  def initCanvas (self):
    try: # to avoid memory leaks remove any pre-existing widgets before adding new ones
      self.grid.removeWidget(self.m)
      self.grid.removeWidget(self.toolbar)
      self.m.setParent(None)
      self.toolbar.setParent(None)
      self.m = self.toolbar = None
    except:
      pass
    self.m = SpikeCanvas(paramf, self.index, parent = self, width=12, height=10, dpi=getmplDPI())
    # this is the Navigation widget
    # it takes the Canvas widget and a parent
    self.toolbar = NavigationToolbar(self.m, self)
    self.grid.addWidget(self.toolbar, 0, 0, 1, 4); 
    self.grid.addWidget(self.m, 1, 0, 1, 4);     

  def initUI (self):
    self.initMenu()
    self.statusBar()
    self.setGeometry(300, 300, 1300, 1100)
    self.setWindowTitle('Spike Viewer - ' + paramf)
    self.grid = grid = QGridLayout()
    self.index = 0
    self.initCanvas()
    self.cb = QComboBox(self)
    self.grid.addWidget(self.cb,2,0,1,4)

    if ntrial > 1:
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

    try: self.setWindowIcon(QIcon(os.path.join('res','icon.png')))
    except: pass

    self.show()

  def onActivated(self, idx):
    if idx != self.index:
      self.index = idx
      if self.index == 0:
        self.statusBar().showMessage('Loading data from all trials.')
      else:
        self.statusBar().showMessage('Loading data from trial ' + str(self.index) + '.')
      self.m.index = self.index
      self.initCanvas()
      self.m.plot()
      self.statusBar().showMessage('')

if __name__ == '__main__':

  app = QApplication(sys.argv)
  ex = SpikeGUI()
  sys.exit(app.exec_())  
  

