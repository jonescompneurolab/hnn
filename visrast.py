import sys, os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pylab as plt
from neuron import h
from L5_pyramidal import L5Pyr
from L2_pyramidal import L2Pyr
from L2_basket import L2Basket
from L5_basket import L5Basket
from run import net
import paramrw

cell = net.cells[-1]

# colors for the different cell types
dclr = {'L2_pyramidal' : 'g',
        'L5_pyramidal' : 'r',
        'L2_basket' : 'w', 
        'L5_basket' : 'b'}

ntrial = 0; tstop = -1; spkpath = ''; paramf = ''; EvokedInputs = OngoingInputs = False;

for i in range(len(sys.argv)):
  if sys.argv[i].endswith('.txt'):
    spkpath = sys.argv[i]
  elif sys.argv[i].endswith('.param'):
    paramf = sys.argv[i]
    tstop = paramrw.find_param(paramf,'tstop')
    ntrial = paramrw.find_param(paramf,'N_trials')
    EvokedInputs = paramrw.usingEvokedInputs(paramf)
    OngoingInputs = paramrw.usingOngoingInputs(paramf)

ddat = {}
try:
  ddat['spk'] = np.loadtxt(spkpath)
except:
  print('Could not load',spkpath)
  quit()

dspk = {'Cell':([],[],[]),'Input':([],[],[])}
# dhist = {'Cell':([],[],[],[]), 'Input':([],[],[])}
dhist = {}
for ty in dclr.keys(): dhist[ty] = []

lt,lgid,lclr=[],[],[]
ncell = len(net.cells)
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
    dspk['Input'][1].append(gid)
    if gid == ncell:
      dspk['Input'][2].append('g')
    elif gid == ncell+1:
      dspk['Input'][2].append('r')
    else:
      dspk['Input'][2].append('w')
    haveinputs = True

binsz = 10.0
for ty in dhist.keys():
  dhist[ty].sort()
  dhist[ty] = np.histogram(dhist[ty],range=(0,tstop),bins=int(tstop/binsz))

def handle_close (evt): quit()

def drawhist (dhist):
  fig = plt.figure()
  fig.canvas.mpl_connect('close_event', handle_close)
  for ty in dhist.keys():
    plt.plot(np.arange(0,tstop,binsz),dhist[ty][0],dclr[ty],linewidth=3)
  ax = plt.gca()
  ax.set_facecolor('k')
  ax.set_xlim((0,tstop))

def drawrast ():
  fig = plt.figure()
  fig.canvas.mpl_connect('close_event', handle_close)
  lk = ['Cell']
  gdx = 111
  if haveinputs:
    lk.append('Input')
    gdx = 211
  for i,k in enumerate(['Input','Cell']):
    ax=fig.add_subplot(gdx)
    ax.scatter(dspk[k][0],dspk[k][1],c=dspk[k][2],s=8**2)
    plt.xlabel('Time (ms)');
    if k == 'Input':
      plt.ylabel('Input')
      ax.set_yticks([])
      red_patch = mpatches.Patch(color='red', label='dist')
      green_patch = mpatches.Patch(color='green', label='prox')
      plt.legend(handles=[red_patch,green_patch])
    else:
      plt.ylabel(k + ' ID')
      white_patch = mpatches.Patch(color='white', label='L2Basket')
      green_patch = mpatches.Patch(color='green', label='L2Pyr')
      red_patch = mpatches.Patch(color='red', label='L5Pyr')
      blue_patch = mpatches.Patch(color='blue', label='L5Basket')
      plt.legend(handles=[white_patch,green_patch,blue_patch,red_patch])
      ax.set_ylim((-1,ncell+1))
      ax.invert_yaxis()
    ax.set_facecolor('k')
    ax.grid(True)
    if tstop != -1: ax.set_xlim((0,tstop))
    if i ==0: ax.set_title('Raster Plot')
    gdx += 1

if __name__ == '__main__':
  plt.ion()
  if ntrial > 0:
    drawhist(dhist)
  else:
    drawrast()
