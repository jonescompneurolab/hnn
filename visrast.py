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

def plotsimdatgl (figure,G,fig):
  global invertedhistax
  if len(ddat.keys()) == 0: return

  try:
    # fig,ax = plt.subplots(); ax.cla()
    xlim_new = (ddat['dpl'][0,0],ddat['dpl'][-1,0])

    # set number of bins (150 bins per 1000ms)
    bins = ceil(150. * (xlim_new[1] - xlim_new[0]) / 1000.) # bins needs to be an int

    # plot histograms of inputs
    print(dfile['spk'],dfile['outparam'])
    extinputs = None

    try:
      extinputs = spikefn.ExtInputs(dfile['spk'], dfile['outparam'])
      extinputs.add_delay_times()
    except:
      print('problem with extinputs')

    hist = {}
    axdist = figure.add_subplot(G[0,0]); axdist.cla() # distal inputs
    axprox = figure.add_subplot(G[1,0]); axprox.cla() # proximal inputs
    if extinputs is not None: # only valid param.txt file after sim was run
      hist['feed_dist'] = extinputs.plot_hist(axdist,'dist',ddat['dpl'][:,0],bins,xlim_new,color='r')
      hist['feed_prox'] = extinputs.plot_hist(axprox,'prox',ddat['dpl'][:,0],bins,xlim_new,color='g')
      if not invertedhistax:# only need to invert axis 1X
        axdist.invert_yaxis()
        invertedhistax = True
      for ax in [axdist,axprox]:
        ax.set_xlim(xlim_new)
        ax.legend()          

    ax = figure.add_subplot(G[2:5,0]); ax.cla() # dipole
    ax.plot(ddat['dpl'][:,0],ddat['dpl'][:,1],'b')
    ax.set_ylabel('dipole (nA m)')
    ax.set_xlim(ddat['dpl'][0,0],ddat['dpl'][-1,0])
    ax.set_ylim(np.amin(ddat['dpl'][:,1]),np.amax(ddat['dpl'][:,1])) # right ylim??
    print('ylim is : ', np.amin(ddat['dpl'][:,1]),np.amax(ddat['dpl'][:,1]))
    # truncate tvec and dpl data using logical indexing
    #t_range = dpl.t[(dpl.t >= xmin) & (dpl.t <= xmax)]
    #dpl_range = dpl.dpl['agg'][(dpl.t >= xmin) & (dpl.t <= xmax)]

    ax = figure.add_subplot(G[6:10,0]); ax.cla() # specgram
    ds = ddat['spec']
    cax = ax.imshow(ds['TFR'],extent=(ds['time'][0],ds['time'][-1],ds['freq'][-1],ds['freq'][0]),aspect='auto',origin='upper',cmap=plt.get_cmap('jet'))
    ax.set_ylabel('Frequency (Hz)')
    ax.set_xlabel('Time (ms)')
    ax.set_xlim(ds['time'][0],ds['time'][-1])
    ax.set_ylim(ds['freq'][-1],ds['freq'][0])
    cbaxes = fig.add_axes([0.915, 0.125, 0.03, 0.2]) 
    cb = plt.colorbar(cax, cax = cbaxes)  
    #self.fig.tight_layout() # tight_layout will mess up colorbar location
  except:
    print('ERR: in plot')

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
  app = QtGui.QApplication([])
  view = pg.GraphicsView()
  l = pg.GraphicsLayout(border=(100,100,100))
  view.setCentralItem(l)
  view.show()
  view.setWindowTitle('Spike Raster')
  view.resize(800,600)
  if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    QtGui.QApplication.instance().exec_()
