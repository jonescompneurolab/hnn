from math import log, exp

"""
from neuron import h
# h.load_file("stdrun.hoc")
import numpy
from pylab import *
from time import time, clock
import os
from conf import dconf
import pickle

dprm = dconf['params']
sampr = dconf['sampr'] # 10KHz sampling rate in txt,npy file (data/15jun12_BS0284_subthreshandspikes_A0.npy)

vtime = h.Vector()
vtime.record(h._ref_t)

tinit = 0.0
tstop = h.tstop

gtmp=h.Vector()

#
def myrun (reconfig=True,inj=0.0,prtime=False):
  if reconfig: safereconfig() # makes sure params set within cell
  stim.amp = inj
  if prtime: clockStart = time()
  # h.run()
  if prtime:
    clockEnd = time()
    print('\nsim runtime:',str(round(clockEnd-clockStart,2)),'secs')

y = h.Vector()
drawOut = False

#
def readdat (sampr=10e3):
  dat = numpy.load(dconf['evolts']) #numpy.load('data/15jun12_BS0284_subthreshandspikes_A0.npy')
  etime = numpy.linspace(0,dat.shape[0]*1e3/sampr,dat.shape[0])
  return dat,etime

dat,etime = readdat(sampr) # dim 1 is voltage

intert = 3000 # 3000 ms in between clamps
offt = 500 # 500 ms before start of first clamp
durt = 1000 # 1000 ms current clamp
padt = 500 # pad around clamp 

#
def getindices (tdx):
  sidx = sampr*(offt/1e3+tdx*(intert+durt)/1e3) - sampr * padt / 1e3
  eidx = sidx + durt * sampr / 1e3 + 2 * sampr * padt / 1e3
  return sidx,eidx

#
def cuttrace (dat,tdx):
  sidx,eidx = getindices(tdx)
  if catdat:
    return dat[sidx:eidx,1], etime[sidx:eidx]
  else:
    return dat[:,tdx],etime

Vector = h.Vector
Iexp = lstimamp = numpy.load(dconf['lstimamp']) # [-0.15+j*0.05 for j in xrange(nstims_fi)]
nstims_fi = len(Iexp) # was 7
alltrace = [i for i in xrange(nstims_fi)]
targSpikes = numpy.load(dconf['spiket']) # just using this for spike frequency - not timing!!
Fexp = [len(arr) for arr in targSpikes] # assumes 1 s stimulus duration
ltracedxsubth = [i for i in xrange(len(Fexp)) if Fexp[i] <= 0.0 and Iexp[i] != 0.0]
ltrace=ltracedxsubth

def issubth (tdx): return ltracedxsubth.count(tdx) > 0
def issuperth (tdx): return not issubth(tdx)

# simple normalization - with a maximum cap
def getnormval (val,maxval,scale=1.0):
  if val > maxval: return scale
  return scale * val / maxval


# interpolate voltage recorded in simulation to a fixed grid (dt millisecond spacing)
# output time,voltage is returned
def interpvolt (tsrc=vtime,vsrc=vsoma,dt=0.1,tshift=tinit,tend=tstop):
  tdest = h.Vector(); tdest.indgen(tshift,tend,dt)
  vdest = h.Vector(); vdest.interpolate(tdest,tsrc,vsrc)
  tdest.sub(tshift)
  return tdest, vdest

tracedx = 0 # which trace to fit (trace index)

#
def plotinterp (vtime,vval,clr):
  it,ival = interpvolt(vtime,vval,1e3/sampr)
  plot(it.as_numpy(),ival.as_numpy(),clr)

#
def voltcompare (tdx,interponly=True,dcurr=None,xl=None):
  if dcurr is not None: subplot(2,1,1)
  dd,tt = cuttrace(dat,tdx)
  tt = linspace(0,tt[-1]-tt[0],len(tt))
  plot(tt,dd,'b')
  if not interponly: plot(vtime.as_numpy(),vsoma.as_numpy(),'r')
  it,iv = interpvolt(vtime,vsoma,1e3/sampr)
  plot(it.as_numpy(),iv.as_numpy(),'r')
  legend(['experiment','simulation'],loc='best')
  xlabel('Time (ms)',fontsize=16); ylabel('Vm',fontsize=16);
  if xl is not None: xlim(xl)
  if dcurr is not None: 
    subplot(2,1,2)
    plotinterp(vtime,dcurr['ina'],'r')
    plotinterp(vtime,dcurr['ik'],'b')
    plotinterp(vtime,dcurr['ica'],'g')
    plotinterp(vtime,dcurr['cai'],'y')
    plotinterp(vtime,dcurr['ih'],'k')
    legend(['ina','ik','ica','cai','ih'],loc='best')
    if xl is not None: xlim(xl)

prtime = True # print simulation duration?

lparam = [p for p in dprm.values()]; 

def lparamindex (lp,s):
  for i,p in enumerate(lp):
    if p.var == s: return i
  return -1

#
def prmnames (): return [prm.var for prm in lparam]

# clamps nval (which is between 0,1) to valid param range
def clampval (prm, nval):
  if nval < 0.0: return prm.minval
  elif nval > 1.0: return prm.maxval
  else: return prm.minval + (prm.maxval - prm.minval) * nval

#
def clampvals (vec,lparam): return [clampval(prm,x) for prm,x in zip(lparam,vec)] 
"""

