import os
from math import sqrt
from copy import deepcopy

from PyQt5.QtWidgets import QSizePolicy, QAction, QFileDialog
from PyQt5.QtGui import QIcon

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

from hnn_core.dipole import average_dipoles, Dipole

from .DataViewGUI import DataViewGUI
from .specfn import spec_dpl_kernel, extract_spec

fontsize = plt.rcParams['font.size'] = 10
random_label = np.random.rand(100)


def extract_psd(dpl, f_max_spec):
    """Extract PSDs for layers using Morlet method

    Parameters
    ----------
    dpls: Dipole object
        Dipole for a single trial
    f_max_spec: float
        Maximum frequency of analysis

    Returns
    ----------
    F: array
        Frequencies associated with Morlet spectral analysis
    psds: list of MortletSpec objects
        List containing results of spectral analysis for each layer

    """

    psds = []
    dt = dpl.times[1] - dpl.times[0]
    tstop = dpl.times[-1]

    spec_results = spec_dpl_kernel(dpl, f_max_spec, dt, tstop)

    for col in ['TFR', 'TFR_L2', 'TFR_L5']:
        psds.append(np.mean(spec_results[col], axis=1))

    return spec_results['freq'], np.array(psds)


class PSDCanvas(FigureCanvasQTAgg):
    def __init__(self, params, sim_data, index, parent=None, width=12,
                 height=10, dpi=120, title='PSD Viewer'):
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
        self.avg_spec = self.gui.avg_spec
        self.avg_dpl = self.gui.avg_dpl
        self.lextdatobj = []

        self.plot()

    def drawpsd(self, dspec, fig, G, ltextra=''):
        global random_label

        lax = []
        avgs = []
        stds = []

        lkF = ['f_L2', 'f_L5', 'f_L2']
        lkS = ['TFR_L2', 'TFR_L5', 'TFR']

        plt.ion()

        gdx = 311

        ltitle = ['Layer 2/3', 'Layer 5', 'Aggregate']

        yl = [1e9, -1e9]

        for _, kS in enumerate(lkS):
            avg = np.mean(dspec[kS], axis=1)
            std = np.std(dspec[kS], axis=1) / sqrt(dspec[kS].shape[1])
            yl[0] = min(yl[0], np.amin(avg - std))
            yl[1] = max(yl[1], np.amax(avg + std))
            avgs.append(avg)
            stds.append(std)

        yl = tuple(yl)
        xl = (dspec['f_L2'][0], dspec['f_L2'][-1])

        for i, kS in enumerate(lkS):
            ax = fig.add_subplot(gdx, label=random_label)
            random_label += 1
            lax.append(ax)

            if i == 2:
                ax.set_xlabel('Frequency (Hz)')

            ax.plot(dspec[lkF[i]], np.mean(dspec[lkS[i]], axis=1), color='w',
                    linewidth=self.gui.linewidth + 2)
            ax.plot(dspec[lkF[i]], avgs[i] - stds[i], color='gray',
                    linewidth=self.gui.linewidth)
            ax.plot(dspec[lkF[i]], avgs[i] + stds[i], color='gray',
                    linewidth=self.gui.linewidth)

            ax.set_ylim(yl)
            ax.set_xlim(xl)

            ax.set_facecolor('k')
            ax.grid(True)
            ax.set_title(ltitle[i])
            ax.set_ylabel(r'$nAm^2$')

            gdx += 1
        return lax

    def clearaxes(self):
        for ax in self.lax:
            ax.set_yticks([])
            ax.cla()

    def clearlextdatobj(self):
        # clear list of external data objects
        for o in self.lextdatobj:
            if isinstance(o, list):
                # this is the plot. clear the line
                o[0].set_visible(False)
            else:
                # this is the legend entry
                o.set_visible(False)
        del self.lextdatobj
        self.lextdatobj = []  # reset list of external data objects

    def plotextdat(self, lF, lextpsd, lextfiles):
        """plot 'external' data (e.g. from experiment/other simulation)"""

        white_patch = mpatches.Patch(color='white', label='Simulation')
        self.lpatch = [white_patch]

        ax = self.lax[2]  # plot on agg

        yl = ax.get_ylim()

        cmap = plt.get_cmap('nipy_spectral')
        csm = plt.cm.ScalarMappable(cmap=cmap)
        csm.set_clim((0, 100))

        for f, lpsd, fname in zip(lF, lextpsd, lextfiles):
            clr = csm.to_rgba(int(np.random.RandomState().uniform(5, 101, 1)))
            avg = np.mean(lpsd, axis=0)
            std = np.std(lpsd, axis=0) / sqrt(lpsd.shape[1])
            self.lextdatobj.append(ax.plot(f, avg, color=clr,
                                           linewidth=self.gui.linewidth + 2))
            self.lextdatobj.append(ax.plot(f, avg - std, '--', color=clr,
                                           linewidth=self.gui.linewidth))
            self.lextdatobj.append(ax.plot(f, avg + std, '--', color=clr,
                                           linewidth=self.gui.linewidth))
            yl = ((min(yl[0], min(avg))), (max(yl[1], max(avg))))
            label_str = fname.split(os.path.sep)[-1].split('.txt')[0]
            new_patch = mpatches.Patch(color=clr, label=label_str)
            self.lpatch.append(new_patch)

        ax.set_ylim(yl)
        self.lextdatobj.append(ax.legend(handles=self.lpatch))

    def plot(self):
        if len(self.specs) == 0:
            # data hasn't been loaded yet
            return

        if self.index == 0:
            ltextra = 'All Trials'
            self.lax = self.drawpsd(self.avg_spec, self.figure, self.G,
                                    ltextra=ltextra)
        else:
            ltextra = 'Trial ' + str(self.index)
            self.lax = self.drawpsd(self.specs[self.index - 1], self.figure,
                                    self.G, ltextra=ltextra)

        self.figure.subplots_adjust(bottom=0.06, left=0.06, right=0.98,
                                    top=0.97, wspace=0.1, hspace=0.09)

        self.draw()


