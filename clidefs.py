# clidefs.py - these are all of the function defs for the cli
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: python3 compatibility)
# last major: (SL: minor)

# Standard modules
import fnmatch, os, re, sys
import numpy as np
from scipy import stats
from multiprocessing import Pool
from subprocess import call
from glob import iglob
from time import time
import ast
import matplotlib.pyplot as plt
import matplotlib as mpl

# local modules
import spikefn
import plotfn
import fileio as fio
import paramrw
import specfn
import pspec
import dipolefn
import axes_create as ac
import pmanu_gamma as pgamma
import subprocess

# Returns length of any list
def number_of_sims(some_list):
    return len(some_list)

# Just a simple thing to print parts of a list
def prettyprint(lines):
    for line in lines:
        print line

# gets a subdir list
def get_subdir_list(dcheck):
    if os.path.exists(dcheck):
        return [name for name in os.listdir(dcheck) if os.path.isdir(os.path.join(dcheck, name))]

    else:
        return []

# generalized function for checking and assigning args
def args_check(dict_default, dict_check):
    if len(dict_check):
        keys_missing = []

        # iterate through possible key vals in dict_check
        for key, val in dict_check.items():
            # check to see if the possible keys are in dict_default
            if key in dict_default.keys():
                # assign the key/val pair in place
                # this operation acts IN PLACE on the supplied dict_default!!
                # therefore, no return value necessary
                try:
                    dict_default[key] = ast.literal_eval(val)

                except ValueError:
                    dict_default[key] = val

            else:
                keys_missing.append(key)

        # if there are any keys missing
        if keys_missing:
            print "Options were not recognized: "
            fio.prettyprint(keys_missing)

def exec_pngv(ddata, dict_opts={}):
    """Attempt to find the PNGs and open them
       [aushnew] pngv {--run=0 --expmt_group='testing' --type='fig_spec'}
    """
    file_viewer(ddata, dict_opts)

# returns average spike data
def exec_spike_rates(ddata, opts):
    # opts should be:
    # opts_default = {
    #     expmt_group: 'something',
    #     celltype: 'L5_pyramidal',
    # }
    expmt_group = opts['expmt_group']
    celltype = opts['celltype']

    list_f_spk = ddata.file_match(expmt_group, 'rawspk')
    list_f_param = ddata.file_match(expmt_group, 'param')

    # note! this is NOT ignoring first 50 ms
    for fspk, fparam in zip(list_f_spk, list_f_param):
        s_all = spikefn.spikes_from_file(fparam, fspk)
        _, p_dict = paramrw.read(fparam)
        T = p_dict['tstop']

        # check if the celltype is in s_all
        if celltype in s_all.keys():
            s = s_all[celltype].spike_list
            n_cells = len(s)

            # grab all the sp_counts
            sp_counts = np.array([len(spikes_cell) for spikes_cell in s])

            # calc mean and stdev
            sp_count_mean = np.mean(sp_counts)
            sp_count_stdev = np.std(sp_counts)

            # calc rate in Hz, assume T in ms
            sp_rates = sp_counts * 1000. / T
            sp_rate_mean = np.mean(sp_rates)
            sp_rate_stdev = np.std(sp_rates)

            # direct
            sp_rate = sp_count_mean * 1000. / T

            print "Sim No. %i, Trial %i, celltype is %s:" % (p_dict['Sim_No'], p_dict['Trial'], celltype)
            print "  spike count mean is: %4.3f" % sp_count_mean
            print "  spike count stdev is: %4.3f" % sp_count_stdev
            print "  spike rate over %4.3f ms is %4.3f Hz +/- %4.3f" % (T, sp_rate_mean, sp_rate_stdev)
            print "  spike rate over %4.3f ms is %4.3f Hz" % (T, sp_rate)

def exec_welch_max(ddata, opts):
    p = {
        'f_min': 0.,
    }

    args_check(p, opts)

    # assume first expmt_group for now
    expmt_group = ddata.expmt_groups[0]

    # grab list of dipoles
    list_dpl = ddata.file_match(expmt_group, 'rawdpl')
    list_param = ddata.file_match(expmt_group, 'param')

    # iterate through dipoles
    for fdpl, fparam in zip(list_dpl, list_param):
        # grab the dt (needed for the Welch)
        dt = paramrw.find_param(fparam, 'dt')

        # grab the dipole
        dpl = dipolefn.Dipole(fdpl)
        dpl.baseline_renormalize(fparam)
        dpl.convert_fAm_to_nAm()

        # create empty pgram
        pgram = dict.fromkeys(dpl.dpl)
        pgram_max = dict.fromkeys(dpl.dpl)

        # perform stationary Welch, since we're not saving this data yet
        for key in pgram.keys():
            pgram[key] = specfn.Welch(dpl.t, dpl.dpl[key], dt)

            # create a mask based on f min
            fmask = (pgram[key].f > p['f_min'])
            P_cut = pgram[key].P[fmask]
            f_cut = pgram[key].f[fmask]

            p_max = np.max(P_cut)
            f_max = f_cut[P_cut == p_max]
            # p_max = np.max(pgram[key].P)
            # f_max = pgram[key].f[pgram[key].P == p_max]

            # not clear why saving for now
            pgram_max[key] = (f_max, p_max)
            print "Max power for %s was %.3e at %4.2f Hz, with f min set to %4.2f" % (key, p_max, f_max, p['f_min'])

# throwaway save method for now
# trial is currently undefined
# function is broken for N_trials > 1
def exec_throwaway(ddata, opts):
    p = {
        'n_sim': 0,
        'n_trial': 0,
    }
    args_check(p, opts)

    p_exp = paramrw.ExpParams(ddata.fparam)
    N_trials = p_exp.N_trials
    print opts, p

    if p['n_sim'] == -1:
        for i in range(p_exp.N_sims):
            if p['n_trial'] == -1:
                for j in range(N_trials):
                    dipolefn.dpl_convert_and_save(ddata, i, j)
            else:
                j = p['n_trial']
                dipolefn.dpl_convert_and_save(ddata, i, j)

    else:
        i = p['n_sim']
        if p['n_trial'] == -1:
            for j in range(N_trials):
                dipolefn.dpl_convert_and_save(ddata, i, j)
        else:
            j = p['n_trial']
            dipolefn.dpl_convert_and_save(ddata, i, j)

    # # take the ith sim, jth trial, do some stuff to it, resave it
    # # only uses first expmt_group
    # expmt_group = ddata.expmt_groups[0]

    # # need n_trials
    # p_exp = paramrw.ExpParams(ddata.fparam)
    # if not p_exp.N_trials:
    #     N_trials = 1
    # else:
    #     N_trials = p_exp.N_trials

    # # absolute number
    # n = i*N_trials + j

    # # grab the correct files
    # f_dpl = ddata.file_match(expmt_group, 'rawdpl')[n]
    # f_param = ddata.file_match(expmt_group, 'param')[n]

    # # print ddata.sim_prefix, ddata.dsim
    # f_name_short = '%s-%03d-T%02d-dpltest.txt' % (ddata.sim_prefix, i, j)
    # f_name = os.path.join(ddata.dsim, expmt_group, f_name_short)
    # print f_name

    # dpl = dipolefn.Dipole(f_dpl)
    # dpl.baseline_renormalize(f_param)
    # print "baseline renormalized"

    # dpl.convert_fAm_to_nAm()
    # print "converted to nAm"

    # dpl.write(f_name)

