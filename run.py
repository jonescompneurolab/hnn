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
import json
import numpy as np
# Cells are defined in other files
from  paramrw import usingOngoingInputs, write_gids_param
import specfn as specfn
#import pickle
import datetime
from conf import readconf
from L5_pyramidal import L5Pyr
from L2_pyramidal import L2Pyr
from L2_basket import L2Basket
from L5_basket import L5Basket

import os.path as op

from hnn_core import simulate_dipole, read_params, Network, MPIBackend, read_spikes
from hnn_core.dipole import average_dipoles

dconf = readconf()

# # save somatic voltage of all cells to pkl object
# def save_vsoma ():
#   for host in range(int(pc.nhost())):
#     if host == get_rank():
#       dsoma = net.get_vsoma()
#       messageid = pc.pack(dsoma) # create a message ID and store this value
#       pc.post(host,messageid) # post the message
#   if get_rank()==0:
#     dsomaout = {}
#     for host in range(int(pc.nhost())):
#       pc.take(host)
#       dsoma_node = pc.upkpyobj()
#       for k,v in dsoma_node.items(): dsomaout[k] = v
#     dsomaout['vtime'] = t_vec.to_python()
#     # print('dsomaout.keys():',dsomaout.keys(),'file:',doutf['file_vsoma'])
#     pickle.dump(dsomaout,open(doutf['file_vsoma'],'wb'))


def setupsimdir (params):
  simdir = os.path.join(dconf['datdir'], params['sim_prefix'])
  try:
    os.mkdir(simdir)
  except FileExistsError:
    pass

  return simdir

def getfname (ddir,key,trial=0,ntrial=1):
  datatypes = {'rawspk': ('spk','.txt'),
               'rawdpl': ('rawdpl','.txt'),
               'normdpl': ('dpl','.txt'), # same output name - do not need both raw and normalized dipole - unless debugging
               'rawcurrent': ('i','.txt'),
               'rawspec': ('rawspec','.npz'),
               'rawspeccurrent': ('speci','.npz'),
               'avgdpl': ('dplavg','.txt'),
               'avgspec': ('specavg','.npz'),
               'figavgdpl': ('dplavg','.png'),
               'figavgspec': ('specavg','.png'),
               'figdpl': ('dpl','.png'),
               'figspec': ('spec','.png'),
               'figspk': ('spk','.png'),
               'param': ('param','.txt'),
               'vsoma': ('vsoma','.pkl'),
               'lfp': ('lfp', '.txt')
             }
  if ntrial == 1 or key == 'param': # param file currently identical for all trials
    return os.path.join(ddir,datatypes[key][0]+datatypes[key][1])
  else:
    return os.path.join(ddir,datatypes[key][0] + '_' + str(trial) + datatypes[key][1])
    

def expandbbox (boxA, boxB):
  return [(min(boxA[i][0],boxB[i][0]),max(boxA[i][1],boxB[i][1]))  for i in range(3)]

def arrangelayers (net):
  # NOTE: will not work with hnn-core as-is. this code modifies NetworkBuilder attributes

  # offsets for L2, L5 cells so that L5 below L2 in display
  dyoff = {L2Pyr: 1000, 'L2_pyramidal' : 1000,
           L5Pyr: -1000-149.39990234375, 'L5_pyramidal' : -1000-149.39990234375,
           L2Basket: 1000, 'L2_basket' : 1000,
           L5Basket: -1000-149.39990234375, 'L5_basket' : -1000-149.39990234375}
  for cell in net.cells: cell.translate3d(0,dyoff[cell.celltype],0)
  dbbox = {x:[[1e9,-1e9],[1e9,-1e9],[1e9,-1e9]] for x in dyoff.keys()}
  for cell in net.cells:
    dbbox[cell.celltype] = expandbbox(dbbox[cell.celltype], cell.getbbox())

