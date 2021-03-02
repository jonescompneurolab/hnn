"""Create the Spectrogram viewing window"""

# Authors: Sam Neymotin <samnemo@gmail.com>
#          Blake Caldwell <blake_caldwell@brown.edu>

import os
import numpy as np

from PyQt5.QtWidgets import QSizePolicy, QAction
from PyQt5.QtGui import QIcon
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from hnn_core.dipole import average_dipoles

from .DataViewGUI import DataViewGUI
from .specfn import MorletSpec
from .simdat import get_dipoles_from_disk
from .paramrw import get_output_dir

fontsize = plt.rcParams['font.size'] = 10


def extract_spec(params):
    """Read dipoles and extract Mortlet spectrograms

    Parameters
    ----------
    params : dict
        Dictionary containing parameters

    Returns
    ----------
    specs: list of MortletSpec objects
        List containing spectrograms of each trial
    avg_spec: MortletSpec objects
        spectrogram averaged over all trials
    dpls: list of Dipole objects
        List containing Dipoles of each trial
    avg_dpl: Dipole object
        Dipole object containing the average of individual trial Dipoles
    """

    sim_dir = os.path.join(get_output_dir(), 'data',
                           params['sim_prefix'])

    dpls = get_dipoles_from_disk(sim_dir, params['N_trials'])
    if len(dpls) == 1:
        avg_dpl = dpls[0]
    else:
        avg_dpl = average_dipoles(dpls)

    specs = []
    for dpltrial in dpls:
        ms = MorletSpec(dpltrial.times, dpltrial.data['agg'], None,
                        p_dict=params)
        specs.append(ms)

    # !!should fix to average of individual spectrograms!!
    avg_spec = MorletSpec(avg_dpl.times, avg_dpl.data['agg'], None,
                          p_dict=params)

    ltfr = [ms.TFR for ms in specs]
    npspec = np.array(ltfr)
    avg_spec.TFR = np.mean(npspec, axis=0)

    return specs, avg_spec, dpls, avg_dpl


class SpecCanvas(FigureCanvasQTAgg):
    """Class for the Spectrogram viewer

    This is designed to be called from SpecViewGUI class to add functionality
    for loading and clearing data
    """
    def __init__(self, params, index, parent=None, width=12, height=10,
                 dpi=120, title='Spectrogram Viewer'):
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
        self.dpls = []
        self.specs = []
        self.lax = []
        self.avg_dpl = []
        self.avg_spec = []

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

    def clearlextdatobj(self):
        if hasattr(self, 'lextdatobj'):
            for o in self.lextdatobj:
                o.set_visible(False)
            del self.lextdatobj

    def drawspec(self, dpls, lspec, sdx, avgdipole, avgspec, fig, G,
                 ltextra=''):
        if len(lspec) == 0:
            return

        plt.ion()

        gdx = 211

        ax = fig.add_subplot(gdx)
        lax = [ax]
        tvec = avgdipole.times

        if sdx == 0:
            for dpltrial in dpls:
                ax.plot(tvec, dpltrial.data['agg'],
                        linewidth=self.gui.linewidth, color='gray')
            ax.plot(tvec, avgdipole.data['agg'],
                    linewidth=self.gui.linewidth + 1, color='black')
        else:
            ax.plot(tvec, dpls[sdx].data['agg'],
                    linewidth=self.gui.linewidth + 1, color='gray')

        ax.set_xlim(tvec[0], tvec[-1])
        ax.set_ylabel('Dipole (nAm)')

        gdx = 212

        ax = fig.add_subplot(gdx)

        if sdx == 0:
            ms = avgspec
        else:
            ms = lspec[sdx - 1]

        ax.imshow(ms.TFR, extent=[tvec[0], tvec[-1], ms.f[-1], ms.f[0]],
                  aspect='auto', origin='upper',
                  cmap=plt.get_cmap(self.spec_cmap))

        ax.set_xlim(tvec[0], tvec[-1])
        ax.set_xlabel('Time (ms)')
        ax.set_ylabel('Frequency (Hz)')

        lax.append(ax)

        return lax

    def plot(self):
        ltextra = 'Trial ' + str(self.index)
        if self.index == 0:
            ltextra = 'All Trials'
        self.lax = self.drawspec(self.dpls, self.specs, self.index,
                                 self.avg_dpl, self.avg_spec, self.figure,
                                 self.G, ltextra=ltextra)
        self.figure.subplots_adjust(bottom=0.06, left=0.06, right=0.98,
                                    top=0.97, wspace=0.1, hspace=0.09)
        self.draw()


class SpecViewGUI(DataViewGUI):
    def __init__(self, CanvasType, params, title):
        self.specs = []  # external data spec
        self.dpls = None
        self.avg_dpl = []
        self.avg_spec = []
        self.params = params
        super(SpecViewGUI, self).__init__(CanvasType, self.params, title)
        self.addLoadDataActions()
        self.loadDisplayData()

    def initCanvas(self):
        super(SpecViewGUI, self).initCanvas()
        self.m.specs = self.specs

    def addLoadDataActions(self):
        loadDataFile = QAction(QIcon.fromTheme('open'), 'Load data.', self)
        loadDataFile.setShortcut('Ctrl+D')
        loadDataFile.setStatusTip('Load experimental (.txt) / ' +
                                  'simulation (.param) data.')
        loadDataFile.triggered.connect(self.loadDisplayData)

        clearDataFileAct = QAction(QIcon.fromTheme('close'), 'Clear data.',
                                   self)
        clearDataFileAct.setShortcut('Ctrl+C')
        clearDataFileAct.setStatusTip('Clear data.')
        clearDataFileAct.triggered.connect(self.clearDataFile)

        self.fileMenu.addAction(loadDataFile)
        self.fileMenu.addAction(clearDataFileAct)

    def loadDisplayData(self):
        specs, avg_spec, dpls, avg_dpl = extract_spec(self.params)
        self.m.dpls = dpls
        self.m.specs = specs
        self.m.avg_dpl = avg_dpl
        self.m.avg_spec = avg_spec

        self.updateCB()
        self.printStat('Extracted ' + str(len(self.m.specs)) +
                       ' spectrograms for ' + self.params['sim_prefix'])

        if len(self.m.specs) > 0:
            self.printStat('Plotting Spectrograms.')
            self.m.plot()
            self.m.draw()  # make sure new lines show up in plot
            self.printStat('')

    def clearDataFile(self):
        self.m.clearlextdatobj()
        self.specs = []
        self.m.draw()
