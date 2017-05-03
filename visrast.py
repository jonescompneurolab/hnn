import sys, os
import numpy as np
import matplotlib.pyplot as plt
import pylab as plt
from neuron import h
from L5_pyramidal import L5Pyr
from L2_pyramidal import L2Pyr
from L2_basket import L2Basket
from L5_basket import L5Basket
from run import net

cell = net.cells[-1]

# colors for the different cell types
dclr = {'L2_pyramidal' : 'g',
        'L5_pyramidal' : 'r',
        'L2_basket' : 'k', 
        'L5_basket' : 'b'}

spkpath = ''; paramf = ''
for i in range(len(sys.argv)):
  if sys.argv[i].endswith('.txt'):
    spkpath = sys.argv[i]
  elif sys.argv[i].endswith('.param'):
    paramf = sys.argv[i]

ddat = {}
try:
  ddat['spk'] = np.loadtxt(spkpath)
except:
  print('Could not load',spkpath)
  quit()

dspk = {'Cell':([],[],[]),'Input':([],[],[])}

lt,lgid,lclr=[],[],[]
ncell = len(net.cells)
haveinputs = False
for (t,gid) in ddat['spk']:
  ty = net.gid_to_type(gid)
  if ty in dclr:
    dspk['Cell'][0].append(t)
    dspk['Cell'][1].append(gid)
    dspk['Cell'][2].append(dclr[ty])
  else:
    dspk['Input'][0].append(t)
    dspk['Input'][1].append(gid)
    dspk['Input'][2].append('w')
    haveinputs = True

def handle_close (evt): quit()

if __name__ == '__main__':
  plt.ion()
  fig = plt.figure()
  fig.canvas.mpl_connect('close_event', handle_close)
  lk = ['Cell']
  gdx = 111
  if haveinputs:
    lk.append('Input')
    gdx = 211
  for i,k in enumerate(lk):
    ax=fig.add_subplot(gdx)
    ax.scatter(dspk[k][0],dspk[k][1],c=dspk[k][2],s=8**2)
    plt.xlabel('Time (ms)');
    plt.ylabel(k + ' ID')
    ax.set_facecolor('k')
    ax.grid(True)
    if i ==0: ax.set_title('Raster Plot')
    gdx += 1

