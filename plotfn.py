# plotfn.py - pall and possibly other plot routines
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: removed it.izip() dependence)
# last major: (SL: toward python3)

from praster import praster
import axes_create as ac
import dipolefn
import paramrw
import pspec
import specfn
import os
import fileio as fio
from multiprocessing import Pool

# terrible handling of variables
def pkernel(dfig, f_param, f_spk, f_dpl, f_spec, key_types, xlim=None, ylim=None):
  gid_dict, p_dict = paramrw.read(f_param)
  tstop = p_dict['tstop']
  # fig dirs
  dfig_dpl = dfig['figdpl']
  dfig_spec = dfig['figspec']
  dfig_spk = dfig['figspk']
  pdipole_dict = {
    'xlim': xlim,
    'ylim': ylim,
    # 'xmin': xlim[0],
    # 'xmax': xlim[1],
    # 'ymin': None,
    # 'ymax': None,
  }
  # plot kernels
  praster(f_param, tstop, f_spk, dfig_spk)
  dipolefn.pdipole(f_dpl, dfig_dpl, pdipole_dict, f_param, key_types)
  # dipolefn.pdipole(f_dpl, f_param, dfig_dpl, key_types, pdipole_dict)
  # usage of xlim to pspec is temporarily disabled. pspec_dpl() will use internal states for plotting
  pspec.pspec_dpl(f_spec, f_dpl, dfig_spec, p_dict, key_types, xlim, ylim, f_param)
  # pspec.pspec_dpl(f_spec, f_dpl, dfig_spec, p_dict, key_types)
  # pspec.pspec_dpl(data_spec, f_dpl, dfig_spec, p_dict, key_types, xlim)
  return 0

# Kernel for plotting dipole and spec with alpha feed histograms
def pkernel_with_hist(datdir, dfig, f_param, f_spk, f_dpl, f_spec, key_types, xlim=None, ylim=None):
  # gid_dict, p_dict = paramrw.read(f_param)
  # tstop = p_dict['tstop']
  # fig dirs
  dfig_dpl = datdir
  dfig_spec = datdir
  dfig_spk = datdir
  pdipole_dict = {
    'xmin': None,
    'xmax': None,
    'ymin': None,
    'ymax': None,
  }
  # plot kernels
  dipolefn.pdipole_with_hist(f_dpl, f_spk, dfig_dpl, f_param, key_types, pdipole_dict)
  pspec.pspec_with_hist(f_spec, f_dpl, f_spk, dfig_spec, f_param, key_types, xlim, ylim)
  return 0

# r is the value returned by pkernel
# this is sort of a dummy function
def cb(r): pass

# plot function - this is sort of a stop-gap and shouldn't live here, really
# reads all data except spec and gid_dict from files
def pallsimp (datdir, p_exp, doutf, xlim=None, ylim=None):
  key_types = p_exp.get_key_types()
  param_list = [doutf['file_param']]
  dpl_list = [doutf['file_dpl']] 
  spec_list = [doutf['file_spec']]
  spk_list = [doutf['file_spikes']]
  dfig_list = [{'figavgdpl': None, 'avgspec': None, 'param': None, 'normdpl': None, 'rawspk': None, 'rawspec': None, 'figavgspec': None, 'rawdpl': None, 'figdpl': None, 'rawcurrent': None, 'avgdpl': None, 'figspk': None, 'rawspeccurrent': None, 'figspec': None}]
  # print('dfig_list:',dfig_list)
  for dfig, f_param, f_spk, f_dpl, f_spec in zip(dfig_list, param_list, spk_list, dpl_list, spec_list):
    pkernel_with_hist(datdir, dfig, f_param, f_spk, f_dpl, f_spec, key_types, xlim, ylim)

# plot function - this is sort of a stop-gap and shouldn't live here, really
# reads all data except spec and gid_dict from files
def pall(datdir, ddir, p_exp, xlim=None, ylim=None):
  # def pall(ddir, p_exp, spec_results, xlim=[0., 'tstop']):
  # runtype allows easy (hard coded switching between two modes)
  # either 'parallel' or 'debug'
  # runtype = 'parallel'
  runtype = 'debug'
  dsim = ddir.dsim
  key_types = p_exp.get_key_types()
  # preallocate lists for use below
  param_list = []
  dpl_list = []
  spec_list = []
  spk_list = []
  dfig_list = []
  # aggregate all file types from individual expmts into lists
  # NB The only reason this works is because the analysis results are returned
  # IDENTICALLY!
  for expmt_group in ddir.expmt_groups:
    # these should be equivalent lengths
    param_list.extend(ddir.file_match(expmt_group, 'param'))
    dpl_list.extend(ddir.file_match(expmt_group, 'rawdpl'))
    spec_list.extend(ddir.file_match(expmt_group, 'rawspec'))
    spk_list.extend(ddir.file_match(expmt_group, 'rawspk'))
    # append as many copies of expmt dfig dict as there were runs in expmt
    # this must be done because we're iterating over ALL expmts at the same time
    for i in range(len(ddir.file_match(expmt_group, 'param'))):
      dfig_list.append(ddir.dfig[expmt_group])
  # create giant list of appropriate files and run them all at the same time
  if runtype is 'parallel':
    # apply async to compiled lists
    pl = Pool()
    for dfig, f_param, f_spk, f_dpl, f_spec in zip(dfig_list, param_list, spk_list, dpl_list, spec_list):
      pl.apply_async(pkernel, (dfig, f_param, f_spk, f_dpl, f_spec, key_types, xlim, ylim), callback=cb)
    pl.close()
    pl.join()
  elif runtype is 'debug':
    # run serially
    for dfig, f_param, f_spk, f_dpl, f_spec in zip(dfig_list, param_list, spk_list, dpl_list, spec_list):
      pkernel_with_hist(dfig, f_param, f_spk, f_dpl, f_spec, key_types, xlim, ylim)
      # pkernel(dfig, f_param, f_spk, f_dpl, f_spec, key_types, xlim, ylim)