def exec_show(ddata, dict_opts):
    dict_opts_default = {
        'run': 0,
        'trial': 0,
        'expmt_group': '',
        'key': 'changed',
        'var_list': [],
    }

    # hack for now to get backward compatibility with this original function
    var_list = dict_opts_default['var_list']

    exclude_list = [
        'sim_prefix',
        'N_trials',
        'Run_Date',
    ]

    args_check(dict_opts_default, dict_opts)
    if dict_opts_default['expmt_group'] not in ddata.expmt_groups:
        # print "Warning: expmt_group %s not found" % dict_opts_default['expmt_group']
        dict_opts_default['expmt_group'] = ddata.expmt_groups[0]

    # output the expmt group used
    print "expmt_group: %s" % dict_opts_default['expmt_group']

    # find the params
    p_exp = paramrw.ExpParams(ddata.fparam)

    if dict_opts_default['key'] == 'changed':
        print "Showing changed ... \n"
        # create a list
        var_list = [val[0] for val in paramrw.changed_vars(ddata.fparam)]

    elif dict_opts_default['key'] in p_exp.keys():
        # create a list with just this element
        var_list = [dict_opts_default['key']]

    else:
        key_part = dict_opts_default['key']
        var_list = [key for key in p_exp.keys() if key_part in key]

    if not var_list:
        print "Keys were not found by exec_show()"
        return 0

    # files
    fprefix = ddata.trial_prefix_str % (dict_opts_default['run'], dict_opts_default['trial'])
    fparam = ddata.create_filename(dict_opts_default['expmt_group'], 'param', fprefix)

    list_param = ddata.file_match(dict_opts_default['expmt_group'], 'param')

    if fparam in list_param:
        # this version of read returns the gid dict as well ...
        _, p = paramrw.read(fparam)

        # use var_list to print values
        for key in var_list:
            if key not in exclude_list:
                try:
                    print '%s: %s' % (key, p[key])

                except KeyError:
                    print "Value %s not found in file %s!" % (key, fparam)

def exec_show_dpl_max(ddata, opts={}):
    p = {
        'layer': 'L5',
        'n_sim': 0,
        'n_trial': 0,
    }
    args_check(p, opts)

    expmt_group = ddata.expmt_groups[0]

    n = p['n_sim'] + p['n_sim']*p['n_trial']

    fdpl = ddata.file_match(expmt_group, 'rawdpl')[n]
    fparam = ddata.file_match(expmt_group, 'param')[n]

    T = paramrw.find_param(fparam, 'tstop')
    xlim = (50., T)

    dpl = dipolefn.Dipole(fdpl)
    dpl.baseline_renormalize(fparam)
    dpl.convert_fAm_to_nAm()

    # add this data to the dict for the string output mapping
    p['dpl_max'] = dpl.lim(p['layer'], xlim)[1]
    p['units'] = dpl.units

    print "The maximal value for the dipole is %(dpl_max)4.3f %(units)s for sim=%(n_sim)i, trial=%(n_trial)i in layer %(layer)s" % (p)
    # print "The maximal value for the dipole is %4.3f %s for sim=%i, trial=%i" % (dpl_max, dpl.units, n_sim, n_trial)

# calculates the mean dipole over a specified range
def exec_calc_dpl_mean(ddata, opts={}):
    for expmt_group in ddata.expmt_groups:
        list_fdpl = ddata.file_match(expmt_group, 'rawdpl')

        # order of l_dpl is same as list_fdpl
        l_dpl = [dipolefn.Dipole(f) for f in list_fdpl]

        for dpl in l_dpl:
            print dpl.mean_stationary(opts)

# calculates the linear regression, shows values of slope (m) and int (b)
# and plots line to dipole fig (in place)
def exec_calc_dpl_regression(ddata, opts={}):
     for expmt_group in ddata.expmt_groups:
        list_fdpl = ddata.file_match(expmt_group, 'rawdpl')
        list_figdpl = ddata.file_match(expmt_group, 'figdpl')

        # this is to overwrite the fig
        for f, ffig in zip(list_fdpl, list_figdpl):
            dipolefn.plinear_regression(ffig, f)

def exec_pdipole_evoked(ddata, ylim=[]):
    # runtype = 'parallel'
    runtype = 'debug'

    expmt_group = ddata.expmt_groups[0]

    # grab just the first element of the dipole list
    dpl_list = ddata.file_match(expmt_group, 'rawdpl')
    param_list = ddata.file_match(expmt_group, 'param')
    spk_list = ddata.file_match(expmt_group, 'rawspk')

    # fig dir will be that of the original dipole
    dfig = ddata.dfig[expmt_group]['figdpl']

    # first file names
    f_dpl = dpl_list[0]
    f_spk = spk_list[0]
    f_param = param_list[0]

    if runtype == 'parallel':
        pl = Pool()
        for f_dpl, f_spk, f_param in zip(dpl_list, spk_list, param_list):
            pl.apply_async(dipolefn.pdipole_evoked, (dfig, f_dpl, f_spk, f_param, ylim))

        pl.close()
        pl.join()

    elif runtype == 'debug':
        for f_dpl, f_spk, f_param in zip(dpl_list, spk_list, param_list):
            dipolefn.pdipole_evoked(dfig, f_dpl, f_spk, f_param, ylim)

# timer function wrapper returns WALL CLOCK time (more or less)
def timer(fn, args):
    t0 = time()
    x = eval(fn + args)
    t1 = time()

    print "%s took %4.4f s" % (fn, t1-t0)

    return x

def exec_pcompare(ddata, cli_args):
    vars = cli_args.split(" ")

    # find any expmt and just take the first one. (below)
    expmt = [arg.split("=")[1] for arg in vars if arg.startswith("expmt")]
    sim0  = int([arg.split("=")[1] for arg in vars if arg.startswith("sim0")][0])
    sim1  = int([arg.split("=")[1] for arg in vars if arg.startswith("sim1")][0])

    sims = [sim0, sim1]

    labels = ['A. Control E$_g$-I$_s$', 'B. Increased E$_g$-I$_s$']

    if expmt:
        psum.pcompare2(ddata, sims, labels, [expmt[0], expmt[0]])
    else:
        psum.pcompare2(ddata, sims, labels)
        # print "not found"

def exec_pcompare3(ddata, cli_args):
    # the args will be the 3 sim numbers.
    # these will be strings out of the split!
    vars = cli_args.split(' ')
    sim_no = int(vars[0])
    # expmt_last = int(vars[1])

    psum.pcompare3(ddata, sim_no)

