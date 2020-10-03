"""File with functions and classes for running the NEURON """

# Authors: Blake Caldwell <blake_caldwell@brown.edu>
#          Sam Neymotin <samnemo@gmail.com>
#          Shane Lee

import os.path as op
import os
import numpy as np
from paramrw import usingOngoingInputs, write_gids_param
import specfn as specfn

from hnn_core import simulate_dipole, Network, MPIBackend
from hnn_core.dipole import average_dipoles


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
                 'vsoma': ('vsoma', '.pkl'),
                 'lfp': ('lfp', '.txt')}

    if ntrial == 1 or key == 'param':
        # param file currently identical for all trials
        return op.join(sim_dir, datatypes[key][0] + datatypes[key][1])
    else:
        return op.join(sim_dir, datatypes[key][0] + '_' + str(trial) +
                            datatypes[key][1])


def simulate(params, data_dir, n_procs=None):
    """Start the simulation with hnn_core.simulate

    Parameters
    ----------
    params : dict
        The parameters
    data_dir : str
        The base path for storing output files (e.g. ~/hnn_out/data)

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
            specfn.analysis_simp(spec_opts, params, dpl,
                                 get_fname(sim_dir, 'rawspec', trial_idx,
                                          params['N_trials']))

        # NOTE: the savefigs functionality is quite complicated and rewriting
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
