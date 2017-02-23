#!/usr/bin/env python
# run.py - primary run function for s1 project
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: removed izip, fixed an nhost bug)
# last major: (SL: toward python3)
# other branch for hnn

import os
import sys
sys.path.append(os.path.join(os.getcwd(), 'fn'))
import time
import shutil
import numpy as np
from neuron import h
h.load_file("stdrun.hoc")

# Cells are defined in other files
import network
import fileio as fio
import paramrw as paramrw
import plotfn as plotfn
import specfn as specfn

# spike write function
def spikes_write(net, filename_spikes):
    pc = h.ParallelContext()

    for rank in range(int(pc.nhost())):
        # guarantees node order and no competition
        pc.barrier()
        if rank == int(pc.id()):
            # net.spiketimes and net.spikegids are type h.Vector()
            L = int(net.spikegids.size())
            with open(filename_spikes, 'a') as file_spikes:
                for i in range(L):
                    file_spikes.write('%3.2f\t%d\n' % (net.spiketimes.x[i], net.spikegids.x[i]))

    # let all nodes iterate through loop in which only one rank writes
    pc.barrier()

# copies param file into root dsim directory
def copy_paramfile(dsim, f_psim, str_date):
    # assumes in this cwd, can use try/except in the future
    print(os.path.join(os.getcwd(), f_psim))
    paramfile = f_psim.split("/")[-1]
    paramfile_orig = os.path.join(os.getcwd(), f_psim)
    paramfile_sim = os.path.join(dsim, paramfile)

    shutil.copyfile(paramfile_orig, paramfile_sim)

    # open the new param file and append the date to it
    with open(paramfile_sim, 'a') as f_param:
        f_param.write('\nRun_Date: %s' % str_date)

