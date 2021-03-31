"""File with functions and classes for running the NEURON """

# Authors: Blake Caldwell <blake_caldwell@brown.edu>
#          Sam Neymotin <samnemo@gmail.com>
#          Shane Lee

import os
import sys
from math import ceil, isclose
from contextlib import redirect_stdout
import traceback
from queue import Queue
from threading import Event, Lock
import numpy as np
from collections import namedtuple

import nlopt
from PyQt5 import QtCore
from hnn_core import simulate_dipole, Network, MPIBackend

from .paramrw import get_output_dir, hnn_core_compat_params


class BasicSignal(QtCore.QObject):
    """for signaling"""
    sig = QtCore.pyqtSignal()


class ObjectSignal(QtCore.QObject):
    """for returning an object"""
    sig = QtCore.pyqtSignal(object)


class QueueSignal(QtCore.QObject):
    """for returning data"""
    qsig = QtCore.pyqtSignal(Queue, str, float)


class QueueDataSignal(QtCore.QObject):
    """for returning data"""
    qsig = QtCore.pyqtSignal(Queue, str, np.ndarray, float, float)


class EventSignal(QtCore.QObject):
    """for synchronization"""
    esig = QtCore.pyqtSignal(Event, str)


class TextSignal(QtCore.QObject):
    """for passing text"""
    tsig = QtCore.pyqtSignal(str)


class DataSignal(QtCore.QObject):
    """for signalling data read"""
    dsig = QtCore.pyqtSignal(str, dict)


class ParamSignal(QtCore.QObject):
    """for updating GUI & param file during optimization"""
    psig = QtCore.pyqtSignal(dict)


class ResultObj(QtCore.QObject):
    def __init__(self, data, params):
        self.data = data
        self.params = params


def _add_missing_frames(tb):
    """take back frames that PyQt hides

    see: https://fman.io/blog/pyqt-excepthook/
    """
    fake_tb = namedtuple(
        'fake_tb', ('tb_frame', 'tb_lasti', 'tb_lineno', 'tb_next')
    )
    result = fake_tb(tb.tb_frame, tb.tb_lasti, tb.tb_lineno, tb.tb_next)
    frame = tb.tb_frame.f_back
    while frame:
        result = fake_tb(frame, frame.f_lasti, frame.f_lineno, result)
        frame = frame.f_back
    return result


def simulate(net):
    """Start the simulation with hnn_core.simulate

    Parameters
    ----------
    net : Network object
        The constructed Network object from hnn-core
    """

    sim_data = {}
    # run the simulation with MPIBackend for faster completion time
    record_vsoma = bool(net.params['record_vsoma'])

    numspikes_params = net.params['numspikes_*']
    # optimization can feed in floats for numspikes
    for param_name, spikes in numspikes_params.items():
        net.params[param_name] = round(spikes)

    sim_data['raw_dpls'] = simulate_dipole(net, net.params['N_trials'],
                                           postproc=False,
                                           record_vsoma=record_vsoma)

    # hnn-core changes this to bool, change back to int
    if isinstance(net.params['record_vsoma'], bool):
        net.params['record_vsoma'] = int(record_vsoma)
    sim_data['gid_ranges'] = net.gid_ranges
    sim_data['spikes'] = net.cell_response
    sim_data['vsoma'] = net.cell_response.vsoma

    return sim_data