# executes the function plotvar in psummary
# At some point, replace 'vars' with a non-standard variable name
def exec_plotvars(cli_args, ddata):
    # split the cli args based on options
    vars = cli_args.split(' --')

    # first part is always the first 2 options (required, no checks)
    vars_to_plot = vars[0].split()

    # grab the experiment handle
    # vars_expmt = [arg.split()[1] for arg in vars if arg.startswith('expmt')]
    vars_opts = [arg.split()[1:] for arg in vars if arg.startswith('opts')]

    # just pass the first of these
    if vars_opts:
        psum.plotvars(ddata, vars_to_plot[0], vars_opts[0])
        # psum.plotvars(ddata, vars_to_plot[0], vars_to_plot[1], vars_opts[0])
    # else:
        # run the plotvar function with the cli args
        # psum.plotvars(ddata, vars_to_plot[0])
        # psum.plotvars(ddata, vars_to_plot[0], vars_to_plot[1])

def exec_pphase(ddata, args):
    args_split = args.split(" ")
    expmt = args_split[0]
    N_sim = int(args_split[1])

    N_bins = 20

    psum.pphase(ddata, expmt, N_sim, N_bins)

# do_phist
def exec_phist(ddata, args):
    # somehow create these plots
    args_split = args.split(" ")
    N_sim = args_split[0]
    N_bins = int(args_split[1])
    psum.pphase_hist(ddata, N_sim, N_bins)

# find the spectral max over an interval, for a particular sim
def exec_specmax(ddata, opts):
    p = {
        'expmt_group': '',
        'n_sim': 0,
        'n_trial': 0,
        't_interval': None,
        'f_interval': None,
        'f_sort': None,
        # 't_interval': [0., -1],
        # 'f_interval': [0., -1],
    }

    args_check(p, opts)

    p_exp = paramrw.ExpParams(ddata.fparam)
    # trial_prefix = p_exp.trial_prefix_str % (p['n_sim'], p['n_trial'])

    if not p['expmt_group']:
        p['expmt_group'] = ddata.expmt_groups[0]

    # Get the associated dipole and spec file
    fspec = ddata.return_specific_filename(p['expmt_group'], 'rawspec', p['n_sim'], p['n_trial'])

    # Load the spec data
    spec = specfn.Spec(fspec)

    # get max data
    data_max = spec.max('agg', p['t_interval'], p['f_interval'], p['f_sort'])

    if data_max:
        print "Max power of %4.2e at f of %4.2f Hz at %4.3f ms" % (data_max['pwr'], data_max['f_at_max'], data_max['t_at_max'])

    # # data_max = specfn.specmax(fspec, p)
    # data = specfn.read(fspec)
    # print data.keys()

    # # grab the min and max f
    # f_min, f_max = p['f_interval']

    # # set f_max
    # if f_max < 0:
    #     f_max = data['freq'][-1]

    # # create an f_mask for the bounds of f, inclusive
    # f_mask = (data['freq']>=f_min) & (data['freq']<=f_max)

    # # do the same for t
    # t_min, t_max = p['t_interval']
    # if t_max < 0:
    #     t_max = data['time'][-1]

    # t_mask = (data['time']>=t_min) & (data['time']<=t_max)

    # # use the masks truncate these appropriately
    # TFR_key = 'TFR'

    # if p['layer'] in ('L2', 'L5'):
    #     TFR_key += '_%s' % p['layer']

    # TFR_fcut = data[TFR_key][f_mask, :]
    # # TFR_fcut = data['TFR'][f_mask, :]
    # TFR_tfcut = TFR_fcut[:, t_mask]

    # f_fcut = data['freq'][f_mask]
    # t_tcut = data['time'][t_mask]

    # # find the max power over this new range
    # # the max_mask is for the entire TFR
    # pwr_max = TFR_tfcut.max()
    # max_mask = (TFR_tfcut==pwr_max)

    # # find the t and f at max
    # # these are slightly crude and do not allow for the possibility of multiple maxes (rare?)
    # t_at_max = t_tcut[max_mask.sum(axis=0)==1]
    # f_at_max = f_fcut[max_mask.sum(axis=1)==1]

    # # friendly printout
    # print "Max power of %4.2e at f of %4.2f Hz at %4.3f ms" % (pwr_max, f_at_max, t_at_max)

    # pd_at_max = 1000./f_at_max
    # t_start = t_at_max - pd_at_max/2.
    # t_end = t_at_max + pd_at_max/2.

    # print "Symmetric interval at %4.2f Hz (T=%4.3f ms) about %4.3f ms is (%4.3f, %4.3f)" % (f_at_max, pd_at_max, t_at_max, t_start, t_end)

    # # output structure
    # data_max = {
    #     'pwr': pwr_max,
    #     't': t_at_max,
    #     'f': f_at_max,
    # }

def exec_specmax_dpl_match(ddata, opts):
    p = {
        'expmt_group': '',
        'n_sim': 0,
        'trials': [0, -1],
        't_interval': None,
        'f_interval': None,
        'f_sort': None,
    }

    args_check(p, opts)

    # set expmt group
    if not p['expmt_group']:
        p['expmt_group'] = ddata.expmt_groups[0]

    # set directory to save fig in and check that it exists
    dir_fig = os.path.join(ddata.dsim, p['expmt_group'], 'figint')
    fio.dir_create(dir_fig)

    # if p['trials'][1] is -1, assume all trials are wanted
    # 1 is subtracted from N_trials to be consistent with manual entry of trial range
    if p['trials'][1] == -1:
        p_exp = paramrw.ExpParams(ddata.fparam)
        p['trials'][1] = p_exp.N_trials - 1

    # Get spec, dpl, and param files
    # Sorry for lack of readability
    spec_list = [ddata.return_specific_filename(p['expmt_group'], 'rawspec', p['n_sim'], i) for i in range(p['trials'][0], p['trials'][1]+1)]
    dpl_list = [ddata.return_specific_filename(p['expmt_group'], 'rawdpl', p['n_sim'], i) for i in range(p['trials'][0], p['trials'][1]+1)]
    param_list = [ddata.return_specific_filename(p['expmt_group'], 'param', p['n_sim'], i) for i in range(p['trials'][0], p['trials'][1]+1)]

    # Get max spectral data
    data_max_list = []

    for fspec in spec_list:
        spec = specfn.Spec(fspec)
        data_max_list.append(spec.max('agg', p['t_interval'], p['f_interval'], p['f_sort']))

    # create fig name
    if p['f_sort']:
        fname_short = "sim-%03i-T%03i-T%03d-sort-%i-%i" %(p['n_sim'], p['trials'][0], p['trials'][1], p['f_sort'][0], p['f_sort'][1])

    else:
        fname_short = "sim-%03i-T%03i-T%03i" %(p['n_sim'], p['trials'][0], p['trials'][1])

    fname = os.path.join(dir_fig, fname_short)

    # plot time-series over proper intervals
    dipolefn.plot_specmax_interval(fname, dpl_list, param_list, data_max_list)

