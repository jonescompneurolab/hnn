"""File with functions and classes for running the NEURON """

# Authors: Blake Caldwell <blake_caldwell@brown.edu>
#          Sam Neymotin <samnemo@gmail.com>
#          Shane Lee

import os.path as op
import os
import numpy as np
from threading import Lock
from time import sleep
from copy import deepcopy
from math import ceil, isclose

from PyQt5.QtCore import QThread, pyqtSignal, QObject
from hnn_core import simulate_dipole, Network, MPIBackend
from hnn_core.dipole import average_dipoles
import nlopt
from psutil import wait_procs, process_iter, NoSuchProcess

from .paramrw import usingOngoingInputs, write_gids_param
from .specfn import analysis_simp
from .simdat import updatelsimdat, updatedat, ddat, updateoptdat
from .simdat import weighted_rmse, initial_ddat, calcerr
from .paramrw import write_legacy_paramf, get_output_dir


def get_fname(sim_dir, key, trial=0, ntrial=1):
    """Build the file names using the old HNN scheme

    Parameters
    ----------
    sim_dir : str
        The base data directory where simulation result files are stored
    key : str
        A string describing the type of file (HNN specific)
    trial : int | None
        Trial number for which to generate files (separate files per trial).
        If None is given, then trial number 0 is assumed.
    ntrial : int | None
        The total number of trials that are part of this simulation. If None
        is given, then a total of 1 trial is assumed.

    Returns
    ----------
    fname : str
        A string with the correct filename
    """

    datatypes = {'rawspk': ('spk', '.txt'),
                 'rawdpl': ('rawdpl', '.txt'),
                 'normdpl': ('dpl', '.txt'),
                 'rawcurrent': ('i', '.txt'),
                 'rawspec': ('rawspec', '.npz'),
                 'rawspeccurrent': ('speci', '.npz'),
                 'avgdpl': ('dplavg', '.txt'),
                 'avgspec': ('specavg', '.npz'),
                 'figavgdpl': ('dplavg', '.png'),
                 'figavgspec': ('specavg', '.png'),
                 'figdpl': ('dpl', '.png'),
                 'figspec': ('spec', '.png'),
                 'figspk': ('spk', '.png'),
                 'param': ('param', '.txt'),
                 'vsoma': ('vsoma', '.pkl')}

    if ntrial == 1 or key == 'param':
        # param file currently identical for all trials
        return op.join(sim_dir, datatypes[key][0] + datatypes[key][1])
    else:
        return op.join(sim_dir, datatypes[key][0] + '_' + str(trial) +
                       datatypes[key][1])


class TextSignal (QObject):
    """for passing text"""
    tsig = pyqtSignal(str)


class ParamSignal (QObject):
    """for updating GUI & param file during optimization"""
    psig = pyqtSignal(dict)


class CanvSignal (QObject):
    """for updating main GUI canvas"""
    csig = pyqtSignal(bool, bool)


def _kill_list_of_procs(procs):
    """tries to terminate processes in a list before sending kill signal"""
    # try terminate first
    for p in procs:
        try:
            p.terminate()
        except NoSuchProcess:
            pass
    _, alive = wait_procs(procs, timeout=3)

    # now try kill
    for p in alive:
        p.kill()
    _, alive = wait_procs(procs, timeout=3)

    return alive


def _get_nrniv_procs_running():
    """return a list of nrniv processes running"""
    ls = []
    name = 'nrniv'
    for p in process_iter(attrs=["name", "exe", "cmdline"]):
        if name == p.info['name'] or \
                p.info['exe'] and os.path.basename(p.info['exe']) == name or \
                p.info['cmdline'] and p.info['cmdline'][0] == name:
            ls.append(p)
    return ls


def _kill_and_check_nrniv_procs():
    """handle killing any stale nrniv processess"""
    procs = _get_nrniv_procs_running()
    if len(procs) > 0:
        running = _kill_list_of_procs(procs)
        if len(running) > 0:
            pids = [str(proc.pid) for proc in running]
            print("ERROR: failed to kill nrniv process(es) %s" %
                  ','.join(pids))


