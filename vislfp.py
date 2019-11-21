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
from filt import boxfilt, hammfilt, lowpass
import spikefn
from math import ceil
from conf import dconf
from specfn import MorletSpec

if dconf['fontsize'] > 0: plt.rcParams['font.size'] = dconf['fontsize']

debug = True

tstop = -1; ntrial = 1; maxlfp = 0; scalefctr = 30e3; lfppath = ''; paramf = ''; laminar = False
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
  if debug: print('readLFPs')
  ddat = {'lfp':{}}
  lfile = os.listdir(basedir)
  maxlfp = 0; tvec = None
  if debug: print('readLFPs:',lfile)
  for f in lfile:
    if f.count('lfp_') > 0 and f.endswith('.txt'):
      lf = f.split('.txt')[0].split('_')
      if debug: print('readLFPs: lf=',lf,'ntrial=',ntrial)
      if ntrial > 1:
        trial = int(lf[1])
        nlfp = int(lf[2])
      else:
        trial = 0
        nlfp = int(lf[1])
      maxlfp = max(nlfp,maxlfp)
      if debug: print('readLFPs:',trial,nlfp,maxlfp)
      fullpath = os.path.join(basedir,f)
      if debug: print('readLFPs: fullpath=',fullpath)
      try:
        k2 = (trial,nlfp)
        #print('k2:',k2)
        ddat['lfp'][k2] = np.loadtxt(fullpath)
        if tvec is None: tvec = ddat['lfp'][k2][:,0]
      except:
        print('exception!')
      print('readLFPs:',ddat['lfp'].keys())
  #print('ddat:',ddat,maxlfp)
  return ddat, maxlfp, tvec

# lowpass filter the items in lfps. lfps is a list or numpy array of LFPs arranged spatially by row
def getlowpass (lfps,sampr,maxf):
  return np.array([lowpass(lfp,maxf,df=sampr,zerophase=True) for lfp in lfps])

# gets 2nd spatial derivative of voltage as approximation of CSD.
# performs lowpass filter on voltages before taking spatial derivative
# input dlfp is dictionary of LFP voltage time-series keyed by (trial, electrode)
# output dCSD is keyed by trial
def getCSD (dlfp,sampr,minf=0.1,maxf=300.0):
  if debug: print('getCSD:','sampr=',sampr,'ntrial=',ntrial,'maxlfp=',maxlfp)
  dCSD = {}
  for trial in range(ntrial):
    if debug: print('trial:',trial)
    lfps = [dlfp[(trial,i)][:,1] for i in range(maxlfp+1)]
    datband = getlowpass(lfps,sampr,maxf)
    dCSD[trial] = -np.diff(datband,n=2,axis=0) # now each row is an electrode -- CSD along electrodes
  return dCSD

try:
  ddat, maxlfp, tvec = readLFPs(basedir,ntrial) 
  if maxlfp > 1: laminar = True
  ddat['spec'] = {}
  waveprm = {'f_max_spec':40.0,'dt':tvec[1]-tvec[0],'tstop':tvec[-1]}
  minwavet = 50.0
  sampr = 1e3 / (tvec[1]-tvec[0])

  if laminar:
    print('getting CSD')
    ddat['CSD'] = getCSD(ddat['lfp'],sampr)
    if ntrial > 1:
      ddat['avgCSD'] = np.zeros(ddat['CSD'][1].shape)
      for i in range(ntrial): ddat['avgCSD'] += ddat['CSD'][i]
      ddat['avgCSD']/=float(ntrial)

  print('Extracting Wavelet spectrogram(s).')
  for i in range(maxlfp+1):
    for trial in range(ntrial):
      ddat['spec'][(trial,i)] = MorletSpec(tvec, ddat['lfp'][(trial,i)][:,1],None,None,waveprm,minwavet)
  if ntrial > 1:
    if debug: print('here')
    davglfp = {}; davgspec = {}
    for i in range(maxlfp+1):
      if debug: print(i,maxlfp,list(ddat['lfp'].keys())[0])
      davglfp[i] = np.zeros(len(ddat['lfp'][list(ddat['lfp'].keys())[0]]),)
      try:
        ms = ddat['spec'][(0,0)]
        if debug: print('shape',ms.TFR.shape,ms.tmin,ms.f[0],ms.f[-1])
        davgspec[i] = [np.zeros(ms.TFR.shape), ms.tmin, ms.f]
      except:
        print('err in davgspec[i]=')
      for trial in range(ntrial):
        davglfp[i] += ddat['lfp'][(trial,i)][:,1]
        davgspec[i][0] += ddat['spec'][(trial,i)].TFR
      davglfp[i] /= float(ntrial)
      davgspec[i][0] /= float(ntrial)
    ddat['avglfp'] = davglfp
    ddat['avgspec'] = davgspec
except:
  print('Could not load LFPs')
  quit()

def getnorm (yin):
  yout = yin - min(yin)
  return yout / max(yout)