def exec_specmax_dpl_tmpl(ddata, opts):
    p = {
        'expmt_group': '',
        'n_sim': 0,
        'trials': [0, -1],
        't_interval': None,
        'f_interval': None,
        'f_sort': None,
    }

    args_check(p, opts)

    # set expmt group
    if not p['expmt_group']:
        p['expmt_group'] = ddata.expmt_groups[0]

    # set directory to save template in and check that it exists
    dir_out = os.path.join(ddata.dsim, p['expmt_group'], 'tmpldpl')
    fio.dir_create(dir_out)

    # if p['trials'][1] is -1, assume all trials are wanted
    # 1 is subtracted from N_trials to be consistent with manual entry of trial range
    if p['trials'][1] == -1:
        p_exp = paramrw.ExpParams(ddata.fparam)
        p['trials'][1] = p_exp.N_trials - 1

    # Get spec, dpl, and param files
    # Sorry for lack of readability
    spec_list = [ddata.return_specific_filename(p['expmt_group'], 'rawspec', p['n_sim'], i) for i in range(p['trials'][0], p['trials'][1]+1)]
    dpl_list = [ddata.return_specific_filename(p['expmt_group'], 'rawdpl', p['n_sim'], i) for i in range(p['trials'][0], p['trials'][1]+1)]
    param_list = [ddata.return_specific_filename(p['expmt_group'], 'param', p['n_sim'], i) for i in range(p['trials'][0], p['trials'][1]+1)]

    # Get max spectral data
    data_max_list = []

    for fspec in spec_list:
        spec = specfn.Spec(fspec)
        data_max_list.append(spec.max('agg', p['t_interval'], p['f_interval'], p['f_sort']))

    # Get time intervals of max spectral pwr
    t_interval_list = [dmax['t_int'] for dmax in data_max_list if dmax is not None]

    # truncate dpl_list to include only sorted trials
    # kind of crazy that this works. Just sayin'...
    dpl_list = [fdpl for fdpl, dmax in zip(dpl_list, data_max_list) if dmax is not None]

    # create file name
    if p['f_sort']:
        fname_short = "sim-%03i-T%03i-T%03d-sort-%i-%i-tmpldpl.txt" %(p['n_sim'], p['trials'][0], p['trials'][1], p['f_sort'][0], p['f_sort'][1])

    else:
        fname_short = "sim-%03i-T%03i-T%03i-tmpldpl.txt" %(p['n_sim'], p['trials'][0], p['trials'][1])

    fname = os.path.join(dir_out, fname_short)

    # Create dpl template
    dipolefn.create_template(fname, dpl_list, param_list, t_interval_list)

def exec_plot_dpl_tmpl(ddata, opts):
    p = {
        'expmt_group': '',
    }

    args_check(p, opts)

    # set expmt group
    if not p['expmt_group']:
        p['expmt_group'] = ddata.expmt_groups[0]

    # set directory to save template in and check that it exists
    dir_out = os.path.join(ddata.dsim, p['expmt_group'], 'figtmpldpl')
    fio.dir_create(dir_out)

    # get template dpl data
    dpl_list = fio.file_match(os.path.join(ddata.dsim, p['expmt_group']), '-tmpldpl.txt')

    # create file name list
    # prefix_list = [fdpl.split('/')[-1].split('-tmpldpl')[0] for fdpl in dpl_list]
    # fname_list = [os.path.join(dir_out, prefix+'-tmpldpl.png') for prefix in prefix_list]

    plot_dict = {
        'xlim': None,
        'ylim': None,
    }

    for fdpl in dpl_list:
        print fdpl
        dipolefn.pdipole(fdpl, dir_out, plot_dict)

# search for the min in a dipole over specified interval
def exec_dipolemin(ddata, expmt_group, n_sim, n_trial, t_interval):
    p_exp = paramrw.ExpParams(ddata.fparam)
    trial_prefix = p_exp.trial_prefix_str % (n_sim, n_trial)

    # list of all the dipoles
    dpl_list = ddata.file_match(expmt_group, 'rawdpl')

    # load the associated dipole file
    # find the specific file
    # assume just the first file
    fdpl = [file for file in dpl_list if trial_prefix in file][0]

    data = np.loadtxt(open(fdpl, 'r'))
    t_vec = data[:, 0]
    data_dpl = data[:, 1]

    data_dpl_range = data_dpl[(t_vec >= t_interval[0]) & (t_vec <= t_interval[1])]
    dpl_min_range = data_dpl_range.min()
    t_min_range = t_vec[data_dpl == dpl_min_range]

    print "Minimum value over t range %s was %4.4f at %4.4f." % (str(t_interval), dpl_min_range, t_min_range)

# averages raw dipole or raw spec over all trials
def exec_avgtrials(ddata, datatype):
    # create the relevant key for the data
    datakey = 'raw' + datatype
    datakey_avg = 'avg' + datatype

    # assumes N_Trials are the same in both
    p_exp = paramrw.ExpParams(ddata.fparam)
    sim_prefix = p_exp.sim_prefix
    N_trials = p_exp.N_trials

    # fix for N_trials=0
    if not N_trials:
        N_trials = 1

    # prefix strings
    exp_prefix_str = p_exp.exp_prefix_str
    trial_prefix_str = p_exp.trial_prefix_str

    # Averaging must be done per expmt
    for expmt_group in ddata.expmt_groups:
        ddatatype = ddata.dfig[expmt_group][datakey]
        dparam = ddata.dfig[expmt_group]['param']

        param_list = ddata.file_match(expmt_group, 'param')
        rawdata_list = ddata.file_match(expmt_group, datakey)

        # if nothing in the raw data list, then generate it for spec
        if datakey == 'rawspec':
            if not len(rawdata_list):
                # generate the data!
                exec_spec_regenerate(ddata)
                rawdata_list = ddata.file_match(expmt_group, datakey)

        # simple length check, but will proceed bluntly anyway.
        # this will result in truncated lists, per zip function
        if len(param_list) != len(rawdata_list):
            print "warning, some weirdness detected in list length in exec_avgtrials. Check yo' lengths!"

        # number of unique simulations, per trial
        # this had better be equivalent as an integer or a float!
        N_unique = len(param_list) / N_trials

        # go through the unique simulations
        for i in range(N_unique):
            # fills in the correct int for the experimental prefix string formatter 'exp_prefix_str'
            prefix_unique = exp_prefix_str % i
            fprefix_long = os.path.join(ddatatype, prefix_unique)
            fprefix_long_param = os.path.join(dparam, prefix_unique)

            # create the sublist of just these trials
            unique_list = [rawdatafile for rawdatafile in rawdata_list if rawdatafile.startswith(fprefix_long)]
            unique_param_list = [pfile for pfile in param_list if pfile.startswith(fprefix_long_param)]

            # one filename per unique
            # length of the unique list is the number of trials for this sim, should match N_trials
            fname_unique = ddata.create_filename(expmt_group, datakey_avg, prefix_unique)

            # Average data for each trial
            # average dipole data
            if datakey == 'rawdpl':
                for f_dpl, f_param in zip(unique_list, unique_param_list):
                    dpl = dipolefn.Dipole(f_dpl)
                    # dpl = dipolefn.Dipole(f_dpl, f_param)

                    # ah, this is required becaused the dpl *file* still contains the raw, un-normalized data
                    dpl.baseline_renormalize(f_param)

                    # initialize and use x_dpl
                    if f_dpl is unique_list[0]:
                        # assume time vec stays the same throughout
                        t_vec = dpl.t
                        x_dpl_agg = dpl.dpl['agg']
                        x_dpl_L2 = dpl.dpl['L2']
                        x_dpl_L5 = dpl.dpl['L5']

                    else:
                        x_dpl_agg += dpl.dpl['agg']
                        x_dpl_L2 += dpl.dpl['L2']
                        x_dpl_L5 += dpl.dpl['L5']

                # poor man's mean
                x_dpl_agg /= len(unique_list)
                x_dpl_L2 /= len(unique_list)
                x_dpl_L5 /= len(unique_list)

                # write this data to the file
                # np.savetxt(fname_unique, avg_data, '%5.4f')
                with open(fname_unique, 'w') as f:
                    for t, x_agg, x_L2, x_L5 in zip(t_vec, x_dpl_agg, x_dpl_L2, x_dpl_L5):
                        f.write("%03.3f\t%5.4f\t%5.4f\t%5.4f\n" % (t, x_agg, x_L2, x_L5))

            # average spec data
            elif datakey == 'rawspec':
                specfn.average(fname_unique, unique_list)
                # # load TFR data into np array and avg by summing and dividing by n_trials
                # data_for_avg = np.array([np.load(file)['TFR'] for file in unique_list])
                # spec_avg = data_for_avg.sum(axis=0)/data_for_avg.shape[0]

                # # load time and freq vectors from the first item on the list, assume all same
                # timevec = np.load(unique_list[0])['time']
                # freqvec = np.load(unique_list[0])['freq']

                # # save the aggregate info
                # np.savez_compressed(fname_unique, time=timevec, freq=freqvec, TFR=spec_avg)