# Plots dipole and spec with alpha feed histograms
def pdpl_pspec_with_hist(ddir, p_exp, xlim=None, ylim=None):
  # def pdpl_pspec_with_hist(ddir, p_exp, spec_results, xlim=[0., 'tstop']):
  # runtype = 'debug'
  runtype = 'parallel'
  # preallocate lists for use below
  param_list = []
  dpl_list = []
  spec_list = []
  spk_list = []
  dfig_list = []
  # Grab all necessary data in aggregated lists
  for expmt_group in ddir.expmt_groups:
    # these should be equivalent lengths
    param_list.extend(ddir.file_match(expmt_group, 'param'))
    dpl_list.extend(ddir.file_match(expmt_group, 'rawdpl'))
    spec_list.extend(ddir.file_match(expmt_group, 'rawspec'))
    spk_list.extend(ddir.file_match(expmt_group, 'rawspk'))
    # append as many copies of expmt dfig dict as there were runs in expmt
    for i in range(len(ddir.file_match(expmt_group, 'param'))):
      dfig_list.append(ddir.dfig[expmt_group])
  # grab the key types
  key_types = p_exp.get_key_types()
  print(spec_list)
  if runtype is 'parallel':
    # apply async to compiled lists
    pl = Pool()
    for dfig, f_param, f_spk, f_dpl, f_spec in zip(dfig_list, param_list, spk_list, dpl_list, spec_list):
      pl.apply_async(pkernel_with_hist, (dfig, f_param, f_spk, f_dpl, f_spec, key_types, xlim, ylim), callback=cb)
    pl.close()
    pl.join()
  elif runtype is 'debug':
    for dfig, f_param, f_spk, f_dpl, f_spec in zip(dfig_list, param_list, spk_list, dpl_list, spec_list):
      pkernel_with_hist(dfig, f_param, f_spk, f_dpl, f_spec, key_types, xlim, ylim)

def aggregate_spec_with_hist(ddir, p_exp, labels):
  untype = 'debug'
  # preallocate lists for use below
  param_list = []
  dpl_list = []
  spec_list = []
  spk_list = []
  dfig_list = []
  spec_list = []
  # Get dimensions for aggregate fig
  N_rows = len(ddir.expmt_groups)
  N_cols = len(ddir.file_match(ddir.expmt_groups[0], 'param'))
  # Create figure
  f = ac.FigAggregateSpecWithHist(N_rows, N_cols)
  # Grab all necessary data in aggregated lists
  for expmt_group in ddir.expmt_groups:
    # these should be equivalent lengths
    param_list.extend(ddir.file_match(expmt_group, 'param'))
    dpl_list.extend(ddir.file_match(expmt_group, 'rawdpl'))
    spec_list.extend(ddir.file_match(expmt_group, 'rawspec'))
    spk_list.extend(ddir.file_match(expmt_group, 'rawspk'))
  # apply async to compiled lists
  if runtype is 'parallel':
    pl = Pool()
    for f_param, f_spk, f_dpl, fspec, ax in zip(param_list, spk_list, dpl_list, spec_list, f.ax_list):
      _, p_dict = paramrw.read(f_param)
      pl.apply_async(specfn.aggregate_with_hist, (f, ax, fspec, f_dpl, f_spk, fparam, p_dict))
    pl.close()
    pl.join()
  elif runtype is 'debug':
    for f_param, f_spk, f_dpl, fspec, ax in zip(param_list, spk_list, dpl_list, spec_list, f.ax_list):
      # _, p_dict = paramrw.read(f_param)
      pspec.aggregate_with_hist(f, ax, fspec, f_dpl, f_spk, f_param)
  # add row labels
  f.add_row_labels(param_list, labels[0])
  # add column labels
  f.add_column_labels(param_list, labels[1])
  fig_name = os.path.join(ddir.dsim, 'aggregate_hist.png')
  f.save(fig_name)
  f.close()
