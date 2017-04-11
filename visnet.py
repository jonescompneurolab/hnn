from morphology import shapeplot, morphology_to_dict
from mpl_toolkits.mplot3d import Axes3D
import pylab as plt
from neuron import h
from L5_pyramidal import L5Pyr
from L2_pyramidal import L2Pyr
from L2_basket import L2Basket
from L5_basket import L5Basket
from run import *

# ls = list(h.allsec())

cell = net.cells[200]

ls = []
for c in net.cells:
  if type(c) == L2Pyr: # L5Pyr: # L5Basket: # L2Basket:
    cell = c
    lss = c.get_sections()
    for s in lss: ls.append(s)
    #if len(ls) > 3*len(lss): break
    break

lsecnames = cell.get_section_names()

print('len(ls) = ',len(ls))
for s in ls: s.nseg=1

def get3dinfo (sidx,eidx):
  llx,lly,llz,lldiam = [],[],[],[]
  for i in range(sidx,eidx,1):
    lx,ly,lz,ldiam = net.cells[i].get3dinfo()
    llx.append(lx); lly.append(ly); llz.append(lz); lldiam.append(ldiam)
  return llx,lly,llz,lldiam

#h.define_shape()

#llx0,lly0,llz0,lldiam0 = get3dinfo(200,210)

# net.movecellstopos()

#llx1,lly1,llz1,lldiam1 = get3dinfo(200,210)

plt.ion(); fig = plt.figure()

allseg = sum([s.nseg for s in ls])

shapeax = plt.subplot(111, projection='3d')
shapeax.set_xlabel('X',fontsize=24); shapeax.set_ylabel('Y',fontsize=24); shapeax.set_zlabel('Z',fontsize=24)
#shapeax.view_init(75,66)

#shapeax.set_xlim3d((-425.11876526,  1890.3420929))
#shapeax.set_ylim3d((-173.77793655,  736.48745499))
#shapeax.set_zlim3d((0,100))

defclr = 'k'; selclr = 'r'
#shapelines = shapeplot(h,shapeax,lw=8)
#shapelines = shapeplot(h,shapeax,lw=8,cvals=[defclr for i in range(allseg)],picker=5)
shapelines = shapeplot(h,shapeax,sections=ls,lw=3,picker=5)

def onclick(event):
  try:
    print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
          (event.button, event.x, event.y, event.xdata, event.ydata))
  except:
    pass

# cid = fig.canvas.mpl_connect('button_press_event', onclick)

# net has cells - net.pos_dict has locations
# net.pos_dict.keys()
# dict_keys(['L2_basket', 'evdist', 'extgauss', 'L5_pyramidal', 'extpois', 'extinput', 'L5_basket', 'evprox1', 'evprox0', 'L2_pyramidal'])

def setcolor (ls,clr):
  for l in ls: l.set_color(clr)

def onpick (event):
  print('onpick')
  thisline = event.artist
  c = thisline.get_color()
  idx = -1
  setcolor(shapelines,defclr)    
  for idx,l in enumerate(shapelines):
    if l == thisline:
      break
  try:
    print('idx is ', idx, 'selected',lsecnames[idx])
    xdata = thisline.get_xdata()
    ydata = thisline.get_ydata()
    ind = event.ind
    points = tuple(zip(xdata[ind], ydata[ind]))
    print('onpick points:', points)
    if c == defclr:
      thisline.set_color(selclr)
    else:
      thisline.set_color(defclr)
    print(ind)
    #print(dir(thisline))
  except:
    pass

cid2 = fig.canvas.mpl_connect('pick_event', onpick)

