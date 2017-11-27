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
from paramrw import usingOngoingInputs
import plotfn as plotfn
import specfn as specfn
import pickle
from dipolefn import Dipole
from conf import readconf
from L5_pyramidal import L5Pyr
from L2_pyramidal import L2Pyr
from L2_basket import L2Basket
from L5_basket import L5Basket
from lfp import LFPElectrode
from morphology import shapeplot, getshapecoords

dconf = readconf()

# data directory - ./data
dproj = dconf['datdir'] # fio.return_data_dir(dconf['datdir'])
debug = dconf['debug']
pc = h.ParallelContext()
pcID = int(pc.id())
f_psim = ''
ntrial = 1
testLFP = dconf['testlfp']; 
testlaminarLFP = dconf['testlaminarlfp']
lelec = [] # list of LFP electrodes

# reads the specified param file
foundprm = False
for i in range(len(sys.argv)):
  if sys.argv[i].endswith('.param'):
    f_psim = sys.argv[i]
    foundprm = True
    if pcID==0 and debug: print('using ',f_psim,' param file.')
  elif sys.argv[i] == 'ntrial' and i+1<len(sys.argv):
    ntrial = int(sys.argv[i+1])
    if ntrial < 1: ntrial = 1
    if pcID==0 and debug: print('ntrial:',ntrial)

if not foundprm:
  f_psim = os.path.join('param','default.param')
  if pcID==0 and debug: print(f_psim)

simstr = f_psim.split(os.path.sep)[-1].split('.param')[0]
datdir = os.path.join(dproj,simstr)

# spike write function
def spikes_write (net, filename_spikes):
  f = open(filename_spikes,'w')
  f.close() # first make sure writes to an empty file
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

# save somatic voltage of all cells to pkl object
def save_vsoma ():
  for host in range(int(pc.nhost())):
    if host == pcID:
      dsoma = net.get_vsoma()
      messageid = pc.pack(dsoma) # create a message ID and store this value
      pc.post(host,messageid) # post the message
  if pcID==0:
    dsomaout = {}
    for host in range(int(pc.nhost())):
      pc.take(host)
      dsoma_node = pc.upkpyobj()
      for k,v in dsoma_node.items(): dsomaout[k] = v
    dsomaout['vtime'] = t_vec.to_python()
    # print('dsomaout.keys():',dsomaout.keys(),'file:',doutf['file_vsoma'])
    pickle.dump(dsomaout,open(doutf['file_vsoma'],'wb'))

#
def savedat (p, rank, t_vec, dp_rec_L2, dp_rec_L5, net):
  global doutf
  # write time and calculated dipole to data file only if on the first proc
  # only execute this statement on one proc
  if rank == 0:
    # write params to the file
    paramrw.write(doutf['file_param'], p, net.gid_dict)
    # write the raw dipole
    with open(doutf['file_dpl'], 'w') as f:
      for k in range(int(t_vec.size())):
        f.write("%03.3f\t" % t_vec.x[k])
        f.write("%5.4f\t" % (dp_rec_L2.x[k] + dp_rec_L5.x[k]))
        f.write("%5.4f\t" % dp_rec_L2.x[k])
        f.write("%5.4f\n" % dp_rec_L5.x[k])
    # renormalize the dipole and save
    dpl = Dipole(doutf['file_dpl']) # fix to allow init from data rather than file
    dpl.baseline_renormalize(doutf['file_param'])
    dpl.convert_fAm_to_nAm()
    dconf['dipole_scalefctr'] = dpl.scale(paramrw.find_param(doutf['file_param'],'dipole_scalefctr'))
    dpl.smooth(paramrw.find_param(doutf['file_param'],'dipole_smooth_win')/h.dt)
    dpl.write(doutf['file_dpl_norm'])
    # write the somatic current to the file
    # for now does not write the total but just L2 somatic and L5 somatic
    with open(doutf['file_current'], 'w') as fc:
      for t, i_L2, i_L5 in zip(t_vec.x, net.current['L2Pyr_soma'].x, net.current['L5Pyr_soma'].x):
        fc.write("%03.3f\t" % t)
        # fc.write("%5.4f\t" % (i_L2 + i_L5))
        fc.write("%5.4f\t" % i_L2)
        fc.write("%5.4f\n" % i_L5)
  # write output spikes
  file_spikes_tmp = fio.file_spike_tmp(dproj)
  spikes_write(net, file_spikes_tmp)
  # move the spike file to the spike dir
  if rank == 0: shutil.move(file_spikes_tmp, doutf['file_spikes'])
  if p['save_vsoma']: save_vsoma()
  for i,elec in enumerate(lelec):
    elec.lfpout(fn=doutf['file_lfp'].split('.txt')[0]+'_'+str(i)+'.txt',tvec = t_vec)

