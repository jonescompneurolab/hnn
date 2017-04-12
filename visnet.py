from morphology import shapeplot
from mpl_toolkits.mplot3d import Axes3D
import pylab as plt
from neuron import h
from L5_pyramidal import L5Pyr
from L2_pyramidal import L2Pyr
from L2_basket import L2Basket
from L5_basket import L5Basket
from run import *

drawallcells = True # False 
cell = net.cells[200]

# colors for the different cell types
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

def get3dinfo (sidx,eidx):
  llx,lly,llz,lldiam = [],[],[],[]
  for i in range(sidx,eidx,1):
    lx,ly,lz,ldiam = net.cells[i].get3dinfo()
    llx.append(lx); lly.append(ly); llz.append(lz); lldiam.append(ldiam)
  return llx,lly,llz,lldiam

def arrangelayers ():
  # offsets for L2, L5 cells so that L5 below L2 in display
  dyoff = {L2Pyr: 1000, 'L2_pyramidal' : 1000,
           L5Pyr: -1000, 'L5_pyramidal' : -1000,
           L2Basket: 1000, 'L2_basket' : 1000,
           L5Basket: -1000, 'L5_basket' : -1000}
  for cell in net.cells: cell.translate3d(0,dyoff[cell.celltype],0)

arrangelayers()

llx,lly,llz,lldiam = get3dinfo(0,270)

plt.ion(); fig = plt.figure()

shapeax = plt.subplot(111, projection='3d')
shapeax.set_xlabel('X',fontsize=24); shapeax.set_ylabel('Y',fontsize=24); shapeax.set_zlabel('Z',fontsize=24)
shapeax.view_init(elev=105,azim=-71)

def countseg (ls): return sum([s.nseg for s in ls])

defclr = 'k'; selclr = 'r'

"""
#shapelines = shapeplot(h,shapeax,lw=8,cvals=[defclr for i in range(allseg)],picker=5)
if drawallcells:
  shapelines = shapeplot(h,shapeax,lw=3)
else:
  shapelines = shapeplot(h,shapeax,sections=ls,lw=3,picker=5)
"""

def drawcells3d ():
  lshapelines = []
  for ty in whichdraw:
    ls = dsec[ty]
    lshapelines.append(shapeplot(h,shapeax,sections=ls,cvals=[dclr[ty] for i in range(countseg(ls))],lw=dlw[ty]))
  return lshapelines

drawcells3d()

def onclick(event):
  try:
    print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
          (event.button, event.x, event.y, event.xdata, event.ydata))
  except:
    pass

def setcolor (ls,clr):
  for l in ls: l.set_color(clr)

# click on section event handler - not used for network 
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

def setcallbacks ():
  lcid = []
  if False: lcid.append(fig.canvas.mpl_connect('button_press_event', onclick))
  if not drawallcells: lcid.append(fig.canvas.mpl_connect('pick_event', onpick))
  return lcid

lcid = setcallbacks()