def getrngfctroff (dat):
  yrng = [max(dat[i,:])-min(dat[i,:]) for i in range(dat.shape[0])]
  mxrng = np.amax(yrng)
  yfctr = [yrng[i]/mxrng for i in range(len(yrng))]
  yoff = [maxlfp - 1 - (i + 1) for i in range(len(yrng))]
  return yrng,yfctr,yoff

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

    p_exp = paramrw.ExpParams(self.paramf, 0)
    expmt_group = p_exp.expmt_groups[0]
    p = p_exp.return_pdict(expmt_group, 0)
    self.spec_cmap = p['spec_cmap']

    self.plot()

  def clearaxes (self):
    try:
      for ax in self.lax:
        ax.set_yticks([])
        ax.cla()
    except:
      pass

  def drawCSD (self, fig, G):
    ax = fig.add_subplot(G[:,2])
    ax.set_yticks([])
    lw = 2; clr = 'k'
    if ntrial > 1:
      if self.index == 0:
        cax = ax.imshow(ddat['avgCSD'],extent=[0, tstop, 0, maxlfp-1], aspect='auto', origin='upper',cmap=plt.get_cmap(self.spec_cmap),interpolation='None')
        # overlay the time-series
        yrng,yfctr,yoff = getrngfctroff(ddat['avgCSD'])
        for i in range(ddat['avgCSD'].shape[0]):
          y = yfctr[i] * getnorm(ddat['avgCSD'][i,:]) + yoff[i]
          ax.plot(tvec,y,clr,linewidth=lw)
      else:
        cax = ax.imshow(ddat['CSD'][self.index-1],extent=[0, tstop, 0, maxlfp-1], aspect='auto', origin='upper',cmap=plt.get_cmap(self.spec_cmap),interpolation='None')
        # overlay the time-series
        yrng,yfctr,yoff = getrngfctroff(ddat['CSD'][self.index-1])
        for i in range(ddat['CSD'][self.index-1].shape[0]):
          y = yfctr[i] * getnorm(ddat['CSD'][self.index-1][i,:]) + yoff[i]
          ax.plot(tvec,y,clr,linewidth=lw)
    else:
      # draw CSD as image; blue/red corresponds to excit/inhib
      cax = ax.imshow(ddat['CSD'][0],extent=[0, tstop, 0, 15], aspect='auto', origin='upper',cmap=plt.get_cmap(self.spec_cmap),interpolation='None')
      # overlay the time-series
      yrng,yfctr,yoff = getrngfctroff(ddat['CSD'][0])
      for i in range(ddat['CSD'][0].shape[0]):
        y = yfctr[i] * getnorm(ddat['CSD'][0][i,:]) + yoff[i]
        ax.plot(tvec,y,clr,linewidth=lw)
    cbaxes = fig.add_axes([0.69, 0.88, 0.005, 0.1]) 
    fig.colorbar(cax, cax=cbaxes, orientation='vertical')
    ax.set_xlim((minwavet,tstop)); ax.set_ylim((0,maxlfp-1))

  def drawLFP (self, fig):

    if laminar:
      nrow = maxlfp+1
      ncol = 3
      ltitle = ['' for x in range(nrow*ncol)]
    else:
      nrow = (maxlfp+1) * 2
      ncol = 1
      ltitle = ['LFP'+str(x) for x in range(nrow)]

    G = gridspec.GridSpec(nrow,ncol)

    white_patch = mpatches.Patch(color='white', label='Average')
    gray_patch = mpatches.Patch(color='gray', label='Individual')
    lpatch = []

    if debug: print('ntrial:',ntrial)

    if ntrial > 1: lpatch = [white_patch,gray_patch]

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
      title = ltitle[nlfp]

      if laminar: ax = fig.add_subplot(G[nlfp, 0])
      else: ax = fig.add_subplot(G[nlfp*2])
        
      self.lax.append(ax)

      if self.index == 0: # draw all along with average
        if ntrial > 1: clr = 'gray'
        else: clr = 'white'
        for i in range(ntrial): ax.plot(tvec,ddat['lfp'][(i,nlfp)][:,1],color=clr,linewidth=2)
        if ntrial > 1: 
          ax.plot(tvec,ddat['avglfp'][nlfp],'w',linewidth=3)
          if nlfp == 0: ax.legend(handles=lpatch)
      else: # draw individual trial
        ax.plot(tvec,ddat['lfp'][(self.index-1,nlfp)][:,1],color='white',linewidth=2)

      if not laminar: ax.set_ylabel(r'$\mu V$')
      if tstop != -1: ax.set_xlim((minwavet,tstop))
      ax.set_ylim(yl)

      ax.set_facecolor('k'); ax.grid(True); ax.set_title(title)

      # plot wavelet spectrogram
      if laminar: ax = fig.add_subplot(G[nlfp, 1])
      else: ax = fig.add_subplot(G[nlfp*2+1])
      self.lax.append(ax)
      if self.index == 0:
        if ntrial > 1:
          TFR,tmin,F = ddat['avgspec'][nlfp]
          ax.imshow(TFR, extent=[tmin, tvec[-1], F[-1], F[0]], aspect='auto', origin='upper',cmap=plt.get_cmap(self.spec_cmap))
        else:
          ms = ddat['spec'][(0,nlfp)]
          ax.imshow(ms.TFR, extent=[ms.tmin, tvec[-1], ms.f[-1], ms.f[0]], aspect='auto', origin='upper',cmap=plt.get_cmap(self.spec_cmap))
      else:
        ms = ddat['spec'][(self.index-1,nlfp)]
        ax.imshow(ms.TFR, extent=[ms.tmin, tvec[-1], ms.f[-1], ms.f[0]], aspect='auto', origin='upper',cmap=plt.get_cmap(self.spec_cmap))
      ax.set_xlim(minwavet,tvec[-1])
      if nlfp == maxlfp: ax.set_xlabel('Time (ms)')
      if not laminar: ax.set_ylabel('Frequency (Hz)');

    if laminar: self.drawCSD(fig, G)

    self.figure.subplots_adjust(bottom=0.04, left=0.04, right=1.0, top=0.99, wspace=0.1, hspace=0.01)

  def plot (self):
    self.drawLFP(self.figure)
    self.draw()

if __name__ == '__main__':
  app = QApplication(sys.argv)
  ex = DataViewGUI(LFPCanvas,paramf,ntrial,'LFP Viewer')
  sys.exit(app.exec_())  
