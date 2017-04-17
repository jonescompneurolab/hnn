## make this version of pyqtgraph importable before any others
## we do this to make sure that, when running examples, the correct library
## version is imported (if there are multiple versions present).
import sys, os

if not hasattr(sys, 'frozen'):
    if __file__ == '<stdin>':
        path = os.getcwd()
    else:
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path.rstrip(os.path.sep)
    if 'pyqtgraph' in os.listdir(path):
        sys.path.insert(0, path) ## examples adjacent to pyqtgraph (as in source tree)
    else:
        for p in sys.path:
            if len(p) < 3:
                continue
            if path.startswith(p):  ## If the example is already in an importable location, promote that location
                sys.path.remove(p)
                sys.path.insert(0, p)

## should force example to use PySide instead of PyQt
if 'pyside' in sys.argv:  
    from PySide import QtGui
elif 'pyqt' in sys.argv: 
    from PyQt4 import QtGui
elif 'pyqt5' in sys.argv: 
    from PyQt5 import QtGui
else:
    from pyqtgraph.Qt import QtGui

import pyqtgraph as pg    
    
## Force use of a specific graphics system
use_gs = 'default'
for gs in ['raster', 'native', 'opengl']:
    if gs in sys.argv:
        use_gs = gs
        QtGui.QApplication.setGraphicsSystem(gs)
        break

print("Using %s (%s graphics system)" % (pg.Qt.QT_LIB, use_gs))

## Enable fault handling to give more helpful error messages on crash. 
## Only available in python 3.3+
try:
    import faulthandler
    faulthandler.enable()
except ImportError:
    pass

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import pyqtgraph as pg
import numpy as np

from morphology import shapeplot, getshapecoords
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
dclr = {'L2_pyramidal' : 'g', L2Pyr: (0.,1.,0.,1.),
        'L5_pyramidal' : 'r', L5Pyr: (1.,0.,0.,1.),
        'L2_basket' : 'k', L2Basket: (1.,1.,1.,1.),
        'L5_basket' : 'b', L5Basket: (0.,0.,1.,1.)}

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

llx,lly,llz,lldiam = get3dinfo(0,270)

def countseg (ls): return sum([s.nseg for s in ls])

defclr = 'k'; selclr = 'r'
useGL = True
fig = None

def drawcells3d ():
  global shapeax,fig
  plt.ion(); fig = plt.figure()
  shapeax = plt.subplot(111, projection='3d')
  #shapeax.set_xlabel('X',fontsize=24); shapeax.set_ylabel('Y',fontsize=24); shapeax.set_zlabel('Z',fontsize=24)
  shapeax.set_xticks([]); shapeax.set_yticks([]); shapeax.set_zticks([])
  shapeax.view_init(elev=105,azim=-71)
  shapeax.grid(False)
  lshapelines = []
  for ty in whichdraw:
    ls = dsec[ty]
    lshapelines.append(shapeplot(h,shapeax,sections=ls,cvals=[dclr[ty] for i in range(countseg(ls))],lw=dlw[ty]))
  return lshapelines

if not useGL: drawcells3d()

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
  if useGL: return []
  lcid = []
  if False: lcid.append(fig.canvas.mpl_connect('button_press_event', onclick))
  if not drawallcells: lcid.append(fig.canvas.mpl_connect('pick_event', onpick))
  return lcid

lcid = setcallbacks()

#
def drawinputs (cell,clr,ax):
  for lsrc in [cell.ncfrom_L2Pyr, cell.ncfrom_L2Basket, cell.ncfrom_L5Pyr, cell.ncfrom_L5Basket]:
    for src in lsrc:
      precell = src.precell()
      ax.plot([precell.pos[0],cell.pos[0]],[precell.pos[1],cell.pos[1]],clr)

#
def drawconn2d ():
  plt.figure()
  ax = plt.gca()
  """
  loc = np.array(net.pos_dict['L2_basket'])
  plot(loc[:,0],loc[:,1],'ko',markersize=14)
  loc = np.array(net.pos_dict['L2_pyramidal'])
  plot(loc[:,0],loc[:,1],'ro',markersize=14)
  loc = np.array(net.pos_dict['L2_basket'])
  plot(loc[:,0],loc[:,1],'bo',markersize=10)
  """
  lx = [cell.pos[0] for cell in net.cells]
  ly = [cell.pos[1] for cell in net.cells]
  ax.plot(lx,ly,'ko',markersize=14)
  """
  self.ncfrom_L2Pyr = []
  self.ncfrom_L2Basket = []
  self.ncfrom_L5Pyr = []
  self.ncfrom_L5Basket = []
  """
  for cell in net.cells:
    drawinputs(cell,'r',ax)
    break

app = QtGui.QApplication([])
w = gl.GLViewWidget()

"""
gx = gl.GLGridItem()
gx.rotate(90, 0, 1, 0)
#gx.translate(-10, 0, 0)
w.addItem(gx)
gy = gl.GLGridItem()
gy.rotate(90, 1, 0, 0)
#gy.translate(0, -10, 0)
w.addItem(gy)
gz = gl.GLGridItem()
#gz.translate(0, 0, -10)
w.addItem(gz)
"""

for cell in net.cells:
  ls = cell.get_sections()
  lx,ly,lz = getshapecoords(h,ls)  
  pts = np.vstack([lx,ly,lz]).transpose()
  plt = gl.GLLinePlotItem(pos=pts, color=dclr[type(cell)], width=2.2, antialias=True, mode='lines')
  w.addItem(plt)

w.opts['distance'] = 4320.9087386478195
w.opts['elevation']=105
w.opts['azimuth']=-71
w.opts['fov'] = 90
w.show()
w.setWindowTitle('Network Visualization')

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
  import sys
  if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    QtGui.QApplication.instance().exec_()

