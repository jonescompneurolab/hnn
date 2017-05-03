import sys, os
import pyqtgraph as pg        
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
from run import net

cell = net.cells[-1]

# colors for the different cell types
dclr = {'L2_pyramidal' : 'g', L2Pyr: (0.,1.,0.,0.6),
        'L5_pyramidal' : 'r', L5Pyr: (1.,0.,0.,0.6),
        'L2_basket' : 'k', L2Basket: (1.,1.,1.,0.6),
        'L5_basket' : 'b', L5Basket: (0.,0.,1.,0.6)}

spkpath = ''; paramf = ''
for i in range(len(sys.argv)):
  if sys.argv[i].endswith('.txt'):
    spkpath = sys.argv[i]
  elif sys.argv[i].endswith('.param'):
    paramf = sys.argv[i]

ddat = {}
ddat['spk'] = np.loadtxt(spkpath)
t,gid=[],[]
for pair in ddat['spk']:
  t.append(pair[0])
  gid.append(pair[1])

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
  app = QtGui.QApplication([])
  view = pg.GraphicsView()
  l = pg.GraphicsLayout(border=(100,100,100))
  view.setCentralItem(l)
  myplot = l.addPlot(row=1,col=1)

  # myplot.plot(t,gid,pen=None,symbol='o')
  # sp = pg.ScatterPlotItem(t,gid)

  view.show()
  view.setWindowTitle('Spike Raster')
  view.resize(800,600)
  if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    QtGui.QApplication.instance().exec_()
