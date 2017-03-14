from configparser import ConfigParser
import io
import pickle
import os
try:
  from StringIO import StringIO
except ImportError:
  from io import StringIO

# default config as string
def_config = """
[params]
[run]
[sim]
simf = run.py
paramf = param/default.param
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
def readconf (fn="netcfg.cfg"):
  config = ConfigParser()
  config.optionxform = str
  #config.read(fn)
  
  with open(fn, 'r') as cfg_file:
    cfg_txt = os.path.expandvars(cfg_file.read())

  #config = ConfigParser.ConfigParser()
  #config.readfp(StringIO.StringIO(cfg_txt))
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

  def getlparam (base, ty):
    lout = []
    if not config.has_section(base): return lout
    lin = config.options(base)    
    """
    if config.has_option(base,'fpath'):
      fn = config.get(base,'fpath')
      d = pickle.load(open(fn))
      print('read dprm from ' , fn)
      return d    
    """
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
  #d['params'] = getparamd('params') # param values optimized by evolution
  #d['fixed'] = getparamd('fixed') # optional fixed values, assigned prior to assignment of evolutionary params

  d['simf'] = confstr('sim','simf','run.py')
  d['paramf'] = confstr('sim','paramf',os.path.join('param','default.param'))

  d['dlg'] = getlparam('dialog', dlgparam)
  d['tab'] = getlparam('tab', tabparam)
  d['param'] = getlparam('param', param)

  """
  recstr = confstr('run','recordV','')
  d['recordV'] = recstr.split(',') # voltage recording locations
  d['recordSpike'] = confstr('run','recordSpike','')
  d['tstop'] = conffloat('run','tstop',2000)
  d['baset'] = conffloat('run','baset',500)
  d['stimdel'] = conffloat('run','stimdel',500)
  d['stimdur'] = conffloat('run','stimdur',1000)
  d['postassign'] = confstr('run','postassign','')
  d['usecvode'] = confbool('run','usecvode','True')
  d['cellimport'] = confstr('run','cellimport','geom')
  d['cellfunc'] = confstr('run','cellfunc','makecell')
  d['useallspikes'] = confbool('run','useallspikes','False')
  d['cellfuncargs'] = confstr('run','cellfuncargs','') # eg if cellfuncargs is (1,2,3) will call makecell(1,2,3)
  d['isivolts'] = confstr('data','isivolts','')
  d['evolts'] = confstr('data','evolts','')
  d['onvolts'] = confstr('data','onvolts','')
  d['offvolts'] = confstr('data','offvolts','')
  d['spikevolts'] = confstr('data','spikevolts','')
  d['spiket'] = confstr('data','spiket','')
  d['sampr'] = conffloat('data','sampr',10000)
  d['lstimamp'] = confstr('data','lstimamp','')
  """

  return d

