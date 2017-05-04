# dipolefn.py - dipole-based analysis functions
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: itertools and return data dir)
# last major: (SL: toward python3)

import fileio as fio
import numpy as np
import ast
import os
import paramrw
import spikefn
import specfn
import matplotlib.pyplot as plt
#from neuron import h as nrn
import axes_create as ac
from math import ceil

# class Dipole() is for a single set of f_dpl and f_param
class Dipole():
    def __init__(self, f_dpl): # fix to allow init from data in memory (not disk)
        """ some usage: dpl = Dipole(file_dipole, file_param)
            this gives dpl.t and dpl.dpl
        """
        self.units = None
        self.N = None
        self.__parse_f(f_dpl)

    # opens the file and sets units
    def __parse_f(self, f_dpl):
        x = np.loadtxt(open(f_dpl, 'r'))
        # better implemented as a dict
        self.t = x[:, 0]
        self.dpl = {
            'agg': x[:, 1],
            'L2': x[:, 2],
            'L5': x[:, 3],
        }
        self.N = self.dpl['agg'].shape[-1]
        # string that holds the units
        self.units = 'fAm'

    # truncate to a length and save here
    def truncate(self, t0, T):
        """ this is independent of the other stuff
            moved to an external function so as to not disturb the delicate genius of this object
        """
        self.t, self.dpl = self.truncate_ext(t0, T)

    # just return the values, do not modify the class internally
    def truncate_ext(self, t0, T):
        # only do this if the limits make sense
        if (t0 >= self.t[0]) & (T <= self.t[-1]):
            dpl_truncated = dict.fromkeys(self.dpl)
            # do this for each dpl
            for key in self.dpl.keys():
                dpl_truncated[key] = self.dpl[key][(self.t >= t0) & (self.t <= T)]
            t_truncated = self.t[(self.t >= t0) & (self.t <= T)]
        return t_truncated, dpl_truncated

    # conversion from fAm to nAm
    def convert_fAm_to_nAm (self):
        """ must be run after baseline_renormalization()
        """
        for key in self.dpl.keys(): self.dpl[key] *= 1e-6
        # change the units string
        self.units = 'nAm'

    def scale (self, fctr):
      for key in self.dpl.keys(): self.dpl[key] *= fctr
      return fctr

    # average stationary dipole over a time window
    def mean_stationary(self, opts_input={}):
        # opts is default AND input to below, can be modified by opts_input
        opts = {
            't0': 50.,
            'tstop': self.t[-1],
            'layer': 'agg',
        }
        # attempt to override the keys in opts
        for key in opts_input.keys():
            # check for each of the keys in opts
            if key in opts.keys():
                # special rule for tstop
                if key == 'tstop':
                    # if value in tstop is -1, then use end to T
                    if opts_input[key] == -1:
                        opts[key] = self.t[-1]
                else:
                    opts[key] = opts_input[key]
        # check for layer in keys
        if opts['layer'] in self.dpl.keys():
            # get the dipole that matches the xlim
            x_dpl = self.dpl[opts['layer']][(self.t > opts['t0']) & (self.t < opts['tstop'])]
            # directly return the average
            return np.mean(x_dpl, axis=0)
        else:
            print("Layer not found. Try one of %s" % self.dpl.keys())

    # finds the max value within a specified xlim
    # def max(self, layer, xlim):
    def lim(self, layer, xlim):
        # better implemented as a dict
        if layer is None:
            dpl_tmp = self.dpl['agg']
        elif layer in self.dpl.keys():
            dpl_tmp = self.dpl[layer]
        # set xmin and xmax
        if xlim is None:
            xmin = self.t[0]
            xmax = self.t[-1]
        else:
            xmin, xmax = xlim
            if xmin < 0.: xmin = 0.
            if xmax < 0.: xmax = self.f[-1]
        dpl_tmp = dpl_tmp[(self.t > xmin) & (self.t < xmax)]
        return (np.min(dpl_tmp), np.max(dpl_tmp))

    # simple layer-specific plot function
    def plot(self, ax, xlim, layer='agg'):
        # plot the whole thing and just change the xlim and the ylim
        # if layer is None:
        #     ax.plot(self.t, self.dpl['agg'])
        #     ymax = self.max(None, xlim)
        #     ylim = (-ymax, ymax)
        #     ax.set_ylim(ylim)
        if layer in self.dpl.keys():
            ax.plot(self.t, self.dpl[layer])
            ylim = self.lim(layer, xlim)
            # force ymax to be something sane
            # commenting this out for now, but
            # we can change if absolutely necessary.
            # ax.set_ylim(top=ymax*1.2)
            # set the lims here, as a default
            ax.set_ylim(ylim)
            ax.set_xlim(xlim)
        else:
            print("raise some error")
        return ax.get_xlim()

    # ext function to renormalize
    # this function changes in place but does NOT write the new values to the file
    def baseline_renormalize(self, f_param):
        # only baseline renormalize if the units are fAm
        if self.units == 'fAm':
            N_pyr_x = paramrw.find_param(f_param, 'N_pyr_x')
            N_pyr_y = paramrw.find_param(f_param, 'N_pyr_y')
            # N_pyr cells in grid. This is PER LAYER
            N_pyr = N_pyr_x * N_pyr_y
            # dipole offset calculation: increasing number of pyr cells (L2 and L5, simultaneously)
            # with no inputs resulted in an aggregate dipole over the interval [50., 1000.] ms that
            # eventually plateaus at -48 fAm. The range over this interval is something like 3 fAm
            # so the resultant correction is here, per dipole
            # dpl_offset = N_pyr * 50.207
            dpl_offset = {
                # these values will be subtracted
                'L2': N_pyr * 0.0443,
                'L5': N_pyr * -49.0502
                # 'L5': N_pyr * -48.3642,
                # will be calculated next, this is a placeholder
                # 'agg': None,
            }
            # L2 dipole offset can be roughly baseline shifted over the entire range of t
            self.dpl['L2'] -= dpl_offset['L2']
            # L5 dipole offset should be different for interval [50., 500.] and then it can be offset
            # slope (m) and intercept (b) params for L5 dipole offset
            # uncorrected for N_cells
            # these values were fit over the range [37., 750.)
            m = 3.4770508e-3
            b = -51.231085
            # these values were fit over the range [750., 5000]
            t1 = 750.
            m1 = 1.01e-4
            b1 = -48.412078
            # piecewise normalization
            self.dpl['L5'][self.t <= 37.] -= dpl_offset['L5']
            self.dpl['L5'][(self.t > 37.) & (self.t < t1)] -= N_pyr * (m * self.t[(self.t > 37.) & (self.t < t1)] + b)
            self.dpl['L5'][self.t >= t1] -= N_pyr * (m1 * self.t[self.t >= t1] + b1)
            # recalculate the aggregate dipole based on the baseline normalized ones
            self.dpl['agg'] = self.dpl['L2'] + self.dpl['L5']
        else:
            print("Warning, no dipole renormalization done because units were in %s" % (self.units))

    # function to write to a file!
    # f_dpl must be fully specified
    def write(self, f_dpl):
        with open(f_dpl, 'w') as f:
            for t, x_agg, x_L2, x_L5 in zip(self.t, self.dpl['agg'], self.dpl['L2'], self.dpl['L5']):
                f.write("%03.3f\t" % t)
                f.write("%.4e\t" % x_agg)
                f.write("%.4e\t" % x_L2)
                f.write("%.4e\n" % x_L5)

