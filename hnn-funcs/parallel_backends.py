"""Parallel backends"""

# Authors: Blake Caldwell <blake_caldwell@brown.edu>
#          Mainak Jas <mainakjas@gmail.com>

import os
import sys
import multiprocessing
import shlex
import pickle
import base64
from warnings import warn
from subprocess import Popen
import selectors
import binascii
from time import sleep


_BACKEND = None


def _clone_and_simulate(net, trial_idx):
    """Run a simulation including building the network

    This is used by both backends. MPIBackend calls this in mpi_child.py, once
    for each trial (blocking), and JoblibBackend calls this for each trial
    (non-blocking)
    """

    # avoid relative lookups after being forked (Joblib)
    from hnn_core.network_builder import NetworkBuilder
    from hnn_core.network_builder import _simulate_single_trial

    neuron_net = NetworkBuilder(net, trial_idx=trial_idx)
    dpl = _simulate_single_trial(neuron_net, trial_idx)

    spikedata = neuron_net.get_data_from_neuron()

    return dpl, spikedata


def _gather_trial_data(sim_data, net, n_trials, postproc):
    """Arrange data by trial

    To be called after simulate(). Returns list of Dipoles, one for each trial,
    and saves spiking info in net (instance of Network).
    """
    dpls = []

    for idx in range(n_trials):
        dpls.append(sim_data[idx][0])
        spikedata = sim_data[idx][1]
        net.cell_response._spike_times.append(spikedata[0])
        net.cell_response._spike_gids.append(spikedata[1])
        net.gid_ranges = spikedata[2]  # only have one gid_ranges
        net.cell_response.update_types(net.gid_ranges)
        net.cell_response._vsoma.append(spikedata[3])
        net.cell_response._isoma.append(spikedata[4])

        if postproc:
            N_pyr_x = net.params['N_pyr_x']
            N_pyr_y = net.params['N_pyr_y']
            winsz = net.params['dipole_smooth_win'] / net.params['dt']
            fctr = net.params['dipole_scalefctr']
            dpls[-1].post_proc(N_pyr_x, N_pyr_y, winsz, fctr)

    return dpls


def _read_all_bytes(fd, chunk_size=4096):
    all_data = b""
    while True:
        data = os.read(fd, chunk_size)
        all_data += data
        if len(data) < chunk_size:
            break

    return all_data


def requires_mpi4py(function):
    """Decorator for testing functions that require MPI."""
    import pytest

    try:
        import mpi4py
        assert hasattr(mpi4py, '__version__')
        skip = False
    except (ImportError, ModuleNotFoundError) as err:
        if "TRAVIS_OS_NAME" not in os.environ:
            skip = True
        else:
            raise ImportError(err)
    reason = 'mpi4py not available'
    return pytest.mark.skipif(skip, reason=reason)(function)


class JoblibBackend(object):
    """The JoblibBackend class.

    Parameters
    ----------
    n_jobs : int | None
        The number of jobs to start in parallel. If None, then 1 trial will be
        started without parallelism

    Attributes
    ----------
    n_jobs : int
        The number of jobs to start in parallel
    """
    def __init__(self, n_jobs=1):
        self.n_jobs = n_jobs
        print("joblib will run over %d jobs" % (self.n_jobs))

    def _parallel_func(self, func):
        if self.n_jobs != 1:
            try:
                from joblib import Parallel, delayed
            except ImportError:
                warn('joblib not installed. Cannot run in parallel.')
                self.n_jobs = 1
        if self.n_jobs == 1:
            my_func = func
            parallel = list
        else:
            parallel = Parallel(self.n_jobs)
            my_func = delayed(func)

        return parallel, my_func

    def __enter__(self):
        global _BACKEND

        self._old_backend = _BACKEND
        _BACKEND = self

        return self

    def __exit__(self, type, value, traceback):
        global _BACKEND

        _BACKEND = self._old_backend

    def simulate(self, net, postproc=True):
        """Simulate the HNN model

        Parameters
        ----------
        net : Network object
            The Network object specifying how cells are
            connected.
        postproc : bool
            If False, no postprocessing applied to the dipole

        Returns
        -------
        dpl: list of Dipole
            The Dipole results from each simulation trial
        """

        n_trials = net.params['N_trials']
        dpls = []

        parallel, myfunc = self._parallel_func(_clone_and_simulate)
        sim_data = parallel(myfunc(net, idx) for idx in range(n_trials))

        dpls = _gather_trial_data(sim_data, net, n_trials, postproc)

        return dpls