# exponentiates value
def expval (prm, val):
  if prm.minval > 0: return exp(val)
  elif prm.maxval < 0: return -exp(val)
  else: return val

#
def expvals (vec,lparam): return [expval(prm,x) for prm,x in zip(lparam,vec)] 

#
def logval (prm, val):
  if prm.minval > 0: return log(val)
  elif prm.maxval < 0: return log(-val)
  else: return val

#
def logvals (vec,lparam): return [logval(prm,x) for prm,x in zip(lparam,vec)] 


"""
#
def assignparams (vparam,lparam,useExp=False):
  if useExp:
    for prm,val in zip(lparam,expvals(vparam,lparam)): # set parameters
      exec(prm.assignstr(val))
  else:
    for prm,val in zip(lparam,vparam): # set parameters
      exec(prm.assignstr(val))

#
def assignrow (nqp, row):
  if row < 0 or row >= nqp.v[0].size(): return None
  nprm = int(nqp.m[0]) - 2 # -2 for idx,err
  vprm = []
  for col in xrange(nprm): vprm.append(nqp.v[col].x[row])
  assignparams(vprm,lparam)
  safereconfig()
  return vprm

#
def printparams (vparam,lparam,useExp=False):
  if useExp:
    for prm,val in zip(lparam,expvals(vparam,lparam)): print(prm.var, ' = ' , val) # set parameters      
  else:
    for prm,val in zip(lparam,vparam): print(prm.var, ' = ' , val) # set parameters      

myerrfunc = None # error function

# create an empty NQS with parameter and error columns
def makeprmnq ():
  lp = prmnames() 
  nqp = h.NQS()
  for s in lp: 
    if type(s) == list:
      nqp.resize(s[0])
    else:
      nqp.resize(s)
  nqp.resize('idx'); nqp.resize('err'); nqp.clear(1e3)
  return nqp

# append parameter values and error to the NQS
def appendprmnq (nqp,vprm,err):
  for i,x in enumerate(vprm): nqp.v[i].append(x)
  sz = nqp.v[0].size()
  nqp.getcol('idx').append(nqp.v[0].size()-1)
  nqp.getcol('err').append(err)

nqp = makeprmnq()

#
def traceerr ():
  toterr = 0.0 # total error across traces
  for tracedx in ltrace:
    print('stim.amp is ', lstimamp[tracedx])
    myrun(reconfig=False,inj=lstimamp[tracedx]) # 
    if drawOut: voltcompare(tracedx)
    err = myerrfunc(tracedx)
    print('err is ' , round(err,6))
    toterr += err
  return toterr

# errwrap - assigns params (xp are param values), evaluates and returns error (uses traceerr)
def errwrap (xp):
  assignparams(xp,lparam,useExp=False)
  printparams(xp,lparam,useExp=False)
  safereconfig()
  toterr = traceerr()
  print('toterr is ' , toterr)
  return toterr

# optimization run - for an individual set of params specified in vparam 
# NB: vparam contains the log of actual param values, & the meaning of params is specified in global lparam
def optrun (vparam):
  if prtime: clockStart = time()
  global tracedx, ltrace
  for prm,val in zip(lparam,expvals(vparam,lparam)): # set parameters
    if val >= prm.minval and val <= prm.maxval:
      exec(prm.assignstr(val))
    else:
      print(val, 'out of bounds for ' , prm.var, prm.minval, prm.maxval)
      appendprmnq(nqp,expvals(vparam,lparam),1e9)
      return 1e9
  if type(vparam)==list: print('set params:', vparam)
  else: print('set params:', vparam.as_numpy())
  safereconfig() # make sure parameters are set in cell
  toterr = traceerr() # total error across traces
  if prtime:
    clockEnd = time()
    print('\nsim runtime:',str(round(clockEnd-clockStart,2)),'secs')
  print('toterr is ' , round(toterr/len(ltrace),6))
  appendprmnq(nqp,expvals(vparam,lparam),toterr / len(ltrace))
  return toterr / len(ltrace) # average

# run sims specified in ltrace and plot comparison of voltages
def voltcomprun (ltrace=None,prtime=False):
  if ltrace is None: ltrace = ltracedxsubth
  for tracedx in ltrace:
    myrun(reconfig=False,inj=lstimamp[tracedx],prtime=prtime) 
    voltcompare(tracedx)  

# mean squared error of voltage
lvoltwin = [] # can use to specify time ranges for volterr
lvoltscale = [] # can use to scale errors (matches to lvoltwin indices)

#
def volterr (tdx):
  it,iv = interpvolt(vtime,vsoma,1e3/sampr)
  dd,tt = cuttrace(dat,tdx)
  npt = len(dd)
  if it.size() > npt: it.resize(npt)
  err = 0; ivnp = iv.as_numpy()
  if len(lvoltwin) > 0:
    if len(lvoltscale) > 0:
      npt = 0; 
      for voltwin,fctr in zip(lvoltwin,lscale):
        sidx,eidx = int(voltwin[0]*sampr/1e3),int(voltwin[1]*sampr/1e3)
        npt += (eidx-sidx+1)
        for idx in xrange(sidx,eidx+1,1): err += fctr * (ivnp[idx] - dd[idx])**2
    else:
      npt = 0; 
      for voltwin in lvoltwin:
        sidx,eidx = int(voltwin[0]*sampr/1e3),int(voltwin[1]*sampr/1e3)
        npt += (eidx-sidx+1)
        for idx in xrange(sidx,eidx+1,1): err += (ivnp[idx] - dd[idx])**2
  else:
    for v1,v2 in zip(ivnp,dd): err += (v1-v2)**2
  return sqrt(err/npt)

# scaled error, scale individual functions, then combine
useV =  False;
scaleV = zeros((len(lstimamp),))

myerrfunc = volterr

# randomized optimization - search random points in param space
def randopt (lparam,nstep,errfunc,saveevery=0,fout=None):
  global myerrfunc, nqp
  myerrfunc = errfunc
  for i in xrange(nstep):
    print('step ' , i+1 , ' of ' , nstep)
    vparam = [p.minval + random.uniform() * (p.maxval-p.minval) for p in lparam]
    vplog = [logval(p,x) for p,x in zip(lparam,vparam)]
    optrun(vplog)
    if fout is not None and saveevery > 0 and i%saveevery==0: nqp.sv(fout)
  if fout is not None: nqp.sv(fout)

# performs praxis optimization using specified params and error function (errfunc)
def praxismatch (vparam,nstep,tol,stepsz,errfunc):
  global myerrfunc, nqp
  h.nqsdel(nqp)
  nqp = makeprmnq()
  myerrfunc = errfunc
  print('using these traces:', ltrace)
  h.attr_praxis(tol, stepsz, 3)
  h.stop_praxis(nstep) # 
  return h.fit_praxis(optrun, vparam)

# use praxis to match voltage traces
def voltmatch (vparam,nstep=10,tol=0.001,stepsz=0.5):
  global tstop
  if len(lvoltwin) > 0:
    tstop = tinit + amax(lvoltwin)
    print('reset tstop to ' , tstop)
  return praxismatch(vparam,nstep,tol,stepsz,volterr)

# get the original param values (stored in lparam)
def getparamorig ():
  vparam = h.Vector()
  for p in lparam: vparam.append( logval(p,p.origval) )
  return vparam

# get random param values (from the set stored in lparam)
def getparamrand (seed):
  rdm = h.Random()
  rdm.ACG(seed)
  vparam = h.Vector()
  for p in lparam: vparam.append( logval(p, rdm.uniform(p.minval,p.maxval)) )
  return vparam

# get 'best' param values found (from opt)
def getparambest ():
  vparam = h.Vector()
  for p in lparam: vparam.append( logval(p,p.bestval) )
  return vparam

def runsaveopt ():
  global ltrace,nqp,vparam
  vparam = getparambest(); 
  assignparams(vparam,lparam,useExp=True); 
  safereconfig(); 
  # lvoltwin = [[495.0,750.0]]
  ltrace=ltracedxsubth
  voltmatch(vparam,nstep=dconf['nstep'],tol=dconf['tol']);
  nqp.sv(dconf['nqp'])
  dconf['vparam'] = vparam.to_python() # output parameter values
  dconf['lparam'] = lparam 
  pickle.dump(dconf,open(dconf['dout'],'w')) # save everything

if __name__ == '__main__':
  if dconf['runopt']: runsaveopt()
"""
