import os
import numpy as np
from math import ceil

from PyQt5 import QtWidgets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec

from .paramrw import countEvokedInputs
from .qt_lib import getscreengeom
from .paramrw import get_output_dir, get_inputs
from .simdata import check_feeds_to_plot, plot_hists_on_gridspec
from .specfn import plot_spec
from .spikefn import ExtInputs

fontsize = plt.rcParams['font.size'] = 10


class SIMCanvas(FigureCanvasQTAgg):
    # matplotlib/pyqt-compatible canvas for drawing simulation & external data
    # based on https://pythonspot.com/en/pyqt5-matplotlib/

    def __init__(self, paramfn, params, parent=None, width=5, height=4,
                 dpi=40, is_optimization=False, title='Simulation Viewer'):
        FigureCanvasQTAgg.__init__(self, Figure(figsize=(width, height),
                                                dpi=dpi))

        self.title = title
        self.sim_data = parent.sim_data
        self.lextdatobj = []  # external data object
        self.clridx = 5  # index for next color for drawing external data
        self.errtot = None
        self.error_list = []

        # legend for dipole signals
        self.lpatch = [mpatches.Patch(color='black', label='Sim.')]
        self.setParent(parent)
        self.parent = parent
        FigureCanvasQTAgg.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding,
                                        QtWidgets.QSizePolicy.Expanding)
        FigureCanvasQTAgg.updateGeometry(self)
        self.params = params
        self.paramfn = paramfn
        self.axdipole = self.axspec = None
        self.G = gridspec.GridSpec(10, 1)
        self._data_dir = os.path.join(get_output_dir(), 'data')

        self.is_optimization = is_optimization
        if not is_optimization:
            self.sim_data.clear_opt_data()

        self.saved_exception = None
        try:
            self.plot()
        except Exception as err:
            self.saved_exception = err

    def plotinputhist(self, extinputs=None, feeds_to_plot=None):
        """ plot input histograms"""

        xmin = 0.
        xmax = self.params['tstop']
        xlim = (xmin, xmax)
        axes = []

        sim_dt = self.params['dt']
        num_step = ceil(xmax / sim_dt) + 1
        times = np.linspace(xmin, xmax, num_step)

        plot_distribs = True
        if extinputs is not None and feeds_to_plot is not None:
            if feeds_to_plot is None:
                feeds_to_plot = check_feeds_to_plot(extinputs.inputs,
                                                    self.params)

            if feeds_to_plot['ongoing'] or feeds_to_plot['evoked'] or \
                    feeds_to_plot['pois']:
                # hist gridspec
                axes = plot_hists_on_gridspec(self.figure, self.G,
                                              feeds_to_plot, extinputs, times,
                                              xlim, self.parent.linewidth)

                plot_distribs = False

        if plot_distribs:
            dinput = self.getInputDistrib()
            feeds_to_plot = check_feeds_to_plot(dinput, self.params)
            if not (feeds_to_plot['ongoing'] or feeds_to_plot['evoked'] or
                    feeds_to_plot['pois']):
                # no plots to create
                return axes

            n_hists = 0

            if feeds_to_plot['evdist']:
                dist_tot = np.zeros(len(dinput['evdist'][0][0]))
                for dist in dinput['evdist']:
                    dist_tot += dist[1]

                axdist = self.figure.add_subplot(self.G[n_hists, :])
                n_hists += 1

                axdist.plot(dinput['evdist'][0][0], dist_tot, color='g',
                            lw=self.parent.linewidth,
                            label='evdist distribution')
                axdist.set_xlim(dinput['evdist'][0][0][0],
                                dinput['evdist'][0][0][-1])
                axdist.invert_yaxis()  # invert the distal input axes
                axes.append(axdist)

            if feeds_to_plot['evprox']:
                prox_tot = np.zeros(len(dinput['evprox'][0][0]))
                for prox in dinput['evprox']:
                    prox_tot += prox[1]

                axprox = self.figure.add_subplot(self.G[n_hists, :])
                n_hists += 1

                axprox.plot(dinput['evprox'][0][0], prox_tot, color='r',
                            lw=self.parent.linewidth,
                            label='evprox distribution')
                axprox.set_xlim(dinput['evprox'][0][0][0],
                                dinput['evprox'][0][0][-1])
                axes.append(axprox)

        return axes

    def clearaxes(self):
        # clear the figures axes
        for ax in self.figure.get_axes():
            if ax:
                ax.cla()

    def getInputDistrib(self):
        import scipy.stats as stats

        dinput = {'evprox': [], 'evdist': [], 'prox': [], 'dist': [],
                  'pois': []}
        try:
            sim_tstop = self.params['tstop']
            sim_dt = self.params['dt']
        except KeyError:
            return dinput

        num_step = ceil(sim_tstop / sim_dt) + 1
        times = np.linspace(0, sim_tstop, num_step)
        ltprox, ltdist = self.getEVInputTimes()
        for prox in ltprox:
            pdf = stats.norm.pdf(times, prox[0], prox[1])
            dinput['evprox'].append((times, pdf))
        for dist in ltdist:
            pdf = stats.norm.pdf(times, dist[0], dist[1])
            dinput['evdist'].append((times, pdf))
        return dinput

    def getEVInputTimes(self):
        # get the evoked input times

        if self.params is None:
            raise ValueError("No valid params found")

        nprox, ndist = countEvokedInputs(self.params)
        ltprox, ltdist = [], []
        for i in range(nprox):
            input_mu = self.params['t_evprox_' + str(i + 1)]
            input_sigma = self.params['sigma_t_evprox_' + str(i + 1)]
            ltprox.append((input_mu, input_sigma))
        for i in range(ndist):
            input_mu = self.params['t_evdist_' + str(i + 1)]
            input_sigma = self.params['sigma_t_evdist_' + str(i + 1)]
            ltdist.append((input_mu, input_sigma))
        return ltprox, ltdist

    def drawEVInputTimes(self, ax, yl, h=0.1, hw=15, hl=15):
        # draw the evoked input times using arrows
        ltprox, ltdist = self.getEVInputTimes()
        yrange = abs(yl[1] - yl[0])

        for tt in ltprox:
            ax.arrow(tt[0], yl[0], 0, h * yrange, fc='r', ec='r',
                     head_width=hw, head_length=hl)
        for tt in ltdist:
            ax.arrow(tt[0], yl[1], 0, -h * yrange, fc='g', ec='g',
                     head_width=hw, head_length=hl)

    def getnextcolor(self):
        # get next color for external data (colors selected in order)
        self.clridx += 5
        if self.clridx > 100:
            self.clridx = 5
        return self.clridx

    def _has_simdata(self):
        """check if any simulation data available"""
        if self.paramfn in self.sim_data._sim_data:
            avg_dpl = self.sim_data._sim_data[self.paramfn]['data']['avg_dpl']
            if avg_dpl is not None:
                return True

        return False

    def plotextdat(self):
        global fontsize

        if self.sim_data._exp_data is None or \
                len(self.sim_data._exp_data) == 0:
            return

        # plot 'external' data (e.g. from experiment/other simulation)
        if self._has_simdata():  # has the simulation been run yet?
            tstop = self.params['tstop']
            # recalculate/save the error
            self.error_list, self.errtot = self.sim_data.calcerr(self.paramfn,
                                                                 tstop)

        if self.axdipole is None:
            self.axdipole = self.figure.add_subplot(self.G[0:-1, 0])
            xl = (0.0, 1.0)
            yl = (-0.001, 0.001)
        else:
            xl = self.axdipole.get_xlim()
            yl = self.axdipole.get_ylim()

        cmap = plt.get_cmap('nipy_spectral')
        csm = plt.cm.ScalarMappable(cmap=cmap)
        csm.set_clim((0, 100))

        # clear annotation objects
        self.clearlextdatobj()

        # add legend items
        if self.is_optimization:
            self.lpatch.append(mpatches.Patch(color='grey',
                                              label='Optimization'))
            self.lpatch.append(mpatches.Patch(color='black', label='Initial'))
        elif self._has_simdata():
            self.lpatch.append(mpatches.Patch(color='black',
                                              label='Simulation'))
        if hasattr(self, 'annot_avg'):
            self.annot_avg.set_visible(False)
            del self.annot_avg

        # add dipole plots of external data
        err_list_index = 0
        for fn, dat in self.sim_data._exp_data.items():
            shp = dat.shape
            clr = csm.to_rgba(self.getnextcolor())
            c = min(shp[1], 1)
            self.lextdatobj.append(self.axdipole.plot(dat[:, 0], dat[:, c],
                                   color=clr,
                                   linewidth=self.parent.linewidth + 1))
            xl = ((min(xl[0], min(dat[:, 0]))), (max(xl[1], max(dat[:, 0]))))
            yl = ((min(yl[0], min(dat[:, c]))), (max(yl[1], max(dat[:, c]))))
            fx = int(shp[0] * float(c) / shp[1])
            if self.error_list:
                tx, ty = dat[fx, 0], dat[fx, c]
                txt = 'RMSE: %.2f' % round(self.error_list[err_list_index], 2)
                if not self.is_optimization:
                    self.axdipole.annotate(txt, xy=(dat[0, 0], dat[0, c]),
                                           xytext=(tx, ty), color=clr,
                                           fontweight='bold')
            label = fn.split(os.path.sep)[-1].split('.txt')[0]
            self.lpatch.append(mpatches.Patch(color=clr, label=label))
            err_list_index += 1

        # update limits based on external data
        self.axdipole.set_xlim(xl)
        self.axdipole.set_ylim(yl)

        if len(self.lpatch) > 0:
            self.axdipole.legend(handles=self.lpatch, loc=2)

        # add RMSE labels
        if self.errtot is not None:
            textcoords = 'axes fraction'
            clr = 'black'
            txt = 'Avg. RMSE: %.2f' % round(self.errtot, 2)
            if self.is_optimization:
                if 'initial_error' in self.sim_data._opt_data:
                    initial_error = self.sim_data._opt_data['initial_error']
                    txt = 'Initial RMSE: %.2f' % round(initial_error, 2)
                    annot_initial = \
                        self.axdipole.annotate(txt, xy=(0, 0),
                                               xytext=(0.86, 0.005),
                                               textcoords=textcoords,
                                               color=clr,
                                               fontweight='bold')
                    self.lextdatobj.append(annot_initial)
                    txt = 'Opt RMSE: %.2f' % round(self.errtot, 2)
                    clr = 'gray'

            annot_avg = self.axdipole.annotate(txt, xy=(0, 0),
                                               xytext=(0.005, 0.005),
                                               textcoords=textcoords,
                                               color=clr,
                                               fontweight='bold')
            self.lextdatobj.append(annot_avg)

        if not self._has_simdata():  # need axis labels
            self.axdipole.set_xlabel('Time (ms)', fontsize=fontsize)
            self.axdipole.set_ylabel('Dipole (nAm)', fontsize=fontsize)
            myxl = self.axdipole.get_xlim()
            if myxl[0] < 0.0:
                self.axdipole.set_xlim((0.0, myxl[1] + myxl[0]))

    def clearlextdatobj(self):
        # clear list of external data objects
        for o in self.lextdatobj:
            if isinstance(o, list):
                # this is the plot. clear the line
                o[0].set_visible(False)
        del self.lextdatobj
        self.lextdatobj = []  # reset list of external data objects
        self.lpatch = []  # reset legend
        self.clridx = 5  # reset index for next color for drawing ext data

    def plotsimdat(self):
        """plot the simulation data"""

        global fontsize

        DrawSpec = False
        xlim = (0.0, 1.0)
        ylim = (-0.001, 0.001)

        if self.params is None:
            data_to_plot = False
            gRow = 0
        else:
            # for later
            ntrial = self.params['N_trials']
            tstop = self.params['tstop']
            dipole_scalefctr = self.params['dipole_scalefctr']
            N_pyr_x = self.params['N_pyr_x']
            N_pyr_y = self.params['N_pyr_y']

            # update xlim to tstop
            xlim = (0.0, tstop)

            # for trying to plot a simulation read from disk (e.g. default)
            if self.paramfn not in self.sim_data._sim_data:
                # load simulation data from disk
                data_to_plot = self.sim_data.update_sim_data_from_disk(
                    self.paramfn, self.params)
            else:
                data_to_plot = True

            if data_to_plot:
                sim_data = self.sim_data._sim_data[self.paramfn]['data']
                trials = [trial_idx for trial_idx in range(ntrial)]
                extinputs = ExtInputs(sim_data['spikes'],
                                      sim_data['gid_ranges'],
                                      trials, self.params)

                feeds_to_plot = check_feeds_to_plot(extinputs.inputs,
                                                    self.params)
            else:
                # best we can do is plot the distributions of the inputs
                extinputs = feeds_to_plot = None

            hist_axes = self.plotinputhist(extinputs, feeds_to_plot)
            gRow = len(hist_axes)

            if data_to_plot:
                # check that dipole data is present
                single_sim = self.sim_data._sim_data[self.paramfn]['data']
                if single_sim['avg_dpl'] is None:
                    data_to_plot = False

                # whether to draw the specgram - should draw if user saved
                # it or have ongoing, poisson, or tonic inputs
                if single_sim['spec'] is not None \
                        and len(single_sim['spec']) > 0 \
                        and (self.params['save_spec_data'] or
                             feeds_to_plot['ongoing'] or
                             feeds_to_plot['pois']):
                    DrawSpec = True

                    first_spec_trial = single_sim['spec'][0]

                    # adjust dipole to match spectogram limits (e.g. missing
                    # first 50 ms b/c edge effects)
                    xlim = (first_spec_trial['time'][0],
                            first_spec_trial['time'][-1])

        if DrawSpec:  # dipole axis takes fewer rows if also drawing specgram
            self.axdipole = self.figure.add_subplot(self.G[gRow:5, 0])
            bottom = 0.08

            # set the axes of input histograms to match dipole and spec plots
            for ax in hist_axes:
                ax.set_xlim(xlim)

        else:
            self.axdipole = self.figure.add_subplot(self.G[gRow:-1, 0])
            # there is no spec plot below, so label dipole with time on x-axis
            self.axdipole.set_xlabel('Time (ms)', fontsize=fontsize)
            bottom = 0.0

        self.axdipole.set_ylim(ylim)
        self.axdipole.set_xlim(xlim)

        left = 0.08
        w, _ = getscreengeom()
        if w < 2800:
            left = 0.1
        # reduce padding
        self.figure.subplots_adjust(left=left, right=0.99, bottom=bottom,
                                    top=0.99, hspace=0.1, wspace=0.1)

        if not data_to_plot:
            # no dipole or spec data to plot
            return

        # plot the dipoles
        self.sim_data.plot_dipole(self.paramfn, self.axdipole,
                                  self.parent.linewidth,
                                  dipole_scalefctr, N_pyr_x, N_pyr_y,
                                  self.is_optimization)

        if DrawSpec:
            self.axspec = self.figure.add_subplot(self.G[6:10, 0])
            cax = plot_spec(self.axspec, sim_data['spec'], ntrial,
                            self.params['spec_cmap'], xlim,
                            fontsize)

            # plot colorbar horizontally to save space
            cbaxes = self.figure.add_axes([0.6, 0.49, 0.3, 0.005])
            plt.colorbar(cax, cax=cbaxes, orientation='horizontal')

    def plotarrows(self):
        # run after scales have been updated
        xl = self.axdipole.get_xlim()
        yl = self.axdipole.get_ylim()

        using_feeds = get_inputs(self.params)
        if using_feeds['evoked']:
            self.drawEVInputTimes(self.axdipole, yl, 0.1,
                                  (xl[1] - xl[0]) * .02,
                                  (yl[1] - yl[0]) * .02)

    def plot(self):
        self.clearaxes()
        plt.close(self.figure)
        self.figure.clf()
        self.axdipole = None

        self.plotsimdat()  # creates self.axdipole
        self.plotextdat()
        self.plotarrows()

        self.draw()