# run the spectral analyses on the somatic current time series
def exec_spec_current(ddata, opts_in=None):
    # p_exp = paramrw.ExpParams(ddata.fparam)

    opts = {
        'type': 'dpl_laminar',
        'f_max': 150.,
        'save_data': 1,
        'runtype': 'parallel',
    }

    if opts_in:
        args_check(opts, opts_in)

    specfn.analysis_typespecific(ddata, opts)

# this function can now use specfn.generate_missing_spec(ddata, f_max)
def exec_spec_regenerate(ddata, f_max=None):
    # regenerate and save spec data
    opts = {
        'type': 'dpl_laminar',
        'f_max': 60.,
        'save_data': 1,
        'runtype': 'parallel',
    }

    # set f_max if provided
    if f_max:
        opts['f_max'] = f_max

    specfn.analysis_typespecific(ddata, opts)

# Time-averaged stationarity analysis - averages spec power over time and plots it
def exec_spec_stationary_avg(ddata, dsim, maxpwr):

    # Prompt user for type of analysis (per expmt or whole sim)
    analysis_type = raw_input('Would you like analysis per expmt or for whole sim? (expmt or sim): ')

    fspec_list = fio.file_match(ddata.dsim, '-spec.npz')
    fparam_list = fio.file_match(ddata.dsim, '-param.txt')
    # fspec_list = fio.file_match(ddata.dsim, '-spec.npz')
    # fparam_list = fio.file_match(ddata.dsim, '-param.txt')

    p_exp = paramrw.ExpParams(ddata.fparam)
    key_types = p_exp.get_key_types()

    # If no saved spec results exist, redo spec analysis
    if not fspec_list:
        print "No saved spec data found. Performing spec analysis...",
        exec_spec_regenerate(ddata)
        fspec_list = fio.file_match(ddata.dsim, '-spec.npz')
        # spec_results = exec_spec_regenerate(ddata)

        print "now doing spec freq-pwr analysis"

    # perform time-averaged stationary analysis
    # specpwr_results = [specfn.specpwr_stationary_avg(fspec) for fspec in fspec_list]
    specpwr_results = []

    for fspec in fspec_list:
        spec = specfn.Spec(fspec)
        specpwr_results.append(spec.stationary_avg())

    # plot for whole simulation
    if analysis_type == 'sim':

        file_name = os.path.join(dsim, 'specpwr.eps')
        pspec.pspecpwr(file_name, specpwr_results, fparam_list, key_types)

        # if maxpwr plot indicated
        if maxpwr:
            f_name = os.path.join(dsim, 'maxpwr.png')
            specfn.pmaxpwr(f_name, specpwr_results, fparam_list)

    # plot per expmt
    if analysis_type == 'expmt':
        for expmt_group in ddata.expmt_groups:
            # create name for figure. Figure saved to expmt directory
            file_name = os.path.join(dsim, expmt_group, 'specpwr.png')

            # compile list of freqpwr results and param pathways for expmt
            partial_results_list = [result for result in specpwr_results if result['expmt']==expmt_group]
            partial_fparam_list = [fparam for fparam in fparam_list if expmt_group in fparam]

            # plot results
            pspec.pspecpwr(file_name, partial_results_list, partial_fparam_list, key_types)

            # if maxpwr plot indicated
            if maxpwr:
                f_name = os.path.join(dsim, expmt_group, 'maxpwr.png')
                specfn.pmaxpwr(f_name, partial_results_list, partial_fparam_list)

