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
from conf import dconf
from specfn import MorletSpec

tstop = -1; ntrial = 0; maxlfp = 0; scalefctr = 30e3; lfppath = ''; paramf = ''
for i in range(len(sys.argv)):
  if sys.argv[i].endswith('.txt'):
    lfppath = sys.argv[i]
  elif sys.argv[i].endswith('.param'):
    paramf = sys.argv[i]
    scalefctr = paramrw.find_param(paramf,'dipole_scalefctr')
    if type(scalefctr)!=float and type(scalefctr)!=int: scalefctr=30e3
    tstop = paramrw.find_param(paramf,'tstop')
    ntrial = paramrw.quickgetprm(paramf,'N_trials',int)
        
basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])

ddat = {}; tvec = None; dspec = None

def readLFPs (basedir, ntrial):
  ddat = {'lfp':{}}
  lfile = os.listdir(basedir)
  maxlfp = 0; tvec = None
  #print(lfile)
  for f in lfile:
    if f.count('lfp_') > 0 and f.endswith('.txt'):
      lf = f.split('.txt')[0].split('_')
      #print(lf,ntrial)
      if ntrial > 0:
        trial = int(lf[1])
        nlfp = int(lf[2])
      else:
        trial = 0
        nlfp = int(lf[1])
      maxlfp = max(nlfp,maxlfp)
      #print(trial,nlfp,maxlfp)
      fullpath = os.path.join(basedir,f)
      #print(fullpath)
      try:
        k2 = (trial,nlfp)
        #print('k2:',k2)
        ddat['lfp'][k2] = np.loadtxt(fullpath)
        if tvec is None: tvec = ddat['lfp'][k2][:,0]
      except:
        print('exception!')
      #print(ddat['lfp'].keys())
  #print('ddat:',ddat,maxlfp)
  return ddat, maxlfp, tvec

try:
  ddat, maxlfp, tvec = readLFPs(basedir,ntrial) 
  ddat['spec'] = {}
  waveprm = {'f_max_spec':40.0,'dt':tvec[1]-tvec[0],'tstop':tvec[-1]}
  minwavet = 50.0
  print('Extracting Wavelet spectrogram(s).')
  for i in range(maxlfp+1):
    if ntrial > 0:
      for trial in range(1,ntrial+1,1):
        ddat['spec'][(trial,i)] = MorletSpec(tvec, ddat['lfp'][(trial,i)][:,1],None,None,waveprm,minwavet)
    else:
      ddat['spec'][(0,i)] = MorletSpec(tvec, ddat['lfp'][(0,i)][:,1],None,None,waveprm,minwavet)
  if ntrial > 0:
    print('here')
    davglfp = {}; davgspec = {}
    for i in range(maxlfp+1):
      print(i,maxlfp,list(ddat['lfp'].keys())[0])
      davglfp[i] = np.zeros(len(ddat['lfp'][list(ddat['lfp'].keys())[0]]),)
      try:
        ms = ddat['spec'][(1,0)]
        print('shape',ms.TFR.shape,ms.tmin,ms.f[0],ms.f[-1])
        davgspec[i] = [np.zeros(ms.TFR.shape), ms.tmin, ms.f]
      except:
        print('err in davgspec[i]=')
      for trial in range(1,ntrial+1,1):
        davglfp[i] += ddat['lfp'][(trial,i)][:,1]
        davgspec[i][0] += ddat['spec'][(trial,i)].TFR
      davglfp[i] /= float(ntrial)
      davgspec[i][0] /= float(ntrial)
    ddat['avglfp'] = davglfp
    ddat['avgspec'] = davgspec
except:
  print('Could not load LFPs')
  quit()

