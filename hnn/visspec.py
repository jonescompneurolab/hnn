"""Create the Spectrogram viewing window"""

# Authors: Sam Neymotin <samnemo@gmail.com>
#          Blake Caldwell <blake_caldwell@brown.edu>

import numpy as np
import os

from PyQt5.QtWidgets import QSizePolicy, QAction, QFileDialog
from PyQt5.QtGui import QIcon

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from hnn_core.dipole import average_dipoles, Dipole

from .DataViewGUI import DataViewGUI
from .specfn import plot_spec, extract_spec

fontsize = plt.rcParams['font.size'] = 10
random_label = np.random.rand(100)


class SpecCanvas(FigureCanvasQTAgg):
    """Class for the Spectrogram viewer

    This is designed to be called from SpecViewGUI class to add functionality
    for loading and clearing data
    """
    def __init__(self, params, sim_data, index, parent=None, width=12,
                 height=10, dpi=120, title='Spectrogram Viewer'):
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
        self.invertedhistax = False
        self.G = gridspec.GridSpec(10, 1)
        self.dpls = self.gui.dpls
        self.specs = self.gui.specs
        self.avg_dpl = self.gui.avg_dpl
        self.lax = []

        if 'spec_cmap' in self.params:
            self.spec_cmap = self.params['spec_cmap']
        else:
            # default to jet, but allow user to change in param file
            self.spec_cmap = 'jet'

        self.plot()

    def clearaxes(self):
        for ax in self.lax:
            ax.set_yticks([])
            ax.cla()

    def drawspec(self, dpls, avgdipole, spec_data, fig, G,
                 ltextra=''):
        global random_label

        ntrial = len(spec_data)
        if ntrial == 0:
            return

        if self.index == 0:
            ntrial = 1

        plt.ion()

        gdx = 211

        ax = fig.add_subplot(gdx, label=random_label)
        random_label += 1
        lax = [ax]

        # use spectogram limits (missing first 50 ms b/c edge effects)
        xlim = (spec_data[0]['time'][0],
                spec_data[0]['time'][-1])

        if self.index == 0:
            for dpltrial in dpls:
                ax.plot(dpltrial.times, dpltrial.data['agg'],
                        linewidth=self.gui.linewidth, color='gray')
            ax.plot(avgdipole.times, avgdipole.data['agg'],
                    linewidth=self.gui.linewidth + 1, color='black')
        else:
            ax.plot(dpls[self.index - 1].times,
                    dpls[self.index - 1].data['agg'],
                    linewidth=self.gui.linewidth + 1,
                    color='gray')

        ax.set_xlim(xlim)
        ax.set_ylabel('Dipole (nAm)')

        gdx = 212

        ax = fig.add_subplot(gdx, label=random_label)
        random_label += 1
        ntrial = len(dpls)

        plot_spec(ax, spec_data, ntrial, self.spec_cmap, xlim)

        lax.append(ax)

        return lax

    def plot(self):
        ltextra = 'Trial ' + str(self.index)
        if self.index == 0:
            ltextra = 'All Trials'
        self.lax = self.drawspec(self.dpls, self.avg_dpl, self.specs,
                                 self.figure, self.G, ltextra=ltextra)
        self.figure.subplots_adjust(bottom=0.06, left=0.06, right=0.98,
                                    top=0.97, wspace=0.1, hspace=0.09)
        self.draw()


