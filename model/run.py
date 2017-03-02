#!/usr/bin/env python
# run.py - primary run function for s1 project
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: removed izip, fixed an nhost bug)
# last major: (SL: toward python3)
# other branch for hnn

import os
import sys
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

# data directory - ./data
dproj = fio.return_data_dir()
simstr = ''
datdir = ''

debug = False 

# spike write function
def spikes_write (net, filename_spikes):
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
def copy_paramfile (dsim, f_psim, str_date):
  fout = os.path.join(dsim,f_psim.split(os.path.sep)[-1])
  shutil.copyfile(f_psim,fout)
  # open the new param file and append the date to it
  with open(fout, 'a') as f_param: f_param.write('\nRun_Date: %s' % str_date)

# callback function for printing out time during simulation run
printdt = 10
def prsimtime ():
  sys.stdout.write('\rSimulation time: {0} ms...'.format(round(h.t,2)))
  sys.stdout.flush()

#
def savedat (p,f_psim,ddir,rank,t_vec,dp_rec_L2,dp_rec_L5,net):
  # create rotating data files and dirs on ONE central node
  doutf = setoutfiles(ddir)
  # write time and calculated dipole to data file only if on the first proc
  # only execute this statement on one proc
  if rank == 0:
    # write the dipole
    with open(doutf['file_dpl'], 'a') as f:
      for k in range(int(t_vec.size())):
        f.write("%03.3f\t" % t_vec.x[k])
        f.write("%5.4f\t" % (dp_rec_L2.x[k] + dp_rec_L5.x[k]))
        f.write("%5.4f\t" % dp_rec_L2.x[k])
        f.write("%5.4f\n" % dp_rec_L5.x[k])
    # write the somatic current to the file
    # for now does not write the total but just L2 somatic and L5 somatic
    with open(doutf['file_current'], 'w') as fc:
      for t, i_L2, i_L5 in zip(t_vec.x, net.current['L2Pyr_soma'].x, net.current['L5Pyr_soma'].x):
        fc.write("%03.3f\t" % t)
        # fc.write("%5.4f\t" % (i_L2 + i_L5))
        fc.write("%5.4f\t" % i_L2)
        fc.write("%5.4f\n" % i_L5)
    # write params to the file
    paramrw.write(doutf['file_param'], p, net.gid_dict)
    if debug:
      with open(doutf['filename_debug'], 'w+') as file_debug:
        for m in range(int(t_vec.size())):
          file_debug.write("%03.3f\t%5.4f\n" % (t_vec.x[m], v_debug.x[m]))
      # also create a debug plot
      pdipole(doutf['filename_debug'], os.getcwd())
  # write output spikes
  file_spikes_tmp = fio.file_spike_tmp(dproj)
  spikes_write(net, file_spikes_tmp)
  # move the spike file to the spike dir
  if rank == 0:
    shutil.move(file_spikes_tmp, doutf['file_spikes'])

#
def runanalysis (ddir,p):
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

#
def savefigs (ddir,p,p_exp):
  print("Plot ...",)
  plot_start = time.time()
  # run plots and epscompress function
  # spec results is passed as an argument here
  # because it's not necessarily saved
  xlim_plot = (0., p['tstop'])
  plotfn.pall(ddir, p_exp, xlim_plot)
  print("time: %4.4f s" % (time.time() - plot_start))

#
def setupsimdir (f_psim,p_exp,rank):
  ddir = fio.SimulationPaths()
  ddir.create_new_sim(dproj, p_exp.expmt_groups, p_exp.sim_prefix)
  if rank==0:
    ddir.create_datadir()
    copy_paramfile(ddir.dsim, f_psim, ddir.str_date)
  return ddir

def getfname (ddir,key): return os.path.join(datdir,ddir._SimulationPaths__datatypes[key])

# create file names
def setoutfiles (ddir):
  doutf = {}
  doutf['file_dpl'] = getfname(ddir,'rawdpl')
  doutf['file_current'] = getfname(ddir,'rawcurrent')
  doutf['file_param'] = getfname(ddir, 'param')
  doutf['file_spikes'] = getfname(ddir, 'rawspk')
  doutf['file_spec'] = getfname(ddir, 'rawspec')
  doutf['filename_debug'] = 'debug.dat'
  return doutf

