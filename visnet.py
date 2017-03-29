from PyNeuronToolbox.morphology import shapeplot
from mpl_toolkits.mplot3d import Axes3D
from PyNeuronToolbox.morphology import shapeplot
from mpl_toolkits.mplot3d import Axes3D
import pylab as plt
from neuron import h
from L5_pyramidal import L5Pyr
from L2_pyramidal import L2Pyr

h('dp_total_L5=dp_total_L2=0')

lcell2 =  []
lcell5 =  []

ncell = 1

for i in range(ncell): lcell2.append(L2Pyr((0,i)))
for i in range(ncell): lcell5.append(L5Pyr((i,0)))

ls = list(h.allsec())
print('len(ls) = ',len(ls))

h.define_shape()
plt.ion()
plt.figure(figsize=(6,6))

allseg = sum([s.nseg for s in ls])

shapeax = plt.subplot(111, projection='3d')
shapeax.view_init(75,66)
shapelines = shapeplot(h,shapeax,lw=8,cvals=['r' for i in range(allseg)])

