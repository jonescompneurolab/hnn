import sys, os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pylab as plt
from simdat import readdpltrials

dplpath = ''; paramf = ''
for i in range(len(sys.argv)):
  if sys.argv[i].endswith('.txt'):
    dplpath = sys.argv[i]
  elif sys.argv[i].endswith('.param'):
    paramf = sys.argv[i]

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

  for i in range(3):
    ax = fig.add_subplot(gdx)

    if i == 2: ax.set_xlabel('Time (ms)');

    if len(ddat['dpltrials']) > 0: # plot dipoles from individual trials
      for dpltrial in ddat['dpltrials']:
        ax.plot(dpltrial[:,0],dpltrial[:,i+1],color='gray',linewidth=1)

    ax.plot(ddat['dpl'][:,0],ddat['dpl'][:,i+1],'w',linewidth=3)
    ax.set_ylabel('dipole (nA m)')

    if i == 0 and len(ddat['dpltrials']) > 0: plt.legend(handles=lpatch)

    ax.set_facecolor('k')
    ax.grid(True)
    ax.set_title(ltitle[i])

    gdx += 1

