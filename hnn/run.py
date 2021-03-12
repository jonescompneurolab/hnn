"""File with functions and classes for running the NEURON """

# Authors: Blake Caldwell <blake_caldwell@brown.edu>
#          Sam Neymotin <samnemo@gmail.com>
#          Shane Lee

import os.path as op
import os
import sys
from time import sleep
from copy import deepcopy
from math import ceil, isclose
from contextlib import redirect_stdout

from PyQt5 import QtCore
from hnn_core import simulate_dipole, Network, MPIBackend
import nlopt
from psutil import wait_procs, process_iter, NoSuchProcess

from .paramrw import write_legacy_paramf, get_output_dir


class TextSignal(QtCore.QObject):
    """for passing text"""
    tsig = QtCore.pyqtSignal(str)


class DataSignal(QtCore.QObject):
    """for signalling data read"""
    dsig = QtCore.pyqtSignal(str, dict)


class ParamSignal(QtCore.QObject):
    """for updating GUI & param file during optimization"""
    psig = QtCore.pyqtSignal(dict)


class CanvSignal(QtCore.QObject):
    """for updating main GUI canvas"""
    csig = QtCore.pyqtSignal(bool, bool)


class ResultObj(QtCore.QObject):
    def __init__(self, data, params):
        self.data = data
        self.params = params


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
    net = Network(params, add_drives_from_params=True)

    sim_data = {}
    # run the simulation with MPIBackend for faster completion time
    with MPIBackend(n_procs=n_procs, mpi_cmd='mpiexec'):
        sim_data['raw_dpls'] = simulate_dipole(net, params['N_trials'],
                                               postproc=False)

    sim_data['gid_ranges'] = net.gid_ranges
    sim_data['spikes'] = net.cell_response

    return sim_data