#
def runanalysis (prm, fparam, fdpl, fspec):
  if pcID==0: print("Running spectral analysis...",)
  spec_opts = {'type': 'dpl_laminar',
               'f_max': prm['f_max_spec'],
               'save_data': 0,
               'runtype': 'parallel',
             }
  t_start_analysis = time.time()
  specfn.analysis_simp(spec_opts, fparam, fdpl, fspec) # run the spectral analysis
  if pcID==0 and debug: print("time: %4.4f s" % (time.time() - t_start_analysis))

#
def savefigs (ddir, prm, p_exp):
  print("Saving figures...",)
  plot_start = time.time()
  # run plots and epscompress function
  # spec results is passed as an argument here
  # because it's not necessarily saved
  xlim_plot = (0., prm['tstop'])
  plotfn.pallsimp(datdir, p_exp, doutf, xlim_plot)
  if debug: print("time: %4.4f s" % (time.time() - plot_start))

#
def setupsimdir (f_psim,p_exp,rank):
  ddir = fio.SimulationPaths()
  ddir.create_new_sim(dproj, p_exp.expmt_groups, p_exp.sim_prefix)
  if rank==0:
    ddir.create_datadir()
    copy_paramfile(ddir.dsim, f_psim, ddir.str_date)
  return ddir

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
    return os.path.join(datdir,datatypes[key][0]+datatypes[key][1])
  else:
    return os.path.join(datdir,datatypes[key][0] + '_' + str(trial) + datatypes[key][1])
    

# create file names
def setoutfiles (ddir,trial=0,ntrial=1):
  # if pcID==0: print('setoutfiles:',trial,ntrial)
  doutf = {}
  doutf['file_dpl'] = getfname(ddir,'rawdpl',trial,ntrial)
  doutf['file_current'] = getfname(ddir,'rawcurrent',trial,ntrial)
  doutf['file_param'] = getfname(ddir, 'param',trial,ntrial)
  doutf['file_spikes'] = getfname(ddir, 'rawspk',trial,ntrial)
  doutf['file_spec'] = getfname(ddir, 'rawspec',trial,ntrial)
  doutf['filename_debug'] = 'debug.dat'
  doutf['file_dpl_norm'] = getfname(ddir,'normdpl',trial,ntrial)
  doutf['file_vsoma'] = getfname(ddir,'vsoma',trial,ntrial)
  doutf['file_lfp'] = getfname(ddir,'lfp',trial,ntrial)
  # if pcID==0: print(doutf)
  return doutf

p_exp = paramrw.ExpParams(f_psim, debug=debug) # creates p_exp.sim_prefix and other param structures
ddir = setupsimdir(f_psim,p_exp,pcID) # one directory for all experiments
# create rotating data files
doutf = setoutfiles(ddir)
# core iterator through experimental groups
expmt_group = p_exp.expmt_groups[0]

simparams = p = p_exp.return_pdict(expmt_group, 0) # return the param dict for this simulation

pc.barrier() # get all nodes to this place before continuing
pc.gid_clear()

# global variables, should be node-independent
h("dp_total_L2 = 0."); h("dp_total_L5 = 0.")

# Set tstop before instantiating any classes
h.tstop = p['tstop']; h.dt = p['dt'] # simulation duration and time-step
h.celsius = p['celsius'] # 37.0 # p['celsius'] # set temperature
# spike file needs to be known by all nodes
file_spikes_tmp = fio.file_spike_tmp(dproj)  
net = network.NetworkOnNode(p) # create node-specific network

t_vec = h.Vector(); t_vec.record(h._ref_t) # time recording
dp_rec_L2 = h.Vector(); dp_rec_L2.record(h._ref_dp_total_L2) # L2 dipole recording
dp_rec_L5 = h.Vector(); dp_rec_L5.record(h._ref_dp_total_L5) # L5 dipole recording  

net.movecellstopos() # position cells in 2D grid

def expandbbox (boxA, boxB):
  return [(min(boxA[i][0],boxB[i][0]),max(boxA[i][1],boxB[i][1]))  for i in range(3)]

