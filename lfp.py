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
based on mh code
"""

from neuron import h
from math import sqrt, log, pi, exp

from pylab import *
ion()

from L5_pyramidal import L5Pyr
cell = L5Pyr()

pc = h.ParallelContext()

# get all Sections
def getallSections (ty='Pyr'):
  ls = h.allsec()
  ls = [s for s in ls if s.name().count(ty)>0 or len(ty)==0]
  return ls

resistivity_of_cytoplasm = 1000 #ohm-cm
nelectrode = 6
lfp_t = h.Vector()
lfp_v = [h.Vector() for _ in range(nelectrode)]
#e_coord = [[0, 4000, 6000], [0, 4000, 5500], [0, 4000, 6500], [0, -4000, 6000], [0, -4000, 5500], [0, -4000, 6500]]
e_coord = [[0, 100.0, 100.0]]

imem_ptrvec = None
imem_vec = None

def transfer_resistance (exyz):
  vres = h.Vector()
  lsec = getallSections()
  for s in lsec:

    x = (h.x3d(0,sec=s) + h.x3d(1,sec=s)) / 2.0
    y = (h.y3d(0,sec=s) + h.y3d(1,sec=s)) / 2.0 
    z = (h.z3d(0,sec=s) + h.z3d(1,sec=s)) / 2.0 

    sigma = 0.3    

    dis = sqrt((exyz[0] - x)**2 + (exyz[1] - y)**2 + (exyz[2] - z)**2 )

    # setting radius limit
    if(dis<(s.diam/2.0)): dis = (s.diam/2.0) + 0.1

    # calculate length of the compartment
    dist_comp = sqrt((h.x3d(1,sec=s) - h.x3d(0,sec=s))**2 + (h.y3d(1,sec=s) - h.y3d(0,sec=s))**2 + (h.z3d(1,sec=s) - h.z3d(0,sec=s))**2)

    dist_comp_x = (h.x3d(1,sec=s) - h.x3d(0,sec=s)) # * 1e-6
    dist_comp_y = (h.y3d(1,sec=s) - h.y3d(0,sec=s)) # * 1e-6
    dist_comp_z = (h.z3d(1,sec=s) - h.z3d(0,sec=s)) # * 1e-6

    sum_dist_comp = sqrt(dist_comp_x**2  + dist_comp_y**2 + dist_comp_z**2)

    # print "sum_dist_comp=",sum_dist_comp, secname(), area(0.5)

    #  setting radius limit
    if sum_dist_comp< s.diam/2.0: sum_dist_comp = s.diam/2.0 + 0.1

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

    line_part1 = 1.0 / (4.0*pi*sum_dist_comp*sigma) * phi * h.area(0.5,sec=s)
    vres.append(line_part1)

  return vres

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

def transfer_resistance2 (exyz):
  vres = h.Vector()
  lsec = getallSections()

  sigma = 0.3    

  for s in lsec:

    lcoord, ldist, lend = getcoordinf(s)

    for i in range(len(lcoord)):
      
      x,y,z = lcoord[i]

      dis = sqrt((exyz[0] - x)**2 + (exyz[1] - y)**2 + (exyz[2] - z)**2 )

      # setting radius limit
      if(dis<(s.diam/2.0)): dis = (s.diam/2.0) + 0.1

      dist_comp = ldist[i] # length of the compartment
      sum_dist_comp = sqrt(dist_comp[0]**2  + dist_comp[0]**2 + dist_comp[0]**2)

      # print "sum_dist_comp=",sum_dist_comp, secname(), area(0.5)

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

      line_part1 = 1.0 / (4.0*pi*sum_dist_comp*sigma) * phi * h.area(0.5,sec=s)
      vres.append(line_part1)

  return vres

vres = transfer_resistance(e_coord[0])
vx = h.Vector(nelectrode)

def lfp_init ():
  global imem_ptrvec, imem_vec, rx, vx, vres
  lsec = getallSections()
  n = len(lsec)
  imem_ptrvec = h.PtrVector(n) # 
  imem_vec = h.Vector(n)  
  for i,s in enumerate(lsec):
    seg = s(0.5)
    #for seg in s # so do not need to use segments...? more accurate to use segments and their neighbors
    imem_ptrvec.pset(i, seg._ref_i_membrane_)

  #for i, cellinfo in enumerate(gidinfo.values()):
  #  seg = cellinfo.cell.soma(0.5)
  #  imem_ptrvec.pset(i, seg._ref_i_membrane_)
  #rx = h.Matrix(nelectrode, n)
  #vx = h.Vector(nelectrode)
  #for i in range(nelectrode):
  #  for j, cellinfo in enumerate(gidinfo.values()):
  #    rx.setval(i, j, transfer_resistance(cellinfo.cell, e_coord[i]))
  #  #rx.setval(i,1,1.0)

def lfp ():
  # print 'ecg t=%g' % pc.t(0)
  imem_ptrvec.gather(imem_vec)
  #s = pc.allreduce(imem_vec.sum(), 1) #verify sum i_membrane_ == stimulus
  #if rank == 0: print pc.t(0), s

  #sum up the weighted i_membrane_. Result in vx
  # rx.mulv(imem_vec, vx)

  for i in range(nelectrode):
    vx.x[i] = 0.0
    for j in range(len(vres)):
      vx.x[i] += imem_vec.x[j] * vres.x[j]
    
  # append to Vector
  lfp_t.append(pc.t(0))
  for i in range(nelectrode): 
    lfp_v[i].append(vx.x[i])

def lfp_setup ():
  global bscallback, fih
  h.cvode.use_fast_imem(1)
  bscallback = h.beforestep_callback(h.cas()(.5))
  bscallback.set_callback(lfp)
  fih = h.FInitializeHandler(1, lfp_init)

def lfp_final ():
  for i in range(nelectrode):
    pc.allreduce(lfp_v[i], 1)

def lfpout (append=0.0):
  fmode = 'w' if append is 0.0 else 'a'
  lfp_final()
  if rank is  0:
    print('len(lfp_t) is %d' % len(lfp_t))
    f = open('lfp.txt', fmode)
    for i in range(len(lfp_t)):
      line = '%g'%lfp_t.x[i]
      for j in range(nelectrode):
        line += ' %g' % lfp_v[j].x[i]
      f.write(line + '\n')
    f.close()
  lfp_t.resize(0)
  for j in range(nelectrode):
    lfp_v[j].resize(0)

def test ():
  h.load_file("stdgui.hoc")
  h.cvode_active(1)

  ns = h.NetStim()
  ns.number = 10
  ns.start = 100
  ns.interval=50.0

  nc = h.NetCon(ns,cell.apicaltuft_ampa)
  nc.weight[0] = 0.001

  h.tstop=2000.0
  lfp_setup()
  lfp_init()
  h.run()
  lfp_final()

  plot(lfp_t,lfp_v[0])
  
if __name__ == '__main__':
  test()
  for i in range(len(lfp_t)):
    print(lfp_t.x[i],)
    for j in range(nelectrode):
      print(lfp_v[j].x[i],)
    print("")