def simulate(params, n_procs=None):
    """Start the simulation with hnn_core.simulate

    Parameters
    ----------
    params : dict
        The parameters

    n_procs : int | None
        The number of MPI processes requested by the user. If None, then will
        attempt to detect number of cores (including hyperthreads) and start
        parallel simulation over all of them.
    """

    # create the network from the parameter file. note, NEURON objects haven't
    # been created yet
    net = Network(params)

    # run the simulation with MPIBackend for faster completion time
    with MPIBackend(n_procs=n_procs, mpi_cmd='mpiexec'):
        dpls = simulate_dipole(net, params['N_trials'])

    ntrial = len(dpls)
    # save average dipole from individual trials in a single file
    if ntrial > 1:
        avg_dpl = average_dipoles(dpls)
    elif ntrial == 1:
        avg_dpl = dpls[0]
    else:
        raise RuntimeError("No dipole(s) rerturned from simulation")

    # make sure the directory for saving data has been created
    data_dir = op.join(get_output_dir(), 'data')
    sim_dir = op.join(data_dir, params['sim_prefix'])
    try:
        os.mkdir(sim_dir)
    except FileExistsError:
        pass

    # now write the files
    # TODO: rawdpl in hnn-core

    avg_dpl.write(op.join(sim_dir, 'dpl.txt'))

    # TODO: Can below be removed if spk.txt is new hnn-core format with 3
    # columns (including spike type)?
    write_gids_param(get_fname(sim_dir, 'param'), net.gid_dict)

    # save spikes by trial
    glob = op.join(sim_dir, 'spk_%d.txt')
    net.spikes.write(glob)

    spike_fn = get_fname(sim_dir, 'rawspk')
    # save spikes from the individual trials in a single file
    with open(spike_fn, 'w') as fspkout:
        for trial_idx in range(len(net.spikes.times)):
            for spike_idx in range(len(net.spikes.times[trial_idx])):
                fspkout.write('{:.3f}\t{}\t{}\n'.format(
                              net.spikes.times[trial_idx][spike_idx],
                              int(net.spikes.gids[trial_idx][spike_idx]),
                              net.spikes.types[trial_idx][spike_idx]))

    # save dipole for each trial and perform spectral analysis
    for trial_idx, dpl in enumerate(dpls):
        dipole_fn = get_fname(sim_dir, 'normdpl', trial_idx,
                              params['N_trials'])
        dpl.write(dipole_fn)

        if params['save_spec_data'] or usingOngoingInputs(params):
            spec_opts = {'type': 'dpl_laminar',
                         'f_max': params['f_max_spec'],
                         'save_data': 1,
                         'runtype': 'parallel'}

            # run the spectral analysis
            analysis_simp(spec_opts, params, dpl,
                          get_fname(sim_dir, 'rawspec', trial_idx,
                                    params['N_trials']))

        # TODO: the savefigs functionality is quite complicated and rewriting
        # from scratch in hnn-core is probably a better option that will allow
        # deprecating the large amount of legacy code

        # if params['save_figs']:
        #     savefigs(params) # save output figures

    if params['save_spec_data'] or usingOngoingInputs(params):
        # save average spectrogram from individual trials in a single file

        dspecin = {}
        dout = {}
        lf = []
        for i in range(ntrial):
            lf.append(op.join(sim_dir, 'rawspec_' + str(i) + '.npz'))

        for f in lf:
            dspecin[f] = np.load(f)
        for k in ['t_L5', 'f_L5', 't_L2', 'f_L2', 'time', 'freq']:
            dout[k] = dspecin[lf[0]][k]
        for k in ['TFR', 'TFR_L5', 'TFR_L2']:
            dout[k] = np.mean(np.array([dspecin[f][k] for f in lf]), axis=0)

        with open(op.join(sim_dir, 'rawspec.npz'), 'wb') as spec_fn:
            np.savez_compressed(spec_fn, t_L5=dout['t_L5'], f_L5=dout['f_L5'],
                                t_L2=dout['t_L2'], f_L2=dout['f_L2'],
                                time=dout['time'], freq=dout['freq'],
                                TFR=dout['TFR'], TFR_L5=dout['TFR_L5'],
                                TFR_L2=dout['TFR_L2'])