# All units for time: ms
def simulate (params, n_core):

  # create the network from the parameter file. note, NEURON objects haven't been created yet
  net = Network(params)

  # TODO: add arrangelayers() to hnn-core or remove
  # arrange cells in layers - for visualization purposes
  # arrangelayers(net)
  ddir = setupsimdir(params)

  # run the simulation with MPI because the user is waiting for it to complete
  with MPIBackend(n_procs=n_core, mpi_cmd='mpiexec'):
    dpls = simulate_dipole(net, params['N_trials'])

  ntrial = len(dpls)
  # save average dipole from individual trials in a single file
  if ntrial > 1:
    avg_dpl = average_dipoles(dpls)
  elif ntrial == 1:
    avg_dpl = dpls[0]
  else:
    raise RuntimeError("No dipole(s) rertuned from simulation")

  # TODO: rawdpl in hnn-core
  avg_dpl.write(os.path.join(ddir, 'dpl.txt'))

  # HNN workflow requires some files to be written to disk. This sets up the directory for all output files
  ddir = setupsimdir(params)

  # now write the files
  params.write(os.path.join(ddir, params['sim_prefix'] + '.json'))

  # TODO: Can below be removed if spk.txt is new hnn-core format with 3 columns (including spike type)?
  write_gids_param(getfname(ddir,'param'), net.gid_dict)

  # save spikes by trial
  net.spikes.write(os.path.join(ddir, 'spk_%d.txt'))

  # save spikes from the individual trials in a single file
  fout = os.path.join(ddir,'spk.txt')
  with open(fout, 'w') as fspkout:
    for trial_idx in range(len(net.spikes.times)):
      for spike_idx in range(len(net.spikes.times[trial_idx])):
        fspkout.write('{:.3f}\t{}\t{}\n'.format(
                      net.spikes.times[trial_idx][spike_idx],
                      int(net.spikes.gids[trial_idx][spike_idx]),
                      net.spikes.types[trial_idx][spike_idx]))

  # save average spectrogram from individual trials in a single file
  lf = [os.path.join(ddir,'rawspec_'+str(i)+'.npz') for i in range(ntrial)]
  dspecin = {}
  dout = {}
  try:
    for f in lf: dspecin[f] = np.load(f)
  except:
    return None
  for k in ['t_L5', 'f_L5', 't_L2', 'f_L2', 'time', 'freq']: dout[k] = dspecin[lf[0]][k]
  for k in ['TFR', 'TFR_L5', 'TFR_L2']: dout[k] = np.mean(np.array([dspecin[f][k] for f in lf]),axis=0)
  with open(os.path.join(ddir,'rawspec.npz'), 'wb') as fdpl:
    np.savez_compressed(fdpl,t_L5=dout['t_L5'],f_L5=dout['f_L5'],t_L2=dout['t_L2'],f_L2=dout['f_L2'],time=dout['time'],freq=dout['freq'],TFR=dout['TFR'],TFR_L5=dout['TFR_L5'],TFR_L2=dout['TFR_L2'])

  # save dipole for each trial and perform spectral analysis
  for trial_idx, dpl in enumerate(dpls):
    file_dipole =  getfname(ddir,'normdpl', trial_idx, params['N_trials'])
    dpl.write(file_dipole)

    # TODO: this should be moved to Network class within hnn-core
    # write the somatic current to a file
    # for now does not write the total but just L2 somatic and L5 somatic
    # X = np.r_[[dpl.t, net.current['L2Pyr_soma'].x, net.current['L5Pyr_soma'].x]].T
    # file_current = getfname(ddir, 'rawcurrent', trial_idx, params['N_trials'])
    # np.savetxt(file_current, X, fmt=['%3.3f', '%5.4f', '%5.4f'],
    #             delimiter='\t')

    # TODO: save_vsoma is coded to work in parallel, so it should be moved to
    # hnn_core.parallel_backends
    # if p['save_vsoma']:
    #   save_vsoma()

    if params['save_spec_data'] or usingOngoingInputs(params):
      spec_opts = {'type': 'dpl_laminar',
                    'f_max': params['f_max_spec'],
                    'save_data': 0,
                    'runtype': 'parallel',
                  }

      # run the spectral analysis
      specfn.analysis_simp(spec_opts, params, dpl,
                           getfname(ddir, 'rawspec', trial_idx, params['N_trials']))

    # NOTE: the savefigs functionality is quite complicated and rewriting from scratch in hnn-core is probably
    # a much better option that allows deprecating the large amount of legacy code
    # if params['save_figs']:
    #   savefigs(params) # save output figures