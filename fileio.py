# fileio.py - general file input/output functions
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: return_data_dir() instead of hardcoded everywhere, etc.)
# last rev: (SL: toward python3)

import datetime, fnmatch, os, shutil, sys
import subprocess, multiprocessing
import numpy as np
import paramrw

# creates data dirs and a dictionary of useful types
# self.dfig is a dictionary of experiments, which is each a dictionary of data type
# keys and the specific directories that contain them.
class SimulationPaths ():
  def __init__ (self):
    # hard coded data types
    # fig extensions are not currently being used as well as they could be
    # add new directories here to be automatically created for every simulation
    self.__datatypes = {'rawspk': 'spk.txt',
                        'rawdpl': 'rawdpl.txt',
                        'normdpl': 'dpl.txt', # same output name - do not need both raw and normalized dipole - unless debugging
                        'rawcurrent': 'i.txt',
                        'rawspec': 'spec.npz',
                        'rawspeccurrent': 'speci.npz',
                        'avgdpl': 'dplavg.txt',
                        'avgspec': 'specavg.npz',
                        'figavgdpl': 'dplavg.png',
                        'figavgspec': 'specavg.png',
                        'figdpl': 'dpl.png',
                        'figspec': 'spec.png',
                        'figspk': 'spk.png',
                        'param': 'param.txt',
                      }
    # empty until a sim is created or read
    self.fparam = None
    self.sim_prefix = None
    self.trial_prefix_str = None
    self.expmt_groups = []
    self.dproj = None
    self.ddate = None
    self.dsim = None
    self.dexpmt_dict = {}
    self.dfig = {}

  # reads sim information based on sim directory and param files
  def read_sim (self, dproj, dsim):
    self.dproj = dproj
    self.dsim = dsim
    # match the param from this sim
    self.fparam = file_match(dsim, '.param')[0]
    self.expmt_groups = paramrw.read_expmt_groups(self.fparam)
    self.sim_prefix = paramrw.read_sim_prefix(self.fparam)
    # this should somehow be supplied by the ExpParams() class, but doing it here
    self.trial_prefix_str = self.sim_prefix + "-%03d-T%02d"
    self.dexpmt_dict = self.__create_dexpmt(self.expmt_groups)
    # create dfig
    self.dfig = self.__read_dirs()
    return self.dsim

  # only run for the creation of a new simulation
  def create_new_sim (self, dproj, expmt_groups, sim_prefix='test'):
    self.dproj = dproj
    self.expmt_groups = expmt_groups
    # prefix for these simulations in both filenames and directory in ddate
    self.sim_prefix = sim_prefix
    # create date and sim directories if necessary
    self.ddate = self.__datedir()
    self.dsim = self.__simdir()
    self.dexpmt_dict = self.__create_dexpmt(self.expmt_groups)
    # dfig is just a record of all the fig directories, per experiment
    # will only be written to at time of creation, by create_dirs
    # dfig is a terrible variable name, sorry!
    self.dfig = self.__ddata_dict_template()

  # this is a hack
  # checks root expmt_group directory for any files i've thrown there
  def find_aggregate_file (self, expmt_group, datatype):
    # file name is in format: '%s-%s-%s' % (sim_prefix, expmt_group, datatype-ish)
    fname = '%s-%s-%s.txt' % (self.sim_prefix, expmt_group, datatype)
    # get a list of txt files in the expmt_group
    # local=1 forces the search to be local to this directory and not recursive
    local = 1
    flist = file_match(self.dexpmt_dict[expmt_group], fname, local)
    return flist

  # returns a filename for an example type of data
  def return_filename_example (self, datatype, expmt_group, sim_no=None, tr=None, ext='png'):
    fname_short = "%s-%s" % (self.sim_prefix, expmt_group)
    if sim_no is not None: fname_short += "-%03i" % (sim_no)
    if tr is not None: fname_short += "-T%03i" % (tr)
    # add the extension
    fname_short += ".%s" % (ext)
    fname = os.path.join(self.dfig[expmt_group][datatype], fname_short)
    return fname

  # creates a dict of dicts for each experiment and all the datatype directories
  # this is the empty template that gets filled in later.
  def __ddata_dict_template (self):
    dfig = dict.fromkeys(self.expmt_groups)
    for key in dfig: dfig[key] = dict.fromkeys(self.__datatypes)
    return dfig

  # read directories for an already existing sim
  def __read_dirs (self):
    dfig = self.__ddata_dict_template()
    for expmt_group, dexpmt in self.dexpmt_dict.items():
      for key in self.__datatypes.keys():
        ddatatype = os.path.join(dexpmt, key)
        dfig[expmt_group][key] = ddatatype
    return dfig

  # create the data directory for the sim
  def create_datadir (self):
    dout = self.__simdir()
    if not safemkdir(dout):
      print("ERR: could not create output dir",dout)

  # extern function to create directories
  def create_dirs (self):
    # create expmt directories
    for expmt_group, dexpmt in self.dexpmt_dict.items():
      dir_create(dexpmt)
      for key in self.__datatypes.keys():
        ddatatype = os.path.join(dexpmt, key)
        self.dfig[expmt_group][key] = ddatatype
        dir_create(ddatatype)

  # Returns date directory
  # this is NOT safe for midnight
  def __datedir (self):
    self.str_date = datetime.datetime.now().strftime("%Y-%m-%d")
    ddate = os.path.join(self.dproj, self.str_date)
    return ddate

  # returns the directory for the sim
  def __simdir (self): return os.path.join(os.path.expanduser('~'),'hnn','data',self.sim_prefix)

  # creates all the experimental directories based on dproj
  def __create_dexpmt (self, expmt_groups):
    d = dict.fromkeys(expmt_groups)
    for expmt_group in d: d[expmt_group] = os.path.join(self.dsim, expmt_group)
    return d

  # dictionary creation
  # this is specific to a expmt_group
  def create_dict (self, expmt_group):
    fileinfo = dict.fromkeys(self.__datatypes)
    for key in self.__datatypes.keys():
      # join directory name
      dtype = os.path.join(self.dexpmt_dict(expmt_group), key)
      fileinfo[key] = (self.__datatypes[key], dtype)
    return fileinfo

  def return_specific_filename(self, expmt_group, datatype, n_sim, n_trial):
    f_list = self.file_match(expmt_group, datatype)
    trial_prefix = self.trial_prefix_str % (n_sim, n_trial)
    # assume there is only one match (this should be true)
    f_datatype = [f for f in f_list if trial_prefix in f][0]
    return f_datatype

  # requires dict lookup
  def create_filename (self, expmt_group, key):
    d = self.__simdir()
    # some kind of if key in self.fileinfo.keys() catch
    file_name_raw = self.__datatypes[key]
    return os.path.join(d,file_name_raw)
    # grab the whole experimental directory
    dexpmt = self.dexpmt_dict[expmt_group]
    # create the full path name for the file
    file_path_full = os.path.join(dexpmt, key, file_name_raw)
    return file_path_full

  # Get the data files matching file_ext in this directory
  # functionally the same as the previous function but with a local scope
  def file_match (self, expmt_group, key):
    # grab the relevant fext
    fext = self.__datatypes[key]
    file_list = []
    ddata = self.__simdir() # 
    # search the sim directory for all relevant files
    if os.path.exists(ddata):
      for root, dirnames, filenames in os.walk(ddata):
        for fname in fnmatch.filter(filenames, '*'+fext): file_list.append(os.path.join(root, fname))
    # sort file list? untested
    file_list.sort()
    return file_list

  def exp_files_of_type (self, datatype):
    # create dict of experiments
    d = dict.fromkeys(self.expmt_groups)
    # create file lists that match the dict keys for only files for this experiment
    # this all would be nicer with a freaking folder
    for key in d: d[key] = [file for file in self.filelists[datatype] if key in file.split("/")[-1]]
    return d

