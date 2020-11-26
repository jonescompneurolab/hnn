import os
from PyQt5.QtWidgets import QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
from math import ceil
from glob import glob
from scipy import signal

from hnn_core import read_spikes

from .spikefn import ExtInputs
from .paramrw import usingOngoingInputs, usingEvokedInputs, usingPoissonInputs
from .paramrw import usingTonicInputs, countEvokedInputs, get_output_dir
from .qt_lib import getscreengeom

drawindivdpl = 1
drawavgdpl = 1
fontsize = plt.rcParams['font.size'] = 10


def read_dpltrials(sim_dir):
    """read dipole data files for individual trials"""
    ldpl = []

    dpl_fname_pattern = os.path.join(sim_dir, 'dpl_*.txt')
    for dipole_fn in sorted(glob(str(dpl_fname_pattern))):
        dpl_trial = None
        try:
            dpl_trial = np.loadtxt(dipole_fn)
        except OSError:
            print('Warning: could not read file:', dipole_fn)
        except ValueError:
            print('Warning: could not read file:', dipole_fn)

        ldpl.append(dpl_trial)

    return ldpl


def get_inputs(params):
    """ get a dictionary of input types used in simulation
        with distal/proximal specificity for evoked,ongoing inputs
    """

    dinty = {'Evoked': False, 'Ongoing': False, 'Poisson': False,
             'Tonic': False, 'EvokedDist': False, 'EvokedProx': False,
             'OngoingDist': False, 'OngoingProx': False}

    dinty['Evoked'] = usingEvokedInputs(params)
    dinty['EvokedDist'] = usingEvokedInputs(params, lsuffty=['_evdist_'])
    dinty['EvokedProx'] = usingEvokedInputs(params, lsuffty=['_evprox_'])
    dinty['Ongoing'] = usingOngoingInputs(params)
    dinty['OngoingDist'] = usingOngoingInputs(params, lty=['_dist'])
    dinty['OngoingProx'] = usingOngoingInputs(params, lty=['_prox'])
    dinty['Poisson'] = usingPoissonInputs(params)
    dinty['Tonic'] = usingTonicInputs(params)

    return dinty