# based on https://nikolak.com/pyqt-threading-tutorial/
class RunSimThread(QThread):
    def __init__(self, p, d, ntrial, ncore, waitsimwin, params, opt=False,
                 baseparamwin=None, mainwin=None):
        QThread.__init__(self)
        self.p = p
        self.d = d
        self.killed = False
        self.ntrial = ntrial
        self.ncore = ncore
        self.waitsimwin = waitsimwin
        self.params = params
        self.opt = opt
        self.baseparamwin = baseparamwin
        self.mainwin = mainwin
        self.paramfn = os.path.join(get_output_dir(), 'param',
                                    self.params['sim_prefix'] + '.param')

        self.txtComm = TextSignal()
        self.txtComm.tsig.connect(self.waitsimwin.updatetxt)

        self.prmComm = ParamSignal()
        if self.baseparamwin is not None:
            self.prmComm.psig.connect(self.baseparamwin.updatesaveparams)

        self.canvComm = CanvSignal()
        if self.mainwin is not None:
            self.canvComm.csig.connect(self.mainwin.initSimCanvas)

        self.lock = Lock()

    def updatewaitsimwin(self, txt):
        self.txtComm.tsig.emit(txt)

    def updatebaseparamwin(self, d):
        self.prmComm.psig.emit(d)

    def updatedispparam(self):
        self.p.psig.emit(self.params)

    def updatedrawerr(self):
        # False means do not recalculate error
        self.canvComm.csig.emit(False, self.opt)

    def stop(self):
        self.killproc()

    def __del__(self):
        self.quit()
        self.wait()

    def run(self):
        msg = ''

        if self.opt and self.baseparamwin is not None:
            try:
                self.optmodel()  # run optimization
            except RuntimeError as e:
                msg = str(e)
                self.baseparamwin.optparamwin.toggleEnableUserFields(
                  self.cur_step, enable=True)
                self.baseparamwin.optparamwin.clear_initial_opt_ranges()
                self.baseparamwin.optparamwin.optimization_running = False
        else:
            try:
                self.runsim()  # run simulation
                # update params in all windows (optimization)
                self.updatedispparam()
            except RuntimeError as e:
                msg = str(e)

        self.d.finishSim.emit(self.opt, msg)  # send the finish signal

    def killproc(self):
        """make sure all nrniv procs have been killed"""
        _kill_and_check_nrniv_procs()

        self.lock.acquire()
        self.killed = True
        self.lock.release()

    def get_proc_stream(self, stream, print_to_console=False):
        for line in iter(stream.readline, ""):
            if print_to_console:
                print(line.strip())
            # send a signal to waitsimwin, which updates its textedit
            self.updatewaitsimwin(line.strip())
        stream.close()

    # run sim command via mpi, then delete the temp file.
    def runsim(self, is_opt=False, banner=True, simlength=None):
        self.lock.acquire()
        self.killed = False
        self.lock.release()

        while True:
            if self.ncore == 0:
                raise RuntimeError("No cores available for simulation")

            try:
                simulate(self.params, self.ncore)
                break
            except RuntimeError as e:
                if self.ncore == 1:
                    # can't reduce ncore any more
                    print(str(e))
                    self.updatewaitsimwin(str(e))
                    _kill_and_check_nrniv_procs()
                    raise RuntimeError("Simulation failed to start")

            # check if proc was killed before retrying with fewer cores
            self.lock.acquire()
            if self.killed:
                self.lock.release()
                # exit using RuntimeError
                raise RuntimeError("Terminated")
            else:
                self.lock.release()

            self.ncore = ceil(self.ncore/2)
            txt = "INFO: Failed starting simulation, retrying with %d cores" \
                % self.ncore
            print(txt)
            self.updatewaitsimwin(txt)

        # should have good data written to files at this point
        updatedat(self.params)

        if not is_opt:
            # update lsimdat and its current sim index
            updatelsimdat(self.paramfn, self.params, ddat['dpl'])

    def optmodel(self):
        need_initial_ddat = False

        # initialize RNG with seed from config
        seed = self.params['prng_seedcore_opt']
        nlopt.srand(seed)

        # initial_ddat stores the initial fit (from "Run Simulation").
        # To be displayed in final dipole plot as black dashed line.
        if len(ddat) > 0:
            initial_ddat['dpl'] = deepcopy(ddat['dpl'])
            initial_ddat['errtot'] = deepcopy(ddat['errtot'])
        else:
            need_initial_ddat = True

        self.baseparamwin.optparamwin.populate_initial_opt_ranges()

        # save initial parameters file
        data_dir = op.join(get_output_dir(), 'data')
        sim_dir = op.join(data_dir, self.params['sim_prefix'])
        param_out = os.path.join(sim_dir, 'before_opt.param')
        write_legacy_paramf(param_out, self.params)

        self.updatewaitsimwin('Optimizing model. . .')

        self.last_step = False
        self.first_step = True
        num_steps = self.baseparamwin.optparamwin.get_num_chunks()
        for step in range(num_steps):
            self.cur_step = step
            if step == num_steps - 1:
                self.last_step = True

            # disable range sliders for each step once that step has begun
            self.baseparamwin.optparamwin.toggleEnableUserFields(step,
                                                                 enable=False)

            self.step_ranges = \
                self.baseparamwin.optparamwin.get_chunk_ranges(step)
            self.step_sims = \
                self.baseparamwin.optparamwin.get_sims_for_chunk(step)

            if self.step_sims == 0:
                txt = "Skipping optimization step %d (0 simulations)" % \
                    (step + 1)
                self.updatewaitsimwin(txt)
                continue

            if len(self.step_ranges) == 0:
                txt = "Skipping optimization step %d (0 parameters)" % \
                    (step + 1)
                self.updatewaitsimwin(txt)
                continue

            txt = "Starting optimization step %d/%d" % (step + 1, num_steps)
            self.updatewaitsimwin(txt)
            self.runOptStep(step)

            if 'dpl' in self.best_ddat:
                ddat['dpl'] = deepcopy(self.best_ddat['dpl'])
            if 'errtot' in self.best_ddat:
                ddat['errtot'] = deepcopy(self.best_ddat['errtot'])

            if need_initial_ddat:
                initial_ddat = deepcopy(ddat)

            # update optdat with best from this step
            updateoptdat(self.paramfn, self.params, ddat['dpl'])

            # put best opt results into GUI and save to param file
            push_values = {}
            for param_name in self.step_ranges.keys():
                push_values[param_name] = self.step_ranges[param_name]['final']
            self.updatebaseparamwin(push_values)
            self.baseparamwin.optparamwin.push_chunk_ranges(step, push_values)

            sleep(1)

            self.first_step = False

        # one final sim with the best parameters to update display
        self.runsim(is_opt=True, banner=False)

        # update lsimdat and its current sim index
        updatelsimdat(self.paramfn, self.params, ddat['dpl'])

        # update optdat with the final best
        updateoptdat(self.paramfn, self.params, ddat['dpl'])

        # re-enable all the range sliders
        self.baseparamwin.optparamwin.toggleEnableUserFields(step,
                                                             enable=True)

        self.baseparamwin.optparamwin.clear_initial_opt_ranges()
        self.baseparamwin.optparamwin.optimization_running = False

    def runOptStep(self, step):
        self.optsim = 0
        self.minopterr = 1e9
        self.stepminopterr = self.minopterr
        self.best_ddat = {}
        self.opt_start = self.baseparamwin.optparamwin.get_chunk_start(step)
        self.opt_end = self.baseparamwin.optparamwin.get_chunk_end(step)
        self.opt_weights = \
            self.baseparamwin.optparamwin.get_chunk_weights(step)

        def optrun(new_params, grad=0):
            txt = "Optimization step %d, simulation %d" % (step + 1,
                                                           self.optsim + 1)
            self.updatewaitsimwin(txt)
            print(txt)

            dtest = {}
            for param_name, test_value in zip(self.step_ranges.keys(),
                                              new_params):
                if test_value >= self.step_ranges[param_name]['minval'] and \
                        test_value <= self.step_ranges[param_name]['maxval']:
                    dtest[param_name] = test_value
                else:
                    # This test is not strictly necessary with COBYLA, but in
                    # case the algorithm is changed at some point in the future
                    print('INFO: optimization chose '
                          '%.3f for %s outside of [%.3f-%.3f].'
                          % (test_value, param_name,
                             self.step_ranges[param_name]['minval'],
                             self.step_ranges[param_name]['maxval']))
                    return 1e9  # invalid param value -> large error

            # put new param values into GUI and save params to file
            self.updatebaseparamwin(dtest)
            sleep(1)

            # run the simulation, but stop early if possible
            self.runsim(is_opt=True, banner=False, simlength=self.opt_end)

            # calculate wRMSE for all steps
            weighted_rmse(ddat, self.opt_end, self.opt_weights,
                          tstart=self.opt_start)
            err = ddat['werrtot']

            if self.last_step:
                # weighted RMSE with weights of all 1's is the same as
                # regular RMSE
                ddat['errtot'] = ddat['werrtot']
                txt = "RMSE = %f" % err
            else:
                # calculate regular RMSE for displaying on plot
                calcerr(ddat, self.opt_end, tstart=self.opt_start)
                txt = "weighted RMSE = %f, RMSE = %f" % (err, ddat['errtot'])

            print(txt)
            self.updatewaitsimwin(os.linesep + 'Simulation finished: ' + txt +
                                  os.linesep)

            data_dir = op.join(get_output_dir(), 'data')
            sim_dir = op.join(data_dir, self.params['sim_prefix'])

            fnoptinf = os.path.join(sim_dir, 'optinf.txt')
            with open(fnoptinf, 'a') as fpopt:
                fpopt.write(str(ddat['errtot']) + os.linesep)  # write error

            # save params numbered by optsim
            param_out = os.path.join(sim_dir, 'step_%d_sim_%d.param' %
                                     (self.cur_step, self.optsim))
            write_legacy_paramf(param_out, self.params)

            if err < self.stepminopterr:
                self.updatewaitsimwin("new best with RMSE %f" % err)

                self.stepminopterr = err
                # save best param file
                param_out = os.path.join(sim_dir, 'step_%d_best.param' %
                                         self.cur_step)
                write_legacy_paramf(param_out, self.params)
                if 'dpl' in ddat:
                    self.best_ddat['dpl'] = ddat['dpl']
                if 'errtot' in ddat:
                    self.best_ddat['errtot'] = ddat['errtot']

            if self.optsim == 0 and not self.first_step:
                # Update plots for the first simulation only of this step
                # (best results from last round). Skip the first step because
                # there are no optimization results to show yet.
                self.updatedrawerr()  # send event to draw updated RMSE

            self.optsim += 1

            return err  # return RMSE

        def optimize(params_input, evals, algorithm):
            opt_params = []
            lb = []
            ub = []

            for param_name in params_input.keys():
                upper = params_input[param_name]['maxval']
                lower = params_input[param_name]['minval']
                if upper == lower:
                    continue

                ub.append(upper)
                lb.append(lower)
                opt_params.append(params_input[param_name]['initial'])

            if algorithm == nlopt.G_MLSL_LDS or algorithm == nlopt.G_MLSL:
                # In case these mixed mode (global + local) algorithms are
                # used in the future
                local_opt = nlopt.opt(nlopt.LN_COBYLA, num_params)
                opt.set_local_optimizer(local_opt)

            opt.set_lower_bounds(lb)
            opt.set_upper_bounds(ub)
            opt.set_min_objective(optrun)
            opt.set_xtol_rel(1e-4)
            opt.set_maxeval(evals)
            opt_results = opt.optimize(opt_params)

            return opt_results

        txt = 'Optimizing from [%3.3f-%3.3f] ms' % (self.opt_start,
                                                    self.opt_end)
        self.updatewaitsimwin(txt)

        num_params = len(self.step_ranges)
        algorithm = nlopt.LN_COBYLA
        opt = nlopt.opt(algorithm, num_params)
        opt_results = optimize(self.step_ranges, self.step_sims, algorithm)

        # update opt params for the next round
        for var_name, new_value in zip(self.step_ranges, opt_results):
            old_value = self.step_ranges[var_name]['initial']

            # only change the parameter value if it changed significantly
            if not isclose(old_value, new_value, abs_tol=1e-9):
                self.step_ranges[var_name]['final'] = new_value
            else:
                self.step_ranges[var_name]['final'] = \
                  self.step_ranges[var_name]['initial']
