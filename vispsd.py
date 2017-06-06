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
#ddat['spectrials']
try:
  specpath = os.path.join(basedir,'rawspec.npz')
  print('specpath',specpath)
  ddat['spec'] = np.load(specpath)
except:
  print('Could not load',specpath)
  quit()

def handle_close (evt): quit()

if __name__ == '__main__':
  lkF = ['f_L2', 'f_L5', 'f_L2']
  lkS = ['TFR_L2', 'TFR_L5', 'TFR']      

  plt.ion()
  fig = plt.figure()
  fig.canvas.mpl_connect('close_event', handle_close)

  gdx = 311

  ltitle = ['Layer2', 'Layer5', 'Aggregate']

  #white_patch = mpatches.Patch(color='white', label='Average')
  #gray_patch = mpatches.Patch(color='gray', label='Individual')
  #lpatch = []
  #if len(ddat['dpltrials']) > 0: lpatch = [white_patch,gray_patch]

  yl = [1e9,-1e9]

  for i in [0,1,2]:
    ddat['avg'+str(i)] = avg = np.mean(ddat['spec'][lkS[i]],axis=1)
    ddat['std'+str(i)] = std = np.std(ddat['spec'][lkS[i]],axis=1) / sqrt(ddat['spec'][lkS[i]].shape[1])
    yl[0] = min(yl[0],np.amin(avg-std))
    yl[1] = max(yl[1],np.amax(avg+std))
    """
    if len(ddat['dpltrials']) > 0: # plot dipoles from individual trials
      for dpltrial in ddat['dpltrials']:
        yl[0] = min(yl[0],dpltrial[:,i].min())
        yl[1] = max(yl[1],dpltrial[:,i].max())
    """
  yl = tuple(yl)
  xl = (ddat['spec']['f_L2'][0],ddat['spec']['f_L2'][-1])

  for i,title in zip([0, 1, 2],ltitle):
    ax = fig.add_subplot(gdx)

    if i == 2: ax.set_xlabel('Frequency (Hz)');

    """
    if len(ddat['dpltrials']) > 0: # plot dipoles from individual trials
      for dpltrial in ddat['dpltrials']:
        ax.plot(dpltrial[:,0],dpltrial[:,i],color='gray',linewidth=2)
    """

    ax.plot(ddat['spec'][lkF[i]],np.mean(ddat['spec'][lkS[i]],axis=1),color='w',linewidth=4)
    avg = ddat['avg'+str(i)]
    std = ddat['std'+str(i)]
    ax.plot(ddat['spec'][lkF[i]],avg-std,color='gray',linewidth=2)
    ax.plot(ddat['spec'][lkF[i]],avg+std,color='gray',linewidth=2)

    # ax.plot(ddat['dpl'][:,0],ddat['dpl'][:,i],'w',linewidth=5)
    # ax.set_ylabel(r'(nAm $\times$ '+str(scalefctr)+')')
    ax.set_ylim(yl)
    ax.set_xlim(xl)

    # if i == 2 and len(ddat['dpltrials']) > 0: plt.legend(handles=lpatch)

    ax.set_facecolor('k')
    ax.grid(True)
    ax.set_title(title)

    gdx += 1