# Cleans input files
def clean_lines (file):
  with open(file) as f_in:
    lines = (line.rstrip() for line in f_in)
    lines = [line for line in lines if line]
  return lines

# this make a little more sense in fileio
def prettyprint (iterable_items):
  for item in iterable_items: print(item)

# create gid dict from a file
def gid_dict_from_file (fparam):
  l = ['L2_pyramidal', 'L5_pyramidal', 'L2_basket', 'L5_basket', 'extinput']
  d = dict.fromkeys(l)
  plist = clean_lines(fparam)
  for param in plist: print(param)

# create file name for temporary spike file
# that every processor is aware of
def file_spike_tmp (dproj):
  filename_spikes = 'spikes_tmp.spk'
  file_spikes = os.path.join(dproj, filename_spikes)
  return file_spikes

# this is ugly, potentially. sorry, future
# i.e will change when the file name format changes
def strip_extprefix (filename):
  f_raw = filename.split("/")[-1]
  f = f_raw.split(".")[0].split("-")[:-1]
  ext_prefix = f.pop(0)
  for part in f: ext_prefix += "-%s" % part
  return ext_prefix

# Get the data files matching file_ext in this directory
# this function traverses ALL directories
# local=1 makes the search local and not recursive
def file_match (dsearch, file_ext, local=0):
  file_list = []
  if not local:
    if os.path.exists(dsearch):
      for root, dirnames, filenames in os.walk(dsearch):
        for fname in fnmatch.filter(filenames, '*'+file_ext):
          file_list.append(os.path.join(root, fname))
  else:
    file_list = [os.path.join(dsearch, file) for file in os.listdir(dsearch) if file.endswith(file_ext)]
  # sort file list? untested
  file_list.sort()
  return file_list