# throwaway save method for now - see note
def dpl_convert_and_save(ddata, i=0, j=0):
    """ trial is currently undefined
        function is broken for N_trials > 1
    """
    # take the ith sim, jth trial, do some stuff to it, resave it
    # only uses first expmt_group
    expmt_group = ddata.expmt_groups[0]

    # need n_trials
    p_exp = paramrw.ExpParams(ddata.fparam)
    if not p_exp.N_trials:
        N_trials = 1
    else:
        N_trials = p_exp.N_trials

    # absolute number
    n = i*N_trials + j

    # grab the correct files
    f_dpl = ddata.file_match(expmt_group, 'rawdpl')[n]
    f_param = ddata.file_match(expmt_group, 'param')[n]

    # print ddata.sim_prefix, ddata.dsim
    f_name_short = '%s-%03d-T%02d-dpltest.txt' % (ddata.sim_prefix, i, j)
    f_name = os.path.join(ddata.dsim, expmt_group, f_name_short)
    print(f_name)

    dpl = Dipole(f_dpl)
    dpl.baseline_renormalize(f_param)
    print("baseline renormalized")

    dpl.convert_fAm_to_nAm()
    print("converted to nAm")

    dpl.write(f_name)

# ddata is a fio.SimulationPaths() object
def calc_aggregate_dipole(ddata):
    for expmt_group in ddata.expmt_groups:
        # create the filename
        dexp = ddata.dexpmt_dict[expmt_group]
        fname_short = '%s-%s-dpl' % (ddata.sim_prefix, expmt_group)
        fname_data = os.path.join(dexp, fname_short + '.txt')

        # grab the list of raw data dipoles and assoc params in this expmt
        dpl_list = ddata.file_match(expmt_group, 'rawdpl')
        param_list = ddata.file_match(expmt_group, 'param')

        for f_dpl, f_param in zip(dpl_list, param_list):
            dpl = Dipole(f_dpl)
            # dpl.baseline_renormalize(f_param)

            # initialize and use x_dpl
            if f_dpl is dpl_list[0]:
                # assume time vec stays the same throughout
                t_vec = dpl.t
                x_dpl = dpl.dpl['agg']

            else:
                # guaranteed to exist after dpl_list[0]
                x_dpl += dpl.dpl['agg']

        # poor man's mean
        x_dpl /= len(dpl_list)

        # write this data to the file
        with open(fname_data, 'w') as f:
            for t, x in zip(t_vec, x_dpl):
                f.write("%03.3f\t%5.4f\n" % (t, x))