def arrangelayers ():
  # offsets for L2, L5 cells so that L5 below L2 in display
  dyoff = {L2Pyr: 1000, 'L2_pyramidal' : 1000,
           L5Pyr: -1000-149.39990234375, 'L5_pyramidal' : -1000-149.39990234375,
           L2Basket: 1000, 'L2_basket' : 1000,
           L5Basket: -1000-149.39990234375, 'L5_basket' : -1000-149.39990234375}
  for cell in net.cells: cell.translate3d(0,dyoff[cell.celltype],0)
  dcheck = {x:False for x in dyoff.keys()}
  dbbox = {x:[[1e9,-1e9],[1e9,-1e9],[1e9,-1e9]] for x in dyoff.keys()}
  for cell in net.cells:

    dbbox[cell.celltype] = expandbbox(dbbox[cell.celltype], cell.getbbox())
    #if dcheck[cell.celltype]: continue
    """
    bbox = cell.getbbox()
    lx,ly,lz = getshapecoords(h,cell.get_sections())  
    if cell.celltype == L2Pyr or cell.celltype == 'L2_pyramidal':
      print('L2Pyr bbox:',bbox)#,lx,ly,lz)
    elif cell.celltype == L5Pyr or cell.celltype == 'L5_pyramidal':
      print('L5Pyr bbox:',bbox)#,lx,ly,lz)
    elif cell.celltype == L2Basket or cell.celltype == 'L2_basket':
      print('L2Basket bbox:',bbox)#,lx,ly,lz)
    elif cell.celltype == L5Basket or cell.celltype == 'L5_basket':
      print('L5Basket bbox:',bbox)#,lx,ly,lz)
    dcheck[cell.celltype]=True
    """
  # for ty in ['L2_basket', 'L2_pyramidal', 'L5_basket', 'L5_pyramidal']: print(ty, dbbox[ty])

arrangelayers() # arrange cells in layers - for visualization purposes

pc.barrier()

# save spikes from the individual trials in a single file
def catspks ():
  lf = [os.path.join(datdir,'spk_'+str(i)+'.txt') for i in range(ntrial)]
  if debug: print('catspk lf:',lf)
  lspk = [[],[]]
  for f in lf:
    xarr = np.loadtxt(f)
    for i in range(2):
      lspk[i].extend(xarr[:,i])
    if debug: print('xarr.shape:',xarr.shape)
  lspk = np.array(lspk).T
  # lspk.sort(axis=1) # not multidim sort - can fix if want spikes across trials in temporal order
  fout = os.path.join(datdir,'spk.txt')
  with open(fout, 'w') as fspkout:
    for i in range(lspk.shape[0]):
      fspkout.write('%3.2f\t%d\n' % (lspk[i,0], lspk[i,1]))
  if debug: print('lspk.shape:',lspk.shape)
  return lspk

# save average dipole from individual trials in a single file
def catdpl ():
  ldpl = []
  for pre in ['dpl','rawdpl']:
    lf = [os.path.join(datdir,pre+'_'+str(i)+'.txt') for i in range(ntrial)]
    dpl = np.mean(np.array([np.loadtxt(f) for f in lf]),axis=0)
    with open(os.path.join(datdir,pre+'.txt'), 'w') as fp:
      for i in range(dpl.shape[0]):
        fp.write("%03.3f\t" % dpl[i,0])
        fp.write("%5.8f\t" % dpl[i,1])
        fp.write("%5.8f\t" % dpl[i,2])
        fp.write("%5.8f\n" % dpl[i,3])
    ldpl.append(dpl)
  return ldpl

# save average spectrogram from individual trials in a single file
def catspec ():
  lf = [os.path.join(datdir,'rawspec_'+str(i)+'.npz') for i in range(ntrial)]
  dspecin = {}
  dout = {}
  try:
    for f in lf: dspecin[f] = np.load(f)
  except:
    return None
  for k in ['t_L5', 'f_L5', 't_L2', 'f_L2', 'time', 'freq']: dout[k] = dspecin[lf[0]][k]
  for k in ['TFR', 'TFR_L5', 'TFR_L2']: dout[k] = np.mean(np.array([dspecin[f][k] for f in lf]),axis=0)
  with open(os.path.join(datdir,'rawspec.npz'), 'wb') as fdpl:
    np.savez_compressed(fdpl,t_L5=dout['t_L5'],f_L5=dout['f_L5'],t_L2=dout['t_L2'],f_L2=dout['f_L2'],time=dout['time'],freq=dout['freq'],TFR=dout['TFR'],TFR_L5=dout['TFR_L5'],TFR_L2=dout['TFR_L2'])
  return dout

# gather trial outputs via either raw concatenation or averaging
def cattrialoutput ():
  global doutf
  lspk = catspks() # concatenate spikes from different trials to a single file
  ldpl = catdpl()
  dspec = catspec()
  del lspk,ldpl,dspec # do not need these variables; returned for testing