class SimData(object):
    """The SimData class"""

    def __init__(self):
        self._sim_data = {}
        self._opt_data = {}
        self._exp_data = {}

    def remove_sim_by_fn(self, paramfn):
        """Deletes sim from SimData

        Parameters
        ----------
        paramfn : str
            Filename of parameter file to remove
        """
        del self._sim_data[paramfn]

    def _update_sim_list(self, paramfn, params, avg_dpl, dpl_trials,
                         spikes=None, spec=None):
        self._sim_data[paramfn] = {'params': params,
                                   'data': {'avg_dpl': avg_dpl,
                                            'dpl_trials': dpl_trials,
                                            'spk': spikes,
                                            'spec': spec}}

    def clear_exp_data(self):
        """Clear all experimental data from SimData"""

        self._exp_data = {}

    def clear_sim_data(self):
        """Clear all simulation data from SimData"""

        self._sim_data.clear()

    def update_exp_data(self, exp_fn, exp_data):
        """Adds experimental data to SimData

        Parameters
        ----------
        exp_fn : str
            Filename of experimental data
        exp_data : array
            Data from np.loadtxt() on experimental data file
        """
        self._exp_data[exp_fn] = exp_data

    def get_exp_data_size(self):
        """Adds experimental data to SimData

        Returns
        ----------
        length: int
            The number of experimental data files in SimData
        """

        return len(self._exp_data)

    def update_sim_data(self, paramfn, params):
        """Adds simulation data to SimData

        Parameters
        ----------
        paramfn : str
            Simulation paramter filename
        params : dict
            Dictionary containing parameters
        """

        data_dir = os.path.join(get_output_dir(), 'data')
        sim_dir = os.path.join(data_dir, params['sim_prefix'])
        warn_nofile = False
        if os.path.exists(sim_dir):
            warn_nofile = True

        warning_message = 'Warning: could not read file:'

        dipole_fn = os.path.join(sim_dir, 'dpl.txt')
        avg_dpl = None
        try:
            avg_dpl = np.loadtxt(dipole_fn)
        except OSError:
            if warn_nofile:
                print(warning_message, dipole_fn)
        except ValueError:
            if warn_nofile:
                print(warning_message, dipole_fn)

        spike_fn = os.path.join(sim_dir, 'spk.txt')
        spikes_array = None
        try:
            raw_spikes = read_spikes(spike_fn)
            spikes_array = np.r_[raw_spikes.times, raw_spikes.gids].T
            if len(spikes_array) == 0 and warn_nofile:
                print(warning_message, spike_fn)
        except ValueError:
            try:
                spikes_array = np.loadtxt(spike_fn)
            except OSError:
                if warn_nofile:
                    print(warning_message, spike_fn)
            except ValueError:
                if warn_nofile:
                    print(warning_message, spike_fn)
        except IndexError:
            print('Warning: incorrect dimensions for spike file: %s' %
                  spike_fn)

        warn_nospec = False
        dinty = get_inputs(params)
        if params['save_spec_data'] or dinty['Ongoing'] or \
                dinty['Poisson'] or dinty['Tonic']:
            warn_nospec = True

        spec_fn = os.path.join(sim_dir, 'rawspec.npz')
        spec = None
        try:
            spec = np.load(spec_fn)
        except OSError:
            if warn_nospec:
                print(warning_message, spec_fn)
        except ValueError:
            if warn_nospec:
                print(warning_message, spec_fn)

        dpl_trials = read_dpltrials(sim_dir)

        self._update_sim_list(paramfn, params, avg_dpl, dpl_trials,
                              spikes_array, spec)

    def calcerr(self, paramfn, tstop, tstart=0.0, weights=None):
        """Calculate root mean squared error using SimData

        Parameters
        ----------
        paramfn : str
            Simulation parameter filename to calculate RMSE for against
            experimental data previously loaded in SimData
        tstop : float
            Time in ms defining the end of the region to calculate RMSE
        tstart : float | None
            Time in ms defining the start of the region to calculate RMSE.
            If None is provided, this defaults to 0.0 ms.
        weights : array | None
            An array containing weights for each data point of the simulation.
            If weights is provided, then the weighted root mean square error
            will be returned. If None is provided, then standard RMSE will be
            returned.

        Returns
        ----------
        lerr : list of floats
            A list of RMSE values between the simulation and each experimental
            data files stored in SimData
        errtot : float
            Average RMSE over all experimental data files
        """

        NSig = errtot = 0.0
        lerr = []
        for _, dat in self._exp_data.items():
            shp = dat.shape

            exp_times = dat[:, 0]
            sim_times = self._sim_data[paramfn]['data']['avg_dpl'][:, 0]

            # do tstart and tstop fall within both datasets?
            # if not, use the closest data point as the new tstop/tstart
            for tseries in [exp_times, sim_times]:
                if tstart < tseries[0]:
                    tstart = tseries[0]
                if tstop > tseries[-1]:
                    tstop = tseries[-1]

            # make sure start and end times are valid for both dipoles
            exp_start_index = (np.abs(exp_times - tstart)).argmin()
            exp_end_index = (np.abs(exp_times - tstop)).argmin()
            exp_length = exp_end_index - exp_start_index

            sim_start_index = (np.abs(sim_times - tstart)).argmin()
            sim_end_index = (np.abs(sim_times - tstop)).argmin()
            sim_length = sim_end_index - sim_start_index

            if weights is not None:
                weight = weights[sim_start_index:sim_end_index]

            for c in range(1, shp[1], 1):
                sim_dpl = self._sim_data[paramfn]['data']['avg_dpl']
                dpl1 = sim_dpl[sim_start_index:sim_end_index, 1]
                dpl2 = dat[exp_start_index:exp_end_index, c]

                if (sim_length > exp_length):
                    # downsample simulation timeseries to match exp data
                    dpl1 = signal.resample(dpl1, exp_length)
                    if weights is not None:
                        weight = signal.resample(weight, exp_length)
                        indices = np.where(weight < 1e-4)
                        weight[indices] = 0

                elif (sim_length < exp_length):
                    # downsample exp timeseries to match simulation data
                    dpl2 = signal.resample(dpl2, sim_length)

                if weights is not None:
                    err0 = np.sqrt((weight * ((dpl1 - dpl2) ** 2)).sum() /
                                   weight.sum())
                else:
                    err0 = np.sqrt(((dpl1 - dpl2) ** 2).mean())
                lerr.append(err0)
                errtot += err0
                NSig += 1

        if not NSig == 0.0:
            errtot /= NSig
        return lerr, errtot

    def clear_opt_data(self):
        self._initial_opt = {}
        self._opt_data = {}

    def update_opt_data(self, paramfn, params, avg_dpl):
        self._opt_data = {'paramfn': paramfn, 'params': params,
                          'data': {'avg_dpl': avg_dpl}}


