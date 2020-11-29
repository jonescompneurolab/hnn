import os
from PyQt5.QtWidgets import QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
from math import ceil
from glob import glob
from scipy import signal

from hnn_core import read_spikes
from hnn_core.dipole import Dipole

from .spikefn import ExtInputs
from .paramrw import get_output_dir, get_fname, get_inputs
from .paramrw import countEvokedInputs
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
            if os.path.exists(sim_dir):
                print('Warning: could not read file:', dipole_fn)
        except ValueError:
            if os.path.exists(sim_dir):
                print('Warning: could not read file:', dipole_fn)

        ldpl.append(dpl_trial)

    return ldpl


def check_feeds_to_plot(feeds_from_spikes, params):
    # ensures synaptic weight > 0
    using_feeds = get_inputs(params)

    feed_counts = {'pois': len(feeds_from_spikes['pois']) > 0,
                   'evdist': len(feeds_from_spikes['evdist']) > 0,
                   'evprox': len(feeds_from_spikes['evprox']) > 0,
                   'dist': len(feeds_from_spikes['dist']) > 0,
                   'prox': len(feeds_from_spikes['prox']) > 0}
    feed_counts['evoked'] = feed_counts['evdist'] or feed_counts['evprox']
    feed_counts['ongoing'] = feed_counts['dist'] or feed_counts['prox']

    feeds_to_plot = {}
    for key in feed_counts.keys():
        feeds_to_plot[key] = feed_counts[key] and using_feeds[key]

    return feeds_to_plot


def plot_hists_on_gridspec(figure, gridspec, feeds_to_plot, extinputs, times,
                           xlim, linewidth):

    axdist = axpois = axprox = None
    axes = []
    n_hists = 0

    # check poisson inputs, create subplot
    if feeds_to_plot['pois']:
        axpois = figure.add_subplot(gridspec[n_hists, :])
        n_hists += 1

    # check distal inputs, create subplot
    if feeds_to_plot['evdist'] or feeds_to_plot['dist']:
        axdist = figure.add_subplot(gridspec[n_hists, :])
        n_hists += 1

    # check proximal inputs, create subplot
    if feeds_to_plot['evprox'] or feeds_to_plot['prox']:
        axprox = figure.add_subplot(gridspec[n_hists, :])
        n_hists += 1

    # check input types provided in simulation
    if feeds_to_plot['pois']:
        extinputs.plot_hist(axpois, 'pois', times, 'auto', xlim,
                            color='k', hty='step',
                            lw=linewidth+1)
        axes.append(axpois)
    if feeds_to_plot['dist']:
        extinputs.plot_hist(axdist, 'dist', times, 'auto', xlim,
                            color='g', lw=linewidth+1)
        axes.append(axdist)
    if feeds_to_plot['prox']:
        extinputs.plot_hist(axprox, 'prox', times, 'auto', xlim,
                            color='r', lw=linewidth+1)
        axes.append(axprox)
    if feeds_to_plot['evdist']:
        extinputs.plot_hist(axdist, 'evdist', times, 'auto', xlim,
                            color='g', hty='step',
                            lw=linewidth+1)
        axes.append(axdist)
    if feeds_to_plot['evprox']:
        extinputs.plot_hist(axprox, 'evprox', times, 'auto', xlim,
                            color='r', hty='step',
                            lw=linewidth+1)
        axes.append(axprox)

    # get the ymax for the two histograms
    ymax = 0
    for ax in [axpois, axdist, axprox]:
        if ax is not None:
            if ax.get_ylim()[1] > ymax:
                ymax = ax.get_ylim()[1]

    # set ymax for both to be the same
    for ax in [axpois, axdist, axprox]:
        if ax is not None:
            ax.set_ylim(0, ymax)
            ax.set_xlim(xlim)
            ax.legend(loc=1)  # legend in upper right

    # invert the distal input axes
    if axdist is not None:
        axdist.invert_yaxis()

    return axes