class SpecViewGUI(DataViewGUI):
    """Class for displaying spectrogram viewer

    Required parameters in params dict: f_max_spec, sim_prefix, spec_cmap
    """
    def __init__(self, CanvasType, params, sim_data, title):
        self.specs = []
        self.lextfiles = []  # external data files
        self.dpls = None
        self.avg_dpl = []
        self.params = params

        # used by loadSimData
        self.sim_data = sim_data
        super(SpecViewGUI, self).__init__(CanvasType, self.params, sim_data,
                                          title)
        self._addLoadDataActions()
        self.loadSimData(self.params['sim_prefix'], self.params['f_max_spec'])

    def _addLoadDataActions(self):
        loadDataFile = QAction(QIcon.fromTheme('open'), 'Load data.', self)
        loadDataFile.setShortcut('Ctrl+D')
        loadDataFile.setStatusTip('Load experimental (.txt) data.')
        loadDataFile.triggered.connect(self.loadDisplayData)

        clearDataFileAct = QAction(QIcon.fromTheme('close'), 'Clear data.',
                                   self)
        clearDataFileAct.setShortcut('Ctrl+C')
        clearDataFileAct.setStatusTip('Clear data.')
        clearDataFileAct.triggered.connect(self.clearDataFile)

        self.fileMenu.addAction(loadDataFile)
        self.fileMenu.addAction(clearDataFileAct)

    def loadSimData(self, sim_prefix, f_max_spec):
        """Load and plot from SimData"""

        # store copy of data in this object, that can be reused by
        # canvas (self.m) on re-instantiation
        if self.sim_data is not None:
            self.avg_dpl = self.sim_data['avg_dpl']
            self.dpls = self.sim_data['dpls']
            self.specs = self.sim_data['spec']
            if self.specs is None or len(self.specs) == 0:
                self.specs = extract_spec(self.dpls, f_max_spec)

            # populate the data inside canvas object before calling
            # self.m.plot()
            self.m.avg_dpl = self.avg_dpl
            self.m.dpls = self.dpls
            self.m.specs = self.specs

            self.ntrial = len(self.specs)

        self.updateCB()
        self.printStat('Extracted ' + str(len(self.m.specs)) +
                       ' spectrograms for ' + sim_prefix)

        if len(self.m.specs) > 0:
            self.printStat('Plotting Spectrograms.')
            self.m.plot()
            self.m.draw()  # make sure new lines show up in plot
            self.printStat('')

    def loadDisplayData(self):
        """Load dipole(s) from .txt file and plot spectrograms"""
        fname = QFileDialog.getOpenFileName(self, 'Open .txt file', 'data')
        fname = os.path.abspath(fname[0])

        if not os.path.isfile(fname):
            return

        self.m.index = 0
        file_data = np.loadtxt(fname, dtype=float)
        if file_data.shape[1] > 2:
            # Multiple trials contained in this file. Only 'agg' dipole is
            # present for each trial
            dpls = []
            ntrials = file_data.shape[1]
            for trial in range(1, ntrials):
                dpl_data = np.c_[file_data[:, trial],
                                 np.zeros(len(file_data[:, trial])),
                                 np.zeros(len(file_data[:, trial]))]
                dpl = Dipole(file_data[:, 0], dpl_data)
                dpls.append(dpl)
            self.dpls = dpls
            self.avg_dpl = average_dipoles(dpls)
        else:
            # Normal dipole file saved by HNN. There is a single trial with
            # column 0: times, column 1: 'agg' dipole, column 2: 'L2' dipole
            # and column 3: 'L5' dipole

            ntrials = 1
            dpl_data = np.c_[file_data[:, 1],
                             file_data[:, 1],
                             file_data[:, 1]]
            dpl = Dipole(file_data[:, 0], dpl_data)

            self.avg_dpl = dpl
            self.dpls = [self.avg_dpl]

        print('Loaded data from %s: %d trials.' % (fname, ntrials))
        print('Extracting Spectrograms...')
        # a progress bar would be helpful right here!
        self.specs = extract_spec(self.dpls, self.params['f_max_spec'])

        # updateCB depends on ntrial being set
        self.ntrial = len(self.specs)
        self.updateCB()
        self.printStat('Extracted ' + str(len(self.specs)) +
                       ' spectrograms from ' + fname)
        self.lextfiles.append(fname)

        if len(self.specs) > 0:
            self.printStat('Plotting Spectrograms.')
            self.m.specs = self.specs
            self.m.dpls = self.dpls
            self.m.avg_dpl = self.avg_dpl
            self.m.plot()
            self.m.draw()  # make sure new lines show up in plot
            self.printStat('')

    def clearDataFile(self):
        """Clear data from file and revert to SimData"""
        self.specs = []
        self.lextfiles = []
        self.m.index = 0
        self.loadSimData(self.params['sim_prefix'], self.params['f_max_spec'])
