import sys, os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pylab as plt
from simdat import readdpltrials
import paramrw

tstop = -1; ntrial = 0; scalefctr = 30e3; dplpath = ''; paramf = ''
for i in range(len(sys.argv)):
  if sys.argv[i].endswith('.txt'):
    dplpath = sys.argv[i]
  elif sys.argv[i].endswith('.param'):
    paramf = sys.argv[i]
    scalefctr = paramrw.find_param(paramf,'dipole_scalefctr')
    tstop = paramrw.find_param(paramf,'tstop')
    ntrial = paramrw.quickgetprm(paramf,'N_trials',int)
        
basedir = os.path.join('data',paramf.split(os.path.sep)[-1].split('.param')[0])

ddat = {}
#ddat['dpltrials'] = readdpltrials(basedir,ntrial)
#ddat['spectrials']
try:
  #ddat['dpl'] = np.loadtxt(os.path.join(basedir,'dpl.txt'))
  ddat['spec'] = np.load(os.path.join(basedir,'rawspec.npz'))
except:
  print('Could not load',dplpath)
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
    avg = np.mean(ddat['spec'][lkS[i]],axis=1)
    yl[0] = min(yl[0],np.amin(avg))
    yl[1] = max(yl[1],np.amax(avg))
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

    # ax.plot(ddat['dpl'][:,0],ddat['dpl'][:,i],'w',linewidth=5)
    # ax.set_ylabel(r'(nAm $\times$ '+str(scalefctr)+')')
    #if tstop != -1: ax.set_xlim((0,tstop))
    ax.set_ylim(yl)
    ax.set_xlim(xl)

    # if i == 2 and len(ddat['dpltrials']) > 0: plt.legend(handles=lpatch)

    ax.set_facecolor('k')
    ax.grid(True)
    ax.set_title(title)

    gdx += 1

