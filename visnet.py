from PyNeuronToolbox.morphology import shapeplot
from mpl_toolkits.mplot3d import Axes3D
from PyNeuronToolbox.morphology import shapeplot
from mpl_toolkits.mplot3d import Axes3D
import pylab as plt
from neuron import h
from L5_pyramidal import L5Pyr
from L2_pyramidal import L2Pyr

h('dp_total_L5=dp_total_L2=0')

cell5 = L5Pyr((0,0))
cell2 = L2Pyr((0,1))

ls = list(h.allsec())
len(ls) # 25

h.define_shape()
plt.ion()
plt.figure(figsize=(6,6))

shapeax = plt.subplot(111, projection='3d')
shapeplot(h,shapeax,lw=4)

