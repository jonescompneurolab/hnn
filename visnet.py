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

for i in range(ncell): lcell2.append(L2Pyr((0,(i+1)*300)))
for i in range(ncell): lcell5.append(L5Pyr((i,0)))

ls = list(h.allsec())
print('len(ls) = ',len(ls))

h.define_shape()
plt.ion()
fig = plt.figure()#figsize=(6,6))

allseg = sum([s.nseg for s in ls])

shapeax = plt.subplot(111, projection='3d')
shapeax.view_init(75,66)

shapeax.set_xlim3d((-425.11876526,  1890.3420929))
shapeax.set_ylim3d((-173.77793655,  736.48745499))
shapeax.set_zlim3d((0,100))

shapelines = shapeplot(h,shapeax,lw=8,cvals=['r' for i in range(allseg)],picker=5)

def onclick(event):
  try:
    print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
          (event.button, event.x, event.y, event.xdata, event.ydata))
  except:
    pass

# cid = fig.canvas.mpl_connect('button_press_event', onclick)

def onpick(event):
  thisline = event.artist
  xdata = thisline.get_xdata()
  ydata = thisline.get_ydata()
  ind = event.ind
  points = tuple(zip(xdata[ind], ydata[ind]))
  print('onpick points:', points)
  c = thisline.get_color()
  thisline.set_color('b')
  #print(dir(thisline))

cid2 = fig.canvas.mpl_connect('pick_event', onpick)