# calculate stimulus evoked dipole
def calc_avgdpl_stimevoked(ddata):
    for expmt_group in ddata.expmt_groups:
        # create the filename
        dexp = ddata.dexpmt_dict[expmt_group]
        fname_short = '%s-%s-dpl' % (ddata.sim_prefix, expmt_group)
        fname_data = os.path.join(dexp, fname_short + '.txt')

        # grab the list of raw data dipoles and assoc params in this expmt
        fdpl_list = ddata.file_match(expmt_group, 'rawdpl')
        param_list = ddata.file_match(expmt_group, 'param')
        spk_list = ddata.file_match(expmt_group, 'rawspk')

        # actual list of Dipole() objects
        dpl_list = [Dipole(fdpl) for fdpl in fdpl_list]
        t_truncated = []

        # iterate through the lists, grab the spike time, phase align the signals,
        # cut them to length, and then mean the dipoles
        for dpl, f_spk, f_param in zip(dpl_list, spk_list, param_list):
            _, p = paramrw.read(f_param)

            # grab the corresponding relevant starting spike time
            s = spikefn.spikes_from_file(f_param, f_spk)
            s = spikefn.alpha_feed_verify(s, p)
            s = spikefn.add_delay_times(s, p)

            # t_evoked is the same for all of the cells in these simulations
            t_evoked = s['evprox0'].spike_list[0][0]

            # attempt to give a 50 ms buffer
            if t_evoked > 50.:
                t0 = t_evoked - 50.
            else:
                t0 = t_evoked

            # truncate the dipole related vectors
            dpl.t = dpl.t[dpl.t > t0]
            dpl.dpl['agg'] = dpl.dpl['agg'][dpl.t > t0]
            t_truncated.append(dpl.t[0])

        # find the t0_max value to compare on other dipoles
        t_truncated -= np.max(t_truncated)

        for dpl, t_adj in zip(dpl_list, t_truncated):
            # negative numbers mean that this vector needs to be shortened by that many ms
            T_new = dpl.t[-1] + t_adj
            dpl.dpl['agg'] = dpl.dpl['agg'][dpl.t < T_new]
            dpl.t = dpl.t[dpl.t < T_new]

            if dpl is dpl_list[0]:
                dpl_total = dpl.dpl['agg']

            else:
                dpl_total += dpl.dpl['agg']

        dpl_mean = dpl_total / len(dpl_list)
        t_dpl = dpl_list[0].t

        # write this data to the file
        with open(fname_data, 'w') as f:
            for t, x in zip(t_dpl, dpl_mean):
                f.write("%03.3f\t%5.4f\n" % (t, x))

# Creates a template of dpl activity by averaging dpl data over specified time intervals
# Assumes t_intervals are all the same length
def create_template(fname, dpl_list, param_list, t_interval_list):
    # iterate over lists, load dpl data and average
    for fdpl, fparam, t_int in zip(dpl_list, param_list, t_interval_list):
        # load ts data
        dpl = Dipole(fdpl)
        dpl.baseline_renormalize(fparam)
        # dpl.convert_fAm_to_nAm()

        # truncate data based on time ranges specified in dmax
        t_cut, dpl_tcut = dpl.truncate_ext(t_int[0], t_int[1])

        if fdpl is dpl_list[0]:
            x_dpl_agg = dpl_tcut['agg']
            x_dpl_L2 = dpl_tcut['L2']
            x_dpl_L5 = dpl_tcut['L5']

        else:
            x_dpl_agg += dpl_tcut['agg']
            x_dpl_L2 += dpl_tcut['L2']
            x_dpl_L5 += dpl_tcut['L5']

    # poor man's mean
    x_dpl_agg /= len(dpl_list)
    x_dpl_L2 /= len(dpl_list)
    x_dpl_L5 /= len(dpl_list)

    # create a tvec that is symmetric about zero and of proper length
    # assume time intervals are identical length for all data
    t_range = t_interval_list[0][1] - t_interval_list[0][0]
    t_start = - t_range / 2.
    t_end = t_range / 2.
    tvec = np.linspace(t_start, t_end, x_dpl_agg.shape[0])
    # tvec = np.linspace(0, t_range, x_dpl_agg.shape[0])

    # save to file
    with open(fname, 'w') as f:
        for t, x_agg, x_L2, x_L5 in zip(tvec, x_dpl_agg, x_dpl_L2, x_dpl_L5):
            f.write("%03.3f\t%5.4f\t%5.4f\t%5.4f\n" % (t, x_agg, x_L2, x_L5))

# one off function to plot linear regression
def plinear_regression(ffig_dpl, fdpl):
    dpl = Dipole(fdpl)
    layer = 'L5'
    t0 = 750.

    # dipole for the given layer, truncated
    # order matters here
    x_dpl = dpl.dpl[layer][(dpl.t > t0)]
    t = dpl.t[dpl.t > t0]

    # take the transpose (T) of a vector of the times and ones for each element
    A = np.vstack([t, np.ones(len(t))]).T

    # find the slope and the y-int of the line fit with least squares method (min. of Euclidean 2-norm)
    m, c = np.linalg.lstsq(A, x_dpl)[0]
    print(m, c)

    # plot me
    f = ac.FigStd()
    f.ax0.plot(t, x_dpl)
    f.ax0.hold(True)
    f.ax0.plot(t, m*t + c, 'r')

    # save over the original
    f.savepng(ffig_dpl)
    f.close()

# plot a dipole to an axis from corresponding dipole and param files
def pdipole_ax(a, f_dpl, f_param):
    dpl = Dipole(f_dpl)
    dpl.baseline_renormalize(f_param)

    a.plot(dpl.t, dpl.dpl['agg'])

    # any further xlim sets can be done by whoever wants to do them later
    a.set_xlim((0., dpl.t[-1]))

    # at least make the ylim symmetrical about 0
    ylim = a.get_ylim()
    abs_y_max = np.max(np.abs(ylim))
    ylim = (-abs_y_max, abs_y_max)
    a.set_ylim(ylim)

    # return the actual time in form of xlim. ain't pretty but works
    return a.get_xlim()

