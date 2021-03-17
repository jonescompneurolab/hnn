import os
import numpy as np
from math import ceil
from glob import glob
from pickle import dump, load

from scipy import signal
from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec

from hnn_core import read_spikes
from hnn_core.dipole import read_dipole, average_dipoles

from .spikefn import ExtInputs
from .specfn import plot_spec
from .paramrw import get_output_dir, get_fname, get_inputs
from .paramrw import countEvokedInputs, read_gids_param
from .qt_lib import getscreengeom

drawindivdpl = 1
drawavgdpl = 1
fontsize = plt.rcParams['font.size'] = 10


def get_dipoles_from_disk(sim_dir, ntrials):
    """Read dipole trial data from disk

    Parameters
    ----------
    sim_dir : str
        Path of simulation data directory
    ntrials : int
        Number of trials expected to be read from disk

    Returns
    ----------
    dpls: list of Dipole objects
        List containing Dipoles of each trial
    """

    dpls = []
    dpl_fname_pattern = os.path.join(sim_dir, 'dpl_*.txt')
    glob_list = sorted(glob(str(dpl_fname_pattern)))
    if len(glob_list) == 0:
        # get the old style filename
        glob_list = [get_fname(sim_dir, 'normdpl')]

    for dipole_fn in glob_list:
        dpl_trial = None
        try:
            dpl_trial = read_dipole(dipole_fn)
        except OSError:
            if os.path.exists(sim_dir):
                print('Warning: could not read file:', dipole_fn)
        except ValueError:
            if os.path.exists(sim_dir):
                print('Warning: could not read file:', dipole_fn)

        dpls.append(dpl_trial)

    if len(dpls) == 0:
        print("Warning: no dipole(s) read from %s" % sim_dir)

    if len(dpls) < ntrials:
        print("Warning: only read %d of %d dipole files in %s" %
              (len(dpls), ntrials, sim_dir))

    return dpls


def read_spectrials(sim_dir):
    """read spectrogram data files for individual trials"""
    spec_list = []

    spec_fname_pattern = os.path.join(sim_dir, 'rawspec_*.npz')
    glob_list = sorted(glob(str(spec_fname_pattern)))
    if len(glob_list) == 0:
        # get the old style filename
        glob_list = [get_fname(sim_dir, 'rawspec')]

    for spec_fn in glob_list:
        spec_trial = None
        try:
            with np.load(spec_fn, allow_pickle=True) as spec_data:
                # need to make a copy of data so we can close NpzFile
                spec_trial = dict(spec_data)
        except OSError:
            if os.path.exists(sim_dir):
                print('Warning: could not read file:', spec_fn)
        except ValueError:
            if os.path.exists(sim_dir):
                print('Warning: could not read file:', spec_fn)

        spec_list.append(spec_trial)

    return spec_list


def read_vsomatrials(sim_dir):
    """read somatic voltage data files for individual trials"""
    vsoma_list = []

    vsoma_fname_pattern = os.path.join(sim_dir, 'vsoma_*.pkl')
    glob_list = sorted(glob(str(vsoma_fname_pattern)))
    if len(glob_list) == 0:
        # get the old style filename
        glob_list = [get_fname(sim_dir, 'vsoma')]

    for vsoma_fn in glob_list:
        vsoma_trial = None
        try:
            with open(vsoma_fn, 'rb') as f:
                vsoma_trial = load(f)
        except OSError:
            if os.path.exists(sim_dir):
                print('Warning: could not read file:', vsoma_fn)
        except ValueError:
            if os.path.exists(sim_dir):
                print('Warning: could not read file:', vsoma_fn)

        vsoma_list.append(vsoma_trial)

    return vsoma_list


