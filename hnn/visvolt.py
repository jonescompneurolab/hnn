"""Create the somatic voltage viewing window"""

# Authors: Sam Neymotin <samnemo@gmail.com>
#          Blake Caldwell <blake_caldwell@brown.edu>

from PyQt5.QtWidgets import QSizePolicy

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

from .DataViewGUI import DataViewGUI

fontsize = plt.rcParams['font.size'] = 10
random_label = np.random.rand(100)


class VoltCanvas(FigureCanvasQTAgg):
    """Class for the somatic voltages viewer

    This is designed to be called from VoltViewGUI class to add functionality
    for loading and clearing data
    """

    def __init__(self, params, sim_data, index, parent=None, width=12,
                 height=10, dpi=120, title='Voltage Viewer'):
        FigureCanvasQTAgg.__init__(self, Figure(figsize=(width, height),
                                                dpi=dpi))
        self.title = title
        self.setParent(parent)
        self.gui = parent
        self.index = index
        FigureCanvasQTAgg.setSizePolicy(self, QSizePolicy.Expanding,
                                        QSizePolicy.Expanding)
        FigureCanvasQTAgg.updateGeometry(self)
        self.params = params
        self.invertedax = False
        self.G = gridspec.GridSpec(10, 1)

        self.sim_data = sim_data
        # colors for the different cell types
        self.dclr = {'L2_pyramidal': 'g',
                     'L5_pyramidal': 'r',
                     'L2_basket': 'w',
                     'L5_basket': 'b'}

        self.plot()

    def drawvolt(self, dvolt, times, fig, G, maxperty=10, ltextra=''):
        """Create voltage plots


        Parameters
        ----------

        dvolt: dict
            Dictionary with somatic voltages for a single trial. Keys are
            gids and value is array of somatic voltages at each timestep
        times: array
            1-D array containing the corresponding times to each somatic
            voltage
        fig: Figure object
            The figure to plot voltages
        G: GridSpec object
            Grid on which to place axes
        maxperty: int
            How many cells of a type to draw. If None, 10 cells will be shown
        ltextra: str
            String containing title of window
        """

        global random_label

        ax = fig.add_subplot(G[0:-1, :], label=random_label)
        random_label += 1

        dcnt = {}  # counts number of times cell of a type drawn
        yoff = 0

        for gid_type in self.dclr.keys():
            for gid in self.sim_data['gid_ranges'][gid_type]:
                if gid_type not in dcnt:
                    dcnt[gid_type] = 0
                elif dcnt[gid_type] > maxperty:
                    continue
                vsoma = np.array(dvolt[gid])
                ax.plot(times, -vsoma + yoff, self.dclr[gid_type],
                        linewidth=self.gui.linewidth)
                yoff += max(vsoma) - min(vsoma)
                dcnt[gid_type] += 1

        white_patch = mpatches.Patch(color='white', label='L2/3 Basket')
        green_patch = mpatches.Patch(color='green', label='L2/3 Pyr')
        red_patch = mpatches.Patch(color='red', label='L5 Pyr')
        blue_patch = mpatches.Patch(color='blue', label='L5 Basket')
        ax.legend(handles=[white_patch, green_patch, blue_patch, red_patch])

        if not self.invertedax:
            ax.set_ylim(ax.get_ylim()[::-1])
            self.invertedax = True

        ax.set_yticks([])

        ax.set_facecolor('k')
        ax.grid(True)
        if self.params['tstop'] > 0:
            ax.set_xlim((0, self.params['tstop']))

        ax.set_title(ltextra)
        ax.set_xlabel('Time (ms)')

    def plot(self):
        if len(self.sim_data['vsoma']) == 0:
            # data hasn't been loaded yet
            return

        ltextra = 'Trial ' + str(self.index)
        volt_data = self.sim_data['vsoma'][self.index]
        times = self.sim_data['dpls'][0].times

        self.drawvolt(volt_data, times, self.figure, self.G,
                      ltextra=ltextra)
        self.figure.subplots_adjust(bottom=0.01, left=0.01, right=0.99,
                                    top=0.99, wspace=0.1, hspace=0.09)

        self.draw()


class VoltViewGUI(DataViewGUI):
    """Class for displaying somatic voltages viewer

    Required parameters in params dict: N_trials, tstop
    """
    def __init__(self, CanvasType, params, sim_data, title):
        self.params = params
        super(VoltViewGUI, self).__init__(CanvasType, params, sim_data, title)

    def updateCB(self):
        self.cb.clear()
        for i in range(self.ntrial):
            self.cb.addItem('Show Trial ' + str(i + 1))
        self.cb.activated[int].connect(self.onActivated)

    def onActivated(self, idx):
        if idx != self.index:
            self.index = idx
            self.statusBar().showMessage('Loading data from trial ' +
                                          str(self.index) + '.')
            self.m.index = self.index
            self.initCanvas()
            self.m.plot()
            self.statusBar().showMessage('')
