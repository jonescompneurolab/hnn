from configparser import ConfigParser
import io
import pickle
import os
import sys
from fileio import safemkdir

try:
  from StringIO import StringIO
except ImportError:
  from io import StringIO

# default config as string
def_config = """
[params]
[run]
dorun = 1
doquit = 1
debug = 0
testlfp = 0
testlaminarlfp = 0
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
[tips]
tstop = Simulation duration; Evoked response simulations typically take 170 ms while ongoing rhythms are run for longer.
dt = Simulation timestep - shorter timesteps mean more accuracy but longer runtimes.
"""

class baseparam:
  pass

class dlgparam (baseparam):
  def __init__ (self, title, dID, ntab):
    self.title = title # displayed text
    self.ID = dID # dialog ID
    self.ntab = ntab # number of tabs (-1 means not using tabs)

class tabparam (baseparam):
  def __init__ (self, title, dID, tID):
    self.title = title # displayed text
    self.dID = dID # dialog ID
    self.tID = tID # tab ID

class param (baseparam):
  def __init__ (self, title, dID, tID, val, ty, rng=None):
    self.title = title
    self.dID = dID
    self.tID = tID # tab ID (-1 means not in a tab)
    self.val = val # value
    self.ty = ty # type (0==number, 1==string)
    self.rng = rng
    if rng: self.bounded=True
    else: self.bounded=False

  # check if value is within bounds
  def inbounds (self,val):
    if not bounded: return True
    return val >= self.rng[0] and val <= self.rng[1]

  def __str__ (self):
    return str(self.val)

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
def readconf (fn="hnn.cfg"):
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

  def getlparam (base, ty):
    lout = []
    if not config.has_section(base): return lout
    lin = config.options(base)    

    for i,prm in enumerate(lin):
      s = config.get(base,prm)
      sp = s.split()
      try:
        lout.append( (prm, ty(*sp)) )
      except:
        print('config skipping ' , s)
        pass
    return lout

  lsec = config.sections()

  d = {}

  d['homeout'] = confint("paths","homeout",1) # whether user home directory for output

  d['simf'] = confstr('sim','simf','run.py')
  d['paramf'] = confstr('sim','paramf',os.path.join('param','default.param'))

  if d['homeout']: # user home directory for output
    dbase = os.path.join(os.path.expanduser('~'),'hnn') # user home directory
    if not safemkdir(dbase): sys.exit(1) # check existence of base hnn output dir
  else: # cwd for output
    dbase = os.getcwd() # use os.getcwd instead for better compatability with NSG

  d['datdir'] = os.path.join(dbase,'data') # data output directory
  d['paramoutdir'] = os.path.join(dbase, 'param')
  d['paramindir'] = confstr('paths','paramindir','param') # this depends on hnn install location  

  for k in ['datdir', 'paramindir', 'paramoutdir']: # need these directories
    if not safemkdir(d[k]): sys.exit(1)

  d['dorun'] = confint("run","dorun",1)
  d['doquit'] = confint("run","doquit",1)
  d['debug'] = confint("run","debug",0)
  d['testlfp'] = confint("run","testlfp",0)
  d['testlaminarlfp'] = confint("run","testlaminarlfp",0)

  d['drawindivdpl'] = confint("draw","drawindivdpl",1)
  d['drawindivrast'] = confint("draw","drawindivrast",1)
  d['fontsize'] = confint("draw","fontsize",0)

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
dconf = readconf(fcfg)