def read_spktrials(sim_dir, gid_ranges):
    spk_fname_pattern = os.path.join(sim_dir, 'spk_*.txt')
    if len(glob(str(spk_fname_pattern))) == 0:
        # if legacy HNN only ran one trial, then no spk_0.txt gets written
        spk_fname_pattern = get_fname(sim_dir, 'rawspk')

    try:
        spikes = read_spikes(spk_fname_pattern, gid_ranges)
    except FileNotFoundError:
        print('Warning: could not read file:', spk_fname_pattern)

    return spikes


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

    plot_linewidth = linewidth + 1
    # check input types provided in simulation
    if feeds_to_plot['pois']:
        extinputs.plot_hist(axpois, 'pois', times, 'auto', xlim,
                            color='k', hty='step',
                            lw=plot_linewidth)
        axes.append(axpois)
    if feeds_to_plot['dist']:
        extinputs.plot_hist(axdist, 'dist', times, 'auto', xlim,
                            color='g', lw=plot_linewidth)
        axes.append(axdist)
    if feeds_to_plot['prox']:
        extinputs.plot_hist(axprox, 'prox', times, 'auto', xlim,
                            color='r', lw=plot_linewidth)
        axes.append(axprox)
    if feeds_to_plot['evdist']:
        extinputs.plot_hist(axdist, 'evdist', times, 'auto', xlim,
                            color='g', hty='step',
                            lw=plot_linewidth)
        axes.append(axdist)
    if feeds_to_plot['evprox']:
        extinputs.plot_hist(axprox, 'evprox', times, 'auto', xlim,
                            color='r', hty='step',
                            lw=plot_linewidth)
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

    def update_sim_data(self, paramfn, params, dpls, avg_dpl, spikes,
                        gid_ranges, spec=None, vsoma=None):
        self._sim_data[paramfn] = {'params': params,
                                   'data': {'dpls': dpls,
                                            'avg_dpl': avg_dpl,
                                            'spikes': spikes,
                                            'gid_ranges': gid_ranges,
                                            'spec': spec, 'vsoma': vsoma}}

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

    def update_sim_data_from_disk(self, paramfn, params):
        """Adds simulation data to SimData

        Parameters
        ----------
        paramfn : str
            Simulation parameter filename
        params : dict
            Dictionary containing parameters

        Returns
        ----------
        found: bool
            Whether simulation data could be read
        """

        sim_dir = os.path.join(self._data_dir, params['sim_prefix'])
        if not os.path.exists(sim_dir):
            self.update_sim_data(paramfn, params, None, None, None, None)
            return False

        dpls = get_dipoles_from_disk(sim_dir, params['N_trials'])
        if len(dpls) == 0:
            self.update_sim_data(paramfn, params, None, None, None, None)
            return False
        elif len(dpls) == 1:
            avg_dpl = dpls[0]
        else:
            avg_dpl = average_dipoles(dpls)

        warning_message = 'Warning: could not read file:'
        # gid_ranges
        paramtxt_fn = get_fname(sim_dir, 'param')
        try:
            gid_ranges = read_gids_param(paramtxt_fn)
        except FileNotFoundError:
            print(warning_message, paramtxt_fn)
            return False

        # spikes
        spikes = read_spktrials(sim_dir, gid_ranges)
        if len(spikes.spike_times) == 0:
            print("Warning: no spikes read from %s" % sim_dir)
        elif len(spikes.spike_times) < params['N_trials']:
            print("Warning: only read %d of %d spike files in %s" %
                  (len(spikes.spike_times), params['N_trials'], sim_dir))

        # spec data
        spec = None
        using_feeds = get_inputs(params)
        if params['save_spec_data'] or using_feeds['ongoing'] or \
                using_feeds['pois'] or using_feeds['tonic']:
            spec = read_spectrials(sim_dir)
            if len(spec) == 0:
                print("Warning: no spec data read from %s" % sim_dir)
            elif len(spec) < params['N_trials']:
                print("Warning: only read %d of %d spec files in %s" %
                      (len(spec), params['N_trials'], sim_dir))

        # somatic voltages
        vsoma = None
        if params['record_vsoma']:
            vsoma = read_vsomatrials(sim_dir)
            if len(vsoma) == 0:
                print("Warning: no somatic voltages read from %s" % sim_dir)
            elif len(vsoma) < params['N_trials']:
                print("Warning: only read %d of %d voltage files in %s" %
                    (len(vsoma), params['N_trials'], sim_dir))

        self.update_sim_data(paramfn, params, dpls, avg_dpl, spikes,
                             gid_ranges, spec, vsoma)

        return True

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
            sim_times = self._sim_data[paramfn]['data']['avg_dpl'].times

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
            trial_data = self._sim_data[paramfn]['data']['dpls']
            if trial_idx > len(trial_data):
                print("Warning: data not available for trials above index",
                      (len(trial_data) - 1))
                return None

            dpltrial = self._sim_data[paramfn]['data']['dpls'][trial_idx]

        return dpltrial

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
            f = plt.figure(figsize=(8, 8))
            font_prop = {'size': 8}
            mpl.rc('font', **font_prop)

            # get inputs from spike file
            gid_ranges = self._sim_data[paramfn]['data']['gid_ranges']
            spikes = self._sim_data[paramfn]['data']['spikes'][trial_idx]
            extinputs = ExtInputs(spikes, gid_ranges, [trial_idx], params)
            feeds_to_plot = check_feeds_to_plot(extinputs.inputs, params)

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

            spec_data = self._sim_data[paramfn]['data']['spec']
            cax = plot_spec(axspec, spec_data, ntrial,
                            params['spec_cmap'], xlim, fontsize)
            f.colorbar(cax, ax=axspec)

            # set xlim based on TFR plot
            # xlim_new = axspec.get_xlim()

            # dipole
            dpl = self._read_dpl(paramfn, trial_idx, ntrial)
            if dpl is None:
                break
            dpl.plot(layer='agg', ax=axdipole, show=False)
            axdipole.set_xlim(xlim)

            spec_fig_fn = get_fname(sim_dir, 'figspec', trial_idx)
            f.savefig(spec_fig_fn, dpi=300)
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
            f = plt.figure(figsize=(12, 6))
            font_prop = {'size': 8}
            mpl.rc('font', **font_prop)

            gid_ranges = self._sim_data[paramfn]['data']['gid_ranges']
            spikes = self._sim_data[paramfn]['data']['spikes'][trial_idx]
            extinputs = ExtInputs(spikes, gid_ranges, [trial_idx], params)
            feeds_to_plot = check_feeds_to_plot(extinputs.inputs, params)

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
            dpl.plot(layer='agg', ax=axdipole, show=False)
            axdipole.set_xlim(xlim)

            dipole_fig_fn = get_fname(sim_dir, 'figdpl', trial_idx)
            f.savefig(dipole_fig_fn, dpi=300)
            plt.close(f)

    def save_vsoma(self, paramfn, params):
        ntrial = params['N_trials']
        sim_dir = os.path.join(self._data_dir, params['sim_prefix'])
        current_sim_data = self._sim_data[paramfn]['data']

        for trial_idx in range(ntrial):
            vsoma_outfn = get_fname(sim_dir, 'vsoma', trial_idx)

            if trial_idx + 1 > len(current_sim_data['vsoma']):
                raise ValueError("No vsoma data for trial %d" % trial_idx)

            vsoma = current_sim_data['vsoma'][trial_idx]

            # store tvec with voltages. it will be the same for
            # all trials
            vsoma['vtime'] = current_sim_data['dpls'][0].times
            with open(str(vsoma_outfn), 'wb') as f:
                dump(vsoma, f)

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
        FigureCanvasQTAgg.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding,
                                        QtWidgets.QSizePolicy.Expanding)
        FigureCanvasQTAgg.updateGeometry(self)
        self.params = params
        self.paramfn = paramfn
        self.axdipole = self.axspec = None
        self.G = gridspec.GridSpec(10, 1)
        self._data_dir = os.path.join(get_output_dir(), 'data')

        self.optMode = optMode
        if not optMode:
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
                                              xlim, self.linewidth)

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

        failed_loading_dpl = False
        failed_loading_spec = False
        only_create_axes = False

        DrawSpec = False
        xlim = (0.0, 1.0)
        only_create_axes = False

        if self.params is not None:
            ntrial = self.params['N_trials']
            # for trying to plot a simulation read from disk (e.g. default)
            if self.paramfn not in self.sim_data._sim_data:
                found = self.sim_data.update_sim_data_from_disk(self.paramfn,
                                                                self.params)
                if not found:
                    # best we can do is plot the distributions of the inputs
                    axes = self.plotinputhist()
                    self.gRow = len(axes)
                    only_create_axes = True

            if not only_create_axes:
                tstop = self.params['tstop']
                xlim = (0.0, tstop)

                sim_data = self.sim_data._sim_data[self.paramfn]['data']
                trials = [trial_idx for trial_idx in range(ntrial)]
                extinputs = ExtInputs(sim_data['spikes'],
                                      sim_data['gid_ranges'],
                                      trials, self.params)

                feeds_to_plot = check_feeds_to_plot(extinputs.inputs,
                                                    self.params)
                axes = self.plotinputhist(extinputs, feeds_to_plot)
                self.gRow = len(axes)

                # check that dipole data is present
                single_sim = self.sim_data._sim_data[self.paramfn]['data']
                if single_sim['avg_dpl'] is None:
                    failed_loading_dpl = True

                if single_sim['spec'] is None or len(single_sim['spec']) == 0:
                    failed_loading_spec = True
                # whether to draw the specgram - should draw if user saved
                # it or have ongoing, poisson, or tonic inputs
                if (not failed_loading_spec) and single_sim['spec'] is \
                        not None \
                        and (self.params['save_spec_data'] or
                             feeds_to_plot['ongoing'] or
                             feeds_to_plot['pois'] or feeds_to_plot['tonic']):
                    DrawSpec = True

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

        if failed_loading_dpl or only_create_axes or self.params is None:
            return

        # get spectrogram if it exists, then adjust axis limits but only
        # if drawing spectrogram
        if DrawSpec:
            single_sim = self.sim_data._sim_data[self.paramfn]['data']
            if single_sim['spec'] is not None:
                first_spec_trial = single_sim['spec'][0]
                # use spectogram limits (missing first 50 ms b/c edge effects)
                xlim = (first_spec_trial['time'][0],
                        first_spec_trial['time'][-1])
            else:
                DrawSpec = False

        yl = [0, 0]
        dpl = self.sim_data._sim_data[self.paramfn]['data']['avg_dpl']
        yl[0] = min(yl[0], np.amin(dpl.data['agg']))
        yl[1] = max(yl[1], np.amax(dpl.data['agg']))

        if not self.optMode:
            # skip for optimization
            # plot average dipoles from prior simulations
            for paramfn in self.sim_data._sim_data.keys():
                old_data = self.sim_data._sim_data[paramfn]['data']['avg_dpl']
                if old_data is None:
                    continue
                times = old_data.times
                old_dpl = old_data.data['agg']
                self.axdipole.plot(times, old_dpl, '--', color='black',
                                   linewidth=self.linewidth)

            sim_data = self.sim_data._sim_data[self.paramfn]['data']
            # plot dipoles from individual trials
            if ntrial > 1 and drawindivdpl and \
                    len(sim_data['dpls']) > 0:
                for dpltrial in sim_data['dpls']:
                    self.axdipole.plot(dpltrial.times, dpltrial.data['agg'],
                                       color='gray',
                                       linewidth=self.linewidth)
                    yl[0] = min(yl[0], dpltrial.data['agg'].min())
                    yl[1] = max(yl[1], dpltrial.data['agg'].max())

            if drawavgdpl or ntrial <= 1:
                # this is the average dipole (across trials)
                # it's also the ONLY dipole when running a single trial
                self.axdipole.plot(dpl.times, dpl.data['agg'], 'k',
                                   linewidth=self.linewidth + 1)
                yl[0] = min(yl[0], dpl.data['agg'].min())
                yl[1] = max(yl[1], dpl.data['agg'].max())
        else:
            if self.sim_data._opt_data['avg_dpl'] is not None:
                # show optimized dipole as gray line
                optdpl = self.sim_data._opt_data['avg_dpl']
                self.axdipole.plot(optdpl.times, optdpl.data['agg'], 'k',
                                   color='gray',
                                   linewidth=self.linewidth + 1)
                yl[0] = min(yl[0], optdpl.data['agg'].min())
                yl[1] = max(yl[1], optdpl.data['agg'].max())

            if self.sim_data._opt_data['initial_dpl'] is not None:
                # show initial dipole in dotted black line
                plot_data = self.sim_data._opt_data['initial_dpl']
                times = plot_data.times
                plot_dpl = plot_data.data['agg']
                self.axdipole.plot(times, plot_dpl, '--', color='black',
                                   linewidth=self.linewidth)
                dpl = self.sim_data._opt_data['initial_dpl'].data['agg']
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
            spec_data = sim_data['spec']
            cax = plot_spec(self.axspec, spec_data, ntrial,
                            self.params['spec_cmap'], xlim,
                            fontsize)
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