class LFPCanvas (FigureCanvas):

  def __init__ (self, paramf, index, parent=None, width=12, height=10, dpi=120, title='LFP Viewer'):
    FigureCanvas.__init__(self, Figure(figsize=(width, height), dpi=dpi))
    self.title = title
    self.setParent(parent)
    self.index = index
    FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
    FigureCanvas.updateGeometry(self)
    self.paramf = paramf
    self.drawwavelet = True
    self.plot()

  def clearaxes (self):
    try:
      for ax in self.lax:
        ax.set_yticks([])
        ax.cla()
    except:
      pass

  def drawLFP (self, fig):

    laminar = False
    if maxlfp > 1: laminar = True
    if laminar:
      nrow = maxlfp+1
      ncol = 2
      gdx = 1
      ltitle = ['' for x in range(nrow*ncol)]
    else:
      nrow = (maxlfp+1) * 2
      ncol = 1
      gdx = 1
      ltitle = ['LFP'+str(x) for x in range(nrow)]

    white_patch = mpatches.Patch(color='white', label='Average')
    gray_patch = mpatches.Patch(color='gray', label='Individual')
    lpatch = []

    print('ntrial:',ntrial)

    if ntrial > 0:
      lpatch = [white_patch,gray_patch]

    yl = [1e9,-1e9]

    minx = 100
    
    for i in [1]: # this gets min,max LFP values
      # print('ddat[lfp].keys():',ddat['lfp'].keys())
      for k in ddat['lfp'].keys():
        yl[0] = min(yl[0],ddat['lfp'][k][minx:-1,i].min())
        yl[1] = max(yl[1],ddat['lfp'][k][minx:-1,i].max())

    yl = tuple(yl) # y-axis range

    self.lax = []

    for nlfp in range(maxlfp+1):
      gdx = nlfp * 2 + 1
      title = ltitle[nlfp]

      i = 1

      # print('row,col,gdx,index',nrow,ncol,gdx,self.index)

      ax = fig.add_subplot(nrow,ncol,gdx)
      self.lax.append(ax)

      if self.index == 0 and ntrial > 0: # draw all along with average
        for j in range(1,ntrial+1,1): ax.plot(tvec,ddat['lfp'][(j,nlfp)][:,1],color='gray',linewidth=2)
        ax.plot(tvec,ddat['avglfp'][nlfp],'w',linewidth=3)
        if i == 1 and nlfp == 0: ax.legend(handles=lpatch)
      else: # draw individual trial
        ax.plot(tvec,ddat['lfp'][(self.index,nlfp)][:,1],color='white',linewidth=2)

      ax.set_ylabel(r'$\mu V$')
      if tstop != -1: ax.set_xlim((minwavet,tstop))
      ax.set_ylim(yl)

      ax.set_facecolor('k'); ax.grid(True); ax.set_title(title)

      gdx += 1

      # plot wavelet spectrogram
      ax = fig.add_subplot(nrow,ncol,gdx)
      self.lax.append(ax)
      if self.index == 0 and ntrial > 0:
        TFR,tmin,F = ddat['avgspec'][nlfp]
        ax.imshow(TFR, extent=[tmin, tvec[-1], F[-1], F[0]], aspect='auto', origin='upper',cmap=plt.get_cmap('jet'))
      else:
        ms = ddat['spec'][(self.index,nlfp)]
        ax.imshow(ms.TFR, extent=[ms.tmin, tvec[-1], ms.f[-1], ms.f[0]], aspect='auto', origin='upper',cmap=plt.get_cmap('jet'))
      ax.set_xlim(minwavet,tvec[-1])
      if nlfp == maxlfp: ax.set_xlabel('Time (ms)')
      if not laminar: ax.set_ylabel('Frequency (Hz)');

    self.figure.subplots_adjust(bottom=0.04, left=0.04, right=1.0, top=0.99, wspace=0.1, hspace=0.01)

  def plot (self):
    self.drawLFP(self.figure)
    self.draw()

if __name__ == '__main__':
  app = QApplication(sys.argv)
  ex = DataViewGUI(LFPCanvas,paramf,ntrial,'HNN LFP Viewer')
  sys.exit(app.exec_())  