# based on https://nikolak.com/pyqt-threading-tutorial/
class RunSimThread(QtCore.QThread):
    """The RunSimThread class.

    Parameters
    ----------

    ncore : int
        Number of cores to run this simulation over
    params : dict
        Dictionary of params describing simulation config
    param_signal : ParamSignal
        Signal to main process to send back params
    done_signal : DoneSignal
        Signal to main process that the simulation has finished
    waitsimwin : WaitSimDialog
        Handle to the Qt dialog during a simulation
    baseparamwin : BaseParamDialog
        Handle to the Qt dialog with parameter values
    mainwin : HNNGUI
        Handle to the main application window
    opt : bool
        Whether this simulation thread is running an optimization

    Attributes
    ----------
    ncore : int
        Number of cores to run this simulation over
    params : dict
        Dictionary of params describing simulation config
    param_signal : ParamSignal
        Signal to main process to send back params
    done_signal : DoneSignal
        Signal to main process that the simulation has finished
    waitsimwin : WaitSimDialog
        Handle to the Qt dialog during a simulation
    baseparamwin : BaseParamDialog
        Handle to the Qt dialog with parameter values
    mainwin : HNNGUI
        Handle to the main application window
    opt : bool
        Whether this simulation thread is running an optimization
    killed : bool
        Whether this simulation was forcefully terminated
    killed : bool
        Whether this simulation was forcefully terminated
    """

    result_signal = QtCore.pyqtSignal(object)

    def __init__(self, ncore, params, param_signal, done_signal, waitsimwin,
                 baseparamwin, result_callback, mainwin, opt=False):
        QtCore.QThread.__init__(self)
        self.ncore = ncore
        self.params = params
        self.param_signal = param_signal
        self.done_signal = done_signal
        self.waitsimwin = waitsimwin
        self.baseparamwin = baseparamwin
        self.mainwin = mainwin
        self.result_signal.connect(result_callback)
        self.opt = opt
        self.killed = False

        self.paramfn = os.path.join(get_output_dir(), 'param',
                                    self.params['sim_prefix'] + '.param')

        self.txtComm = TextSignal()
        self.txtComm.tsig.connect(self.waitsimwin.updatetxt)

        self.prmComm = ParamSignal()
        self.prmComm.psig.connect(self.baseparamwin.updatesaveparams)

        self.canvComm = CanvSignal()
        self.canvComm.csig.connect(self.mainwin.initSimCanvas)

    def _updatewaitsimwin(self, txt):
        """Used to write messages to simulation window"""
        self.txtComm.tsig.emit(txt)

    class _log_sim_status(object):
        """Replaces sys.stdout.write() to write message to simulation window"""
        def __init__(self, parent):
            self.out = sys.stdout
            self.parent = parent

        def write(self, message):
            self.out.write(message)
            stripped_message = message.strip()
            if not stripped_message == '':
                self.parent._updatewaitsimwin(stripped_message)

        def flush(self):
            self.out.flush()

    def _updatebaseparamwin(self, d):
        """Signals baseparamwin to update its parameter from passed dict"""
        self.prmComm.psig.emit(d)

    def _updatedispparam(self):
        """Signals baseparamwin to run updateDispParam"""
        self.param_signal.psig.emit(self.params)

    def _updatedrawerr(self):
        """Signals mainwin to redraw canvas with RMSE"""
        # When self.opt is false, do not recalculate error
        self.canvComm.csig.emit(False, self.opt)

    def stop(self):
        """Terminate running simulation"""
        _kill_and_check_nrniv_procs()
        self.killed = True

    def __del__(self):
        self.quit()
        self.wait()

    def run(self):
        """Start simulation"""

        msg = ''

        if self.opt:
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
                self._runsim()  # run simulation

                # update params in all windows (optimization)
                self._updatedispparam()
            except RuntimeError as e:
                msg = str(e)

        self.done_signal.finishSim.emit(self.opt, msg)

    # run sim command via mpi, then delete the temp file.
    def _runsim(self, is_opt=False, banner=True, simlength=None):
        self.killed = False

        while True:
            if self.ncore == 0:
                raise RuntimeError("No cores available for simulation")

            try:
                sim_log = self._log_sim_status(parent=self)
                with redirect_stdout(sim_log):
                    sim_data = simulate(self.params, self.ncore)
                break
            except RuntimeError as e:
                if self.ncore == 1:
                    # can't reduce ncore any more
                    print(str(e))
                    self._updatewaitsimwin(str(e))
                    _kill_and_check_nrniv_procs()
                    raise RuntimeError("Simulation failed to start")

            # check if proc was killed before retrying with fewer cores
            if self.killed:
                # exit using RuntimeError
                raise RuntimeError("Terminated")

            self.ncore = ceil(self.ncore / 2)
            txt = "INFO: Failed starting simulation, retrying with %d cores" \
                % self.ncore
            print(txt)
            self._updatewaitsimwin(txt)

        # put sim_data into the val attribute of a ResultObj
        self.result_signal.emit(ResultObj(sim_data, self.params))

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

        self._updatewaitsimwin('Optimizing model. . .')

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
                self._updatewaitsimwin(txt)
                continue

            if len(self.step_ranges) == 0:
                txt = "Skipping optimization step %d (0 parameters)" % \
                    (step + 1)
                self._updatewaitsimwin(txt)
                continue

            txt = "Starting optimization step %d/%d" % (step + 1, num_steps)
            self._updatewaitsimwin(txt)
            self.runOptStep(step)

            if 'dpl' in self.best_ddat:
                ddat['dpl'] = deepcopy(self.best_ddat['dpl'])
            if 'errtot' in self.best_ddat:
                ddat['errtot'] = deepcopy(self.best_ddat['errtot'])

            if need_initial_ddat:
                save_initial_sim_data()
                initial_ddat = deepcopy(ddat)

            # update optdat with best from this step
            update_opt_data(self.paramfn, self.params, ddat['dpl'])

            # put best opt results into GUI and save to param file
            push_values = {}
            for param_name in self.step_ranges.keys():
                push_values[param_name] = self.step_ranges[param_name]['final']
            self._updatebaseparamwin(push_values)
            self.baseparamwin.optparamwin.push_chunk_ranges(step, push_values)

            sleep(1)

            self.first_step = False

        # one final sim with the best parameters to update display
        self._runsim(is_opt=True, banner=False)

        # update lsimdat and its current sim index
        update_sim_data_from_disk(self.paramfn, self.params, ddat['dpl'])

        # update optdat with the final best
        update_opt_data_from_disk(self.paramfn, self.params, ddat['dpl'])

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
            self._updatewaitsimwin(txt)
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
            self._updatebaseparamwin(dtest)
            sleep(1)

            # run the simulation, but stop early if possible
            self._runsim(is_opt=True, banner=False, simlength=self.opt_end)

            # calculate wRMSE for all steps
            calcerr(self.paramfn, self.opt_end, tstart=self.opt_start,
                    weights=self.opt_weights)
            err = ddat['werrtot']

            if self.last_step:
                # weighted RMSE with weights of all 1's is the same as
                # regular RMSE
                ddat['errtot'] = ddat['werrtot']
                txt = "RMSE = %f" % err
            else:
                # calculate regular RMSE for displaying on plot
                calcerr(self.paramfn, self.opt_end, tstart=self.opt_start)
                txt = "weighted RMSE = %f, RMSE = %f" % (err, ddat['errtot'])

            print(txt)
            self._updatewaitsimwin(os.linesep + 'Simulation finished: ' + txt +
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
                self._updatewaitsimwin("new best with RMSE %f" % err)

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
                self._updatedrawerr()  # send event to draw updated RMSE

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
        self._updatewaitsimwin(txt)

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
