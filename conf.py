from configparser import ConfigParser
import io
import pickle
import os
import sys
from collections import OrderedDict

try:
  from StringIO import StringIO
except ImportError:
  from io import StringIO

# default config as string
def_config = """
[run]
dorun = 1
doquit = 1
[paths]
paramindir = param
homeout = 1
[sim]
simf = run.py
paramf = param/default.param
[draw]
drawindivdpl = 1
drawindivrast = 1
fontsize = 0
drawavgdpl = 0
[tips]
tstop = Simulation duration; Evoked response simulations typically take 170 ms while ongoing rhythms are run for longer.
dt = Simulation timestep - shorter timesteps mean more accuracy but longer runtimes.
[opt]
decay_multiplier = 1.6
"""

# make dir, catch exceptions
def safemkdir (dn):
  try:
    os.mkdir(dn)
  except FileExistsError:
    pass
  except OSError:
    print('ERR: incorrect permissions for creating', dn)
    raise

  return True

# parameter used for optimization
class param:
  def __init__ (self, origval, minval, maxval, bounded, var, bestval=None):
    self.origval = origval
    self.minval = minval
    self.maxval = maxval
    self.bounded = bounded
    self.bestval = bestval
    if var.count(',') > 0: self.var = var.split(',')
    else: self.var = var
  def __str__ (self):
    sout = ''
    for s in [self.var, self.minval, self.maxval, self.origval, self.bounded, self.bestval]:
      sout += str(s)
      sout += ' '
    return sout
  def assignstr (self, val):  # generates string for execution
    if type(self.var) == list:
      astr = ''
      for var in self.var: astr += var + ' = ' + str(val) + ';'
      return astr
    else:
      return self.var + ' = ' + str(val)
  def inbounds (self,val):   # check if value is within bounds
    if not bounded: return True
    return val >= self.minval and val <= self.maxval
  # only return assignstr if val is within bounds
  def checkassign (self,val):
    if self.inbounds(val):
      return self.assignstr(val)
    else:
      return None

# write config file starting with defaults and new entries
# specified in section (sec) , option (opt), and value (val)
# saves to output filepath fn
def writeconf (fn,sec,opt,val):
  conf = ConfigParser()
  conf.readfp(io.BytesIO(def_config)) # start with defaults
  # then change entries by user-specs
  for i in range(len(sec)): conf.set(sec[i],opt[i],val[i])
  # write config file
  with open(fn, 'wb') as cfile: conf.write(cfile)

def str2bool (v): return v.lower() in ("true", "t", "1")

# read config file
def readconf (fn="hnn.cfg",nohomeout=False):
  config = ConfigParser()
  config.optionxform = str
  
  with open(fn, 'r') as cfg_file:
    cfg_txt = os.path.expandvars(cfg_file.read())

  config.readfp(StringIO(cfg_txt))

  def conffloat (base,var,defa): # defa is default value
    val = defa
    try: val=config.getfloat(base,var)
    except: pass
    return val

  def confint (base,var,defa):
    val = defa
    try: val=config.getint(base,var)
    except: pass
    return val

  def confstr (base,var,defa):
    val = defa
    try: val = config.get(base,var)
    except: pass
    return val

  def confbool (base,var,defa):
    return str2bool(confstr(base,var,defa))

  def readtips (d):
    if not config.has_section('tips'): return None
    ltips = config.options('tips')
    for i,prm in enumerate(ltips):
      d[prm] = config.get('tips',prm).strip()      

  d = {}

  d['homeout'] = confint("paths","homeout",1) # whether user home directory for output
  if nohomeout: d['homeout'] = 0 # override config file with commandline

  d['simf'] = confstr('sim','simf','run.py')
  d['paramf'] = confstr('sim','paramf',os.path.join('param','default.param'))


  # dbase - optional config setting to change base output directory
  if config.has_option('paths','dbase'):
    dbase = config.get('paths','dbase').strip()
    if not safemkdir(dbase): sys.exit(1) # check existence of base hnn output dir
  else:
    if d['homeout']: # user home directory for output
      if 'SYSTEM_USER_DIR' in os.environ:
        dbase = os.path.join(os.environ["SYSTEM_USER_DIR"],'hnn_out') # user home directory
      else:
        dbase = os.path.join(os.path.expanduser('~'),'hnn_out') # user home directory
      if not safemkdir(dbase): sys.exit(1) # check existence of base hnn output dir
    else: # cwd for output
      dbase = os.getcwd()

  d['dbase'] = dbase
  d['datdir'] = os.path.join(dbase,'data') # data output directory
  d['paramoutdir'] = os.path.join(dbase, 'param')
  d['paramindir'] = confstr('paths','paramindir','param') # this depends on hnn install location  
  d['dataf'] = confstr('paths','dataf','')

  for k in ['datdir', 'paramindir', 'paramoutdir']: # need these directories
    if not safemkdir(d[k]): sys.exit(1)

  d['dorun'] = confint("run","dorun",1)
  d['doquit'] = confint("run","doquit",1)

  d['drawindivdpl'] = confint("draw","drawindivdpl",1)
  d['drawavgdpl'] = confint("draw","drawavgdpl",0)
  d['drawindivrast'] = confint("draw","drawindivrast",1)
  d['fontsize'] = confint("draw","fontsize",0)

  d['decay_multiplier'] = conffloat('opt','decay_multiplier',1.6)

  readtips(d) # read tooltips for parameters

  return d

# determine config file name
def setfcfg ():
  fcfg = "hnn.cfg" # default config file name
  for i in range(len(sys.argv)):
    if sys.argv[i].endswith(".cfg") and os.path.exists(sys.argv[i]):
      fcfg = sys.argv[i]
  # print("hnn config file is " , fcfg)
  return fcfg

fcfg = setfcfg() # config file name
nohomeout = False
for i in range(len(sys.argv)):  # override homeout option through commandline flag
  if sys.argv[i] == '-nohomeout' or sys.argv[i] == 'nohomeout': nohomeout = True
dconf = readconf(fcfg,nohomeout)