# pdipole is for a single dipole file, should be for a
def pdipole(f_dpl, dfig, plot_dict, f_param=None, key_types={}):
    """ single dipole file combination (incl. param file)
        this should be done with an axis input too
        two separate functions, a pdipole kernel function and a specific function for this simple plot
    """
    # dpl is an obj of Dipole() class
    dpl = Dipole(f_dpl)

    if f_param:
        dpl.baseline_renormalize(f_param)

    dpl.convert_fAm_to_nAm()

    # split to find file prefix
    file_prefix = f_dpl.split('/')[-1].split('.')[0]


    # parse xlim from plot_dict
    if plot_dict['xlim'] is None:
        xmin = dpl.t[0]
        xmax = dpl.t[-1]

    else:
        xmin, xmax = plot_dict['xlim']

        if xmin < 0.:
            xmin = 0.

        if xmax < 0.:
            xmax = self.f[-1]

    # # get xmin and xmax from the plot_dict
    # if plot_dict['xmin'] is None:
    #     xmin = 0.
    # else:
    #     xmin = plot_dict['xmin']

    # if plot_dict['xmax'] is None:
    #     xmax = p_dict['tstop']
    # else:
    #     xmax = plot_dict['xmax']

    # truncate them using logical indexing
    t_range = dpl.t[(dpl.t >= xmin) & (dpl.t <= xmax)]
    dpl_range = dpl.dpl['agg'][(dpl.t >= xmin) & (dpl.t <= xmax)]

    f = ac.FigStd()
    f.ax0.plot(t_range, dpl_range)

    # sorry about the parity between vars here and above with xmin/xmax
    if plot_dict['ylim'] is None:
    # if plot_dict['ymin'] is None or plot_dict['ymax'] is None:
        pass
    else:
        f.ax0.set_ylim(plot_dict['ylim'][0], plot_dict['ylim'][1])
        # f.ax0.set_ylim(plot_dict['ymin'], plot_dict['ymax'])

    # Title creation
    if f_param and key_types:
        # grabbing the p_dict from the f_param
        _, p_dict = paramrw.read(f_param)

        # useful for title strings
        title_str = ac.create_title(p_dict, key_types)
        f.f.suptitle(title_str)

    # create new fig name
    fig_name = os.path.join(dfig, file_prefix+'.png')

    # savefig
    plt.savefig(fig_name, dpi=300)
    f.close()

# plot vertical lines corresponding to the evoked input times
def pdipole_evoked(dfig, f_dpl, f_spk, f_param, ylim=[]):
    """ for each individual simulation/trial
    """
    gid_dict, p_dict = paramrw.read(f_param)

    # get the spike dict from the files
    s_dict = spikefn.spikes_from_file(f_param, f_spk)
    s = s_dict.keys()
    s.sort()

    # create an empty dict 'spk_unique'
    spk_unique = dict.fromkeys([key for key in s_dict.keys() if key.startswith(('evprox', 'evdist'))])

    for key in spk_unique:
        spk_unique[key] = s_dict[key].unique_all(0)

    # draw vertical lines for each item in this

    # x_dipole is dipole data
    # x_dipole = np.loadtxt(open(f_dpl, 'r'))
    dpl = Dipole(f_dpl)

    # split to find file prefix
    file_prefix = f_dpl.split('/')[-1].split('.')[0]

    # # set xmin value
    # xmin = xlim[0] / p_dict['dt']

    # # set xmax value
    # if xlim[1] == 'tstop':
    #     xmax = p_dict['tstop'] / p_dict['dt']
    # else:
    #     xmax = xlim[1] / p_dict['dt']

    # these are the vectors for now, but this is going to change
    t_vec = dpl.t
    dp_total = dpl.dpl['agg']

    f = ac.FigStd()

    # hold on
    f.ax0.hold(True)

    f.ax0.plot(t_vec, dp_total)

    lines_spk = dict.fromkeys(spk_unique)

    print(spk_unique)

    # plot the lines
    for key in spk_unique:
        print(key, spk_unique[key])
        x_val = spk_unique[key][0]
        lines_spk[key] = plt.axvline(x=x_val, linewidth=0.5, color='r')

    # title_txt = [key + ': {:.2e}' % p_dict[key] for key in key_types['dynamic_keys']]
    title_txt = 'test'
    f.ax0.set_title(title_txt)

    if ylim:
        f.ax0.set_ylim(ylim)

    fig_name = os.path.join(dfig, file_prefix+'.png')

    plt.savefig(fig_name, dpi=300)
    f.close()

# Plots dipole with histogram of alpha feed inputs - slightly deprecated, see note
def pdipole_with_hist(f_dpl, f_spk, dfig, f_param, key_types, plot_dict):
  """ this function has not been converted to use the Dipole() class yet
  """
  # dpl is an obj of Dipole() class
  dpl = Dipole(f_dpl)
  dpl.baseline_renormalize(f_param)
  dpl.convert_fAm_to_nAm()
  # split to find file prefix
  file_prefix = f_dpl.split('/')[-1].split('.')[0]
  # grabbing the p_dict from the f_param
  _, p_dict = paramrw.read(f_param)
  # get xmin and xmax from the plot_dict
  if plot_dict['xmin'] is None:
    xmin = 0.
  else:
    xmin = plot_dict['xmin']
  if plot_dict['xmax'] is None:
    xmax = p_dict['tstop']
  else:
    xmax = plot_dict['xmax']
  # truncate tvec and dpl data using logical indexing
  t_range = dpl.t[(dpl.t >= xmin) & (dpl.t <= xmax)]
  dpl_range = dpl.dpl['agg'][(dpl.t >= xmin) & (dpl.t <= xmax)]
  # Plotting
  f = ac.FigDplWithHist()
  # dipole
  f.ax['dipole'].plot(t_range, dpl_range)
  # set new xlim based on dipole plot
  xlim_new = f.ax['dipole'].get_xlim()
  # Get extinput data and account for delays
  extinputs = spikefn.ExtInputs(f_spk, f_param)
  extinputs.add_delay_times()
  # set number of bins (150 bins per 1000ms)
  bins = ceil(150. * (xlim_new[1] - xlim_new[0]) / 1000.) # bins needs to be an int
  # plot histograms
  hist = {}
  hist['feed_prox'] = extinputs.plot_hist(f.ax['feed_prox'], 'prox', dpl.t, bins, xlim_new, color='red')
  hist['feed_dist'] = extinputs.plot_hist(f.ax['feed_dist'], 'dist', dpl.t, bins, xlim_new, color='green')
  # Invert dist histogram
  f.ax['feed_dist'].invert_yaxis()
  # for now, set the xlim for the other one, force it!
  f.ax['dipole'].set_xlim(xlim_new)
  f.ax['feed_prox'].set_xlim(xlim_new)
  f.ax['feed_dist'].set_xlim(xlim_new)
  # set hist axis properties
  f.set_hist_props(hist)
  # Add legend to histogram
  for key in f.ax.keys():
    if 'feed' in key:
      f.ax[key].legend()
  # force xlim on histograms
  f.ax['feed_prox'].set_xlim((xmin, xmax))
  f.ax['feed_dist'].set_xlim((xmin, xmax))
  title_str = ac.create_title(p_dict, key_types)
  f.f.suptitle(title_str)
  fig_name = os.path.join(dfig, file_prefix+'.png')
  plt.savefig(fig_name)
  f.close()