# Get minimum list of param dicts (i.e. excludes duplicates due to N_trials > 1)
def fparam_match_minimal (dsim, p_exp):
  # Complete list of all param dicts used in simulation
  fparam_list_complete = file_match(dsim, '-param.txt')
  # List of indices from which to pull param dicts from fparam_list_complete
  N_trials = p_exp.N_trials
  if not N_trials: N_trials = 1
  indexes = np.arange(0, len(fparam_list_complete), N_trials)
  # Pull unique param dicts from fparam_list_complete
  fparam_list_minimal = [fparam_list_complete[ind] for ind in indexes]
  return fparam_list_minimal

# check any directory
def dir_check (d):
  if not os.path.isdir(d): return 0
  else: return os.path.isdir(d)

# only create if check comes back 0
def dir_create (d):
  if not dir_check(d): os.makedirs(d)

# non-destructive copy routine
def dir_copy (din, dout):
  # this command should work on most posix systems
  cmd_cp = 'cp -R %s %s' % (din, dout)
  # if the dir doesn't already exist, copy it over
  if not dir_check(dout):
    # print the actual command when successful
    print(cmd_cp)
    # use call to run the command
    subprocess.call(cmd_cp, shell=True)
    return 0
  else:
    print("Directory already exists.")

# Finds and moves files to created subdirectories.
def subdir_move (dir_out, name_dir, file_pattern):
  dir_name = os.path.join(dir_out, name_dir)
  # create directories that do not exist
  if not os.path.isdir(dir_name): os.mkdir(dir_name)
  for filename in glob.iglob(os.path.join(dir_out, file_pattern)): shutil.move(filename, dir_name)

# currently used only minimally in epscompress
# need to figure out how to change argument list in cmd as below
def cmds_runmulti (cmdlist):
  n_threads = multiprocessing.cpu_count()
  list_runs = [cmdlist[i:i+n_threads] for i in range(0, len(cmdlist), n_threads)]
  # open devnull for writing extraneous output
  with open(os.devnull, 'w') as devnull:
    for sublist in list_runs:
      procs = [subprocess.Popen(cmd, stdout=devnull, stderr=devnull) for cmd in sublist]
      for proc in procs: proc.wait()

# small kernel for png optimization based on fig directory
def pngoptimize (dfig):
  local = 0
  pnglist = file_match(dfig, '.png', local)
  cmds_opti = [('optipng', pngfile) for pngfile in pnglist]
  cmds_runmulti(cmds_opti)

# list spike raster eps files and then rasterize them to HQ png files, lossless compress,
# reencapsulate as eps, and remove backups when successful
def epscompress (dfig_spk, fext_figspk, local=0):
  cmds_gs = []
  cmds_opti = []
  cmds_encaps = []
  n_threads = multiprocessing.cpu_count()
  # lists of eps files and corresponding png files
  # fext_figspk, dfig_spk = fileinfo['figspk']
  epslist = file_match(dfig_spk, fext_figspk, local)
  pnglist = [f.replace('.eps', '.png') for f in epslist]
  epsbackuplist = [f.replace('.eps', '.bak.eps') for f in epslist]
  # create command lists for gs, optipng, and convert
  for pngfile, epsfile in zip(pnglist, epslist):
    cmds_gs.append(('gs -r300 -dEPSCrop -dTextAlphaBits=4 -sDEVICE=png16m -sOutputFile=%s -dBATCH -dNOPAUSE %s' % (pngfile, epsfile)))
    cmds_opti.append(('optipng', pngfile))
    cmds_encaps.append(('convert %s eps3:%s' % (pngfile, epsfile)))
  # create procs list of manageable lists and run
  runs_gs = [cmds_gs[i:i+n_threads] for i in range(0, len(cmds_gs), n_threads)]
  # run each sublist differently
  for sublist in runs_gs:
    procs_gs = [subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for cmd in sublist]
    for proc in procs_gs: proc.wait()
  # create optipng procs list and run
  cmds_runmulti(cmds_opti)
  # backup original eps files temporarily
  for epsfile, epsbakfile in zip(epslist, epsbackuplist): shutil.move(epsfile, epsbakfile)
  # recreate original eps files, now encapsulated, optimized rasters
  # cmds_runmulti(cmds_encaps)
  runs_encaps = [cmds_encaps[i:i+n_threads] for i in range(0, len(cmds_encaps), n_threads)]
  for sublist in runs_encaps:
    procs_encaps = [subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE) for cmd in sublist]
    for proc in procs_encaps: proc.wait()
  # remove all of the backup files
  for epsbakfile in epsbackuplist: os.remove(epsbakfile)

# make dir, catch exceptions
def safemkdir (dn):
  try:
    os.mkdir(dn)
    return True
  except OSError:
    if not os.path.exists(dn):
      print('ERR: could not create', dn)
      return False
    else:
      return True

# returns the data dir
def return_data_dir ():
  dfinal = os.path.join('.','data')
  if not safemkdir(dfinal): sys.exit(1)
  return dfinal

if __name__ == '__main__':
  return_data_dir()