class SimData(object):
    """The SimData class"""

    def __init__(self):
        self._sim_data = {}
        self._opt_data = {}
        self._exp_data = {}
        self._data_dir = os.path.join(get_output_dir(), 'data')

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

        sim_dir = os.path.join(self._data_dir, params['sim_prefix'])
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
            spikes_array = np.r_[raw_spikes.spike_times,
                                 raw_spikes.spike_gids].T
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
        using_feeds = get_inputs(params)
        if params['save_spec_data'] or using_feeds['ongoing'] or \
                using_feeds['pois'] or using_feeds['tonic']:
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

    def _read_dpl(self, paramfn, trial_idx, ntrial):
        if ntrial == 1:
            dpltrial = self._sim_data[paramfn]['data']['avg_dpl']
        else:
            trial_data = self._sim_data[paramfn]['data']['dpl_trials']
            if trial_idx > len(trial_data):
                print("Warning: data not available for trials above index",
                      (len(trial_data) - 1))
                return None

            dpltrial = self._sim_data[paramfn]['data']['dpl_trials'][trial_idx]

        dpl_data = np.c_[dpltrial[:, 1],
                         dpltrial[:, 2],
                         dpltrial[:, 3]]

        return Dipole(dpltrial[:, 0], dpl_data)

    def _plot_spec(self, ax, paramfn, params, xlim, fontsize):
        single_spec = self._sim_data[paramfn]['data']['spec']

        # Plot TFR data and add colorbar
        plot = ax.imshow(single_spec['TFR'],
                         extent=(single_spec['time'][0],
                                 single_spec['time'][-1],
                                 single_spec['freq'][-1],
                                 single_spec['freq'][0]),
                         aspect='auto', origin='upper',
                         cmap=plt.get_cmap(params['spec_cmap']))
        ax.set_ylabel('Frequency (Hz)', fontsize=fontsize)
        ax.set_xlabel('Time (ms)', fontsize=fontsize)
        ax.set_xlim(xlim)
        ax.set_ylim(single_spec['freq'][-1], single_spec['freq'][0])

        return plot

    def save_spec_with_hist(self, paramfn, params):
        sim_dir = os.path.join(self._data_dir, params['sim_prefix'])
        ntrial = params['N_trials']
        xmin = 0.
        xmax = params['tstop']
        xlim = (xmin, xmax)
        linewidth = 1

        num_step = ceil(xmax / params['dt']) + 1
        times = np.linspace(xmin, xmax, num_step)

        for trial_idx in range(ntrial):
            spec_fn = get_fname(sim_dir, 'rawspec', trial_idx, ntrial)
            spike_fn = get_fname(sim_dir, 'rawspk', trial_idx, ntrial)
            out_paramfn = get_fname(sim_dir, 'param', trial_idx, ntrial)

            # Generate file prefix
            fprefix = os.path.splitext(os.path.split(spec_fn)[-1])[0]

            # Create the fig name
            fig_name = os.path.join(sim_dir, fprefix+'.png')

            f = plt.figure(figsize=(8, 8))
            font_prop = {'size': 8}
            mpl.rc('font', **font_prop)

            # get inputs from spike file
            extinputs = ExtInputs(spike_fn, out_paramfn, params)
            extinputs.add_delay_times()
            feeds_from_spikes = extinputs.inputs
            feeds_to_plot = check_feeds_to_plot(feeds_from_spikes, params)

            if feeds_to_plot['ongoing'] or feeds_to_plot['evoked'] or \
                    feeds_to_plot['pois']:
                # hist gridspec
                gs2 = gridspec.GridSpec(2, 1, hspace=0.14, bottom=0.75,
                                        top=0.95, left=0.1, right=0.82)

                plot_hists_on_gridspec(f, gs2, feeds_to_plot, extinputs,
                                       times, xlim, linewidth)

            # the right margin is a hack and NOT guaranteed!
            # it's making space for the stupid colorbar that creates a new
            # grid to replace gs1 when called, and it doesn't update the
            # params of gs1
            gs0 = gridspec.GridSpec(1, 4, wspace=0.05, hspace=0., bottom=0.05,
                                    top=0.45, left=0.1, right=1.)
            gs1 = gridspec.GridSpec(2, 1, height_ratios=[1, 3], bottom=0.50,
                                    top=0.70, left=0.1, right=0.82)

            axspec = f.add_subplot(gs0[:, :])
            axdipole = f.add_subplot(gs1[:, :])

            cax = self._plot_spec(axspec, paramfn, params, xlim, fontsize)
            f.colorbar(cax, ax=axspec)

            # set xlim based on TFR plot
            # xlim_new = axspec.get_xlim()

            # dipole
            dpl = self._read_dpl(paramfn, trial_idx, ntrial)
            if dpl is None:
                break
            dpl.plot(axdipole, 'agg', show=False)
            axdipole.set_xlim(xlim)

            f.savefig(fig_name, dpi=300)
            plt.close(f)

    def save_dipole_with_hist(self, paramfn, params):
        sim_dir = os.path.join(self._data_dir, params['sim_prefix'])
        ntrial = params['N_trials']
        xmin = 0.
        xmax = params['tstop']
        xlim = (xmin, xmax)
        linewidth = 1

        num_step = ceil(xmax / params['dt']) + 1
        times = np.linspace(xmin, xmax, num_step)

        for trial_idx in range(ntrial):
            dipole_fn = get_fname(sim_dir, 'normdpl', trial_idx, ntrial)
            spike_fn = get_fname(sim_dir, 'rawspk', trial_idx, ntrial)
            out_paramfn = get_fname(sim_dir, 'param', trial_idx, ntrial)

            # split to find file prefix
            file_prefix = dipole_fn.split('/')[-1].split('.')[0]
            # Create the fig name
            fig_name = os.path.join(sim_dir, file_prefix+'.png')
            f = plt.figure(figsize=(12, 6))
            font_prop = {'size': 8}
            mpl.rc('font', **font_prop)

            extinputs = ExtInputs(spike_fn, out_paramfn, params)
            extinputs.add_delay_times()
            feeds_from_spikes = extinputs.inputs
            feeds_to_plot = check_feeds_to_plot(feeds_from_spikes, params)

            if feeds_to_plot['ongoing'] or feeds_to_plot['evoked'] or \
                    feeds_to_plot['pois']:
                # hist gridspec
                gs1 = gridspec.GridSpec(2, 1, hspace=0.14, bottom=0.60,
                                        top=0.95, left=0.1, right=0.90)

                plot_hists_on_gridspec(f, gs1, feeds_to_plot, extinputs,
                                       times, xlim, linewidth)

            # dipole gridpec
            gs0 = gridspec.GridSpec(1, 1, wspace=0.05, hspace=0, bottom=0.10,
                                    top=0.55, left=0.1, right=0.90)
            axdipole = f.add_subplot(gs0[:, :])

            # dipole
            dpl = self._read_dpl(paramfn, trial_idx, ntrial)
            if dpl is None:
                break
            dpl.plot(axdipole, 'agg', show=False)
            axdipole.set_xlim(xlim)

            fig_name = os.path.join(sim_dir, file_prefix+'.png')
            f.savefig(fig_name, dpi=300)
            plt.close(f)


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
        self._data_dir = os.path.join(get_output_dir(), 'data')

        self.optMode = optMode
        if not optMode:
            self.sim_data.clear_opt_data()
        self.plot()

    def initaxes(self):
        # initialize the axes
        self.axdipole = self.axspec = None

    def plotinputhist(self, extinputs=None, feeds_to_plot=None,
                      plot_distribs=False):
        """ plot input histograms"""

        xmin = 0.
        xmax = self.params['tstop']
        xlim = (xmin, xmax)
        axes = []

        sim_dt = self.params['dt']
        num_step = ceil(xmax / sim_dt) + 1
        times = np.linspace(xmin, xmax, num_step)

        sim_dir = os.path.join(self._data_dir, self.params['sim_prefix'])
        spike_fn = os.path.join(sim_dir, 'spk.txt')
        out_paramfn = os.path.join(sim_dir, 'param.txt')

        if not plot_distribs:
            if feeds_to_plot is None:
                extinputs = ExtInputs(spike_fn, out_paramfn, self.params)
                extinputs.add_delay_times()
                dinput = extinputs.inputs
                feeds_to_plot = check_feeds_to_plot(dinput, self.params)

            if feeds_to_plot['ongoing'] or feeds_to_plot['evoked'] or \
                    feeds_to_plot['pois']:
                # hist gridspec
                axes = plot_hists_on_gridspec(self.figure, self.G,
                                              feeds_to_plot, extinputs, times,
                                              xlim, self.linewidth)
            else:
                plot_distribs = True

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
                            lw=self.linewidth,
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
                            lw=self.linewidth,
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
            xlim = (0.0, 1.0)
        else:
            tstop = self.params['tstop']
            xlim = (0.0, tstop)
            sim_dir = os.path.join(self._data_dir, self.params['sim_prefix'])
            spike_fn = os.path.join(sim_dir, 'spk.txt')
            out_paramfn = os.path.join(sim_dir, 'param.txt')
            try:
                extinputs = ExtInputs(spike_fn, out_paramfn, self.params)
                extinputs.add_delay_times()
                feeds_from_spikes = extinputs.inputs
                feeds_to_plot = check_feeds_to_plot(feeds_from_spikes,
                                                    self.params)
                axes = self.plotinputhist(extinputs, feeds_to_plot,
                                          plot_distribs=False)
                self.gRow = len(axes)
            except FileNotFoundError:
                axes = self.plotinputhist(plot_distribs=True)
                self.gRow = len(axes)

            # for trying to plot a simulation read from disk (e.g. default)
            if self.paramfn not in self.sim_data._sim_data:
                self.sim_data.update_sim_data(self.paramfn, self.params)

            # check that dipole data is present
            single_sim = self.sim_data._sim_data[self.paramfn]['data']
            if single_sim['avg_dpl'] is None:
                failed_loading = True

            # whether to draw the specgram - should draw if user saved it or
            # have ongoing, poisson, or tonic inputs
            DrawSpec = (not failed_loading) and \
                single_sim['spec'] is not None and \
                (self.params['save_spec_data'] or feeds_to_plot['ongoing']
                 or feeds_to_plot['pois'] or feeds_to_plot['tonic'])

        if DrawSpec:  # dipole axis takes fewer rows if also drawing specgram
            self.axdipole = self.figure.add_subplot(self.G[self.gRow:5, 0])
            bottom = 0.08
        else:
            self.axdipole = self.figure.add_subplot(self.G[self.gRow:-1, 0])

        ylim = (-0.001, 0.001)
        self.axdipole.set_ylim(ylim)
        self.axdipole.set_xlim(xlim)

        left = 0.08
        w, _ = getscreengeom()
        if w < 2800:
            left = 0.1
        # reduce padding
        self.figure.subplots_adjust(left=left, right=0.99, bottom=bottom,
                                    top=0.99, hspace=0.1, wspace=0.1)

        if failed_loading or only_create_axes:
            return

        # get spectrogram if it exists, then adjust axis limits but only
        # if drawing spectrogram
        if DrawSpec:
            single_sim = self.sim_data._sim_data[self.paramfn]['data']
            if single_sim['spec'] is not None:
                # use spectogram limits (missing first 50 ms b/c edge effects)
                xl = (single_sim['spec']['time'][0],
                      single_sim['spec']['time'][-1])
            else:
                DrawSpec = False

        yl = [0, 0]
        dpl = self.sim_data._sim_data[self.paramfn]['data']['avg_dpl']
        yl[0] = min(yl[0], np.amin(dpl[:, 1]))
        yl[1] = max(yl[1], np.amax(dpl[:, 1]))

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
                    yl[0] = min(yl[0], dpltrial[:, 1].min())
                    yl[1] = max(yl[1], dpltrial[:, 1].max())

            if drawavgdpl or self.params['N_trials'] <= 1:
                # this is the average dipole (across trials)
                # it's also the ONLY dipole when running a single trial
                self.axdipole.plot(dpl[:, 0], dpl[:, 1], 'k',
                                   linewidth=self.linewidth + 1)
                yl[0] = min(yl[0], dpl[:, 1].min())
                yl[1] = max(yl[1], dpl[:, 1].max())
        else:
            if self.sim_data._opt_data['avg_dpl'] is not None:
                # show optimized dipole as gray line
                optdpl = self.sim_data._opt_data['avg_dpl']
                self.axdipole.plot(optdpl[:, 0], optdpl[:, 1], 'k',
                                   color='gray',
                                   linewidth=self.linewidth + 1)
                yl[0] = min(yl[0], optdpl[:, 1].min())
                yl[1] = max(yl[1], optdpl[:, 1].max())

            if self.sim_data._opt_data['initial_dpl'] is not None:
                # show initial dipole in dotted black line
                plot_data = self.sim_data._opt_data['initial_dpl']
                times = plot_data[:, 0]
                plot_dpl = plot_data[:, 0]
                self.axdipole.plot(times, plot_dpl, '--', color='black',
                                   linewidth=self.linewidth)
                dpl = self.sim_data._opt_data['initial_dpl'][:, 1]
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
        self.axdipole.set_xlim(xlim)
        self.axdipole.set_ylim(yl)

        if DrawSpec:
            gRow = 6
            self.axspec = self.figure.add_subplot(self.G[gRow:10, 0])
            cax = self.sim_data._plot_spec(self.axspec, self.paramfn,
                                           self.params, xl, fontsize)
            cbaxes = self.figure.add_axes([0.6, 0.49, 0.3, 0.005])
            # plot colorbar horizontally to save space
            plt.colorbar(cax, cax=cbaxes, orientation='horizontal')
        else:
            self.axdipole.set_xlabel('Time (ms)', fontsize=fontsize)

    def plotarrows(self):
        # run after scales have been updated
        xl = self.axdipole.get_xlim()
        yl = self.axdipole.get_ylim()

        using_feeds = get_inputs(self.params)
        if using_feeds['evoked']:
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
