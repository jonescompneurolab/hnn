import os
import sys
import numpy as np
from math import ceil
from glob import glob
from pickle import dump, load
from copy import deepcopy

from scipy import signal
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from hnn_core import read_spikes
from hnn_core.dipole import read_dipole, average_dipoles

from .spikefn import ExtInputs
from .specfn import plot_spec
from .paramrw import get_output_dir, get_fname, get_inputs
from .paramrw import read_gids_param

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
        self._opt_data = {'initial_dpl': None,
                          'initial_error': sys.float_info.max}
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
        success: bool
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
            return False
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
                dpl1 = sim_dpl.data['agg'][sim_start_index:sim_end_index]
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
        self._opt_data = {'initial_dpl': None,
                          'initial_error': sys.float_info.max}

    def in_sim_data(self, paramfn):
        if paramfn in self._sim_data:
            return True
        return False

    def update_opt_data(self, paramfn, params, avg_dpl, dpls=None,
                        spikes=None, gid_ranges=None, spec=None,
                        vsoma=None):
        self._opt_data = {'initial_dpl': self._opt_data['initial_dpl'],
                          'initial_error': self._opt_data['initial_error'],
                          'paramfn': paramfn,
                          'params': params,
                          'data': {'dpls': None,
                                   'avg_dpl': avg_dpl,
                                   'spikes': None,
                                   'gid_ranges': None,
                                   'spec': None,
                                   'vsoma': None}}

    def update_initial_opt_data_from_sim_data(self, event, paramfn):
        if paramfn not in self._sim_data:
            raise ValueError("Simulation not in sim_data: %s" % paramfn)

        single_sim_data = self._sim_data[paramfn]['data']
        self._opt_data['initial_dpl'] = \
            deepcopy(single_sim_data['avg_dpl'])
        self._opt_data['initial_error'] = self.get_err(paramfn)

        event.set()

    def get_err(self, paramfn, tstop=None):
        if paramfn not in self._sim_data:
            raise ValueError("Simulation not in sim_data: %s" % paramfn)

        if tstop is None:
            tstop = self._sim_data[paramfn]['params']['tstop']
        _,  err = self.calcerr(paramfn, tstop)
        return err

    def get_err_wrapper(self, queue, paramfn, tstop=None):
        err = self.get_err(paramfn, tstop)
        queue.put(err)

    def get_werr(self, paramfn, weights, tstop=None, tstart=None):
        if paramfn not in self._sim_data:
            raise ValueError("Simulation not in sim_data: %s" % paramfn)

        if tstop is None:
            tstop = self._sim_data[paramfn]['params']['tstop']
        _,  werr = self.calcerr(paramfn, tstop, tstart, weights)
        return werr

    def get_werr_wrapper(self, queue, paramfn, weights, tstop=None,
                         tstart=None):
        err = self.get_werr(paramfn, weights, tstop, tstart)
        queue.put(err)

    def update_opt_data_from_sim_data(self, event, paramfn):
        if paramfn not in self._sim_data:
            raise ValueError("Simulation not in sim_data: %s" % paramfn)

        sim_params = self._sim_data[paramfn]['params']
        single_sim = self._sim_data[paramfn]['data']
        self._opt_data = {'initial_dpl': self._opt_data['initial_dpl'],
                          'initial_error': self._opt_data['initial_error'],
                          'paramfn': paramfn,
                          'params': deepcopy(sim_params),
                          'data': {'dpls': deepcopy(single_sim['dpls']),
                                   'avg_dpl': deepcopy(single_sim['avg_dpl']),
                                   'spikes': deepcopy(single_sim['spikes']),
                                   'gid_ranges':
                                       deepcopy(single_sim['gid_ranges']),
                                   'spec': deepcopy(single_sim['spec']),
                                   'vsoma': deepcopy(single_sim['vsoma'])}}

        event.set()

    def update_sim_data_from_opt_data(self, event, paramfn):
        opt_data = self._opt_data['data']
        single_sim = {'paramfn': paramfn,
                      'params': deepcopy(self._opt_data['params']),
                      'data': {'dpls': deepcopy(opt_data['dpls']),
                               'avg_dpl': deepcopy(opt_data['avg_dpl']),
                               'spikes': deepcopy(opt_data['spikes']),
                               'gid_ranges':
                                   deepcopy(opt_data['gid_ranges']),
                               'spec': deepcopy(opt_data['spec']),
                               'vsoma': deepcopy(opt_data['vsoma'])}}
        self._sim_data[paramfn] = single_sim

        event.set()

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
            single_sim = self._sim_data[paramfn]['data']

            # get inputs from spike file
            gid_ranges = single_sim['gid_ranges']
            spikes = single_sim['spikes'][trial_idx]
            extinputs = ExtInputs(spikes, gid_ranges, [trial_idx], params)
            feeds_to_plot = check_feeds_to_plot(extinputs.inputs, params)

            dpl = self._read_dpl(paramfn, trial_idx, ntrial)
            if dpl is None:
                continue

            # whether to draw the specgram - should draw if user saved
            # it or have ongoing, poisson, or tonic inputs
            if single_sim['spec'] is None \
                    or len(single_sim['spec']) == 0 \
                    or not (params['save_spec_data'] or
                            feeds_to_plot['ongoing'] or
                            feeds_to_plot['pois']):
                continue

            # go ahead and plot figure
            f = plt.figure(figsize=(8, 8))
            font_prop = {'size': 8}
            mpl.rc('font', **font_prop)

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
            dpl = self._read_dpl(paramfn, trial_idx, ntrial)
            if dpl is None:
                continue

            # go ahead and plot figure
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

    def plot_dipole(self, paramfn, ax, linewidth, dipole_scalefctr, N_pyr_x=0,
                    N_pyr_y=0, is_optimization=False):
        """Plot the dipole(s) HNN style

        Parameters
        ----------
        paramfn : str
            Simulation parameter filename to lookup data from prior simulation
        ax : axis object
            Axis on which to plot dipoles(s)
        linewidth : int
            Base width for dipole lines. Averages will be one size larger
        dipole_scalefctr : float
            Scaling factor applied to dipole data
        N_pyr_x : int
            Nr of cells (x)
        N_pyr_y : int
            Nr of cells (y)
        is_optimization : bool
            True if plots should be specific for optimization results
        """

        yl = [0, 0]
        dpl = self._sim_data[paramfn]['data']['avg_dpl']
        yl[0] = min(yl[0], np.amin(dpl.data['agg']))
        yl[1] = max(yl[1], np.amax(dpl.data['agg']))

        if not is_optimization:
            # plot average dipoles from prior simulations
            old_dpl = self._sim_data[paramfn]['data']['avg_dpl']
            ax.plot(old_dpl.times, old_dpl.data['agg'], '--', color='black',
                    linewidth=linewidth)

            sim_data = self._sim_data[paramfn]['data']
            ntrial = len(sim_data['dpls'])
            # plot dipoles from individual trials
            if ntrial > 1 and drawindivdpl:
                for dpltrial in sim_data['dpls']:
                    ax.plot(dpltrial.times, dpltrial.data['agg'],
                            color='gray',
                            linewidth=linewidth)
                    yl[0] = min(yl[0], dpltrial.data['agg'].min())
                    yl[1] = max(yl[1], dpltrial.data['agg'].max())

            if drawavgdpl or ntrial == 1:
                # this is the average dipole (across trials)
                # it's also the ONLY dipole when running a single trial
                ax.plot(dpl.times, dpl.data['agg'], 'k',
                        linewidth=linewidth + 1)
                yl[0] = min(yl[0], dpl.data['agg'].min())
                yl[1] = max(yl[1], dpl.data['agg'].max())
        elif 'data' in self._opt_data:
            if 'avg_dpl' not in self._opt_data['data'] or \
                    'initial_dpl' not in self._opt_data:
                # if there was an exception running optimization
                # still plot average dipole from sim
                ax.plot(dpl.times, dpl.data['agg'], 'k',
                        linewidth=linewidth + 1)
                yl[0] = min(yl[0], dpl.data['agg'].min())
                yl[1] = max(yl[1], dpl.data['agg'].max())
            else:
                if self._opt_data['data']['avg_dpl'] is not None:
                    # show optimized dipole as gray line
                    optdpl = self._opt_data['data']['avg_dpl']
                    ax.plot(optdpl.times, optdpl.data['agg'], 'k',
                            color='gray', linewidth=linewidth + 1)
                    yl[0] = min(yl[0], optdpl.data['agg'].min())
                    yl[1] = max(yl[1], optdpl.data['agg'].max())

                if self._opt_data['initial_dpl'] is not None:
                    # show initial dipole in dotted black line
                    plot_data = self._opt_data['initial_dpl']
                    times = plot_data.times
                    plot_dpl = plot_data.data['agg']
                    ax.plot(times, plot_dpl, '--', color='black',
                            linewidth=linewidth)
                    dpl = self._opt_data['initial_dpl'].data['agg']
                    yl[0] = min(yl[0], dpl.min())
                    yl[1] = max(yl[1], dpl.max())

        # get the number of pyramidal neurons used in the simulation and
        # multiply by scale factor to get estimated number of pyramidal
        # neurons for y-axis label
        num_pyr = int(N_pyr_x * N_pyr_y * 2)
        NEstPyr = int(num_pyr * float(dipole_scalefctr))
        if NEstPyr > 0:
            ax.set_ylabel(r'Dipole (nAm $\times$ ' +
                          str(dipole_scalefctr) +
                          ')\nFrom Estimated ' +
                          str(NEstPyr) + ' Cells', fontsize=fontsize)
        else:
            # is this handling overflow?
            ax.set_ylabel(r'Dipole (nAm $\times$ ' +
                          str(dipole_scalefctr) +
                          ')\n', fontsize=fontsize)
        ax.set_ylim(yl)
