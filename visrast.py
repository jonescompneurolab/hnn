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
ddat['spk'] = np.loadtxt(spkpath)
t,gid,clr=[],[],[]
for pair in ddat['spk']:
  t.append(pair[0])
  gid.append(pair[1])  
  ty = net.gid_to_type(gid[-1])
  if ty in dclr:
    clr.append(dclr[ty])
  else:
    clr.append('w')

plt.ion()
plt.figure()
ax=plt.gca()
ax.scatter(t,gid,c=clr,s=8**2)
plt.xlabel('Time (ms)'); plt.ylabel('ID')
ax.set_facecolor('k')
ax.grid(True)
ax.set_title('Raster Plot')