# based on https://nikolak.com/pyqt-threading-tutorial/
class SimThread(QtCore.QThread):
    """The SimThread class.

    Parameters
    ----------

    ncore : int
        Number of cores to run this simulation over
    params : dict
        Dictionary of params describing simulation config
    result_callback: function
        Handle to for callback to call after every sim completion
    mainwin : HNNGUI
        Handle to the main application window

    Attributes
    ----------
    ncore : int
        Number of cores to run this simulation over
    params : dict
        Dictionary of params describing simulation config
    mainwin : HNNGUI
        Handle to the main application window
    is_optimization : bool
        Whether this simulation thread is running an optimization
    baseparamwin : BaseParamDialog
        Handle to BaseParamDialog
    killed : bool
        Whether this simulation was forcefully terminated. Will not continue
        relaunching simulations if True
    paramfn : str
        The parameter file name (full path) to simulate
    result_signal : ObjectSignal object
        Signal to be emitted at the end of every simulation for updating
        sim_data in main thread
    msg_signal : TextSignal object
        Signal to be emitted for updating the simulations status dialog box
    param_signal : ParamSignal object
        Signal to be emitted for updating the params in the GUI
    done_signal : TextSignal object
        Signal to be emitted at completion of a simulation. Not emitted for
        when running an optimization simulation.
    killed_lock : threading.Lock
        Lock to protect killed variable mutual exclusion
    backend : MPIBackend
        The hnn-core backend responsible for running simulations
    """

    def __init__(self, ncore, params, result_callback, mainwin):
        QtCore.QThread.__init__(self)
        sys.excepthook = self._excepthook
        self.ncore = ncore
        self.params = params
        self.mainwin = mainwin
        self.is_optimization = self.mainwin.is_optimization
        self.baseparamwin = self.mainwin.baseparamwin
        self.killed = False
        self.backend = None
        self.killed_lock = Lock()

        self.paramfn = os.path.join(get_output_dir(), 'param',
                                    self.params['sim_prefix'] + '.param')

        self.result_signal = ObjectSignal()
        self.result_signal.sig.connect(result_callback)

        self.msg_signal = TextSignal()
        self.msg_signal.tsig.connect(self.mainwin.waitsimwin.updatetxt)

        self.param_signal = ParamSignal()
        self.param_signal.psig.connect(self.baseparamwin.updateDispParam)

        self.done_signal = TextSignal()
        self.done_signal.tsig.connect(self.mainwin.done)

    def _excepthook(self, exc_type, exc_value, exc_tb):
        enriched_tb = _add_missing_frames(exc_tb) if exc_tb else exc_tb
        traceback.print_exception(exc_type, exc_value, enriched_tb)

    def _updatewaitsimwin(self, txt):
        """Used to write messages to simulation window"""
        self.msg_signal.tsig.emit(txt)

    class _log_sim_status(object):
        """Replaces sys.stdout.write() to write output to simulation window"""
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

    def stop(self):
        """Terminate running simulation"""
        with self.killed_lock:
            self.killed = True

            if self.backend is not None:
                self.backend.terminate()

    def run(self, sim_length=None):
        """Start simulation

        Parameters
        ----------
        sim_length : float | None
            Optional to limit the stopping point of the simulation. If None,
            the entire simulation length will be run until 'tstop'
        """

        msg = ''
        banner = not self.is_optimization
        self._run(banner=banner, sim_length=sim_length)  # run simulation

        if not self.is_optimization:
            self.param_signal.psig.emit(self.params)
            self.done_signal.tsig.emit(msg)

        # gracefully stop this thread
        self.quit()

    def _run(self, banner=True, sim_length=None):
        with self.killed_lock:
            self.killed = False

        # make copy of params dict in Params object before
        # modifying tstop
        sim_params = hnn_core_compat_params(self.params)
        if sim_length is not None:
            sim_params['tstop'] = round(sim_length, 8)

        while True:
            if self.ncore == 0:
                raise RuntimeError("No cores available for simulation")

            try:
                sim_log = self._log_sim_status(parent=self)
                with redirect_stdout(sim_log):
                    # create the network from the parameter file
                    # Note: NEURON objects haven't been created yet
                    net = Network(sim_params, add_drives_from_params=True)
                    with MPIBackend(
                            n_procs=self.ncore, mpi_cmd='mpiexec') as backend:
                        self.backend = backend
                        with self.killed_lock:
                            if self.killed:
                                raise RuntimeError("Terminated")
                        sim_data = simulate(net)
                    self.backend = None
                break
            except RuntimeError as e:
                if self.ncore == 1:
                    # can't reduce ncore any more
                    print(str(e))
                    self._updatewaitsimwin(str(e))
                    raise RuntimeError("Simulation failed to start")

            # check if proc was killed before retrying with fewer cores
            with self.killed_lock:
                if self.killed:
                    raise RuntimeError("Terminated")

            self.ncore = ceil(self.ncore / 2)
            txt = "INFO: Failed starting simulation, retrying with %d cores" \
                % self.ncore
            print(txt)
            self._updatewaitsimwin(txt)

        # put sim_data into the val attribute of a ResultObj
        self.result_signal.sig.emit(ResultObj(sim_data, self.params))