class SIMCanvas (FigureCanvasQTAgg):
    # matplotlib/pyqt-compatible canvas for drawing simulation & external data
    # based on https://pythonspot.com/en/pyqt5-matplotlib/

    def __init__(self, paramfn, params, parent=None, width=5, height=4,
                 dpi=40, optMode=False, title='Simulation Viewer'):
        FigureCanvasQTAgg.__init__(self, Figure(figsize=(width, height),
                                                dpi=dpi))

        self.title = title
        self.sim_data = parent.sim_data
        self.lextdatobj = []  # external data object
        self.clridx = 5  # index for next color for drawing external data

        # legend for dipole signals
        self.lpatch = [mpatches.Patch(color='black', label='Sim.')]
        self.setParent(parent)
        self.linewidth = parent.linewidth
        FigureCanvasQTAgg.setSizePolicy(self, QSizePolicy.Expanding,
                                        QSizePolicy.Expanding)
        FigureCanvasQTAgg.updateGeometry(self)
        self.params = params
        self.paramfn = paramfn
        self.initaxes()
        self.G = gridspec.GridSpec(10, 1)

        self.optMode = optMode
        if not optMode:
            self.sim_data.clear_opt_data()
        self.plot()

    def initaxes(self):
        # initialize the axes
        self.axdist = self.axprox = self.axdipole = self.axspec = None
        self.axpois = None

    def plotinputhist(self, xl, dinty):
        """ plot input histograms
            xl = x axis limits
            dinty = dict of input types used,
                    determines how many/which axes created/displayed
        """

        extinputs = None
        plot_distribs = False

        if self.params is None:
            raise ValueError("No valid params found")

        sim_tstop = self.params['tstop']
        sim_dt = self.params['tstop']
        num_step = ceil(sim_tstop / sim_dt) + 1
        times = np.linspace(0, sim_tstop, num_step)

        data_dir = os.path.join(get_output_dir(), 'data')
        sim_dir = os.path.join(data_dir, self.params['sim_prefix'])
        spike_fn = os.path.join(sim_dir, 'spk.txt')
        out_paramfn = os.path.join(sim_dir, 'param.txt')
        try:
            extinputs = ExtInputs(spike_fn, out_paramfn, self.params)
            extinputs.add_delay_times()
            dinput = extinputs.inputs
        except ValueError:
            dinput = self.getInputDistrib()
            plot_distribs = True

        if len(dinput['dist']) <= 0 and len(dinput['prox']) <= 0 and \
                len(dinput['evdist']) <= 0 and len(dinput['evprox']) <= 0 and \
                len(dinput['pois']) <= 0:
            return False

        self.hist = {'feed_dist': None,
                     'feed_prox': None,
                     'feed_evdist': None,
                     'feed_evprox': None,
                     'feed_pois': None}

        # dinty ensures synaptic weight > 0
        hasPois = len(dinput['pois']) > 0 and dinty['Poisson']
        gRow = 0
        self.axdist = self.axprox = self.axpois = None  # axis objects

        # check poisson inputs, create subplot
        if hasPois:
            self.axpois = self.figure.add_subplot(self.G[gRow, 0])
            gRow += 1

        # check distal inputs, create subplot
        if (len(dinput['dist']) > 0 and dinty['OngoingDist']) or \
                (len(dinput['evdist']) > 0 and dinty['EvokedDist']):
            self.axdist = self.figure.add_subplot(self.G[gRow, 0])
            gRow += 1

        # check proximal inputs, create subplot
        if (len(dinput['prox']) > 0 and dinty['OngoingProx']) or \
                (len(dinput['evprox']) > 0 and dinty['EvokedProx']):
            self.axprox = self.figure.add_subplot(self.G[gRow, 0])
            gRow += 1

        # check input types provided in simulation
        if extinputs is not None and self._has_simdata():
            if hasPois:
                extinputs.plot_hist(self.axpois, 'pois', times, 'auto', xl,
                                    color='k', hty='step',
                                    lw=self.linewidth+1)

            # dinty condition ensures synaptic weight > 0
            if len(dinput['dist']) > 0 and dinty['OngoingDist']:
                extinputs.plot_hist(self.axdist, 'dist', times, 'auto', xl,
                                    color='g', lw=self.linewidth+1)

            if len(dinput['prox']) > 0 and dinty['OngoingProx']:
                extinputs.plot_hist(self.axprox, 'prox', times, 'auto', xl,
                                    color='r', lw=self.linewidth+1)

            if len(dinput['evdist']) > 0 and dinty['EvokedDist']:
                extinputs.plot_hist(self.axdist, 'evdist', times, 'auto', xl,
                                    color='g', hty='step',
                                    lw=self.linewidth+1)

            if len(dinput['evprox']) > 0 and dinty['EvokedProx']:
                extinputs.plot_hist(self.axprox, 'evprox', times, 'auto', xl,
                                    color='r', hty='step',
                                    lw=self.linewidth+1)
        elif plot_distribs:
            if len(dinput['evprox']) > 0 and dinty['EvokedProx']:
                prox_tot = np.zeros(len(dinput['evprox'][0][0]))
                for prox in dinput['evprox']:
                    prox_tot += prox[1]
                self.axprox.plot(dinput['evprox'][0][0], prox_tot, color='r',
                                 lw=self.linewidth,
                                 label='evprox distribution')
                self.axprox.set_xlim(dinput['evprox'][0][0][0],
                                     dinput['evprox'][0][0][-1])
            if len(dinput['evdist']) > 0 and dinty['EvokedDist']:
                dist_tot = np.zeros(len(dinput['evdist'][0][0]))
                for dist in dinput['evdist']:
                    dist_tot += dist[1]
                self.axdist.plot(dinput['evdist'][0][0], dist_tot, color='g',
                                 lw=self.linewidth,
                                 label='evdist distribution')
                self.axprox.set_xlim(dinput['evdist'][0][0][0],
                                     dinput['evdist'][0][0][-1])

        ymax = 0
        for ax in [self.axpois, self.axdist, self.axprox]:
            if ax is not None:
                if ax.get_ylim()[1] > ymax:
                    ymax = ax.get_ylim()[1]

        if ymax == 0:
            return False
        else:
            for ax in [self.axpois, self.axdist, self.axprox]:
                if ax is not None:
                    ax.set_ylim(0, ymax)
            if self.axdist:
                self.axdist.invert_yaxis()
            for ax in [self.axpois, self.axdist, self.axprox]:
                if ax:
                    ax.set_xlim(xl)
                    ax.legend(loc=1)  # legend in upper right
            return True, gRow

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
            input_mu = self.params['t_evprox_' + str(i+1)]
            input_sigma = self.params['sigma_t_evprox_' + str(i+1)]
            ltprox.append((input_mu, input_sigma))
        for i in range(ndist):
            input_mu = self.params['t_evdist_' + str(i+1)]
            input_sigma = self.params['sigma_t_evdist_' + str(i+1)]
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
        avg_dpl = self.sim_data._sim_data[self.paramfn]['data']['avg_dpl']
        if avg_dpl is not None:
            return True

        return False

    def plotextdat(self, recalcErr=True):
        global fontsize

        if self.sim_data._exp_data is None or \
                len(self.sim_data._exp_data) == 0:
            return

        initial_err = None
        # plot 'external' data (e.g. from experiment/other simulation)
        if self._has_simdata():  # has the simulation been run yet?
            if recalcErr:
                tstop = self.params['tstop']
                # recalculate/save the error?
                self.lerr, self.errtot = self.sim_data.calcerr(self.paramfn,
                                                               tstop)

            if self.optMode:
                initial_err = self.sim_data._opt_data['initial_error']

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

        self.clearlextdatobj()  # clear annotation objects

        ddx = 0
        for fn, dat in self.sim_data._exp_data.items():
            shp = dat.shape
            clr = csm.to_rgba(self.getnextcolor())
            c = min(shp[1], 1)
            self.lextdatobj.append(self.axdipole.plot(dat[:, 0], dat[:, c],
                                   color=clr, linewidth=self.linewidth + 1))
            xl = ((min(xl[0], min(dat[:, 0]))), (max(xl[1], max(dat[:, 0]))))
            yl = ((min(yl[0], min(dat[:, c]))), (max(yl[1], max(dat[:, c]))))
            fx = int(shp[0] * float(c) / shp[1])
            if self.lerr:
                tx, ty = dat[fx, 0], dat[fx, c]
                txt = 'RMSE: %.2f' % round(self.lerr[ddx], 2)
                if not self.optMode:
                    self.axdipole.annotate(txt, xy=(dat[0, 0], dat[0, c]),
                                           xytext=(tx, ty), color=clr,
                                           fontweight='bold')
            label = fn.split(os.path.sep)[-1].split('.txt')[0]
            self.lpatch.append(mpatches.Patch(color=clr, label=label))
            ddx += 1

        self.axdipole.set_xlim(xl)
        self.axdipole.set_ylim(yl)

        if self.lpatch:
            self.axdipole.legend(handles=self.lpatch, loc=2)

        if self.errtot:
            tx, ty = 0, 0
            if self.optMode and initial_err:
                clr = 'black'
                txt = 'RMSE: %.2f' % round(initial_err, 2)
                textcoords = 'axes fraction'
                self.annot_avg = self.axdipole.annotate(txt, xy=(0, 0),
                                                        xytext=(0.005, 0.005),
                                                        textcoords=textcoords,
                                                        color=clr,
                                                        fontweight='bold')
                clr = 'gray'
                txt = 'RMSE: %.2f' % round(self.errtot, 2)
                self.annot_avg = self.axdipole.annotate(txt, xy=(0, 0),
                                                        xytext=(0.86, 0.005),
                                                        textcoords=textcoords,
                                                        color=clr,
                                                        fontweight='bold')
            else:
                clr = 'black'
                txt = 'Avg. RMSE: %.2f' % round(self.errtot, 2)
                self.annot_avg = self.axdipole.annotate(txt, xy=(0, 0),
                                                        xytext=(0.005, 0.005),
                                                        textcoords=textcoords,
                                                        color=clr,
                                                        fontweight='bold')

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

        if self.optMode:
            self.lpatch.append(mpatches.Patch(color='grey',
                                              label='Optimization'))
            self.lpatch.append(mpatches.Patch(color='black', label='Initial'))
        elif self._has_simdata():
            self.lpatch.append(mpatches.Patch(color='black',
                                              label='Simulation'))
        if hasattr(self, 'annot_avg'):
            self.annot_avg.set_visible(False)
            del self.annot_avg

    def plotsimdat(self):
        """plot the simulation data"""

        global drawindivdpl, drawavgdpl, fontsize

        self.gRow = 0
        bottom = 0.0

        failed_loading = False
        only_create_axes = False

        if self.params is None:
            only_create_axes = True
            DrawSpec = False
            xl = (0.0, 1.0)
        else:
            # setup the figure axis for drawing the dipole signal
            dinty = get_inputs(self.params)

            self.sim_data.update_sim_data(self.paramfn, self.params)

            single_sim_data = self.sim_data._sim_data[self.paramfn]['data']
            if single_sim_data['avg_dpl'] is None:
                failed_loading = True

            xl = (0.0, self.params['tstop'])
            if dinty['Ongoing'] or dinty['Evoked'] or dinty['Poisson']:
                xo = self.plotinputhist(xl, dinty)
                if xo:
                    self.gRow = xo[1]

            # whether to draw the specgram - should draw if user saved it or
            # have ongoing, poisson, or tonic inputs
            DrawSpec = (not failed_loading) and \
                single_sim_data['spec'] is not None and \
                (self.params['save_spec_data'] or dinty['Ongoing']
                 or dinty['Poisson'] or dinty['Tonic'])

        if DrawSpec:  # dipole axis takes fewer rows if also drawing specgram
            self.axdipole = self.figure.add_subplot(self.G[self.gRow:5, 0])
            bottom = 0.08
        else:
            self.axdipole = self.figure.add_subplot(self.G[self.gRow:-1, 0])

        yl = (-0.001, 0.001)
        self.axdipole.set_ylim(yl)
        self.axdipole.set_xlim(xl)

        left = 0.08
        w, _ = getscreengeom()
        if w < 2800:
            left = 0.1
        # reduce padding
        self.figure.subplots_adjust(left=left, right=0.99, bottom=bottom,
                                    top=0.99, hspace=0.1, wspace=0.1)

        if failed_loading or only_create_axes:
            return

        ds = None
        tstop = self.params['tstop']
        dt = self.params['dt']
        xl = (0, tstop)

        # get spectrogram if it exists, then adjust axis limits but only
        # if drawing spectrogram
        if DrawSpec:
            single_sim_data = self.sim_data._sim_data[self.paramfn]['data']
            if single_sim_data['spec'] is not None:
                ds = single_sim_data['spec']  # spectrogram
                xl = (ds['time'][0], ds['time'][-1])  # use spectogram limits
            else:
                DrawSpec = False

        sampr = 1e3 / dt  # dipole sampling rate
        # use these indices to find dipole min,max
        sidx, eidx = int(sampr*xl[0] / 1e3), int(sampr*xl[1] / 1e3)

        yl = [0, 0]
        dpl = self.sim_data._sim_data[self.paramfn]['data']['avg_dpl']
        yl[0] = min(yl[0], np.amin(dpl[sidx:eidx, 1]))
        yl[1] = max(yl[1], np.amax(dpl[sidx:eidx, 1]))

        if not self.optMode:
            # skip for optimization
            # plot average dipoles from prior simulations
            for paramfn in self.sim_data._sim_data.keys():
                old_data = self.sim_data._sim_data[paramfn]['data']['avg_dpl']
                if old_data is None:
                    continue
                times = old_data[:, 0]
                old_dpl = old_data[:, 1]
                self.axdipole.plot(times, old_dpl, '--', color='black',
                                   linewidth=self.linewidth)

            sim_data = self.sim_data._sim_data[self.paramfn]['data']
            # plot dipoles from individual trials
            if self.params['N_trials'] > 1 and drawindivdpl and \
                    len(sim_data['dpl_trials']) > 0:
                for dpltrial in sim_data['dpl_trials']:
                    self.axdipole.plot(dpltrial[:, 0], dpltrial[:, 1],
                                       color='gray',
                                       linewidth=self.linewidth)
                    yl[0] = min(yl[0], dpltrial[sidx:eidx, 1].min())
                    yl[1] = max(yl[1], dpltrial[sidx:eidx, 1].max())

            if drawavgdpl or self.params['N_trials'] <= 1:
                # this is the average dipole (across trials)
                # it's also the ONLY dipole when running a single trial
                self.axdipole.plot(dpl[:, 0], dpl[:, 1], 'k',
                                   linewidth=self.linewidth + 1)
                yl[0] = min(yl[0], dpl[sidx:eidx, 1].min())
                yl[1] = max(yl[1], dpl[sidx:eidx, 1].max())
        else:
            if self.sim_data._opt_data['avg_dpl'] is not None:
                # show optimized dipole as gray line
                optdpl = self.sim_data._opt_data['avg_dpl']
                self.axdipole.plot(optdpl[:, 0], optdpl[:, 1], 'k',
                                   color='gray',
                                   linewidth=self.linewidth + 1)
                yl[0] = min(yl[0], optdpl[sidx:eidx, 1].min())
                yl[1] = max(yl[1], optdpl[sidx:eidx, 1].max())

            if self.sim_data._opt_data['initial_dpl'] is not None:
                # show initial dipole in dotted black line
                plot_data = self.sim_data._opt_data['initial_dpl']
                times = plot_data[:, 0]
                plot_dpl = plot_data[:, 0]
                self.axdipole.plot(times, plot_dpl, '--', color='black',
                                   linewidth=self.linewidth)
                dpl = self.sim_data._opt_data['initial_dpl'][sidx:eidx, 1]
                yl[0] = min(yl[0], dpl.min())
                yl[1] = max(yl[1], dpl.max())

        scalefctr = float(self.params['dipole_scalefctr'])

        # get the number of pyramidal neurons used in the simulation
        try:
            x = self.params['N_pyr_x']
            y = self.params['N_pyr_y']
            num_pyr = int(x * y * 2)
        except KeyError:
            num_pyr = 0

        NEstPyr = int(num_pyr * scalefctr)

        if NEstPyr > 0:
            self.axdipole.set_ylabel(r'Dipole (nAm $\times$ ' +
                                     str(scalefctr) +
                                     ')\nFrom Estimated ' +
                                     str(NEstPyr) + ' Cells',
                                     fontsize=fontsize)
        else:
            self.axdipole.set_ylabel(r'Dipole (nAm $\times$ ' +
                                     str(scalefctr) +
                                     ')\n', fontsize=fontsize)
        self.axdipole.set_xlim(xl)
        self.axdipole.set_ylim(yl)

        if DrawSpec:
            gRow = 6
            self.axspec = self.figure.add_subplot(self.G[gRow:10, 0])
            cax = self.axspec.imshow(ds['TFR'], extent=(ds['time'][0],
                                                        ds['time'][-1],
                                                        ds['freq'][-1],
                                                        ds['freq'][0]),
                                     aspect='auto', origin='upper',
                                     cmap=plt.get_cmap(
                                         self.params['spec_cmap']))
            self.axspec.set_ylabel('Frequency (Hz)', fontsize=fontsize)
            self.axspec.set_xlabel('Time (ms)', fontsize=fontsize)
            self.axspec.set_xlim(xl)
            self.axspec.set_ylim(ds['freq'][-1], ds['freq'][0])
            cbaxes = self.figure.add_axes([0.6, 0.49, 0.3, 0.005])
            # plot colorbar horizontally to save space
            plt.colorbar(cax, cax=cbaxes, orientation='horizontal')
        else:
            self.axdipole.set_xlabel('Time (ms)', fontsize=fontsize)

    def plotarrows(self):
        # run after scales have been updated
        xl = self.axdipole.get_xlim()
        yl = self.axdipole.get_ylim()

        dinty = get_inputs(self.params)
        if dinty['Evoked']:
            self.drawEVInputTimes(self.axdipole, yl, 0.1,
                                  (xl[1] - xl[0]) * .02,
                                  (yl[1] - yl[0]) * .02)

    def plot(self, recalcErr=True):
        self.clearaxes()
        plt.close(self.figure)
        self.figure.clf()
        self.axdipole = None

        self.plotsimdat()  # creates self.axdipole
        self.plotextdat(recalcErr)
        self.plotarrows()

        self.draw()
