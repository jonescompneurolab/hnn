"""
LFPsim - Simulation scripts to compute Local Field Potentials (LFP) from cable compartmental
models of neurons and networks implemented in NEURON simulation environment.

LFPsim works reliably on biophysically detailed multi-compartmental neurons with ion channels in
some or all compartments.

Last updated 12-March-2016
Developed by : Harilal Parasuram & Shyam Diwakar
Computational Neuroscience & Neurophysiology Lab, School of Biotechnology, Amrita University, India.
Email: harilalp@am.amrita.edu; shyam@amrita.edu
www.amrita.edu/compneuro 

translated to Python and modified to use use_fast_imem by Sam Neymotin
based on mhines code
"""

from neuron import h
from math import sqrt, log, pi, exp
from seg3d import *
from pylab import *

# get all Sections
def getallSections (ty='Pyr'):
  ls = h.allsec()
  ls = [s for s in ls if s.name().count(ty)>0 or len(ty)==0]
  return ls

def getcoordinf (s):
  lcoord = []; ldist = []; lend = []; lsegloc = []
  if s.nseg == 1:
    i = 1
    x0, y0, z0 = s.x3d(i-1,sec=s), s.y3d(i-1, sec=s), s.z3d(i-1, sec=s)
    x1, y1, z1 = s.x3d(i,sec=s), s.y3d(i, sec=s), s.z3d(i, sec=s)
    lcoord.append([(x0+x1)/2.0,(y0+y1)/2.0,(z0+z1)/2.0])
    dist = sqrt((x1-x0)**2 + (y1-y0)**2 + (z1-z0)**2) 
    ldist.append( dist )    
    lend.append([x1, y1, z1])
    lsegloc.append(0.5)
  else:
    for i in range(1,s.n3d(),1):
      x0, y0, z0 = s.x3d(i-1,sec=s), s.y3d(i-1, sec=s), s.z3d(i-1, sec=s)
      x1, y1, z1 = s.x3d(i,sec=s), s.y3d(i, sec=s), s.z3d(i, sec=s)
      lcoord.append( [(x0+x1)/2.,(y0+y1)/2.(z0+z1)/2.] )
      dist = sqrt((x1-x0)**2 + (y1-y0)**2 + (z1-z0)**2) 
      ldist.append( dist )  
      lend.append([x1, y1, z1])
      lsegloc.append()
  return lcoord, ldist, lend, lsegloc

# this function not used ... yet
def transfer_resistance2 (exyz):
  vres = h.Vector()
  lsec = getallSections()
  sigma = 3.0 # extracellular conductivity in mS/cm
  # see http://jn.physiology.org/content/104/6/3388.long shows table of values with conductivity
  for s in lsec:
    lcoord, ldist, lend = getcoordinf(s)
    for i in range(len(lcoord)):      
      x,y,z = lcoord[i]
      dis = sqrt((exyz[0] - x)**2 + (exyz[1] - y)**2 + (exyz[2] - z)**2 )
      # setting radius limit
      if(dis<(s.diam/2.0)): dis = (s.diam/2.0) + 0.1

      dist_comp = ldist[i] # length of the compartment
      sum_dist_comp = sqrt(dist_comp[0]**2  + dist_comp[0]**2 + dist_comp[0]**2)

      # print "sum_dist_comp=",sum_dist_comp, secname()

      #  setting radius limit
      if sum_dist_comp < s.diam/2.0: sum_dist_comp = s.diam/2.0 + 0.1

      long_dist_x = exyz[0] - lend[i][0]
      long_dist_y = exyz[1] - lend[i][1]
      long_dist_z = exyz[2] - lend[i][2]

      sum_HH = long_dist_x*dist_comp_x + long_dist_y*dist_comp_y + long_dist_z*dist_comp_z

      final_sum_HH = sum_HH / sum_dist_comp

      sum_temp1 = long_dist_x**2 + long_dist_y**2 + long_dist_z**2
      r_sq = sum_temp1 - (final_sum_HH * final_sum_HH)

      Length_vector = final_sum_HH + sum_dist_comp                

      if final_sum_HH < 0 and Length_vector <= 0:
        phi=log((sqrt(final_sum_HH**2 + r_sq) - final_sum_HH)/(sqrt(Length_vector**2+r_sq)-Length_vector))
      elif final_sum_HH > 0  and Length_vector > 0:
        phi=log((sqrt(Length_vector**2+r_sq) + Length_vector)/(sqrt(final_sum_HH**2+r_sq) + final_sum_HH))
      else:
        phi=log(((sqrt(Length_vector**2+r_sq)+Length_vector) * (sqrt(final_sum_HH**2+r_sq)-final_sum_HH))/r_sq)

      line_part1 = 1.0 / (4.0*pi*sum_dist_comp*sigma) * phi 
      vres.append(line_part1)

  return vres