class OptThread(SimThread):
    """The OptThread class.

    Parameters
    ----------

    ncore : int
        Number of cores to run this simulation over
    params : dict
        Dictionary of params describing simulation config
    num_steps : int
        Total number of steps in optimization process
    seed : seed for optimization set in the GUI. The parameter for this is
        'prng_seedcore_opt', but it is not read from the parameter file by
        hnn-core
    sim_data : SimData object
        Reference to the class containing simulation data. Only used for
        references to functions for emitting signals. The one exception is
        using the SimData.in_sim_data member function
    result_callback: function
        Handle to for callback to call after every sim completion
    mainwin : HNNGUI
        Handle to the main application window
    opt_callback : function
        Handle for callback after optimization is complete

    Attributes (unique from SimThread)
    ----------
    optparamwin : OptEvokedInputParamDialog
        Handle to the optimization configuration dialog box
    cur_itr : int
        Current iteration/simulation of the current step
    cur_step : int
        Stores the current optimization step in progress
    num_steps : int
        Total number of steps in optimization process
    num_params : int
        Number of parameters to be optimized in every step
    step_ranges : dict
        Parameter ranges for this step
    step_sims : int
        Number of sim in this step
    sim_data : SimData object
        Reference to the class containing simulation data. Only used for
        references to functions for emitting signals. The one exception is
        using the SimData.in_sim_data member function
    result_callback: function
        Handle for callback to call after every sim completion
    seed : seed for optimization set in the GUI. The parameter for this is
        'prng_seedcore_opt', but it is not read from the parameter file by
        hnn-core
    best_step_werr : float
        The current best weighted RMSE for this step
    initial_err : float
        The regular RMSE for initial simulation
    paramfn : str
        The parameter file name (full path) to simulate
    sim_thread : SimThread object
        The thread running a simulation. Used for running optimization
        iterations and initial or final simulations, if necessary.
    sim_running : bool
        Whether a current simulation is running at sim_thread handle
    opt_start : float
        Time in ms to begin optimization over the dipole waveform in this
        step. Used for weighted RMSE calculation, but not for running
        simulations (first part of simulation may be ignored)
    opt_end : float
        Time is ms to stop
    opt : nlopt.opt object
    opt_weights : np.ndarray
        Array containing the weights used for RMSE calculation for this step
    killed : bool
        Whether this simulation was forcefully terminated. Will not continue
        relaunching simulations if True
    done_signal : TextSignal object
        Signal to be emitted at completion of optimization. Connected to
        opt_callback param to this function
    refresh_signal : BasicSignal object
        Signal to be emitted for refreshing the plots in the main GUI
    update_sim_data_from_opt_data : EventSignal object
        Signal to be emitted for updating sim_data[paramfn] with the
        contents of opt_data
    update_opt_data_from_sim_data : EventSignal object
        Signal to be emitted for updating opt_data with the
        contents of sim_data[paramfn]
    update_initial_opt_data_from_sim_data : EventSignal object
        Signal to be emitted for updating opt_data with initial dipole
        and initial error using the contents of sim_data[paramfn]
    get_err_from_sim_data : QueueSignal object
        Signal to be emitted to request the regular RMSE be put in the queue
    get_werr_from_sim_data : QueueDataSignal object
        Signal to be emitted to request the weighted RMSE be put in the queue
    """
    def __init__(self, ncore, params, num_steps, seed, sim_data,
                 result_callback, opt_callback, mainwin):
        super().__init__(ncore, params, result_callback, mainwin)
        self.optparamwin = self.baseparamwin.optparamwin
        self.cur_itr = 0
        self.cur_step = 0
        self.num_steps = num_steps
        self.num_params = 0
        self.step_ranges = {}
        self.step_sims = 0
        self.sim_data = sim_data
        self.result_callback = result_callback
        self.seed = seed
        self.best_step_werr = sys.float_info.max
        self.initial_err = sys.float_info.max
        self.sim_thread = None
        self.sim_running = False
        self.opt_start = 0.0
        self.opt_end = 0.0
        self.opt = None
        self.opt_weights = None
        self.killed = False

        self.done_signal.tsig.connect(opt_callback)

        self.refresh_signal = BasicSignal()
        self.refresh_signal.sig.connect(self.mainwin.initSimCanvas)

        self.update_sim_data_from_opt_data = EventSignal()
        self.update_sim_data_from_opt_data.esig.connect(
            sim_data.update_sim_data_from_opt_data)

        self.update_opt_data_from_sim_data = EventSignal()
        self.update_opt_data_from_sim_data.esig.connect(
            sim_data.update_opt_data_from_sim_data)

        self.update_initial_opt_data_from_sim_data = EventSignal()
        self.update_initial_opt_data_from_sim_data.esig.connect(
            sim_data.update_initial_opt_data_from_sim_data)

        self.get_err_from_sim_data = QueueSignal()
        self.get_err_from_sim_data.qsig.connect(sim_data.get_err_wrapper)

        self.get_werr_from_sim_data = QueueDataSignal()
        self.get_werr_from_sim_data.qsig.connect(sim_data.get_werr_wrapper)

    def run(self):
        msg = ''
        self._run()  # run optimization
        self.done_signal.tsig.emit(msg)

    def stop(self):
        """Terminate running simulation"""
        with self.killed_lock:
            self.killed = True
            self.sim_thread.stop()

        self.done_signal.tsig.emit("Optimization terminated")

    def _run(self):
        # initialize RNG with seed from config
        nlopt.srand(self.seed)
        self._get_initial_data()

        for step in range(self.num_steps):
            self.cur_step = step
            self.cur_itr = 0

            # disable range sliders for each step once that step has begun
            self.optparamwin.toggle_enable_user_fields(self.cur_step,
                                                       enable=False)

            self.step_sims = self.optparamwin.get_sims_for_chunk(step)

            if self.step_sims == 0:
                txt = "Skipping optimization step %d (0 simulations)" % \
                    (step + 1)
                self._updatewaitsimwin(txt)
                continue

            self.step_ranges = self.optparamwin.get_chunk_ranges(step)
            if len(self.step_ranges) == 0:
                txt = "Skipping optimization step %d (0 parameters)" % \
                    (step + 1)
                self._updatewaitsimwin(txt)
                continue

            txt = "Starting optimization step %d/%d" % (step + 1,
                                                        self.num_steps)
            self._updatewaitsimwin(txt)
            print(txt)

            self.opt_start = self.optparamwin.get_chunk_start(self.cur_step)
            self.opt_end = self.optparamwin.get_chunk_end(self.cur_step)
            txt = 'Optimizing from [%3.3f-%3.3f] ms' % (self.opt_start,
                                                        self.opt_end)
            self._updatewaitsimwin(txt)
            print(txt)

            # weights calculated once per step
            self.opt_weights = \
                self.optparamwin.get_chunk_weights(self.cur_step)

            # run an opt step
            algorithm = nlopt.LN_COBYLA
            self.num_params = len(self.step_ranges)
            self.opt = nlopt.opt(algorithm, self.num_params)
            opt_results = self._run_opt_step(self.step_ranges, self.step_sims,
                                             algorithm)

            # update with optimized params for the next round
            for var_name, new_value in zip(self.step_ranges, opt_results):
                old_value = self.step_ranges[var_name]['initial']

                # only change the parameter value if it changed significantly
                if not isclose(old_value, new_value, abs_tol=1e-9):
                    self.step_ranges[var_name]['final'] = new_value
                else:
                    self.step_ranges[var_name]['final'] = \
                        self.step_ranges[var_name]['initial']

            # push into GUI and save to param file so that next simulation
            # starts from there.
            push_values = {}
            for param_name in self.step_ranges.keys():
                push_values[param_name] = self.step_ranges[param_name]['final']
            self.baseparamwin.update_gui_params(push_values)

            # update optimization dialog window
            self.optparamwin.push_chunk_ranges(push_values)

        # update opt_data with the final best
        update_event = Event()
        self.update_sim_data_from_opt_data.esig.emit(update_event,
                                                     self.paramfn)
        update_event.wait()
        self.refresh_signal.sig.emit()  # redraw with updated RMSE

        # check that optimization improved RMSE
        err_queue = Queue()
        self.get_err_from_sim_data.qsig.emit(err_queue, self.paramfn,
                                             self.params['tstop'])
        final_err = err_queue.get()
        print("Best RMSE: %f" % final_err)
        if final_err > self.initial_err:
            txt = "Warning: optimization failed to improve RMSE below" + \
                  " %.2f. Reverting to old parameters." % \
                        round(self.initial_err, 2)
            self._updatewaitsimwin(txt)
            print(txt)

            initial_params = self.optparamwin.get_initial_params()
            # populate param values into GUI and save params to file
            self.baseparamwin.update_gui_params(initial_params)

            # update optimization dialog window
            self.optparamwin.push_chunk_ranges(initial_params)

            # run a full length simulation
            self.sim_thread = SimThread(self.ncore, self.params,
                                        self.result_callback,
                                        mainwin=self.mainwin)
            self.sim_running = True
            self.sim_thread.run()
            self.sim_thread.wait()
            with self.killed_lock:
                if self.killed:
                    self.quit()
            self.sim_running = False

    def _get_initial_data(self):
        """Run an initial simulation if necessary"""

        # Has this simulation been run before (is there data?)
        # Note, we are not sending a signal here because synchronization is
        # not necessary. The reference to self.sim_data was passed in at
        # OptThread creation and we are checking here whether there was data
        # for this paramfn at that time. In other words,
        # sim_data[self.paramfn] has not been updated since creation of this
        # OptThread
        if not self.sim_data.in_sim_data(self.paramfn):
            # run a full length simulation
            txt = "Running a simulation with initial parameter set before" + \
                " beginning optimization."
            self._updatewaitsimwin(txt)
            print(txt)

            self.sim_thread = SimThread(self.ncore, self.params,
                                        self.result_callback,
                                        mainwin=self.mainwin)
            self.sim_running = True
            self.sim_thread.run()
            self.sim_thread.wait()
            with self.killed_lock:
                if self.killed:
                    self.quit()
            self.sim_running = False

            # results are in self.sim_data now

        # store the initial fit for display in final dipole plot as
        # black dashed line.
        update_event = Event()
        self.update_opt_data_from_sim_data.esig.emit(update_event,
                                                     self.paramfn)
        update_event.wait()
        update_event.clear()
        self.update_initial_opt_data_from_sim_data.esig.emit(update_event,
                                                             self.paramfn)
        update_event.wait()

        err_queue = Queue()
        self.get_err_from_sim_data.qsig.emit(err_queue, self.paramfn,
                                             self.params['tstop'])
        self.initial_err = err_queue.get()

    def _opt_sim(self, new_params, grad=0):
        """Run a SimThread simulation and calculate weighted RMSE

        Called by nlopt.opt routine
        """
        txt = "Optimization step %d, simulation %d" % (self.cur_step + 1,
                                                       self.cur_itr + 1)
        self._updatewaitsimwin(txt)
        print(txt)

        # Prepare a dict of parameters for this simulation to populate in GUI
        opt_params = {}
        for param_name, param_value in zip(self.step_ranges.keys(),
                                           new_params):
            if param_value >= self.step_ranges[param_name]['minval'] and \
                    param_value <= self.step_ranges[param_name]['maxval']:
                opt_params[param_name] = param_value
            else:
                # This test is not strictly necessary with COBYLA, but in
                # case the algorithm is changed at some point in the future
                print('INFO: optimization chose '
                      '%.3f for %s outside of [%.3f-%.3f].'
                      % (param_value, param_name,
                         self.step_ranges[param_name]['minval'],
                         self.step_ranges[param_name]['maxval']))
                return sys.float_info.max  # return the worst fit ever

        # populate param values into GUI
        self.baseparamwin.update_gui_params(opt_params)

        sim_params = self.params.copy()
        for param_name, param_value in opt_params.items():
            sim_params[param_name] = param_value

        # run the simulation, but stop at self.opt_end
        self.sim_thread = SimThread(self.ncore, sim_params,
                                    self.result_callback,
                                    mainwin=self.mainwin)

        self.sim_running = True
        # may not need to run the entire simulation
        self.sim_thread.run(sim_length=self.opt_end)
        self.sim_thread.wait()
        with self.killed_lock:
            if self.killed:
                self.quit()
        self.sim_running = False

        # calculate wRMSE for all steps
        err_queue = Queue()
        self.get_werr_from_sim_data.qsig.emit(err_queue, self.paramfn,
                                              self.opt_weights, self.opt_end,
                                              self.opt_start)
        werr = err_queue.get()

        txt = "Weighted RMSE = %f" % werr
        print(txt)
        self._updatewaitsimwin(os.linesep + 'Simulation finished: ' + txt +
                               os.linesep)

        # save params numbered by cur_itr
        # data_dir = op.join(get_output_dir(), 'data')
        # sim_dir = op.join(data_dir, self.params['sim_prefix'])
        # param_out = os.path.join(sim_dir, 'step_%d_sim_%d.param' %
        #                          (self.cur_step, self.cur_itr))
        # write_legacy_paramf(param_out, self.params)

        if werr < self.best_step_werr:
            self._updatewaitsimwin("new best with RMSE %f" % werr)

            update_event = Event()
            self.update_opt_data_from_sim_data.esig.emit(update_event,
                                                         self.paramfn)
            update_event.wait()

            self.best_step_werr = werr
            # save best param file
            # param_out = os.path.join(sim_dir, 'step_%d_best.param' %
            #                          self.cur_step)
            # write_legacy_paramf(param_out, self.params)

        if self.cur_itr == 0 and self.cur_step > 0:
            # Update plots for the first simulation only of this step
            # (best results from last round). Skip the first step because
            # there are no optimization results to show yet.
            self.refresh_signal.sig.emit()  # redraw with updated RMSE

        self.cur_itr += 1

        return werr

    def _run_opt_step(self, params_input, num_sims, algorithm):
        """Core function for starting the nlopt optimization routine"""
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
            local_opt = nlopt.opt(nlopt.LN_COBYLA, self.num_params)
            self.opt.set_local_optimizer(local_opt)

        self.opt.set_lower_bounds(lb)
        self.opt.set_upper_bounds(ub)

        # minimize the wRMSE returned by self._opt_sim
        self.opt.set_min_objective(self._opt_sim)
        self.opt.set_xtol_rel(1e-4)
        self.opt.set_maxeval(num_sims)

        # start the optimization: run self.runsim for # iterations in num_sims
        opt_results = self.opt.optimize(opt_params)

        return opt_results