# Time-averaged Spectral-power analysis/plotting of avg spec data
def exec_spec_avg_stationary_avg(ddata, dsim, opts):

    # Prompt user for type of analysis (per expmt or whole sim)
    analysis_type = raw_input('Would you like analysis per expmt or for whole sim? (expmt or sim): ')

    spec_results_avged = fio.file_match(ddata.dsim, '-specavg.npz')
    fparam_list = fio.file_match(ddata.dsim, '-param.txt')

    p_exp = paramrw.ExpParams(ddata.fparam)
    key_types = p_exp.get_key_types()

    # If no avg spec data found, generate it.
    if not spec_results_avged:
        exec_avgtrials(ddata, 'spec')
        spec_results_avged = fio.file_match(ddata.dsim, '-specavg.npz')

    # perform time-averaged stationarity analysis
    # specpwr_results = [specfn.specpwr_stationary_avg(dspec) for dspec in spec_results_avged]
    specpwr_results = []

    for fspec in spec_results_avged:
        spec = specfn.Spec(fspec)
        specpwr_results.append(spec.stationary_avg())

    # create fparam list to match avg'ed data
    N_trials = p_exp.N_trials
    nums = np.arange(0, len(fparam_list), N_trials)
    fparam_list = [fparam_list[num] for num in nums]

    # plot for whole simulation
    if analysis_type == 'sim':

        # if error bars indicated
        if opts['errorbars']:
            # get raw (non avg'ed) spec data
            raw_spec_data = fio.file_match(ddata.dsim, '-spec.npz')

            # perform freqpwr analysis on raw data
            # raw_specpwr = [specfn.specpwr_stationary_avg(dspec)['p_avg'] for dspec in raw_spec_data]
            raw_specpwr = []

            for fspec in raw_spec_data:
                spec = specfn.Spec(fspec)
                raw_specpwr.append(spec.stationary_avg()['p_avg'])

            # calculate standard error
            error_vec = specfn.calc_stderror(raw_specpwr)

        else:
            error_vec = []

        file_name = os.path.join(dsim, 'specpwr-avg.eps')
        pspec.pspecpwr(file_name, specpwr_results, fparam_list, key_types, error_vec)

        # # if maxpwr plot indicated
        # if maxpwr:
        #     f_name = os.path.join(dsim, 'maxpwr-avg.png')
        #     specfn.pmaxpwr(f_name, freqpwr_results_list, fparam_list)

    # plot per expmt
    if analysis_type == 'expmt':
        for expmt_group in ddata.expmt_groups:
            # if error bars indicated
            if opts['errorbars']:
                # get exmpt group raw spec data
                raw_spec_data = ddata.file_match(expmt_group, 'rawspec')

                # perform stationary analysis on raw data
                raw_specpwr = [specfn.specpwr_stationary_avg(dspec)['p_avg'] for dspec in raw_spec_data]

                # calculate standard error
                error_vec = specfn.calc_stderror(raw_specpwr)

            else:
                error_vec = []

            # create name for figure. Figure saved to expmt directory
            file_name = os.path.join(dsim, expmt_group, 'specpwr-avg.png')

            # compile list of specpwr results and param pathways for expmt
            partial_results_list = [result for result in specpwr_results if result['expmt']==expmt_group]
            partial_fparam_list = [fparam for fparam in fparam_list if expmt_group in fparam]

            # plot results
            pspec.pspecpwr(file_name, partial_results_list, partial_fparam_list, key_types, error_vec)

            # # if maxpwr plot indicated
            # if maxpwr:
            #     f_name = os.path.join(dsim, expmt_group, 'maxpwr-avg.png')
            #     specfn.pmaxpwr(f_name, partial_results_list, partial_fparam_list)

# Averages spec pwr over time and plots it with histogram of alpha feeds per simulation
# Currently not completed
def freqpwr_with_hist(ddata, dsim):
    fspec_list = fio.file_match(ddata.dsim, '-spec.npz')
    spk_list = fio.file_match(ddata.dsim, '-spk.txt')
    fparam_list = fio.file_match(ddata.dsim, '-param.txt')

    p_exp = paramrw.ExpParams(ddata.fparam)
    key_types = p_exp.get_key_types()

    # If no save spec reslts exist, redo spec analysis
    if not fspec_list:
        print "No saved spec data found. Performing spec analysis...",
        exec_spec_regenerate(ddata)
        fspec_list = fio.file_match(ddata.dsim, '-spec.npz')
        # spec_results = exec_spec_regenerate(ddata)

        print "now doing spec freq-pwr analysis"

    # perform freqpwr analysis
    freqpwr_results_list = [specfn.freqpwr_analysis(fspec) for fspec in fspec_list]

    # Plot
    for freqpwr_result, f_spk, fparam in zip(freqpwr_results_list, spk_list, fparam_list):
        gid_dict, p_dict = paramrw.read(fparam)
        file_name = 'freqpwr.png'

        specfn.pfreqpwr_with_hist(file_name, freqpwr_result, f_spk, gid_dict, p_dict, key_types)

# runs plotfn.pall *but* checks to make sure there are spec data
def exec_replot(ddata, opts):
# def regenerate_plots(ddata, xlim=[0, 'tstop']):
    p = {
        'xlim': None,
        'ylim': None,
    }

    args_check(p, opts)

    # recreate p_exp ... don't like this
    # ** should be guaranteed to be identical **
    p_exp = paramrw.ExpParams(ddata.fparam)

    # grab the list of spec results that exists
    # there is a method in SimulationPaths/ddata for this specifically, this should be deprecated
    # fspec_list = fio.file_match(ddata.dsim, '-spec.npz')

    # generate data if no spec exists here
    if not fio.file_match(ddata.dsim, '-spec.npz'):
    # if not fspec_list:
        print "No saved spec data found. Performing spec anaylsis ... "
        exec_spec_regenerate(ddata)
        # spec_results = exec_spec_regenerate(ddata)

    # run our core pall plot
    plotfn.pall(ddata, p_exp, p['xlim'], p['ylim'])

# function to add alpha feed hists
def exec_addalphahist(ddata, opts):
# def exec_addalphahist(ddata, xlim=[0, 'tstop']):
    p = {
        'xlim': None,
        'ylim': None,
    }

    args_check(p, opts)

    p_exp = paramrw.ExpParams(ddata.fparam)

    # generate data if no spec exists here
    if not fio.file_match(ddata.dsim, '-spec.npz'):
        print "No saved spec data found. Performing spec anaylsis ... "
        exec_spec_regenerate(ddata)

    plotfn.pdpl_pspec_with_hist(ddata, p_exp, p['xlim'], p['ylim'])
    # plotfn.pdpl_pspec_with_hist(ddata, p_exp, spec_list, xlim)

def exec_aggregatespec(ddata, labels):
    p_exp = paramrw.ExpParams(ddata.fparam)

    fspec_list = fio.file_match(ddata.dsim, '-spec.npz')

    # generate data if no spec exists here
    if not fspec_list:
        print "No saved spec data found. Performing spec anaylsis ... "
        exec_spec_regenerate(ddata)

    plotfn.aggregate_spec_with_hist(ddata, p_exp, labels)

def exec_pgamma_spec_fig():
    pgamma.spec_fig()

def exec_pgamma_spikephase():
    # the directory here is hardcoded for now, inside the function
    pgamma.spikephase()

def exec_pgamma_peaks():
    pgamma.peaks()

def exec_pgamma_sub_examples():
    pgamma.sub_dist_examples()

def exec_pgamma_sub_example2():
    pgamma.sub_dist_example2()