# For a given ddata (SimulationPaths object), find the mean dipole
def pdipole_exp(ddata, ylim=[]):
    """ over ALL trials in ALL conditions in EACH experiment
    """
    # sim_prefix
    fprefix = ddata.sim_prefix

    # create the figure name
    fname_exp = '%s_dpl' % (fprefix)
    fname_exp_fig = os.path.join(ddata.dsim, fname_exp + '.png')

    # create one figure comparing across all
    N_expmt_groups = len(ddata.expmt_groups)
    f_exp = ac.FigDipoleExp(ddata.expmt_groups)

    # empty list for the aggregate dipole data
    dpl_exp = []

    # go through each expmt
    for expmt_group in ddata.expmt_groups:
        # create the filename
        dexp = ddata.dexpmt_dict[expmt_group]
        fname_short = '%s-%s-dpl' % (fprefix, expmt_group)
        fname_data = os.path.join(dexp, fname_short + '.txt')
        fname_fig = os.path.join(ddata.dfig[expmt_group]['figdpl'], fname_short + '.png')

        # grab the list of raw data dipoles and assoc params in this expmt
        dpl_list = ddata.file_match(expmt_group, 'rawdpl')
        param_list = ddata.file_match(expmt_group, 'param')

        for f_dpl, f_param in zip(dpl_list, param_list):
            dpl = Dipole(f_dpl)
            dpl.baseline_renormalize(f_param)
            # x_tmp = np.loadtxt(open(file, 'r'))

            # initialize and use x_dpl
            if f_dpl is dpl_list[0]:

                # assume time vec stays the same throughout
                t_vec = dpl.t
                x_dpl = dpl.dpl['agg']

            else:
                # guaranteed to exist after dpl_list[0]
                x_dpl += dpl.dpl['agg']

        # poor man's mean
        x_dpl /= len(dpl_list)

        # save this in a list to do comparison figure
        # order is same as ddata.expmt_groups
        dpl_exp.append(x_dpl)

        # write this data to the file
        with open(fname_data, 'w') as f:
            for t, x in zip(t_vec, x_dpl):
                f.write("%03.3f\t%5.4f\n" % (t, x))

        # create the plot I guess?
        f = ac.FigStd()
        f.ax0.plot(t_vec, x_dpl)

        if len(ylim):
            f.ax0.set_ylim(ylim)

        f.savepng(fname_fig)
        f.close()

    # plot the aggregate data using methods defined in FigDipoleExp()
    f_exp.plot(t_vec, dpl_exp)

    # attempt at setting titles
    for ax, expmt_group in zip(f_exp.ax, ddata.expmt_groups):
        ax.set_title(expmt_group)

    f_exp.savepng(fname_exp_fig)
    f_exp.close()

