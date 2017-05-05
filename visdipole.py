import sys, os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pylab as plt
from simdat import readdpltrials

tstop = -1; scalefctr = 30e3; dplpath = ''; paramf = ''
for i in range(len(sys.argv)):
  if sys.argv[i].endswith('.txt'):
    dplpath = sys.argv[i]
  elif sys.argv[i].endswith('.param'):
    paramf = sys.argv[i]
    import paramrw
    scalefctr = paramrw.find_param(paramf,'dipole_scalefctr')
    tstop = paramrw.find_param(paramf,'tstop')
        
basedir = os.path.join('data',paramf.split(os.path.sep)[-1].split('.param')[0])

ddat = {}
ddat['dpltrials'] = readdpltrials(basedir)
try:
  ddat['dpl'] = np.loadtxt(os.path.join(basedir,'dpl.txt'))
except:
  print('Could not load',dplpath)
  quit()

def handle_close (evt): quit()

if __name__ == '__main__':
  plt.ion()
  fig = plt.figure()
  fig.canvas.mpl_connect('close_event', handle_close)

  gdx = 311

  ltitle = ['Layer2', 'Layer5', 'Aggregate']

  white_patch = mpatches.Patch(color='white', label='Average')
  gray_patch = mpatches.Patch(color='gray', label='Individual')
  lpatch = []
  if len(ddat['dpltrials']) > 0: lpatch = [white_patch,gray_patch]

  for i,title in zip([2, 3, 1],ltitle):
    ax = fig.add_subplot(gdx)

    if i == 1: ax.set_xlabel('Time (ms)');

    if len(ddat['dpltrials']) > 0: # plot dipoles from individual trials
      for dpltrial in ddat['dpltrials']:
        ax.plot(dpltrial[:,0],dpltrial[:,i],color='gray',linewidth=2)

    ax.plot(ddat['dpl'][:,0],ddat['dpl'][:,i],'w',linewidth=5)
    ax.set_ylabel(r'(nAm $\times$ '+str(scalefctr)+')')
    if tstop != -1: ax.set_xlim((0,tstop))

    if i == 2 and len(ddat['dpltrials']) > 0: plt.legend(handles=lpatch)

    ax.set_facecolor('k')
    ax.grid(True)
    ax.set_title(title)

    gdx += 1