class PSDViewGUI(DataViewGUI):
    """Class for displaying spectrogram viewer

    Required parameters: N_trials, f_max_spec, sim_prefix
    """
    def __init__(self, CanvasType, params, sim_data, title):
        self.specs = []  # used by drawspec
        self.psds = []  # used by plotextdat
        self.lextfiles = []  # external data files
        self.lF = []  # frequencies associated with external data psd
        self.dpls = None
        self.avg_dpl = []
        self.avg_spec = {}
        self.params = params

        # used by loadSimData
        self.sim_data = sim_data
        super(PSDViewGUI, self).__init__(CanvasType, params, sim_data, title)
        self.addLoadDataActions()
        self.loadSimData()

    def addLoadDataActions(self):
        loadDataFile = QAction(QIcon.fromTheme('open'), 'Load data file.',
                               self)
        loadDataFile.setShortcut('Ctrl+D')
        loadDataFile.setStatusTip('Load experimental (.txt) data.')
        loadDataFile.triggered.connect(self.loadDisplayData)

        clearDataFileAct = QAction(QIcon.fromTheme('close'),
                                   'Clear data.', self)
        clearDataFileAct.setShortcut('Ctrl+C')
        clearDataFileAct.setStatusTip('Clear data.')
        clearDataFileAct.triggered.connect(self.clearDataFile)

        self.fileMenu.addAction(loadDataFile)
        self.fileMenu.addAction(clearDataFileAct)

    def loadSimData(self):
        """Load and plot from SimData"""

        # store copy of data in this object, that can be reused by
        # canvas (self.m) on re-instantiation
        if self.sim_data is not None:
            self.avg_dpl = self.sim_data['avg_dpl']
            self.dpls = self.sim_data['dpls']
            self.specs = self.sim_data['spec']
            if self.specs is None or len(self.specs) == 0:
                self.specs = extract_spec(self.dpls, self.params['f_max_spec'])

            # calculate TFR from spec trial data
            self.avg_spec = deepcopy(self.specs[0])
            ntrials = self.params['N_trials']
            TFR_list = [self.specs[i]['TFR'] for i in range(ntrials)]
            TFR_L2_list = [self.specs[i]['TFR_L2'] for i in range(ntrials)]
            TFR_L5_list = [self.specs[i]['TFR_L5'] for i in range(ntrials)]
            self.avg_spec['TFR'] = np.mean(np.array(TFR_list), axis=0)
            self.avg_spec['TFR_L2'] = np.mean(np.array(TFR_L2_list), axis=0)
            self.avg_spec['TFR_L5'] = np.mean(np.array(TFR_L5_list), axis=0)

            # populate the data inside canvas object before calling
            # self.m.plot()
            self.m.avg_dpl = self.avg_dpl
            self.m.dpls = self.dpls
            self.m.specs = self.specs
            self.m.avg_spec = self.avg_spec

        if len(self.specs) > 0:
            self.printStat('Plotting simulation PSDs.')
            self.m.lF = self.lF
            self.m.dpls = self.dpls
            self.m.avg_dpl = self.avg_dpl
            self.m.plot()
            self.m.draw()  # make sure new lines show up in plot
            self.printStat('')

    def loadDisplayData(self):
        """Load dipole(s) from .txt file and plot PSD"""
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
        f_max_spec = 120.0  # use 120 Hz as maximum for PSD plots

        # a progress bar would be helpful right here!
        f, psd = extract_psd(self.avg_dpl, f_max_spec)
        self.psds.append(psd)
        self.lF.append(f)

        # updateCB depends on ntrial being set
        # self.ntrial = len(self.specs)
        # self.updateCB()
        self.printStat('Extracted ' + str(len(self.psds)) + ' PSDs from ' +
                       fname)
        self.lextfiles.append(fname)

        if len(self.psds) > 0:
            self.printStat('Plotting ext data PSDs.')
            self.m.lF = self.lF
            self.m.psds = self.psds
            self.m.dpls = self.dpls
            self.m.avg_dpl = self.avg_dpl
            self.m.plotextdat(self.lF, self.psds, self.lextfiles)
            self.m.draw()  # make sure new lines show up in plot
            self.printStat('')

    def clearDataFile(self):
        self.m.clearlextdatobj()
        self.lextpsd = []
        self.lextfiles = []
        self.lF = []
        self.m.draw()