# For a given ddata (SimulationPaths object), find the mean dipole
def pdipole_exp2(ddata):
    """ over ALL trials in ALL conditions in EACH experiment
        appears to be an iteration on pdipole_exp()
    """
    # grab the original dipole from a specific dir
    dproj = fio.return_data_dir()

    runtype = 'somethingotherthandebug'
    # runtype = 'debug'

    # really shoddy testing code! sorry!
    if runtype == 'debug':
        ddate = '2013-04-08'
        dsim = 'mubaseline-15-000'
        i_ctrl = 0
    else:
        ddate = raw_input('Short date directory? ')
        dsim = raw_input('Sim name? ')
        i_ctrl = ast.literal_eval(raw_input('Sim number: '))
    dcheck = os.path.join(dproj, ddate, dsim)

    # create a blank ddata structure
    ddata_ctrl = fio.SimulationPaths()
    dsim = ddata_ctrl.read_sim(dproj, dcheck)

    # find the mu_low and mu_high in the expmtgroup names
    # this means the group names must be well formed
    for expmt_group in ddata_ctrl.expmt_groups:
        if 'mu_low' in expmt_group:
            mu_low_group = expmt_group
        elif 'mu_high' in expmt_group:
            mu_high_group = expmt_group

    # choose the first [0] from the list of the file matches for mu_low
    fdpl_mu_low = ddata_ctrl.file_match(mu_low_group, 'rawdpl')[i_ctrl]
    fparam_mu_low = ddata_ctrl.file_match(mu_low_group, 'param')[i_ctrl]
    fspk_mu_low = ddata_ctrl.file_match(mu_low_group, 'rawspk')[i_ctrl]
    fspec_mu_low = ddata_ctrl.file_match(mu_low_group, 'rawspec')[i_ctrl]

    # choose the first [0] from the list of the file matches for mu_high
    fdpl_mu_high = ddata_ctrl.file_match(mu_high_group, 'rawdpl')[i_ctrl]
    fparam_mu_high = ddata_ctrl.file_match(mu_high_group, 'param')[i_ctrl]
    # fspk_mu_high = ddata_ctrl.file_match(mu_high_group, 'rawspk')[i_ctrl]

    # grab the relevant dipole and renormalize it for mu_low
    dpl_mu_low = Dipole(fdpl_mu_low)
    dpl_mu_low.baseline_renormalize(fparam_mu_low)

    # grab the relevant dipole and renormalize it for mu_high
    dpl_mu_high = Dipole(fdpl_mu_high)
    dpl_mu_high.baseline_renormalize(fparam_mu_high)

    # input feed information
    s = spikefn.spikes_from_file(fparam_mu_low, fspk_mu_low)
    _, p_ctrl = paramrw.read(fparam_mu_low)
    s = spikefn.alpha_feed_verify(s, p_ctrl)
    s = spikefn.add_delay_times(s, p_ctrl)

    # hard coded bin count for now
    tstop = paramrw.find_param(fparam_mu_low, 'tstop')
    bins = spikefn.bin_count(150., tstop)

    # sim_prefix
    fprefix = ddata.sim_prefix

    # create the figure name
    fname_exp = '%s_dpl' % (fprefix)
    fname_exp_fig = os.path.join(ddata.dsim, fname_exp + '.png')

    # create one figure comparing across all
    N_expmt_groups = len(ddata.expmt_groups)
    ax_handles = [
        'spec',
        'input',
        'dpl_mu_low',
        'dpl_mu_high',
    ]
    f_exp = ac.FigDipoleExp(ax_handles)

    # plot the ctrl dipoles
    f_exp.ax['dpl_mu_low'].plot(dpl_mu_low.t, dpl_mu_low.dpl['agg'], color='k')
    f_exp.ax['dpl_mu_low'].hold(True)
    f_exp.ax['dpl_mu_high'].plot(dpl_mu_high.t, dpl_mu_high.dpl['agg'], color='k')
    f_exp.ax['dpl_mu_high'].hold(True)

    # function creates an f_exp.ax_twinx list and returns the index of the new feed
    ax_twin_name = f_exp.create_axis_twinx('input')
    if not ax_twin_name:
        print("You've got bigger problems, I'm afraid")

    # input hist information: predicated on the fact that the input histograms
    # should be identical for *all* of the inputs represented in this figure
    spikefn.pinput_hist(f_exp.ax['input'], f_exp.ax_twinx['input'], s['alpha_feed_prox'][0].spike_list, s['alpha_feed_dist'][0].spike_list, n_bins)

    # grab the max counts for both hists
    # the [0] item of hist are the counts
    max_hist = np.max([np.max(hist[key][0]) for key in hist.keys()])
    ymax = 2 * max_hist

    # plot the spec here
    pc = specfn.pspec_ax(f_exp.ax['spec'], fspec_mu_low)
    print(f_exp.ax[0].get_xlim())

    # deal with the axes here
    f_exp.ax_twinx['input'].set_ylim((ymax, 0))
    f_exp.ax['input'].set_ylim((0, ymax))

    f_exp.ax['input'].set_xlim((50., tstop))
    f_exp.ax_twinx['input'].set_xlim((50., tstop))

    # empty list for the aggregate dipole data
    dpl_exp = []

    # go through each expmt
    # calculation is extremely redundant
    for expmt_group in ddata.expmt_groups:
        # a little sloppy, just find the param file
        # this param file was for the baseline renormalization and
        # assumes it's the same in all for this expmt_group
        # also for getting the gid_dict, also assumed to be the same
        fparam = ddata.file_match(expmt_group, 'param')[0]

        # general check to see if the aggregate dipole data exists
        if 'mu_low' in expmt_group or 'mu_high' in expmt_group:
            # check to see if these files exist
            flist = ddata.find_aggregate_file(expmt_group, 'dpl')

            # if no file exists, then find one
            if not len(flist):
                calc_aggregate_dipole(ddata)
                flist = ddata.find_aggregate_file(expmt_group, 'dpl')

            # testing the first file
            list_spk = ddata.file_match(expmt_group, 'rawspk')
            list_s_dict = [spikefn.spikes_from_file(fparam, fspk) for fspk in list_spk]
            list_evoked = [s_dict['evprox0'].spike_list[0][0] for s_dict in list_s_dict]
            lines_spk = [f_exp.ax[2].axvline(x=x_val, linewidth=0.5, color='r') for x_val in list_evoked]
            lines_spk = [f_exp.ax[3].axvline(x=x_val, linewidth=0.5, color='r') for x_val in list_evoked]

        # handle mu_low and mu_high separately
        if 'mu_low' in expmt_group:
            dpl_mu_low_ev = Dipole(flist[0])
            dpl_mu_low_ev.baseline_renormalize(fparam)
            f_exp.ax['dpl_mu_low'].plot(dpl_mu_low_ev.t, dpl_mu_low_ev.dpl['agg'])

        elif 'mu_high' in expmt_group:
            dpl_mu_high_ev = Dipole(flist[0])
            dpl_mu_high_ev.baseline_renormalize(fparam)
            f_exp.ax['dpl_mu_high'].plot(dpl_mu_high_ev.t, dpl_mu_high_ev.dpl['agg'])

    f_exp.ax['dpl_mu_low'].set_xlim(50., tstop)
    f_exp.ax['dpl_mu_high'].set_xlim(50., tstop)

    f_exp.savepng(fname_exp_fig)
    f_exp.close()

