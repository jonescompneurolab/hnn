# cli.py - routines for the command line interface console s1sh.py
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: return_data_dir())
# last major: (SL: reorganized show and pngv)

from cmd import Cmd
from datetime import datetime
import ast, multiprocessing, os, signal, subprocess, time
import readline as rl
import itertools as it

import clidefs
import fileio as fio
import paramrw
import specfn
import dipolefn
import ppsth
import praw

class Console(Cmd):
    def __init__(self, file_input=""):
        Cmd.__init__(self)
        self.prompt = '\033[93m' + "[s1] " + '\033[0m'
        self.intro  = "\nThis is the SomatoSensory SHell\n"
        self.dproj = fio.return_data_dir()
        self.server_default = self.__check_server()
        self.f_history = '.s1sh_hist_local'
        self.ddate = ''
        self.dlast = []
        self.dlist = []
        self.dsim = []
        self.expmts = []
        self.sim_list = []
        self.param_list = []
        self.var_list = []
        self.N_sims = 0

        # check to see if file_input is legit
        if os.path.isfile(file_input):
            self.file_input = file_input

        else:
            # use a default
            self.file_input = 'param/debug.param'

        # get initial count of avail processors for subprocess/multiprocessing routines
        self.nprocs = multiprocessing.cpu_count()

        # Create the initial datelist
        self.datelist = clidefs.get_subdir_list(self.dproj)

        # create the initial paramfile list
        self.__get_paramfile_list()

        # set the date, grabs a dlist
        self.do_setdate(datetime.now().strftime("%Y-%m-%d"))

    # splits argstring in format of --opt0=val0 --opt1=val1
    def __split_args(self, args):
        # split based on leading --
        args_tmp = args.split(' --')

        # only take the args that start with -- and include a =
        # drop the leading --
        # args_opt = [arg[2:] for arg in args_tmp if arg.startswith('--')]
        args_opt = [arg for arg in args_tmp if '=' in arg]
        arg_list = []
        for arg in args_opt:
            # getting rid of first case, ugh, hack!
            if arg.startswith('--'):
                arg_list.append(arg[2:].split('='))
            else:
                arg_list.append(arg.split('='))

        return arg_list

    def __create_dict_from_args(self, args):
        # split based on leading --
        args_tmp = args.split(' --')

        # only take the args that start with -- and include a =
        # drop the leading --
        # args_opt = [arg[2:] for arg in args_tmp if arg.startswith('--')]
        args_opt = [arg for arg in args_tmp if '=' in arg]
        arg_dict = {}
        for arg in args_opt:
            # getting rid of first case, ugh, hack!
            if arg.startswith('--'):
                args_tmp = arg[2:].split('=')
                arg_dict[args_tmp[0]] = args_tmp[1]

            else:
                args_tmp = arg.split('=')
                arg_dict[args_tmp[0]] = args_tmp[1]

        return arg_dict

    # generalized function for checking and assigning args
    def __check_args(self, dict_opts, list_opts):
        # assumes list_opts comes from __split_args()
        if len(list_opts):
            # iterate through possible key vals in list_opts
            keys_missing = []
            for key, val in list_opts:
                # check to see if the possible keys are in dict_opts
                if key in dict_opts.keys():
                    # assign the key/val pair in place
                    # this operation acts IN PLACE on the supplied dict_opts!!
                    # therefore, no return value necessary
                    dict_opts[key] = ast.literal_eval(val)
                else:
                    keys_missing.append(key)

            # if there are any keys missing
            if keys_missing:
                print "Options were not recognized: "
                fio.prettyprint(keys_missing)

    # checks to see if a default server file is found, if not, ask for one
    def __check_server(self):
        f_server = os.path.join(self.dproj, '.server_default')

        if os.path.isfile(f_server):
            # read the file and set the default server
            lines_f = fio.clean_lines(f_server)

            # there should only be one thing in this file, so assume that's the server name
            return lines_f[0]
        else:
            return ''

    # create a list of parameter files
    def __get_paramfile_list(self):
        dparam_default = os.path.join(os.getcwd(), 'param')
        self.paramfile_list = [f for f in os.listdir(dparam_default) if f.endswith('.param')]

    def do_debug(self, args):
        """Qnd function to test other functions
        """
        self.do_setdate('2013-12-04')
        self.do_load('ftremor-003')
        clidefs.exec_pgamma_spec_fig()
        # self.do_pgamma_sub_example2('')
        # self.do_setdate('pub')
        # self.do_spec_current("--runtype='debug' --f_max=250.")
        # self.do_load('2013-06-28_gamma_weak_L5-000')
        # self.do_pgamma_hf_epochs('')
        # self.do_load('2013-08-12_gamma_sub_50Hz-001')
        # self.do_pgamma_spikephase('')
        # self.do_pgamma_prox_dist_new('')
        # self.do_throwaway('--n_trial=-1')
        # self.do_load('2013-08-07_gamma_sub_50Hz_stdev-000')
        # self.do_pgamma_stdev_new('--f_max_welch=150.')
        # self.do_load('2013-06-28_gamma_sub_f-000')
        # self.do_pgamma_stdev_new('--f_max_welch=150.')
        # self.do_load('2013-07-15_gamma_L5weak_L2weak-000')
        # self.do_pgamma_laminar('')
        # self.do_pgamma_compare_ping('')
        # self.do_show_dpl_max('')
        # self.do_pgamma_peaks('')
        # self.do_welch_max('')
        # self.do_pgamma_sub_examples('')
        # self.do_pgamma_distal_phase('--spec0=5 --spec1=9 --spec2=15')
        # self.do_specmax('--expmt_group="weak" --f_interval=[50., 75] --t_interval=[50., 550.]')
        # self.do_spike_rates('')
        # self.do_save('')
        # self.do_calc_dpl_regression('')
        # self.do_calc_dpl_mean("--t0=100. --tstop=1000. --layer='L2'")
        # self.do_praw('')
        # self.do_pdipole('grid')
        # self.do_pngv('')
        # self.do_show('testing in (0, 0)')
        # self.do_calc_dipole_avg('')
        # self.do_pdipole('evaligned')
        # self.do_avgtrials('dpl')
        # self.do_replot('')
        # self.do_spec_regenerate('--f_max=50.')
        # self.do_addalphahist('--xmin=0 --xmax=500')
        # self.do_avgtrials('dpl')
        # self.do_dipolemin('in (mu, 0, 2) on [400., 410.]')
        # self.epscompress('spk')
        # self.do_psthgrid()

    def do_throwaway(self, args):
        ''' This is a throwaway dipole saving function. Usage:
            [s1] throwaway {--n_sim=12} {--n_trial=3}
        '''
        dict_opts = self.__create_dict_from_args(args)

        # run the throwaway save function!
        clidefs.exec_throwaway(self.ddata, dict_opts)
        # clidefs.exec_throwaway(self.ddata, opts['n_sim'], opts['n_trial'])

    def do_spike_rates(self, args):
        opts = {
            'expmt_group': 'weak',
            'celltype': 'L5_pyramidal',
        }
        l_opts = self.__split_args(args)
        self.__check_args(opts, l_opts)

        clidefs.exec_spike_rates(self.ddata, opts)

    def do_calc_dpl_mean(self, args):
        '''Returns the mean dipole to screen. Usage:
           [s1] calc_dpl_mean
        '''
        opts = {
            't0': 50.,
            'tstop': -1,
            'layer': 'agg',
        }

        l_opts = self.__split_args(args)
        self.__check_args(opts, l_opts)

        # run the function
        clidefs.exec_calc_dpl_mean(self.ddata, opts)

    def do_calc_dpl_regression(self, args):
        clidefs.exec_calc_dpl_regression(self.ddata)

    def do_show_dpl_max(self, args):
        dict_opts = self.__create_dict_from_args(args)
        clidefs.exec_show_dpl_max(self.ddata, dict_opts)

    def do_pgamma_peaks(self, args):
        clidefs.exec_pgamma_peaks()

    def do_pgamma_sub_examples(self, args):
        clidefs.exec_pgamma_sub_examples()

    def do_pgamma_sub_example2(self, args):
        clidefs.exec_pgamma_sub_example2()

    def do_pgamma_hf(self, args):
        dict_opts = self.__create_dict_from_args(args)
        clidefs.exec_pgamma_hf(self.ddata, dict_opts)

    def do_pgamma_hf_epochs(self, args):
        dict_opts = self.__create_dict_from_args(args)
        clidefs.exec_pgamma_hf_epochs(self.ddata, dict_opts)

    def do_pgamma_distal_phase(self, args):
        '''Generates gamma fig for distal phase. Requires spec data for layers to exist. Usage:
           [s1] spec_current
           [s1] pgamma_distal_phase {--spec0=0 --spec1=1, --spec2=2}
        '''

        opts = {
            'spec0': 0,
            'spec1': 1,
            'spec2': 1,
        }

        l_opts = self.__split_args(args)
        self.__check_args(opts, l_opts)

        clidefs.exec_pgamma_distal_phase(self.ddata, opts)

    def do_pgamma_stdev(self, args):
        '''Generates gamma fig for standard deviation. Requires spec data for layers to exist. Usage:
           [s1] spec_current
           [s1] pgamma_stdev
        '''
        clidefs.exec_pgamma_stdev(self.ddata)

    def do_pgamma_stdev_new(self, args):
        '''Generates gamma fig for standard deviation. Requires spec data for layers to exist. Usage:
           [s1] spec_current
           [s1] pgamma_stdev_new
        '''
        dict_opts = self.__create_dict_from_args(args)
        clidefs.exec_pgamma_stdev_new(self.ddata, dict_opts)

    def do_pgamma_prox_dist_new(self, args):
        dict_opts = self.__create_dict_from_args(args)
        clidefs.exec_pgamma_prox_dist_new(self.ddata, dict_opts)

    def do_pgamma_laminar(self, args):
        '''Generates a comparison figure of aggregate, L2 and L5 data. Taken from 1 data set. Usage:
           [s1] pgamma_laminar
        '''
        clidefs.exec_pgamma_laminar(self.ddata)

    def do_pgamma_compare_ping(self, args):
        '''Generates gamma fig for comparison of PING and weak PING. Will need 2 data sets! Usage:
            [s1] pgamma_compare_ping
        '''
        clidefs.exec_pgamma_compare_ping()

    def do_pgamma_spikephase(self, args):
        clidefs.exec_pgamma_spikephase()

    def do_spec_current(self, args):
        # parse list of opts
        dict_opts = self.__create_dict_from_args(args)

        # actually run the analysis
        self.spec_current_tmp = clidefs.exec_spec_current(self.ddata, dict_opts)

    def do_praw(self, args):
        '''praw is a fully automated function to replace the dipole plots with aggregate dipole/spec/spikes plots. Usage:
           [s1] praw
        '''
        praw.praw(self.ddata)

    # update the dlist
    def __update_dlist(self):
        if os.path.exists(self.ddate):
            self.dlist = [d for d in os.listdir(self.ddate) if os.path.isdir(os.path.join(self.ddate, d))]

    def do_setdate(self, args):
        """Sets the date string to the specified date
        """
        if args:
            if args == 'today':
                dcheck = os.path.join(self.dproj, datetime.now().strftime("%Y-%m-%d"))
            else:
                dcheck = os.path.join(self.dproj, args)

            if os.path.exists(dcheck):
                self.ddate = dcheck

            else:
                self.ddate = os.path.join(self.dproj, 'pub')

        self.__update_dlist()

        print "Date set to", self.ddate

    def complete_setdate(self, text, line, j0, J):
        """complete function for setdate
        """
        if text:
            print text
            x = [item for item in self.datelist if item.startswith(text)]
            if x:
                return x
        else:
            return self.datelist

    def do_load(self, args):
        """Load parameter file and regens all vars
           Date needs to be set correctly for this to work. See 'help setdate'
           Usage example:
           [s1sh] setdate 2013-01-01
           [s1sh] load mucomplex-000

           Running without arguments will load the last modified directory found in the date dir:
           [s1] load
        """
        if not args:
            # attempt to load the most recent in the dproj/ddate
            # find the most recent directory in this folder
            list_d = []

            for dsim_short in os.listdir(self.ddate):
                # check to see if dsim_tmp is actually a dir
                dsim_tmp = os.path.join(self.ddate, dsim_short)

                # append to list along with its modified time (mtime)
                if os.path.isdir(dsim_tmp):
                    list_d.append((dsim_tmp, time.ctime(os.path.getmtime(dsim_tmp))))

            # sort by mtime
            list_d.sort(key=lambda x: x[1])

            # grab the directory name of the most recent dir
            dcheck = list_d[-1][0]

        else:
            # dir_check is the attempt at creating this directory
            dcheck = os.path.join(self.dproj, self.ddate, args)

        # check existence of the path
        if os.path.exists(dcheck):
            # create blank ddata structure from SimPaths
            self.ddata = fio.SimulationPaths()

            # set dsim after using ddata's readsim method
            self.dsim = self.ddata.read_sim(self.dproj, dcheck)
            self.p_exp = paramrw.ExpParams(self.ddata.fparam)
            print self.ddata.fparam
            self.var_list = paramrw.changed_vars(self.ddata.fparam)

        else:
            print dcheck
            print "Could not find that dir, maybe check your date?"

    def complete_load(self, text, line, j0, J):
        """complete function for load
        """
        if text:
            return [item for item in self.dlist if item.startswith(text)]

        else:
            return self.dlist

    def do_sync(self, args):
        """Sync with specified remote server. If 'exclude' is unspecified, by default will use the exclude_eps.txt file in the data dir. If exclude is specified, it will look in the root data dir. Usage examples:
           [s1] sync 2013-03-25
           [s1] sync 2013-03-25 --exclude=somefile.txt
        """
        try:
            fshort_exclude = ''
            list_args = args.split('--')

            # expect first arg to be the dsubdir
            dsubdir = list_args.pop(0)

            for arg in list_args:
                if arg:
                    opt, val = arg.split('=')

                    if opt == 'exclude':
                        fshort_exclude = val

            if not self.server_default:
                server_remote = raw_input("Server address: ")
            else:
                server_remote = self.server_default
                print "Attempting to use default server ..."

            # run the command
            if fshort_exclude:
                clidefs.exec_sync(self.dproj, server_remote, dsubdir, fshort_exclude)
            else:
                clidefs.exec_sync(self.dproj, server_remote, dsubdir)

            # path
            newdir = os.path.join('from_remote', dsubdir)
            self.do_setdate(newdir)

        except:
            print "Something went wrong here."

    def do_giddict(self, args):
        pass

    def do_welch_max(self, args):
        dict_opts = self.__create_dict_from_args(args)
        clidefs.exec_welch_max(self.ddata, dict_opts)

    def do_specmax(self, args):
        """Find the max spectral power, report value and time.
           Usage: specmax {--expmt_group=0 --simrun=0 --trial=0 --t_interval=[0, 1000] --f_interval=[0, 100.]}
        """
        dict_opts = self.__create_dict_from_args(args)
        clidefs.exec_specmax(self.ddata, dict_opts)

    def do_specmax_dpl_match(self, args):
        """Plots dpl around max spectral power over specified time and frequency intervals
        usage: specmax_dpl_match --t_interval=[0, 1000] --f_interval=[0, 100] --f_sorted=[0, 100]
        """
        dict_opts = self.__create_dict_from_args(args)
        clidefs.exec_specmax_dpl_match(self.ddata, dict_opts)

    def do_specmax_dpl_tmpl(self, args):
        """Isolates dpl waveforms producing specified spectral frequencies
           across trails and averages them to produce a stereotypical waveform
           Usage: specmax_dpl_tmpl --expmt_group --n_sim --trials --t_interval
                  --f_interval --f_sort
        """
        dict_opts = self.__create_dict_from_args(args)
        clidefs.exec_specmax_dpl_tmpl(self.ddata, dict_opts)

    def do_plot_dpl_tmpl(self, args):
        """Plots stereotypical waveforms produced by do_specmax_dpl_tmpl
           usage: plot_dpl_tmpl --expmt_group
        """
        dict_opts = self.__create_dict_from_args(args)
        clidefs.exec_plot_dpl_tmpl(self.ddata, dict_opts)

    def do_dipolemin(self, args):
        """Find the minimum of a particular dipole
           Usage: dipolemin in (<expmt>, <simrun>, <trial>) on [interval]
        """
        # look for first keyword
        if args.startswith("in"):
            try:
                # split by 'in' to get the interval
                s = args.split(" on ")

                # values are then in first part of s
                # yeah, this is gross, sorry. just parsing between parens for params
                expmt_group, n_sim_str, n_trial_str = s[0][s[0].find("(")+1:s[0].find(")")].split(", ")
                n_sim = int(n_sim_str)
                n_trial = int(n_trial_str)

                t_interval = ast.literal_eval(s[-1])
                clidefs.exec_dipolemin(self.ddata, expmt_group, n_sim, n_trial, t_interval)

            except ValueError:
                self.do_help('dipolemin')

        else:
            self.do_help('dipolemin')

    def do_file(self, args):
        """Attempts to open a new file of params
        """
        if not args:
            print self.file_input
        elif os.path.isfile(args):
            self.file_input = args
            print "New file is:", self.file_input
        else:
            # try searching specifcally in param dir
            f_tmp = os.path.join('param', args)
            if os.path.isfile(f_tmp):
                self.file_input = f_tmp
            else:
                print "Does not appear to exist"
                return 0

    # tab complete rules for file
    def complete_file(self, text, line, j0, J):
        return [item for item in self.paramfile_list if item.startswith(text)]

    def do_diff(self, args):
        """Runs a diff on various data types
        """
        pass

    def do_testls(self, args):
        # file_list = fio.file_match('../param', '*.param')
        print "dlist is:", self.dlist
        print "datelist is:", self.datelist
        print "expmts is:", self.expmts

    def do_expmts(self, args):
        """Show list of experiments for active directory.
        """
        try:
            clidefs.prettyprint(self.ddata.expmt_groups)
        except AttributeError:
            self.do_help('expmts')
            print "No active directory?"

    def do_vars(self, args):
        """Show changed variables in loaded simulation and their values. vars comes from p_exp. Usage:
           [s1] vars
        """
        print "\nVars changed in this simulation:"

        # iterate through params and print them raw
        for var in self.var_list:
            print "  %s: %s" % (var[0], var[1])

        # also print experimental groups
        print "\nExperimental groups:"
        self.do_expmts('')

        # cheap newline
        print ""

    # this is an old function obsolete for this project
    def do_view(self, args):
        """Views the changes in the .params file. Use like 'load'
           but does not commit variables to workspace
        """
        dcheck = os.path.join(self.dproj, self.ddate, args)

        if os.path.exists(dcheck):
            # get a list of the .params files
            sim_list = fio.gen_sim_list(dcheck)
            expmts = gen_expmts(sim_list[0])
            var_list = changed_vars(sim_list)

            clidefs.prettyprint(sim_list)
            clidefs.prettyprint(expmts)
            for var in var_list:
                print var[0]+":", var[1]

    def complete_view(self, text, line, j0, J):
        """complete function for view
        """
        if text:
            x = [item for item in self.dlist if item.startswith(text)]
            if x:
                return x
            else:
                return 0
        else:
            return self.dlist

    def do_list(self, args):
        """Lists simulations on a given date
           'args' is a date
        """
        if not args:
            dcheck = os.path.join(self.dproj, self.ddate)

        else:
            dcheck = os.path.join(self.dproj, args)

        if os.path.exists(dcheck):
            self.__update_dlist()

            # dir_list = [name for name in os.listdir(dcheck) if os.path.isdir(os.path.join(dcheck, name))]
            clidefs.prettyprint(self.dlist)

        else:
            print "Cannot find directory"
            return 0

    def do_pngoptimize(self, args):
        """Optimizes png figures based on current directory
        """
        fio.pngoptimize(self.simpaths.dsim)

    def do_avgtrials(self, args):
        """Averages raw data over all trials for each simulation.
           Usage:
           [s1] avgtrials <datatype>
           where <datatype> is either dpl or spec
        """
        if not args:
            print "You did not specify whether to avgerage dpl or spec data. Try again."

        else:
            datatype = args
            clidefs.exec_avgtrials(self.ddata, datatype)

    def do_spec_regenerate(self, args):
        """Regenerates spec data and saves it to proper expmt directories. Usage:
           [s1] spec_regenerate {--f_max=80.}
        """

        # use __split_args()
        l_opts = self.__split_args(args)

        # these are the opts for which we are looking
        opts = {
            'f_max': None,
        }

        # parse the opts
        self.__check_args(opts, l_opts)

        # use exec_spec_regenerate to regenerate spec data
        clidefs.exec_spec_regenerate(self.ddata, opts['f_max'])
        # self.spec_results = clidefs.exec_spec_regenerate(self.ddata, opts['f_max'])

    def do_spec_stationary_avg(self, args):
        """Averages spec power over time and plots freq vs power. Fn can act per expmt or over entire simulation. If maxpwr supplied as arg, also plots freq at which max avg pwr occurs v.s input freq
        """
        if args == 'maxpwr':
            clidefs.exec_spec_stationary_avg(self.ddata, self.dsim, maxpwr=1)

        else:
            clidefs.exec_spec_stationary_avg(self.ddata, self.dsim, maxpwr=0)

    def do_spec_avg_stationary_avg(self, args):
        """Performs time-averaged stationarity analysis on avg'ed spec data.
           Sorry for the terrible name...
        """
        # parse args
        l_opts = self.__split_args(args)

        # "default" opts
        opts = {
            'errorbars': None
        }

        # parse opts
        self.__check_args(opts, l_opts)

        clidefs.exec_spec_avg_stationary_avg(self.ddata, self.dsim, opts)

    def do_freqpwrwithhist(self, args):
        clidefs.freqpwr_with_hist(self.ddata, self.dsim)

    def do_calc_dipole_avg(self, args):
        """Calculates average dipole using dipolefn.calc_avgdpl_stimevoked:
           Usage: [s1] calc_dipole_avg
        """
        dipolefn.calc_avgdpl_stimevoked(self.ddata)

    def do_pdipole(self, args):
        """Regenerates plots in given directory. Usage:
           To run on current working directory and regenerate each individual plot: 'pdipole'
           To run aggregates for all simulations (across all trials/conditions) in a directory: 'pdipole exp'
           To run aggregates with lines marking evoked times, run: 'pdipole evoked'
        """
        # temporary arg split
        arg_tmp = args.split(' ')

        # list of acceptable runtypes
        runtype_list = [
            'exp',
            'exp2',
            'evoked',
            'evaligned',
            'avg',
            'grid',
        ]

        # minimal checks in this function
        # assume that no ylim argument was specified
        if len(arg_tmp) == 1:
            runtype = arg_tmp[0]
            ylim = []

        else:
            # set the runtype to the first
            if arg_tmp[0] in runtype_list:
                runtype = arg_tmp[0]

            # get the list of optional args
            arg_list = self.__split_args(args)

            # default values for various params
            # i_ctrl = 0
            for opt, val in arg_list:
                # currently not being used
                if opt == 'i_ctrl':
                    i_ctrl = int(val)

            # assume the first arg is correct, split on that
            # arg_ylim_tmp = args.split(runtype)

            # if len(arg_ylim_tmp) == 2:
            #     ylim_read = ast.literal_eval(arg_ylim_tmp[-1].strip())
            #     ylim = ylim_read

            # else:
            #     ylim = []

        if runtype == 'exp':
            # run the avg dipole per experiment (across all trials/simulations)
            # using simpaths (ddata)
            dipolefn.pdipole_exp(self.ddata, ylim)

        elif runtype == 'exp2':
            dipolefn.pdipole_exp2(self.ddata)
            # dipolefn.pdipole_exp2(self.ddata, i_ctrl)

        elif runtype == 'evoked':
            # add the evoked lines to the pdipole individual simulations
            clidefs.exec_pdipole_evoked(self.ddata, ylim)

        elif runtype == 'evaligned':
            dipolefn.pdipole_evoked_aligned(self.ddata)

        elif runtype == 'avg':
            # plot average over all TRIALS of a param regime
            # requires that avg dipole data exist
            clidefs.exec_plotaverages(self.ddata, ylim)

        elif runtype == 'grid':
            dipolefn.pdipole_grid(self.ddata)

    def do_replot(self, args):
        """Regenerates plots in given directory. Usage:
           Usage: replot --xlim=[0, 1000] --ylim=[0, 100]
           xlim is a time interval
           ylim is a frequency interval
        """
        # preallocate variables so they always exist
        # xmin = 0.
        # xmax = 'tstop'

        # # Parse args if they exist
        # if args:
        #     arg_list = [arg for arg in args.split('--') if arg is not '']

        #     # Assign value to above variables if the value exists as input
        #     for arg in arg_list:
        #         if arg.startswith('xmin'):
        #             xmin = float(arg.split('=')[-1])

        #         elif arg.startswith('xmax'):
        #             xmax = float(arg.split('=')[-1])

        #         else:
        #             print "Did not recognize argument %s. Not doing anything with it" % arg

        #     # Check to ensure xmin less than xmax
        #     if xmin and xmax:
        #         if xmin > xmax:
        #             print "xmin greater than xmax. Defaulting to sim parameters"
        #             xmin = 0.
        #             xmax = 'tstop'

        dict_opts = self.__create_dict_from_args(args)

        # check for spec data, create it if didn't exist, and then run the plots
        clidefs.exec_replot(self.ddata, dict_opts)
        # clidefs.regenerate_plots(self.ddata, [xmin, xmax])

    def do_addalphahist(self, args):
        """Adds histogram of alpha feed input times to dpl and spec plots. Usage:
           [s1] addalphahist {--xlim=[0, 1000] --ylim=[0, 100]}
           xlim is a time interval
           ylim is a frequency interval
        """
        # # preallocate variables so they always exist
        # xmin = 0.
        # xmax = 'tstop'

        # # Parse args if they exist
        # if args:
        #     arg_list = [arg for arg in args.split('--') if arg is not '']

        #     # Assign value to above variables if the value exists as input
        #     for arg in arg_list:
        #         if arg.startswith('xmin'):
        #             xmin = float(arg.split('=')[-1])

        #         elif arg.startswith('xmax'):
        #             xmax = float(arg.split('=')[-1])

        #         else:
        #             print "Did not recognize argument %s. Not doing anything with it" %arg

        #     # Check to ensure xmin less than xmax
        #     if xmin and xmax:
        #         if xmin > xmax:
        #             print "xmin greater than xmax. Defaulting to sim parameters"
        #             xmin = 0.
        #             xmax = 'tstop'

        dict_opts = self.__create_dict_from_args(args)
        clidefs.exec_addalphahist(self.ddata, dict_opts)
        # clidefs.exec_addalphahist(self.ddata, [xmin, xmax])

    def do_aggregatespec(self, args):
        """Creates aggregates all spec data with histograms into one massive fig.
           Must supply column label and row label as --row_label:param --column_label:param"
           row_label should be param that changes only over experiments
           column_label should be a param that changes trial to trial
        """
        arg_list = [arg for arg in args.split('--') if arg is not '']

        # Parse args
        for arg in arg_list:
            if arg.startswith('row'):
                row_label = arg.split(':')[-1]

                # See if a list is being passed in
                if row_label.startswith('['):
                    row_label = arg.split('[')[-1].split(']')[0].split(', ')

                else:
                    row_label = arg.split(':')[-1].split(' ')[0]

            elif arg.startswith('column'):
                column_label = arg.split(':')[-1].split(' ')[0]

            else:
                print "Did not recongnize argument. Going to break now."

        clidefs.exec_aggregatespec(self.ddata, [row_label, column_label])

    def do_plotaverages(self, args):
        """Creates plots of averaged dipole or spec data. Automatically checks if data exists. Usage:
           'plotaverages'
        """

        clidefs.exec_plotaverages(self.ddata)

    def do_phaselock(self, args):
        """Calculates phaselock values between dipole and inputs
        """
        args_dict = self.__create_dict_from_args(args)
        clidefs.exec_phaselock(self.ddata, args_dict)

    def do_epscompress(self, args):
        """Runs the eps compress utils on the specified fig type (currently either spk or spec)
        """
        for expmt_group in self.ddata.expmt_groups:
            if args == 'figspk':
                d_eps = self.ddata.dfig[expmt_group]['figspk']
            elif args == 'figspec':
                d_eps = self.ddata.dfig[expmt_group]['figspec']

            try:
                fio.epscompress(d_eps, '.eps')
            except UnboundLocalError:
                print "oy, this is embarrassing."

    def do_psthgrid(self, args):
        """Aggregate plot of psth
        """
        ppsth.ppsth_grid(self.simpaths)

    # save currently fails when no dir is loaded
    def do_save(self, args):
        """Copies the entire current directory over to the cppub directory
        """
        clidefs.exec_save(self.dproj, self.ddate, self.dsim)

    # currently doesn't work with mpi interfacing
    # def do_runsim(self, args):
    #     """Run the simulation code
    #     """
    #     try:
    #         cmd_list = []
    #         cmd_list.append('mpiexec -n %i ./s1run.py %s' % (self.nprocs, self.file_input))

    #         for cmd in cmd_list:
    #             subprocess.call(cmd, shell=True)

    #     except (KeyboardInterrupt):
    #         print "Caught a break"

    def do_hist(self, args):
        """Print a list of commands that have been entered"""
        print self._hist

    def do_pwd(self, args):
        """Displays active dir_data"""
        print self.dsim

    def do_ls(self, args):
        """Displays active param list"""
        clidefs.prettyprint(self.param_list)

    def do_show(self, args):
        dict_opts = self.__create_dict_from_args(args)
        clidefs.exec_show(self.ddata, dict_opts)

    def complete_show(self, text, line, j0, J):
        """Completion function for show
        """
        if text:
            return [expmt for expmt in self.expmts if expmt.startswith(text)]
        else:
            return self.expmts

    def do_showf(self, args):
        """Show frequency information from rate files
        """
        vars = args.split(' in ')
        expmt = vars[0]
        n = int(vars[1])

        if n < self.N_sims:
            drates = os.path.join(self.dsim, expmt, 'rates')
            ratefile_list = fio.file_match(drates, '*.rates')

            with open(ratefile_list[n]) as frates:
                lines = (line.rstrip() for line in frates)
                lines = [line for line in lines if line]

            clidefs.prettyprint(lines)
        else:
            print "In do_showf in cli: out of range?"
            return 0

    def complete_showf(self, text, line, j0, J):
        """Completion function for showf
        """
        if text:
            return [expmt for expmt in self.expmts if expmt.startswith(text)]
        else:
            return self.expmts

    def do_Nsims(self, args):
        """Show number of simulations in each 'experiment'
        """
        print self.N_sims

    def do_pngv(self, args):
        dict_opts = self.__create_dict_from_args(args)
        clidefs.exec_pngv(self.ddata, dict_opts)

    def complete_pngv(self, text, line, j0, J):
        if text:
            return [expmt for expmt in self.expmts if expmt.startswith(text)]
        else:
            return self.expmts

    ## Command definitions to support Cmd object functionality ##
    def do_exit(self, args):
        """Exits from the console
        """
        return -1

    def do_EOF(self, args):
        """Exit on system end of file character
        """
        return self.do_exit(args)

    def do_shell(self, args):
        """Pass command to a system shell when line begins with '!'
        """
        os.system(args)

    def do_help(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of commands for which help is available
           'help <command>' or '? <command>' gives help on <command>
        """
        ## The only reason to define this method is for the help text in the doc string
        Cmd.do_help(self, args)

    ## Override methods in Cmd object ##
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        Cmd.preloop(self)   ## sets up command completion
        self._hist    = self.load_history()
        self._locals  = {}      ## Initialize execution namespace for user
        self._globals = {}

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
        """
        self.write_history()
        Cmd.postloop(self)   ## Clean up command completion
        print "Exiting..."

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modify the input line
            before execution (for example, variable substitution) do it here.
        """
        self._hist += [ line.strip() ]
        return line

    def postcmd(self, stop, line):
        """If you want to stop the console, return something that evaluates to true.
           If you want to do some post command processing, do it here.
        """
        return stop

    def emptyline(self):
        """Do nothing on empty input line"""
        pass

    def default(self, line):
        """Called on an input line when the command prefix is not recognized.
           In that case we execute the line as Python code.
        """
        try:
            exec(line) in self._locals, self._globals
        except Exception, e:
            print e.__class__, ":", e

    # Function to read the history file
    def load_history(self):
        with open(self.f_history) as f_in:
            lines = (line.rstrip() for line in f_in)
            lines = [line for line in lines if line]

        return lines

    def history_remove_dupes(self):
        unique_set = set()
        return [x for x in self._hist if x not in unique_set and not unique_set.add(x)]

    # function to write the history file
    def write_history(self):
        # first we will clean the list of dupes
        unique_history = self.history_remove_dupes()
        with open(self.f_history, 'w') as f_out:
            for line in unique_history[-100:]:
                f_out.write(line+'\n')