# run individual trials via runsim, then calc/save average dipole/specgram
# evinputinc is an increment (in milliseconds) that gets added to the evoked inputs on each
# successive trial. the default value is 0.0.
def runtrials (ntrial, inc_evinput=0.0):
  global doutf
  if pcID==0: print('Running', ntrial, 'trials.')
  for i in range(ntrial):
    if pcID==0: print('Running trial',i+1,'...')
    doutf = setoutfiles(ddir,i,ntrial)
    # initrands(ntrial+(i+1)**ntrial) # reinit for each trial
    net.state_init() # initialize voltages
    runsim() # run the simulation
    net.reset_src_event_times(inc_evinput = inc_evinput * (i + 1)) # adjusts the rng seeds and then the feed/event input times
  doutf = setoutfiles(ddir,0,1) # reset output files based on sim name
  if pcID==0: cattrialoutput() # get/save the averages

def initrands (s=0): # fix to use s
  # if there are N_trials, then randomize the seed
  # establishes random seed for the seed seeder (yeah.)
  # this creates a prng_tmp on each, but only the value from 0 will be used
  prng_tmp = np.random.RandomState()
  if pcID == 0:
    r = h.Vector(1, s) # initialize vector to 1 element, with a 0
    if ntrial == 1:
      prng_base = np.random.RandomState(pcID + s)
    else:
      # Create a random seed value
      r.x[0] = prng_tmp.randint(1e9)
  else: r = h.Vector(1, s) # create the vector 'r' but don't change its init value
  pc.broadcast(r, 0) # broadcast random seed value in r to everyone
  # set object prngbase to random state for the seed value
  # other random seeds here will then be based on the gid
  prng_base = np.random.RandomState(int(r.x[0]))
  # seed list is now a list of seeds to be changed on each run
  # otherwise, its originally set value will remain
  # give a random int seed from [0, 1e9]
  for param in p_exp.prng_seed_list: # this list empty for single experiment/trial
    p[param] = prng_base.randint(1e9)
  # print('simparams[prng_seedcore]:',simparams['prng_seedcore'])
  

initrands(0) # init once

def setupLFPelectrodes ():
  lelec = []
  if testlaminarLFP:
    for y in np.linspace(1466.0,-72.0,16): lelec.append(LFPElectrode([370.0, y, 450.0], pc = pc))
  elif testLFP:
    lelec.append(LFPElectrode([370.0, 1050.0, 450.0], pc = pc))
    lelec.append(LFPElectrode([370.0, 208.0, 450.0], pc = pc))
  return lelec

lelec = setupLFPelectrodes()
  
# All units for time: ms
def runsim ():
  t0 = time.time() # clock start time

  pc.set_maxstep(10) # sets the default max solver step in ms (purposefully large)

  for elec in lelec:
    elec.setup()
    elec.LFPinit()

  h.finitialize() # initialize cells to -65 mV, after all the NetCon delays have been specified
  if pcID == 0: 
    for tt in range(0,int(h.tstop),printdt): h.cvode.event(tt, prsimtime) # print time callbacks
  
  h.fcurrent()  
  h.frecord_init() # set state variables if they have been changed since h.finitialize
  pc.psolve(h.tstop) # actual simulation - run the solver
  pc.barrier()

  # these calls aggregate data across procs/nodes
  pc.allreduce(dp_rec_L2, 1); 
  pc.allreduce(dp_rec_L5, 1) # combine dp_rec on every node, 1=add contributions together  
  for elec in lelec: elec.lfp_final()
  net.aggregate_currents() # aggregate the currents independently on each proc
  # combine net.current{} variables on each proc
  pc.allreduce(net.current['L5Pyr_soma'], 1); pc.allreduce(net.current['L2Pyr_soma'], 1)

  pc.barrier()

  # write time and calculated dipole to data file only if on the first proc
  # only execute this statement on one proc
  savedat(p, pcID, t_vec, dp_rec_L2, dp_rec_L5, net)

  for elec in lelec: print('end; t_vec.size()',t_vec.size(),'elec.lfp_t.size()',elec.lfp_t.size())

  if pcID == 0:
    if debug: print("Simulation run time: %4.4f s" % (time.time()-t0))
    if debug: print("Simulation directory is: %s" % ddir.dsim)    
    if paramrw.find_param(doutf['file_param'],'save_spec_data') or usingOngoingInputs(doutf['file_param']): 
      runanalysis(p, doutf['file_param'], doutf['file_dpl_norm'], doutf['file_spec']) # run spectral analysis
    if paramrw.find_param(doutf['file_param'],'save_figs'): savefigs(ddir,p,p_exp) # save output figures

  pc.barrier() # make sure all done in case multiple trials

if __name__ == "__main__":
  if dconf['dorun']:
    if ntrial > 1: runtrials(ntrial,p['inc_evinput'])
    else: runsim()
    pc.runworker()
    pc.done()
  if dconf['doquit']: h.quit()