# represents a simple LFP electrode
class LFPElectrode ():

  def __init__ (self, coord, sigma = 3.0, pc = None, usePoint = True):

    self.sigma = sigma # extracellular conductivity in mS/cm (uniform for simplicity)
    # see http://jn.physiology.org/content/104/6/3388.long shows table of values with conductivity
    self.coord = coord
    self.vres = None
    self.vx = None

    self.imem_ptrvec = self.imem_vec = self.rx = self.vx = self.vres = None
    self.bscallback = self.fih = None

    if pc is None: self.pc = h.ParallelContext()
    else: self.pc = pc

  def setup (self):
    h.cvode.use_fast_imem(1) # enables fast calculation of transmembrane current (nA) at each segment 
    self.bscallback = h.beforestep_callback(h.cas()(.5))
    self.bscallback.set_callback(self.callback)
    fih = h.FInitializeHandler(1, self.LFPinit)

  def transfer_resistance (self, exyz,usePoint=True):
    vres = h.Vector()
    lsec = getallSections()
    for s in lsec:

      x = (h.x3d(0,sec=s) + h.x3d(1,sec=s)) / 2.0
      y = (h.y3d(0,sec=s) + h.y3d(1,sec=s)) / 2.0 
      z = (h.z3d(0,sec=s) + h.z3d(1,sec=s)) / 2.0 

      sigma = self.sigma

      dis = sqrt((exyz[0] - x)**2 + (exyz[1] - y)**2 + (exyz[2] - z)**2 )

      # setting radius limit
      if(dis<(s.diam/2.0)): dis = (s.diam/2.0) + 0.1

      if usePoint:
        point_part1 = 10000.0 * (1.0 / (4.0 * pi * dis * sigma)) # x10000 for units of microV : nA/(microm*(mS/cm)) -> microV
        vres.append(point_part1)
      else:
        # calculate length of the compartment
        dist_comp = sqrt((h.x3d(1,sec=s) - h.x3d(0,sec=s))**2 + (h.y3d(1,sec=s) - h.y3d(0,sec=s))**2 + (h.z3d(1,sec=s) - h.z3d(0,sec=s))**2)

        dist_comp_x = (h.x3d(1,sec=s) - h.x3d(0,sec=s)) 
        dist_comp_y = (h.y3d(1,sec=s) - h.y3d(0,sec=s)) 
        dist_comp_z = (h.z3d(1,sec=s) - h.z3d(0,sec=s)) 

        sum_dist_comp = sqrt(dist_comp_x**2  + dist_comp_y**2 + dist_comp_z**2)

        # print "sum_dist_comp=",sum_dist_comp, secname()

        #  setting radius limit
        if sum_dist_comp < s.diam/2.0: sum_dist_comp = s.diam/2.0 + 0.1

        long_dist_x = exyz[0] - h.x3d(1,sec=s)
        long_dist_y = exyz[1] - h.y3d(1,sec=s)
        long_dist_z = exyz[2] - h.z3d(1,sec=s)

        sum_HH = long_dist_x*dist_comp_x + long_dist_y*dist_comp_y + long_dist_z*dist_comp_z

        final_sum_HH = sum_HH / sum_dist_comp

        sum_temp1 = long_dist_x**2 + long_dist_y**2 + long_dist_z**2
        r_sq = sum_temp1 -(final_sum_HH * final_sum_HH)

        Length_vector = final_sum_HH + sum_dist_comp                

        if final_sum_HH < 0 and Length_vector <= 0:
          phi=log((sqrt(final_sum_HH**2 + r_sq) - final_sum_HH)/(sqrt(Length_vector**2+r_sq)-Length_vector))
        elif final_sum_HH > 0  and Length_vector > 0:
          phi=log((sqrt(Length_vector**2+r_sq) + Length_vector)/(sqrt(final_sum_HH**2+r_sq) + final_sum_HH))
        else:
          phi=log(((sqrt(Length_vector**2+r_sq)+Length_vector) * (sqrt(final_sum_HH**2+r_sq)-final_sum_HH))/r_sq)

        line_part1 = 10000.0 * (1.0 / (4.0*pi*sum_dist_comp*sigma) * phi) # x10000 for units of microV
        vres.append(line_part1)

    return vres

  def LFPinit (self):
    lsec = getallSections()
    n = len(lsec)
    # print('In LFPinit - pc.id = ',self.pc.id(),'len(lsec)=',n)
    self.imem_ptrvec = h.PtrVector(n) # 
    self.imem_vec = h.Vector(n)  
    for i,s in enumerate(lsec):
      seg = s(0.5)
      #for seg in s # so do not need to use segments...? more accurate to use segments and their neighbors
      self.imem_ptrvec.pset(i, seg._ref_i_membrane_)

    self.vres = self.transfer_resistance(self.coord)
    self.lfp_t = h.Vector()
    self.lfp_v = h.Vector()

    #for i, cellinfo in enumerate(gidinfo.values()):
    #  seg = cellinfo.cell.soma(0.5)
    #  imem_ptrvec.pset(i, seg._ref_i_membrane_)
    #rx = h.Matrix(nelectrode, n)
    #vx = h.Vector(nelectrode)
    #for i in range(nelectrode):
    #  for j, cellinfo in enumerate(gidinfo.values()):
    #    rx.setval(i, j, transfer_resistance(cellinfo.cell, e_coord[i]))
    #  #rx.setval(i,1,1.0)

  def callback (self):
    # print('In lfp callback - pc.id = ',self.pc.id(),' t=',self.pc.t(0))
    self.imem_ptrvec.gather(self.imem_vec)
    #s = pc.allreduce(imem_vec.sum(), 1) #verify sum i_membrane_ == stimulus
    #if rank == 0: print pc.t(0), s

    #sum up the weighted i_membrane_. Result in vx
    # rx.mulv(imem_vec, vx)

    val = 0.0
    for j in range(len(self.vres)): val += self.imem_vec.x[j] * self.vres.x[j]

    # append to Vector
    self.lfp_t.append(self.pc.t(0))
    self.lfp_v.append(val)

  def lfp_final (self):
    self.pc.allreduce(self.lfp_v, 1)

  def lfpout (self,fn = 'LFP.txt', append=False, tvec = None):
    fmode = 'w'
    if append: fmode = 'a'
    if int(self.pc.id()) == 0:
      print('len(lfp_t) is %d' % len(self.lfp_t))
      f = open(fn, fmode)
      if tvec is None:
        for i in range(1, len(self.lfp_t), 1):
          line = '%g' % self.lfp_v.x[i]
          f.write(line + '\n')
      else:
        for i in range(1, len(self.lfp_t), 1):
          line = '%g'%self.lfp_t.x[i]
          line += ' %g' % self.lfp_v.x[i]
          f.write(line + '\n')
      f.close()

def test ():
  from L5_pyramidal import L5Pyr
  cell = L5Pyr()

  h.load_file("stdgui.hoc")
  h.cvode_active(1)

  ns = h.NetStim()
  ns.number = 10
  ns.start = 100
  ns.interval=50.0

  nc = h.NetCon(ns,cell.apicaltuft_ampa)
  nc.weight[0] = 0.001

  h.tstop=2000.0

  elec = LFPElectrode([0, 100.0, 100.0], pc = h.ParallelContext())
  elec.setup()
  elec.LFPinit()
  h.run()
  elec.lfp_final()
  ion()
  plot(elec.lfp_t, elec.lfp_v)
  
if __name__ == '__main__':
  test()
  """
  for i in range(len(lfp_t)):
    print(lfp_t.x[i],)
    for j in range(nelectrode):
      print(lfp_v[j].x[i],)
    print("")
  """