def exec_phaselock(ddata, opts):
    p = {
        't_interval': [50, 1000],
        'f_max': 60.,
    }
    args_check(p, opts)

    # Do this per expmt group
    for expmt_group in ddata.expmt_groups:
        # Get paths to relevant files
        list_dpl = ddata.file_match(expmt_group, 'rawdpl')
        list_spk = ddata.file_match(expmt_group, 'rawspk')
        list_param = ddata.file_match(expmt_group, 'param')

        avg_spec = ddata.file_match(expmt_group, 'avgspec')[0]

        tmp_array_dpl = []
        tmp_array_spk = []

        for f_dpl, f_spk, f_param in zip(list_dpl, list_spk, list_param):
            # load Dpl data, do stuff, and store it
            print f_dpl
            dpl = dipolefn.Dipole(f_dpl)
            dpl.baseline_renormalize(f_param)
            dpl.convert_fAm_to_nAm()
            t, dp = dpl.truncate_ext(p['t_interval'][0], p['t_interval'][1])
            dp = dp['agg']
            tmp_array_dpl.append(dp)

            # Load extinput data, do stuff, and store it
            try:
                extinput = spikefn.ExtInputs(f_spk, f_param)
            except ValueError:
                print("Error: could not load spike timings from %s" % f_spk)
                return

            extinput.add_delay_times()
            extinput.get_envelope(dpl.t, feed='dist', bins=150)
            inputs, t = extinput.truncate_ext('env', p['t_interval'])
            tmp_array_spk.append(inputs)

        # Convert tmp arrays (actually lists) to numpy nd arrays
        array_dpl = np.array(tmp_array_dpl)
        array_spk = np.array(tmp_array_spk)

        # Phase-locking analysis
        phase = specfn.PhaseLock(array_dpl, array_spk, list_param[0], p['f_max'])

        fname_d = os.path.join(ddata.dsim, expmt_group, 'phaselock-%iHz.npz' %p['f_max'])
        np.savez_compressed(fname_d, t=phase.data['t'], f=phase.data['f'], B=phase.data['B'])

        # Plotting
        # Should be moved elsewhere
        avg_dpl = np.mean(array_dpl, axis=0)
        avg_spk = np.mean(array_spk, axis=0)

        f = ac.FigPhase()

        extent_xy = [t[0], t[-1], phase.data['f'][-1], 0]
        pc1 = f.ax['phase'].imshow(phase.data['B'], extent=extent_xy, aspect='auto', origin='upper',cmap=plt.get_cmap('jet'))
        pc1.set_clim([0, 1])
        cb1 = f.f.colorbar(pc1, ax=f.ax['phase'])
        # cb1.set_clim([0, 1])

        spec = specfn.Spec(avg_spec)
        pc2 = spec.plot_TFR(f.ax['spec'], xlim=[t[0], t[-1]])
        pc2.set_clim([0, 3.8e-7])
        cb2 = f.f.colorbar(pc2, ax=f.ax['spec'])
        # cb2.set_clim([0, 3.6e-7])

        f.ax['dipole'].plot(t, avg_dpl)
        f.ax['dipole'].set_xlim([t[0], t[-1]])
        f.ax['dipole'].set_ylim([-0.0015, 0.0015])

        f.ax['input'].plot(t, avg_spk)
        f.ax['input'].set_xlim([t[0], t[-1]])
        f.ax['input'].set_ylim([-1, 5])
        f.ax['input'].invert_yaxis()

        f.ax['phase'].set_xlabel('Time (ms)')
        f.ax['phase'].set_ylabel('Frequency (Hz)')

        fname = os.path.join(ddata.dsim, expmt_group, 'phaselock-%iHz.png' %p['f_max'])
        print fname

        f.savepng(fname)

# runs the gamma plot for a comparison of the high frequency
def exec_pgamma_hf(ddata, opts):
    p = {
        'xlim_window': [0., -1],
        'n_sim': 0,
        'n_trial': 0,
    }
    args_check(p, opts)
    pgamma.hf(ddata, p['xlim_window'], p['n_sim'], p['n_trial'])

def exec_pgamma_hf_epochs(ddata, opts):
    p = {}
    args_check(p, opts)
    pgamma.hf_epochs(ddata)

# comparison of all layers and aggregate data
def exec_pgamma_laminar(ddata):
    pgamma.laminar(ddata)

# comparison between a PING (ddata0) and a weak PING (ddata1) data set
def exec_pgamma_compare_ping():
    # def exec_pgamma_compare_ping(ddata0, ddata1, opts):
    pgamma.compare_ping()

# plot for gamma stdev on a given ddata
def exec_pgamma_stdev(ddata):
    pgamma.pgamma_stdev(ddata)

def exec_pgamma_prox_dist_new(ddata, opts):
    p = {
        'f_max_welch': 80.,
    }

    args_check(p, opts)
    pgamma.prox_dist_new(ddata, p)

def exec_pgamma_stdev_new(ddata, opts):
    p = {
        'f_max_welch': 80.,
    }

    args_check(p, opts)
    pgamma.pgamma_stdev_new(ddata, p)

# plot for gamma distal phase on a given ddata
def exec_pgamma_distal_phase(ddata, opts):
    pgamma.pgamma_distal_phase(ddata, opts['spec0'], opts['spec1'], opts['spec2'])

# plot data averaged over trials
# dipole and spec should be split up at some point (soon)
# ylim specified here is ONLY for the dipole
def exec_plotaverages(ddata, ylim=[]):
    # runtype = 'parallel'
    runtype = 'debug'

    # this is a qnd check to create the fig dir if it doesn't already exist
    # backward compatibility check for sims that didn't auto-create these dirs
    for expmt_group in ddata.expmt_groups:
        dfig_avgdpl = ddata.dfig[expmt_group]['figavgdpl']
        dfig_avgspec = ddata.dfig[expmt_group]['figavgspec']

        # create them if they did not previously exist
        fio.dir_create(dfig_avgdpl)
        fio.dir_create(dfig_avgspec)

    # presumably globally true information
    p_exp = paramrw.ExpParams(ddata.fparam)
    key_types = p_exp.get_key_types()

    # empty lists to be used/appended
    dpl_list = []
    spec_list = []
    dfig_list = []
    dfig_dpl_list = []
    dfig_spec_list = []
    pdict_list = []

    # by doing all file operations sequentially by expmt_group in this iteration
    # trying to guarantee order better than before
    for expmt_group in ddata.expmt_groups:
        # print expmt_group, ddata.dfig[expmt_group]

        # avgdpl and avgspec data paths
        # fio.file_match() returns lists sorted
        # dpl_list_expmt is so i can iterate through them in a sec
        dpl_list_expmt = fio.file_match(ddata.dfig[expmt_group]['avgdpl'], '-dplavg.txt')
        dpl_list += dpl_list_expmt
        spec_list += fio.file_match(ddata.dfig[expmt_group]['avgspec'], '-specavg.npz')

        # create redundant list of avg dipole dirs and avg spec dirs
        # unique parts are expmt group names
        # create one entry for each in dpl_list
        dfig_list_expmt = [ddata.dfig[expmt_group] for path in dpl_list_expmt]
        dfig_list += dfig_list_expmt
        dfig_dpl_list += [dfig['figavgdpl'] for dfig in dfig_list_expmt]
        dfig_spec_list += [dfig['figavgspec'] for dfig in dfig_list_expmt]

        # param list to match avg data lists
        fparam_list = fio.fparam_match_minimal(ddata.dfig[expmt_group]['param'], p_exp)
        pdict_list += [paramrw.read(f_param)[1] for f_param in fparam_list]

    if dpl_list:
        # new input to dipolefn
        pdipole_dict = {
            'xlim': None,
            'ylim': None,
            # 'xmin': 0.,
            # 'xmax': None,
            # 'ymin': None,
            # 'ymax': None,
        }

        # if there is a length, assume it's 2 (it should be!)
        if len(ylim):
            pdipole_dict['ymin'] = ylim[0]
            pdipole_dict['ymax'] = ylim[1]

        if runtype == 'debug':
            for f_dpl, f_param, dfig_dpl in zip(dpl_list, fparam_list, dfig_dpl_list):
                dipolefn.pdipole(f_dpl, dfig_dpl, pdipole_dict, f_param, key_types)

        elif runtype == 'parallel':
            pl = Pool()
            for f_dpl, f_param, dfig_dpl in zip(dpl_list, fparam_list, dfig_dpl_list):
                pl.apply_async(dipolefn.pdipole, (f_dpl, f_param, dfig_dpl, key_types, pdipole_dict))

            pl.close()
            pl.join()

    else:
        print "No avg dipole data found."
        return 0

    # if avg spec data exists
    if spec_list:
        if runtype == 'debug':
            for f_spec, f_dpl, f_param, dfig_spec, pdict in zip(spec_list, dpl_list, fparam_list, dfig_spec_list, pdict_list):
                pspec.pspec_dpl(f_spec, f_dpl, dfig_spec, pdict, key_types, f_param=f_param)

        elif runtype == 'parallel':
            pl = Pool()
            for f_spec, f_dpl, dfig_spec, pdict in zip(spec_list, dpl_list, dfig_spec_list, pdict_list):
                pl.apply_async(pspec.pspec_dpl, (f_spec, f_dpl, dfig_spec, pdict, key_types))

            pl.close()
            pl.join()

    else:
        print "No averaged spec data found. Run avgtrials()."
        return 0