# All units for time: ms
def exec_runsim(f_psim):
    # clock start time
    t0 = time.time()

    # dealing with multiple params - there is a lot of overhead to this
    # read the ranges of params and make up all combinations
    # for loop that changes these params serially, with different file names and whatnot
    # serial execution of each param file, since we're already doing charity here
    # copy the param file and write the param dict to a file for that specific sim.

    pc = h.ParallelContext()
    rank = int(pc.id())
    # print(rank, pc.nhost())

    # creates p_exp.sim_prefix and other param structures
    p_exp = paramrw.ExpParams(f_psim)

    # project directory
    dproj = fio.return_data_dir()
    # dproj = './repo/data/s1' # ...

    # one directory for all experiments
    if rank == 0:
        ddir = fio.SimulationPaths()
        ddir.create_new_sim(dproj, p_exp.expmt_groups, p_exp.sim_prefix)
        ddir.create_dirs()

        copy_paramfile(ddir.dsim, f_psim, ddir.str_date)

    # iterate through groups and through params in the group
    if rank == 0:
        N_expmt_groups = len(p_exp.expmt_groups)
        s = '%i total experimental group'

        # purely for vanity
        if N_expmt_groups > 1:
            s += 's'

        print(s % N_expmt_groups)

    # Set number of trials per unique simulation per experiment
    # if N_trials is set to 0, run 1 anyway!
    if not p_exp.N_trials:
        N_trialruns = 1

    else:
        N_trialruns = p_exp.N_trials

    # core iterator through experimental groups
    for expmt_group in p_exp.expmt_groups:
        if rank == 0:
            print("Experimental group: %s" % expmt_group)
            N_total_runs = p_exp.N_sims * N_trialruns

            # simulation times, to get a qnd avg
            t_sims = np.zeros(N_total_runs)

        # iterate through number of unique simulations
        for i in range(p_exp.N_sims):
            if rank == 0:
                t_expmt_start = time.time()

            # return the param dict for this simulation
            p = p_exp.return_pdict(expmt_group, i)

            # iterate through trialruns
            for j in range(N_trialruns):
                # get all nodes to this place before continuing
                # tries to ensure we're all running the same params at the same time!
                pc.barrier()
                pc.gid_clear()

                if rank == 0:
                    # create a compound index for all sims
                    n = i*N_trialruns+j

                    # trial start time
                    t_trial_start = time.time()

                    # print the run number
                    print("Run %i of %i" % (n, N_total_runs-1))

                # global variable bs, should be node-independent
                h("dp_total_L2 = 0.")
                h("dp_total_L5 = 0.")

                # if there are N_trials, then randomize the seed
                # establishes random seed for the seed seeder (yeah.)
                # this creates a prng_tmp on each, but only the value from 0 will be used
                prng_tmp = np.random.RandomState()

                if rank == 0:
                    # initialize vector to 1 element, with a 0
                    # v = h.Vector(Length, Init)
                    r = h.Vector(1, 0)

                    # seeds that come from prng_base are stereotyped
                    # these are seeded with seed rank! Blerg.
                    if not p_exp.N_trials:
                        prng_base = np.random.RandomState(rank)
                    else:
                        # Create a random seed value
                        r.x[0] = prng_tmp.randint(1e9)
                else:
                    # create the vector 'r' but don't change its init value
                    r = h.Vector(1, 0)

                # broadcast random seed value in r to everyone
                pc.broadcast(r, 0)

                # set object prngbase to random state for the seed value
                # other random seeds here will then be based on the gid
                prng_base = np.random.RandomState(int(r.x[0]))

                # seed list is now a list of seeds to be changed on each run
                # otherwise, its originally set value will remain
                # give a random int seed from [0, 1e9]
                for param in p_exp.prng_seed_list:
                    p[param] = prng_base.randint(1e9)

                # Set tstop before instantiating any classes
                h.tstop = p['tstop']
                h.dt = p['dt']

                # create prefix for files everyone knows about
                exp_prefix = p_exp.trial_prefix_str % (i, j)

                # spike file needs to be known by all nodes
                file_spikes_tmp = fio.file_spike_tmp(dproj)

                # Create network from net's Network class
                net = network.NetworkOnNode(p)

                # debug: off (0), on (1)
                debug = 0

                # create rotating data files and dirs on ONE central node
                if rank == 0:
                    # create file names
                    file_dpl = ddir.create_filename(expmt_group, 'rawdpl', exp_prefix)
                    file_current = ddir.create_filename(expmt_group, 'rawcurrent', exp_prefix)
                    file_param = ddir.create_filename(expmt_group, 'param', exp_prefix)
                    file_spikes = ddir.create_filename(expmt_group, 'rawspk', exp_prefix)
                    file_spec = ddir.create_filename(expmt_group, 'rawspec', exp_prefix)

                    # if debug is set to 1, this debug block will run
                    if debug:
                        # net's method rec_debug(rank, gid)
                        v_debug = net.rec_debug(0, 8)
                        filename_debug = 'debug.dat'

                # set t vec to record
                t_vec = h.Vector()
                t_vec.record(h._ref_t)

                # set dipoles to record
                dp_rec_L2 = h.Vector()
                dp_rec_L2.record(h._ref_dp_total_L2)

                # L5 dipole
                dp_rec_L5 = h.Vector()
                dp_rec_L5.record(h._ref_dp_total_L5)

                # sets the default max solver step in ms (purposefully large)
                pc.set_maxstep(10)

                # initialize cells to -65 mV and compile code
                # after all the NetCon delays have been specified
                # and run the solver
                h.finitialize()
                h.fcurrent()

                # set state variables if they have been changed since h.finitialize
                h.frecord_init()

                # actual simulation
                pc.psolve(h.tstop)

                # combine dp_rec, this combines on every proc
                # 1 refers to adding the contributions together
                pc.allreduce(dp_rec_L2, 1)
                pc.allreduce(dp_rec_L5, 1)

                # aggregate the currents independently on each proc
                net.aggregate_currents()

                # combine the net.current{} variables on each proc
                pc.allreduce(net.current['L5Pyr_soma'], 1)
                pc.allreduce(net.current['L2Pyr_soma'], 1)

                # write time and calculated dipole to data file only if on the first proc
                # only execute this statement on one proc
                if rank == 0:
                    # write the dipole
                    with open(file_dpl, 'a') as f:
                        for k in range(int(t_vec.size())):
                        # for i, t in enumerate(t_vec):
                            # write t, total dipole, L2 dipole, L5 dipole
                            f.write("%03.3f\t" % t_vec.x[k])
                            f.write("%5.4f\t" % (dp_rec_L2.x[k] + dp_rec_L5.x[k]))
                            f.write("%5.4f\t" % dp_rec_L2.x[k])
                            f.write("%5.4f\n" % dp_rec_L5.x[k])

                    # write the somatic current to the file
                    # for now does not write the total but just L2 somatic and L5 somatic
                    with open(file_current, 'w') as fc:
                        for t, i_L2, i_L5 in zip(t_vec.x, net.current['L2Pyr_soma'].x, net.current['L5Pyr_soma'].x):
                            fc.write("%03.3f\t" % t)
                            # fc.write("%5.4f\t" % (i_L2 + i_L5))
                            fc.write("%5.4f\t" % i_L2)
                            fc.write("%5.4f\n" % i_L5)

                    # write the params, but add some more information
                    p['Sim_No'] = i
                    p['Trial'] = j
                    p['exp_prefix'] = exp_prefix

                    # write params to the file
                    paramrw.write(file_param, p, net.gid_dict)

                    if debug:
                        with open(filename_debug, 'w+') as file_debug:
                            for m in range(int(t_vec.size())):
                                file_debug.write("%03.3f\t%5.4f\n" % (t_vec.x[m], v_debug.x[m]))

                        # also create a debug plot
                        pdipole(filename_debug, os.getcwd())

                # write output spikes
                spikes_write(net, file_spikes_tmp)

                # move the spike file to the spike dir
                if rank == 0:
                    shutil.move(file_spikes_tmp, file_spikes)
                    t_sims[n] = time.time() - t_trial_start
                    print("... finished in: %4.4f s" % (t_sims[n]))

        # completely superficial
        if rank == 0:
            # print qnd mean
            print("Total runtime: %4.4f s, Mean runtime: %4.4f s" % (np.sum(t_sims), np.mean(t_sims)))

            # this prints a newline without having to specify it.
            print("")

    # plot should probably be moved outside of this
    if pc.nhost() > 1:
        pc.runworker()
        pc.done()

        t1 = time.time()
        if rank == 0:
            print("Simulation run time: %4.4f s" % (t1-t0))
            print("Simulation directory is: %s" % ddir.dsim)
            print("Analysis ...",)

            t_start_analysis = time.time()

            # run the spectral analysis
            spec_opts = {
                'type': 'dpl_laminar',
                'f_max': p['f_max_spec'],
                'save_date': 0,
                'runtype': 'parallel',
            }

            specfn.analysis_typespecific(ddir, spec_opts)

            print("time: %4.4f s" % (time.time() - t_start_analysis))
            print("Plot ...",)

            plot_start = time.time()

            # run plots and epscompress function
            # spec results is passed as an argument here
            # because it's not necessarily saved
            xlim_plot = (0., p['tstop'])
            plotfn.pall(ddir, p_exp, xlim_plot)

            # do the relevant png optimization
            # fio.pngoptimize(ddir.dsim)

            print("time: %4.4f s" % (time.time() - plot_start))

        h.quit()

    else:
        # end clock time
        t1 = time.time()
        print("Simulation run time: %4.4f s" % (t1-t0))

if __name__ == "__main__":
  # reads the specified param file
  if len(sys.argv) > 1:
    f_psim = sys.argv[1]
  else:
    f_psim = "param/default.param"
    print("Using param/default.param")
  exec_runsim(f_psim)
