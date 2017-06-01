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
import pickle

# colors for the different cell types
dclr = {'L2_pyramidal' : 'g',
        'L5_pyramidal' : 'r',
        'L2_basket' : 'w', 
        'L5_basket' : 'b'}

ntrial = 0; tstop = -1; outparamf = voltpath = paramf = ''; 

maxperty = 10 # how many cells of a type to draw

for i in range(len(sys.argv)):
  if sys.argv[i].endswith('.pkl'):
    voltpath = sys.argv[i]
  elif sys.argv[i].endswith('.param'):
    paramf = sys.argv[i]
    tstop = paramrw.quickgetprm(paramf,'tstop',float)
    ntrial = paramrw.quickgetprm(paramf,'N_trials',int)
    outparamf = os.path.join('data',paramf.split('.param')[0].split(os.path.sep)[-1],'param.txt')
  elif sys.argv[i] == 'maxperty':
    maxperty = int(sys.argv[i])

ncell = len(net.cells)

invertedax = False

def drawvolt (dvolt, fig, G, sz=8, ltextra=''):
  global invertedax
  lax = []
  row = 0
  ax = fig.add_subplot(G[row:-1,:])

  lax.append(ax)

  dcnt = {}
  
  vtime = dvolt['vtime']
  yoff = 0
  # print(dvolt.keys())
  for gid,it in dvolt.items():
    ty,vsoma = it[0],it[1]
    # print('ty:',ty,'gid:',gid)
    if type(gid) != int: continue
    if ty not in dcnt: dcnt[ty] = 1
    if dcnt[ty] > maxperty: continue
    ax.plot(vtime, -vsoma + yoff, dclr[ty], linewidth = 1)
    yoff += max(vsoma) - min(vsoma)
    dcnt[ty] += 1
            
  white_patch = mpatches.Patch(color='white', label='L2Basket')
  green_patch = mpatches.Patch(color='green', label='L2Pyr')
  red_patch = mpatches.Patch(color='red', label='L5Pyr')
  blue_patch = mpatches.Patch(color='blue', label='L5Basket')
  ax.legend(handles=[white_patch,green_patch,blue_patch,red_patch])

  if not invertedax: 
    ax.invert_yaxis()
    invertedax = True

  ax.set_yticks([])

  ax.set_facecolor('k')
  ax.grid(True)
  if tstop != -1: ax.set_xlim((0,tstop))
  if i ==0: ax.set_title(ltextra)
  ax.set_xlabel('Time (ms)');
  return lax

class VoltCanvas (FigureCanvas):
  def __init__ (self, paramf, index, parent=None, width=12, height=10, dpi=100, title='Voltage Viewer'):
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

  def plot (self):
    if self.index == 0:
      dvolt = pickle.load(open(voltpath,'rb'))
      self.lax = drawvolt(dvolt,self.figure, self.G, 5, ltextra='All Trials')
    else:
      voltpathtrial = os.path.join('data',paramf.split('.param')[0].split(os.path.sep)[-1],'vsoma_'+str(self.index)+'.pkl') 
      dvolttrial = pickle.load(open(voltpathtrial,'rb'))
      self.lax=drawvolt(dvolttrial,self.figure, self.G, 5, ltextra='Trial '+str(self.index));
    self.draw()

class VoltGUI (QMainWindow):
  def __init__ (self):
    global dfile, ddat, paramf
    super().__init__()        
    self.initUI()

  def initMenu (self):
    exitAction = QAction(QIcon.fromTheme('exit'), 'Exit', self)        
    exitAction.setShortcut('Ctrl+Q')
    exitAction.setStatusTip('Exit HNN Volt Viewer.')
    exitAction.triggered.connect(qApp.quit)

    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')
    menubar.setNativeMenuBar(False)
    fileMenu.addAction(exitAction)

  def initCanvas (self):
    try: # to avoid memory leaks remove any pre-existing widgets before adding new ones
      self.grid.removeWidget(self.m)
      self.grid.removeWidget(self.toolbar)
      self.m.setParent(None)
      self.toolbar.setParent(None)
      self.m = self.toolbar = None
    except:
      pass
    self.m = VoltCanvas(paramf, self.index, parent = self, width=12, height=10)
    # this is the Navigation widget
    # it takes the Canvas widget and a parent
    self.toolbar = NavigationToolbar(self.m, self)
    self.grid.addWidget(self.toolbar, 0, 0, 1, 4); 
    self.grid.addWidget(self.m, 1, 0, 1, 4);     

  def initUI (self):
    self.initMenu()
    self.statusBar()
    self.setGeometry(300, 300, 1300, 1100)
    self.setWindowTitle('HNN Volt Viewer - ' + paramf)
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
  ex = VoltGUI()
  sys.exit(app.exec_())  
  

