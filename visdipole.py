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
from math import ceil
from simdat import readdpltrials
from conf import dconf

tstop = -1; ntrial = 0; scalefctr = 30e3; dplpath = ''; paramf = ''
for i in range(len(sys.argv)):
  if sys.argv[i].endswith('.txt'):
    dplpath = sys.argv[i]
  elif sys.argv[i].endswith('.param'):
    paramf = sys.argv[i]
    scalefctr = paramrw.find_param(paramf,'dipole_scalefctr')
    if type(scalefctr)!=float and type(scalefctr)!=int: scalefctr=30e3
    tstop = paramrw.find_param(paramf,'tstop')
    ntrial = paramrw.quickgetprm(paramf,'N_trials',int)
        
basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])

ddat = {}
ddat['dpltrials'] = readdpltrials(basedir,ntrial)
try:
  ddat['dpl'] = np.loadtxt(os.path.join(basedir,'dpl.txt'))
except:
  print('Could not load',dplpath)
  quit()

class DipoleCanvas (FigureCanvas):

  def __init__ (self, paramf, index, parent=None, width=12, height=10, dpi=120, title='Dipole Viewer'):
    FigureCanvas.__init__(self, Figure(figsize=(width, height), dpi=dpi))
    self.title = title
    self.setParent(parent)
    self.index = index
    FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
    FigureCanvas.updateGeometry(self)
    self.paramf = paramf
    self.plot()

  def clearaxes (self):
    try:
      for ax in self.lax:
        ax.set_yticks([])
        ax.cla()
    except:
      pass

  def drawdipole (self, fig):

    gdx = 311

    ltitle = ['Layer2', 'Layer5', 'Aggregate']

    white_patch = mpatches.Patch(color='white', label='Average')
    gray_patch = mpatches.Patch(color='gray', label='Individual')
    lpatch = []

    if len(ddat['dpltrials']) > 0: lpatch = [white_patch,gray_patch]

    yl = [1e9,-1e9]
    
    for i in [2,3,1]:
      yl[0] = min(yl[0],ddat['dpl'][:,i].min())
      yl[1] = max(yl[1],ddat['dpl'][:,i].max())
      if len(ddat['dpltrials']) > 0: # plot dipoles from individual trials
        for dpltrial in ddat['dpltrials']:
          yl[0] = min(yl[0],dpltrial[:,i].min())
          yl[1] = max(yl[1],dpltrial[:,i].max())

    yl = tuple(yl)

    self.lax = []

    for i,title in zip([2, 3, 1],ltitle):
      ax = fig.add_subplot(gdx)
      self.lax.append(ax)

      if i == 1: ax.set_xlabel('Time (ms)');

      lw = 2
      if self.index != 0: lw = 5

      if len(ddat['dpltrials']) > 0: # plot dipoles from individual trials
        for ddx,dpltrial in enumerate(ddat['dpltrials']):
          if self.index == 0 or ddx == self.index-1:
            ax.plot(dpltrial[:,0],dpltrial[:,i],color='gray',linewidth=lw)

      if self.index == 0: ax.plot(ddat['dpl'][:,0],ddat['dpl'][:,i],'w',linewidth=5)

      ax.set_ylabel(r'(nAm $\times$ '+str(scalefctr)+')')
      if tstop != -1: ax.set_xlim((0,tstop))
      ax.set_ylim(yl)

      if i == 2 and len(ddat['dpltrials']) > 0: ax.legend(handles=lpatch)

      ax.set_facecolor('k')
      ax.grid(True)
      ax.set_title(title)

      gdx += 1

  def plot (self):
    self.drawdipole(self.figure)
    self.draw()

if __name__ == '__main__':
  app = QApplication(sys.argv)
  ex = DataViewGUI(DipoleCanvas,paramf,ntrial,'HNN Dipole Viewer')
  sys.exit(app.exec_())  
