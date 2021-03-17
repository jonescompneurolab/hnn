"""Class for Dipole viewing window"""

# Authors: Sam Neymotin <samnemo@gmail.com>
#          Blake Caldwell <blake_caldwell@brown.edu>

import numpy as np

from PyQt5.QtWidgets import QSizePolicy

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

fontsize = plt.rcParams['font.size'] = 10
random_label = np.random.rand(100)


class DipoleCanvas(FigureCanvasQTAgg):


    def __init__(self, params, sim_data, index, parent=None, width=12,
                 height=10, dpi=120, title='Dipole Viewer'):
        FigureCanvasQTAgg.__init__(self, Figure(figsize=(width, height),
                                   dpi=dpi))
        self.title = title
        self.setParent(parent)
        self.gui = parent
        self.index = index
        self.sim_data = sim_data
        FigureCanvasQTAgg.setSizePolicy(self, QSizePolicy.Expanding,
                                        QSizePolicy.Expanding)
        FigureCanvasQTAgg.updateGeometry(self)

        self.params = params
        self.scalefctr = self.params['dipole_scalefctr']
        if type(self.scalefctr) != float and type(self.scalefctr) != int:
            self.scalefctr = 30e3
        self.tstop = self.params['tstop']
        self.ntrial = self.params['N_trials']

        self.plot()

    def plot(self):
        global random_label

        gdx = 311

        ltitle = ['Layer 2/3', 'Layer 5', 'Aggregate']
        dipole_keys = ['L2', 'L5', 'agg']

        white_patch = mpatches.Patch(color='white', label='Average')
        gray_patch = mpatches.Patch(color='gray', label='Individual')
        lpatch = []

        if len(self.sim_data['dpls']) > 0:
            lpatch = [white_patch, gray_patch]

        yl = [1e9, -1e9]
        for key in dipole_keys:
            yl[0] = min(yl[0], np.amin(self.sim_data['avg_dpl'].data[key]))
            yl[1] = max(yl[1], np.amax(self.sim_data['avg_dpl'].data[key]))

            # plot dipoles from individual trials
            if len(self.sim_data['dpls']) > 0:
                for dpltrial in self.sim_data['dpls']:
                    yl[0] = min(yl[0], np.amin(dpltrial.data[key]))
                    yl[1] = max(yl[1], np.amax(dpltrial.data[key]))
        yl = tuple(yl)

        for key, title in zip(dipole_keys, ltitle):
            ax = self.figure.add_subplot(gdx, label=random_label)
            random_label += 1

            if key == 'agg':
                ax.set_xlabel('Time (ms)')

            lw = self.gui.linewidth
            if self.index != 0:
                lw = self.gui.linewidth + 2

            # plot dipoles from individual trials
            if len(self.sim_data['dpls']) > 0:
                for ddx, dpltrial in enumerate(self.sim_data['dpls']):
                    if self.index == 0 or (self.index > 0 and
                                           ddx == (self.index - 1)):
                        ax.plot(dpltrial.times, dpltrial.data[key],
                                color='gray', linewidth=lw)

            # average dipole (across trials)
            if self.index == 0:
                ax.plot(self.sim_data['avg_dpl'].times,
                        self.sim_data['avg_dpl'].data[key], 'w',
                        linewidth=self.gui.linewidth + 2)

            ax.set_ylabel(r'(nAm $\times$ ' + str(self.scalefctr) + ')')
            if self.tstop != -1:
                ax.set_xlim((0, self.tstop))
            ax.set_ylim(yl)

            if key == 'L2' and len(self.sim_data['dpls']) > 0:
                ax.legend(handles=lpatch)

            ax.set_facecolor('k')
            ax.grid(True)
            ax.set_title(title)

            gdx += 1

        self.figure.subplots_adjust(bottom=0.06, left=0.06, right=1.0,
                                    top=0.97, wspace=0.1, hspace=0.09)

        self.draw()
