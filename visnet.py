from morphology import shapeplot, morphology_to_dict
from mpl_toolkits.mplot3d import Axes3D
import pylab as plt
from neuron import h
from L5_pyramidal import L5Pyr
from L2_pyramidal import L2Pyr
from L2_basket import L2Basket
from L5_basket import L5Basket
from run import *

drawallcells = True # False # True
ndraw = 100
cell = net.cells[200]

dclr = {'L2_pyramidal' : 'g', L2Pyr: 'g',
        'L5_pyramidal' : 'r', L5Pyr: 'r',
        'L2_basket' : 'k', L2Basket: 'k',
        'L5_basket' : 'b', L5Basket: 'b'}

def cellsecbytype (ty):
  lss = []
  for cell in net.cells:
    if type(cell) == ty:
      ls = cell.get_sections()
      for s in ls: lss.append(s)
  return lss

def getdrawsec (ncells=1,ct=L2Pyr):
  global cell
  if drawallcells: return list(h.allsec())
  ls = []
  nfound = 0
  for c in net.cells:
    if type(c) == ct: 
      cell = c
      lss = c.get_sections()
      for s in lss: ls.append(s)
      nfound += 1
      if nfound >= ncells: break
  return ls

dsec = {}
for ty in [L2Pyr, L5Pyr, L2Basket, L5Basket]: dsec[ty] = cellsecbytype(ty)
dlw = {L2Pyr:1, L5Pyr:1,L2Basket:4,L5Basket:4}
whichdraw = [L2Pyr, L2Basket, L5Pyr, L5Basket]

lsecnames = cell.get_section_names()

# for s in ls: s.nseg=1

def get3dinfo (sidx,eidx):
  llx,lly,llz,lldiam = [],[],[],[]
  for i in range(sidx,eidx,1):
    lx,ly,lz,ldiam = net.cells[i].get3dinfo()
    llx.append(lx); lly.append(ly); llz.append(lz); lldiam.append(ldiam)
  return llx,lly,llz,lldiam

llx0,lly0,llz0,lldiam0 = get3dinfo(0,270)

net.movecellstopos()
# h.define_shape()

dyoff = {L2Pyr: 1000, 'L2_pyramidal' : 1000,
         L5Pyr: -1000, 'L5_pyramidal' : -1000,
         L2Basket: 1000, 'L2_basket' : 1000,
         L5Basket: -1000, 'L5_basket' : -1000}
for cell in net.cells: cell.translate3d(0,dyoff[cell.celltype],0)

llx1,lly1,llz1,lldiam1 = get3dinfo(0,270)

plt.ion(); fig = plt.figure()

# allseg = sum([s.nseg for s in ls])

shapeax = plt.subplot(111, projection='3d')
shapeax.set_xlabel('X',fontsize=24); shapeax.set_ylabel('Y',fontsize=24); shapeax.set_zlabel('Z',fontsize=24)
#shapeax.view_init(75,66)
shapeax.view_init(elev=120,azim=-90)

def countseg (ls): return sum([s.nseg for s in ls])

#shapeax.set_xlim3d((-425.11876526,  1890.3420929))
#shapeax.set_ylim3d((-173.77793655,  736.48745499))
#shapeax.set_zlim3d((0,100))

defclr = 'k'; selclr = 'r'

"""
#shapelines = shapeplot(h,shapeax,lw=8,cvals=[defclr for i in range(allseg)],picker=5)
if drawallcells:
  shapelines = shapeplot(h,shapeax,lw=3)
else:
  shapelines = shapeplot(h,shapeax,sections=ls,lw=3,picker=5)
"""

for ty in whichdraw:
  ls = dsec[ty]
  shapelines = shapeplot(h,shapeax,sections=ls,cvals=[dclr[ty] for i in range(countseg(ls))],lw=dlw[ty])

def onclick(event):
  try:
    print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
          (event.button, event.x, event.y, event.xdata, event.ydata))
  except:
    pass

# cid = fig.canvas.mpl_connect('button_press_event', onclick)

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

if not drawallcells and ndraw==1: cid2 = fig.canvas.mpl_connect('pick_event', onpick)