# rsync command with excludetype input
def exec_sync(droot, server_remote, dsubdir, fshort_exclude='exclude_eps.txt'):
    # make up the local exclude file name
    # f_exclude = os.path.join(droot, 'exclude_eps.txt')
    f_exclude = os.path.join(droot, fshort_exclude)

    # create remote and local directories, they should look similar
    dremote = os.path.join(droot, dsubdir)
    dlocal = os.path.join(droot, 'from_remote')

    # creat the rsync command
    cmd_rsync = "rsync -ruv --exclude-from '%s' -e ssh %s:%s %s" % (f_exclude, server_remote, dremote, dlocal)

    call(cmd_rsync, shell=True)

# save to cppub
def exec_save(dproj, ddate, dsim):
    if fio.dir_check(dsim):
        dsave_root = os.path.join(dproj, 'pub')

        # check to see if this dir exists or not, and create it if not
        fio.dir_create(dsave_root)

        dsave_short = '%s_%s' % (ddate.split('/')[-1], dsim.split('/')[-1])
        dsave = os.path.join(dsave_root, dsave_short)

        # use fileio routine to non-destructively copy dir
        fio.dir_copy(dsim, dsave)

    else:
        print "Not sure I can find that directory."
        return 1

# Creates a pdf from a file list and saves it generically to ddata
def pdf_create(ddata, fprefix, flist):
    file_out = os.path.join(ddata, fprefix + '-summary.pdf')

    # create the beginning of the call to ghostscript
    gscmd = 'gs -dNumRenderingThreads=8 -dBATCH -dNOPAUSE -sDEVICE=pdfwrite -sOutputFile=' + file_out + ' -f '

    for file in flist:
        gscmd += file + ' '

    # print gscmd
    call(gscmd, shell=True)

    return file_out

# PDF Viewer
def view_pdf(pdffile):
    if sys.platform.startswith('darwin'):
        app_pdf = 'open -a skim '
    elif sys.platform.startswith('linux'):
        app_pdf = 'evince '

    call([app_pdf + pdffile + ' &'], shell=True)

# PDF finder ... (this is starting to get unwieldy)
def find_pdfs(ddata, expmt):
    if expmt == 'all':
        # This is recursive
        # find the ONE pdf in the root dir
        # all refers to the aggregated pdf file
        pdf_list = [f for f in iglob(os.path.join(ddata, '*.pdf'))]

    elif expmt == 'each':
        # get each and every one of these (syntax matches below)
        pdf_list = fio.file_match(ddata, '*.pdf')
    else:
        # do this non-recursively (i.e. just for this directory)
        dexpmt = os.path.join(ddata, expmt, '*.pdf')
        pdf_list = [f for f in iglob(dexpmt)]

    # Check the length of pdf_list
    if len(pdf_list) > 3:
        print "There are", len(pdf_list), "files here."
        str_open = raw_input("Do you want to open them all? ")
    else:
        # just set to open the files if fewer than 3
        str_open = 'y'

    # now check for a yes and go
    if str_open == 'y':
        for file in pdf_list:
            view_pdf(file)
    else:
        print "Okay, good call. Here's the consolation prize:\n"
        prettyprint(pdf_list)

# Cross-platform file viewing using eog or xee, cmd is pngv in cli.py
def view_img(dir_data, ext):
    # platform and extension specific opening
    if sys.platform.startswith('darwin'):
        ext_img = '/*' + ext
        app_img = 'open -a xee '

    elif sys.platform.startswith('linux'):
        if ext == 'png':
            app_img = 'eog '
        elif ext == 'eps':
            app_img = 'evince '
        ext_img = '/*' + ext + '&'

    call([app_img + os.path.join(dir_data, 'spec') + ext_img], shell=True)

# Cross platform file viewing over all exmpts
def file_viewer(ddata, dict_opts):
    opts_default = {
        'expmt_group': ddata.expmt_groups[0],
        'type': 'figspec',
        'run': 'all',
    }
    args_check(opts_default, dict_opts)

    # return a list of files by run
    if opts_default['run'] == 'all':
        flist = ddata.file_match(opts_default['expmt_group'], opts_default['type'])

    else:
        flist = ddata.file_match_by_run(**opts_default)

    # sort the list in place
    flist.sort()

    # create a list of files for the argument to the program
    files_arg = ' '.join(flist)

    if sys.platform.startswith('darwin'):
        app_img = 'open -a preview '
        subprocess.call([app_img + files_arg], shell=True)

    elif sys.platform.startswith('linux'):
        app_img = 'eog '
        subprocess.call([app_img + files_arg + '&'], shell=True)

# a really simple image viewer, views images in dimg
def png_viewer_simple(dimg):
    list_fpng = fio.file_match(dimg, '*.png')

    # Create an empty file argument
    files_arg = ''
    for file in list_fpng:
        files_arg += file + ' '

    # uses xee
    if sys.platform.startswith('darwin'):
        app_img = 'open -a xee '
        call([app_img + files_arg], shell=True)

    # uses eye of gnome (eog)
    elif sys.platform.startswith('linux'):
        app_img = 'eog '
        call([app_img + files_arg + '&'], shell=True)