# For a given ddata (SimulationPaths object), find the mean dipole
def pdipole_evoked_aligned(ddata):
    """ over ALL trials in ALL conditions in EACH experiment
        appears to be iteration over pdipole_exp2()
    """
    # grab the original dipole from a specific dir
    dproj = fio.return_data_dir()

    runtype = 'somethingotherthandebug'
    # runtype = 'debug'

    if runtype == 'debug':
        ddate = '2013-04-08'
        dsim = 'mubaseline-04-000'
        i_ctrl = 0
    else:
        ddate = raw_input('Short date directory? ')
        dsim = raw_input('Sim name? ')
        i_ctrl = ast.literal_eval(raw_input('Sim number: '))
    dcheck = os.path.join(dproj, ddate, dsim)

    # create a blank ddata structure
    ddata_ctrl = fio.SimulationPaths()
    dsim = ddata_ctrl.read_sim(dproj, dcheck)

    # find the mu_low and mu_high in the expmtgroup names
    # this means the group names must be well formed
    for expmt_group in ddata_ctrl.expmt_groups:
        if 'mu_low' in expmt_group:
            mu_low_group = expmt_group
        elif 'mu_high' in expmt_group:
            mu_high_group = expmt_group

    # choose the first [0] from the list of the file matches for mu_low
    fdpl_mu_low = ddata_ctrl.file_match(mu_low_group, 'rawdpl')[i_ctrl]
    fparam_mu_low = ddata_ctrl.file_match(mu_low_group, 'param')[i_ctrl]
    fspk_mu_low = ddata_ctrl.file_match(mu_low_group, 'rawspk')[i_ctrl]
    fspec_mu_low = ddata_ctrl.file_match(mu_low_group, 'rawspec')[i_ctrl]

    # choose the first [0] from the list of the file matches for mu_high
    fdpl_mu_high = ddata_ctrl.file_match(mu_high_group, 'rawdpl')[i_ctrl]
    fparam_mu_high = ddata_ctrl.file_match(mu_high_group, 'param')[i_ctrl]

    # grab the relevant dipole and renormalize it for mu_low
    dpl_mu_low = Dipole(fdpl_mu_low)
    dpl_mu_low.baseline_renormalize(fparam_mu_low)

    # grab the relevant dipole and renormalize it for mu_high
    dpl_mu_high = Dipole(fdpl_mu_high)
    dpl_mu_high.baseline_renormalize(fparam_mu_high)

    # input feed information
    s = spikefn.spikes_from_file(fparam_mu_low, fspk_mu_low)
    _, p_ctrl = paramrw.read(fparam_mu_low)
    s = spikefn.alpha_feed_verify(s, p_ctrl)
    s = spikefn.add_delay_times(s, p_ctrl)

    # find tstop, assume same over all. grab the first param file, get the tstop
    tstop = paramrw.find_param(fparam_mu_low, 'tstop')

    # hard coded bin count for now
    n_bins = spikefn.bin_count(150., tstop)

    # sim_prefix
    fprefix = ddata.sim_prefix

    # create the figure name
    fname_exp = '%s_dpl_align' % (fprefix)
    fname_exp_fig = os.path.join(ddata.dsim, fname_exp + '.png')

    # create one figure comparing across all
    N_expmt_groups = len(ddata.expmt_groups)
    ax_handles = [
        'spec',
        'input',
        'dpl_mu',
        'spk',
    ]
    f_exp = ac.FigDipoleExp(ax_handles)

    # plot the ctrl dipoles
    f_exp.ax['dpl_mu'].plot(dpl_mu_low.t, dpl_mu_low.dpl, color='k')
    f_exp.ax['dpl_mu'].hold(True)
    f_exp.ax['dpl_mu'].plot(dpl_mu_high.t, dpl_mu_high.dpl)

    # function creates an f_exp.ax_twinx list and returns the index of the new feed
    f_exp.create_axis_twinx('input')

    # input hist information: predicated on the fact that the input histograms
    # should be identical for *all* of the inputs represented in this figure
    # places 2 histograms on two axes (meant to be one axis flipped)
    hists = spikefn.pinput_hist(f_exp.ax['input'], f_exp.ax_twinx['input'], s['alpha_feed_prox'].spike_list, s['alpha_feed_dist'].spike_list, n_bins)

    # grab the max counts for both hists
    # the [0] item of hist are the counts
    max_hist = np.max([np.max(hists[key][0]) for key in hists.keys()])
    ymax = 2 * max_hist

    # plot the spec here
    pc = specfn.pspec_ax(f_exp.ax['spec'], fspec_mu_low)

    # deal with the axes here
    f_exp.ax['input'].set_ylim((0, ymax))
    f_exp.ax_twinx['input'].set_ylim((ymax, 0))
    # f_exp.ax[1].set_ylim((0, ymax))

    # f_exp.ax[1].set_xlim((50., tstop))

    # turn hold on
    f_exp.ax[dpl_mu].hold(True)

    # empty list for the aggregate dipole data
    dpl_exp = []

    # go through each expmt
    # calculation is extremely redundant
    for expmt_group in ddata.expmt_groups:
        # a little sloppy, just find the param file
        # this param file was for the baseline renormalization and
        # assumes it's the same in all for this expmt_group
        # also for getting the gid_dict, also assumed to be the same
        fparam = ddata.file_match(expmt_group, 'param')[0]

        # general check to see if the aggregate dipole data exists
        if 'mu_low' in expmt_group or 'mu_high' in expmt_group:
            # check to see if these files exist
            flist = ddata.find_aggregate_file(expmt_group, 'dpl')

            # if no file exists, then find one
            if not len(flist):
                calc_aggregate_dipole(ddata)
                flist = ddata.find_aggregate_file(expmt_group, 'dpl')

            # testing the first file
            list_spk = ddata.file_match(expmt_group, 'rawspk')
            list_s_dict = [spikefn.spikes_from_file(fparam, fspk) for fspk in list_spk]
            list_evoked = [s_dict['evprox0'].spike_list[0][0] for s_dict in list_s_dict]
            lines_spk = [f_exp.ax['dpl_mu'].axvline(x=x_val, linewidth=0.5, color='r') for x_val in list_evoked]
            lines_spk = [f_exp.ax['spk'].axvline(x=x_val, linewidth=0.5, color='r') for x_val in list_evoked]

        # handle mu_low and mu_high separately
        if 'mu_low' in expmt_group:
            dpl_mu_low_ev = Dipole(flist[0])
            dpl_mu_low_ev.baseline_renormalize(fparam)
            f_exp.ax['spk'].plot(dpl_mu_low_ev.t, dpl_mu_low_ev.dpl, color='k')

            # get xlim stuff
            t0 = dpl_mu_low_ev.t[0]
            T = dpl_mu_low_ev.t[-1]

        elif 'mu_high' in expmt_group:
            dpl_mu_high_ev = Dipole(flist[0])
            dpl_mu_high_ev.baseline_renormalize(fparam)
            f_exp.ax['spk'].plot(dpl_mu_high_ev.t, dpl_mu_high_ev.dpl, color='b')

    f_exp.ax['input'].set_xlim(50., tstop)

    for ax_name in f_exp.ax_handles[2:]:
        ax.set_xlim((t0, T))

    f_exp.savepng(fname_exp_fig)
    f_exp.close()