# All units for time: ms
def runsim (f_psim):
  t0 = time.time() # clock start time

  pc = h.ParallelContext()
  rank = int(pc.id()) # print(rank, pc.nhost())  
  p_exp = paramrw.ExpParams(f_psim) # creates p_exp.sim_prefix and other param structures
  ddir = setupsimdir(f_psim,p_exp,rank) # one directory for all experiments
  # core iterator through experimental groups
  expmt_group = p_exp.expmt_groups[0]

  p = p_exp.return_pdict(expmt_group, 0) # return the param dict for this simulation

  pc.barrier() # get all nodes to this place before continuing
  pc.gid_clear()
  
  # global variables, should be node-independent
  h("dp_total_L2 = 0."); h("dp_total_L5 = 0.")

  # if there are N_trials, then randomize the seed
  # establishes random seed for the seed seeder (yeah.)
  # this creates a prng_tmp on each, but only the value from 0 will be used
  prng_tmp = np.random.RandomState()
  if rank == 0:
    r = h.Vector(1, 0) # initialize vector to 1 element, with a 0
    prng_base = np.random.RandomState(rank)
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
  for param in p_exp.prng_seed_list: p[param] = prng_base.randint(1e9)

  # Set tstop before instantiating any classes
  h.tstop = p['tstop']; h.dt = p['dt'] # simulation duration and time-step
  # spike file needs to be known by all nodes
  file_spikes_tmp = fio.file_spike_tmp(dproj)  
  net = network.NetworkOnNode(p) # create node-specific network
  if debug: v_debug = net.rec_debug(0, 8) # net's method rec_debug(rank, gid)
  else: v_debug = None

  t_vec = h.Vector(); t_vec.record(h._ref_t) # time recording
  dp_rec_L2 = h.Vector(); dp_rec_L2.record(h._ref_dp_total_L2) # L2 dipole recording
  dp_rec_L5 = h.Vector(); dp_rec_L5.record(h._ref_dp_total_L5) # L5 dipole recording  
  pc.set_maxstep(10) # sets the default max solver step in ms (purposefully large)
  h.finitialize() # initialize cells to -65 mV, after all the NetCon delays have been specified
  if rank == 0: 
    for tt in range(0,int(h.tstop),printdt): h.cvode.event(tt, prsimtime) # print time callbacks
  h.fcurrent()  
  h.frecord_init() # set state variables if they have been changed since h.finitialize
  pc.psolve(h.tstop) # actual simulation - run the solver
  pc.allreduce(dp_rec_L2, 1); pc.allreduce(dp_rec_L5, 1) # combine dp_rec on every node, 1=add contributions together  
  net.aggregate_currents() # aggregate the currents independently on each proc
  # combine net.current{} variables on each proc
  pc.allreduce(net.current['L5Pyr_soma'], 1); pc.allreduce(net.current['L2Pyr_soma'], 1)

  # write time and calculated dipole to data file only if on the first proc
  # only execute this statement on one proc
  savedat(p,f_psim,ddir,rank,t_vec,dp_rec_L2,dp_rec_L5,net)

  if pc.nhost() > 1:
    pc.runworker()
    pc.done()
    t1 = time.time()
    if rank == 0:
      print("Simulation run time: %4.4f s" % (t1-t0))
      print("Simulation directory is: %s" % ddir.dsim)
  else:    
    t1 = time.time() # end clock time
    print("Simulation run time: %4.4f s" % (t1-t0))

  #runanalysis(ddir,p) # run spectral analysis
  #savefigs(ddir,p,p_exp) # save output figures

  if pc.nhost() > 1: h.quit()

if __name__ == "__main__":
  # reads the specified param file
  foundprm = False
  for i in range(len(sys.argv)):
    if sys.argv[i].endswith('.param'):
      f_psim = sys.argv[i]
      foundprm = True
      print('using ',f_psim,' param file.')
      break
  if not foundprm:
    f_psim = os.path.join('param','default.param')
    print(f_psim)
  simstr = f_psim.split(os.path.sep)[-1].split('.param')[0]
  datdir = os.path.join(dproj,simstr)
  runsim(f_psim)