class MPIBackend(object):
    """The MPIBackend class.

    Parameters
    ----------
    n_procs : int | None
        The number of MPI processes requested by the user. If None, then will
        attempt to detect number of cores (including hyperthreads) and start
        parallel simulation over all of them.
    mpi_cmd : str
        The name of the mpi launcher executable. Will use 'mpiexec'
        (openmpi) by default.

    Attributes
    ----------

    n_procs : int
        The number of processes MPI will actually use (spread over cores). This
        can be less than the user specified value if limited by the cores on
        the system, the number of cores allowed by the job scheduler, or
        if mpi4py could not be loaded.
    mpi_cmd_str : str
        The string of the mpi command with number of procs and options
    proc_data_bytes: bytes object
        This will contain data received from the MPI child process via stderr.

    """
    def __init__(self, n_procs=None, mpi_cmd='mpiexec'):
        self.proc_data_bytes = b''

        n_logical_cores = multiprocessing.cpu_count()
        if n_procs is None:
            self.n_procs = n_logical_cores
        else:
            self.n_procs = n_procs

        # obey limits set by scheduler
        if hasattr(os, 'sched_getaffinity'):
            scheduler_cores = len(os.sched_getaffinity(0))
            self.n_procs = min(self.n_procs, scheduler_cores)

        # did user try to force running on more cores than available?
        oversubscribe = False
        if self.n_procs > n_logical_cores:
            oversubscribe = True

        hyperthreading = False

        try:
            import mpi4py
            mpi4py.__version__  # for flake8 test

            try:
                import psutil

                n_physical_cores = psutil.cpu_count(logical=False)

                # detect if we need to use hwthread-cpus with mpiexec
                if self.n_procs > n_physical_cores:
                    hyperthreading = True

            except ImportError:
                warn('psutil not installed, so cannot detect if hyperthreading'
                     'is enabled, assuming yes.')
                hyperthreading = True

        except ImportError:
            warn('mpi4py not installed. will run on single processor')
            self.n_procs = 1

        self.mpi_cmd_str = mpi_cmd

        if self.n_procs == 1:
            print("Backend will use 1 core. Running simulation without MPI")
            return
        else:
            print("MPI will run over %d processes" % (self.n_procs))

        if hyperthreading:
            self.mpi_cmd_str += ' --use-hwthread-cpus'

        if oversubscribe:
            self.mpi_cmd_str += ' --oversubscribe'

        self.mpi_cmd_str += ' -np ' + str(self.n_procs)

        self.mpi_cmd_str += ' nrniv -python -mpi -nobanner ' + \
            sys.executable + ' ' + \
            os.path.join(os.path.dirname(sys.modules[__name__].__file__),
                         'mpi_child.py')

    def __enter__(self):
        global _BACKEND

        self._old_backend = _BACKEND
        _BACKEND = self

        return self

    def __exit__(self, type, value, traceback):
        global _BACKEND

        _BACKEND = self._old_backend

    def _read_stderr(self, fd, mask):
        """read stderr from fd until end of simulation signal is received"""
        data = _read_all_bytes(fd)
        if len(data) > 0:
            str_data = data.decode()
            if '@' in str_data:
                # extract the signal
                signal_index_start = str_data.rfind('@end_of_data:')
                signal_index_end = str_data.rfind('@')
                if signal_index_start < 0 or signal_index_end < 0 or \
                        signal_index_end <= signal_index_start:
                    raise ValueError("Invalid signal start (%d) or end (%d) " %
                                     (signal_index_start, signal_index_end) +
                                     "index")

                # signal without '@' on either side
                signal = str_data[signal_index_start + 1:signal_index_end]

                # remove the signal from the stderr output
                spliced_str_data = str_data[0:signal_index_start] + \
                    str_data[signal_index_end + 1:]

                # add the output bytes and return the signal
                self.proc_data_bytes += spliced_str_data.encode()

                split_string = signal.split(':')
                if len(split_string) > 1 and len(split_string[1]) > 0:
                    data_len = int(split_string[1])
                else:
                    raise ValueError("Completion signal from child MPI process"
                                     " did not contain data length.")

                return data_len

            self.proc_data_bytes += data

        return None

    def _read_stdout(self, fd, mask):
        """read stdout fd until receiving the process simulation is complete"""
        data = _read_all_bytes(fd)
        if len(data) > 0:
            str_data = data.decode()
            if str_data == 'end_of_sim':
                return str_data
            elif 'end_of_sim' in str_data:
                sys.stdout.write(str_data.replace('end_of_sim', ''))
                return 'end_of_sim'

            # output from process includes newlines
            sys.stdout.write(str_data)

        return None

    def _process_child_data(self, data_bytes, data_len):
        if not data_len == len(data_bytes):
            # This is indicative of a failure. For debugging purposes.
            warn("Length of received data unexpected. Expecting %d bytes, "
                 "got %d" % (data_len, len(data_bytes)))

        if len(data_bytes) == 0:
            raise RuntimeError("MPI simulation didn't return any data")

        # decode base64 byte string
        try:
            data_pickled = base64.b64decode(data_bytes, validate=True)
        except binascii.Error:
            # This is here for future debugging purposes. Unit tests can't
            # reproduce an incorrectly padded string, but this has been an
            # issue before
            raise ValueError("Incorrect padding for data length %d bytes" %
                             len(data_bytes) + " (mod 4 = %d)" %
                             (len(data_bytes) % 4))

        # unpickle the data
        return pickle.loads(data_pickled)

    def simulate(self, net, postproc=True):
        """Simulate the HNN model in parallel on all cores

        Parameters
        ----------
        net : Network object
            The Network object specifying how cells are
            connected.
        postproc: bool
            If False, no postprocessing applied to the dipole

        Returns
        -------
        dpl: list of Dipole
            The Dipole results from each simulation trial
        """

        # just use the joblib backend for a single core
        if self.n_procs == 1:
            return JoblibBackend(n_jobs=1).simulate(net, postproc)

        n_trials = net.params['N_trials']
        print("Running %d trials..." % (n_trials))
        dpls = []

        # Split the command into shell arguments for passing to Popen
        if 'win' in sys.platform:
            use_posix = True
        else:
            use_posix = False

        cmdargs = shlex.split(self.mpi_cmd_str, posix=use_posix)

        pickled_params = base64.b64encode(pickle.dumps(net.params))

        # set some MPI environment variables
        my_env = os.environ.copy()
        if 'win' not in sys.platform:
            my_env["OMPI_MCA_btl_base_warn_component_unused"] = '0'

        if 'darwin' in sys.platform:
            my_env["PMIX_MCA_gds"] = "^ds12"  # open-mpi/ompi/issues/7516
            my_env["TMPDIR"] = "/tmp"  # open-mpi/ompi/issues/2956

        # set up pairs of pipes to communicate with subprocess
        (pipe_stdin_r, pipe_stdin_w) = os.pipe()
        (pipe_stdout_r, pipe_stdout_w) = os.pipe()
        (pipe_stderr_r, pipe_stderr_w) = os.pipe()

        # Start the simulation in parallel!
        proc = Popen(cmdargs, stdin=pipe_stdin_r, stdout=pipe_stdout_w,
                     stderr=pipe_stderr_w, env=my_env, cwd=os.getcwd(),
                     universal_newlines=True)

        # process will read stdin on startup for params
        os.write(pipe_stdin_w, pickled_params)

        # signal that we are done writing params
        os.close(pipe_stdin_w)
        os.close(pipe_stdin_r)

        # create the selector instance and register all input events
        # with self.read_stdout which will only echo to stdout
        self.sel = selectors.DefaultSelector()
        self.sel.register(pipe_stdout_r, selectors.EVENT_READ,
                          self._read_stdout)
        self.sel.register(pipe_stderr_r, selectors.EVENT_READ,
                          self._read_stdout)

        data_len = 0
        completed = False
        timeout = 0
        # loop while the process is running
        while True:
            if not proc.poll() is None:
                if completed is True:
                    break
                elif timeout > 4:
                    # This is indicative of a failure. For debugging purposes.
                    warn("Timed out (5s) waiting for end of data after child "
                         "process stopped")
                    break
                else:
                    timeout += 1
                    sleep(1)

            # wait for an event on the selector, timeout after 1s
            events = self.sel.select(timeout=1)
            for key, mask in events:
                callback = key.data
                completion_signal = callback(key.fileobj, mask)
                if completion_signal is not None:
                    if completion_signal == "end_of_sim":
                        # finishied receiving printable output
                        # everything else received is data
                        self.sel.unregister(pipe_stderr_r)
                        self.sel.register(pipe_stderr_r, selectors.EVENT_READ,
                                          self._read_stderr)
                    elif isinstance(completion_signal, int):
                        data_len = completion_signal
                        self.sel.unregister(pipe_stdout_r)
                        completed = True

                        # there could still be data in stderr, so we return
                        # to waiting until the process ends
                    else:
                        raise ValueError("Unrecognized signal received from "
                                         "MPI child")

        # cleanup the selector
        self.sel.unregister(pipe_stderr_r)
        self.sel.close()

        # done with stdout and stderr
        os.close(pipe_stdout_r)
        os.close(pipe_stdout_w)
        os.close(pipe_stderr_r)
        os.close(pipe_stderr_w)

        # if simulation failed, raise exception
        if proc.returncode != 0:
            raise RuntimeError("MPI simulation failed")

        sim_data = self._process_child_data(self.proc_data_bytes, data_len)

        dpls = _gather_trial_data(sim_data, net, n_trials, postproc)
        return dpls