# create a grid of all dipoles in this dir
def pdipole_grid(ddata):
    # iterate through expmt_groups
    for expmt_group in ddata.expmt_groups:
        fname_short = "%s-%s-dpl.png" % (ddata.sim_prefix, expmt_group)
        fname = os.path.join(ddata.dsim, expmt_group, fname_short)

        # simple usage, just checks how many dipole files (total in an expmt)
        # and then plots dumbly to a grid
        dpl_list = ddata.file_match(expmt_group, 'rawdpl')
        param_list = ddata.file_match(expmt_group, 'param')

        # assume tstop is the same everywhere
        tstop = paramrw.find_param(param_list[0], 'tstop')

        # length of the dpl list
        N_dpl = len(dpl_list)

        # make a 5-col figure
        N_cols = 5

        # force int arithmetic
        # this is the BASE number of rows, one might be added!
        N_rows = int(N_dpl) // int(N_cols)

        # if the mod is not 0, add a row
        if (N_dpl % N_cols):
            N_rows += 1

        # print(N_dpl, N_cols, N_rows)
        f = ac.FigGrid(N_rows, N_cols, tstop)

        l = []
        r = 0
        for ax_list in f.ax:
            l.extend([(r,c) for c in range(len(ax_list))])
            r += 1

        # automatically truncates the loc list to the size of dpl_list
        for loc, fdpl, fparam in zip(l, dpl_list, param_list):
            r = loc[0]
            c = loc[1]
            pdipole_ax(f.ax[r][c], fdpl, fparam)

        f.savepng(fname)
        f.close()

def plot_specmax_interval(fname, dpl_list, param_list, specmax_list):
    N_trials = len([d for d in specmax_list if d is not None])

    # instantiate figure
    f = ac.FigInterval(N_trials+1)

    # set spacing between plots
    spacers = np.arange(0.5e-4, N_trials*1e-4, 1e-4)

    # invert order of spacers so first trial is at top of plot
    spacers =  spacers[::-1]

    # iterate over various lists and plot to axis
    i = 0

    for fdpl, fparam, dmax in zip(dpl_list, param_list, specmax_list):
    # for fdpl, dmax, space in zip(dpl_list, specmax_list, spacers):
        if dmax is not None:
            # load ts data
            dpl = Dipole(fdpl)
            dpl.baseline_renormalize(fparam)
            dpl.convert_fAm_to_nAm()

            # truncate data based on time ranges specified in dmax
            t_cut, dpl_tcut = dpl.truncate_ext(dmax['t_int'][0], dmax['t_int'][1])

            # create a tvec that is symmetric about zero and of proper length
            t_range = dmax['t_int'][1] - dmax['t_int'][0]
            t_start = 0 - t_range / 2.
            t_end = 0 + t_range / 2.
            tvec = np.linspace(t_start, t_end, dpl_tcut['agg'].shape[0])

            # plot to proper height
            f.ax['ts'].plot(tvec, dpl_tcut['agg']+spacers[i])

            # add text with pertinent information
            x_offset = f.ax['ts'].get_xlim()[1] + 25
            f.ax['ts'].text(x_offset, spacers[i], 'freq: %s Hz\ntime: %s ms\n%s' %(dmax['f_at_max'],dmax['t_at_max'], dmax['fname']), fontsize=12, verticalalignment='center')

            i += 1

    # force xlim for now
    # f.ax['ts'].set_xlim(-100, 100)

    # save fig
    f.savepng(fname+'.png')

    # close fig
    f.close()
