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

translated to Python by Sam Neymotin
"""

from neuron import h
from math import sqrt, log, PI, exp

# Set default electrode position
elec_x = -100
elec_y = 50
elec_z = 0
place_mea_electrode = 0

MoveElec = h.Shape(0)  #  Created morphology view plot, didn't map it to the screen

# get all Sections
def getallSections ():
  allsecs=h.SectionList() # no .clear() command
  roots=h.SectionList()
  roots.allroots()
  for s in roots:
    s.push()
    allsecs.wholetree()
  return allsecs

def insertLFP ():
  lsec = getallSections()
  for s in lsec:
    if h.issection(".*dummy.*",sec=s): continue
    if h.issection(".*myelin.*",sec=s): continue
    if h.issection(".*node.*",sec=s): continue
    if h.issection(".*branch.*",sec=s): continue
    # Inserting extracellular electrode to all compartments and setting extracellular medium parameters
    s.insert("extracellular")
    s.insert("lfp")

    s.local_xc_0 = xc[0] #  extracellular capacitance
    s.local_xc_1 = xc[1] 

    s.local_xg_0 = xg[0] #  extracellular conductance
    s.local_xg_1 = xg[1]

    s.local_xraxial_0 = xraxial[0] #  extracellular axial resistance
    s.local_xraxial_1 = xraxial[1]

  
#  Procedure to update extracellular medium parameters from UI
def change_local_xc_0 (xc0):
  lsec = getallSections()
  for s in lsec: s.xc[0] = xc0

def change_local_xc_1 (xc1):
  lsec = getallSections()
  for s in lsec: s.xc[1] = xc1

def change_local_xg_0 (xg0):
  lsec = getallSections()
  for s in lsec: s.xg[0] = xg0

def change_local_xg_1 (xg1):
  lsec = getallSections()
  for s in lsec: s.xg[1] = xg1

def change_local_xraxial_0 (xr0):
  lsec = getallSections()
  for s in lsec: s.xraxial[0] = xr0

def change_local_xraxial_1 (xr1):
  lsec = getallSections()
  for s in lsec: s.xraxial[1] = xr1

# Procedure for computing LFP via three schema, Point Source Approximation(PSA), Line Source
# Approximation (LSA), RC filter methods.

def re_insert_elec():
  lsec = getallSections()
  for s in lsec:
    if h.ismembrane("lfp",sec=s):
      x = (h.x3d(0,sec=s) + h.x3d(1,sec=s)) / 2.0
      y = (h.y3d(0,sec=s) + h.y3d(1,sec=s)) / 2.0 
      z = (h.z3d(0,sec=s) + h.z3d(1,sec=s)) / 2.0 

      sigma = 0.3

      if(elec_x==elec_y==elec_z==0): elec_z=1

      dis = sqrt((elec_x - x)**2 + (elec_y - y)**2 + (elec_z - z)**2 )

      # setting radius limit
      if(dis<(s.diam/2.0)): dis = (s.diam/2.0) + 0.1

      point_part1 = (1.0 / (4.0 * 3.141 * dis * sigma)) * s.area(0.5)

      # calculate length of the compartment
      dist_comp = sqrt((h.x3d(1,sec=s) - h.x3d(0,sec=s))**2 + (h.y3d(1,sec=s) - h.y3d(0,sec=s))**2 + (h.z3d(1,sec=s) - h.z3d(0,sec=s))**2)

      dist_comp_x = (h.x3d(1,sec=s) - h.x3d(0,sec=s)) # * 1e-6
      dist_comp_y = (h.y3d(1,sec=s) - h.y3d(0,sec=s)) # * 1e-6
      dist_comp_z = (h.z3d(1,sec=s) - h.z3d(0,sec=s)) # * 1e-6

      sum_dist_comp = sqrt(dist_comp_x**2  + dist_comp_y**2 + dist_comp_z**2)

      # print "sum_dist_comp=",sum_dist_comp, secname(), area(0.5)

      #  setting radius limit
      if sum_dist_comp< s.diam/2.0: sum_dist_comp = s.diam/2.0 + 0.1

      long_dist_x = elec_x - h.x3d(1,sec=s)
      long_dist_y = elec_y - h.y3d(1,sec=s)
      long_dist_z = elec_z - h.z3d(1,sec=s)

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

      line_part1 = 1.0 / (4.0*PI*sum_dist_comp*sigma) * phi * s.area(0.5)

      #  RC algorithm implementation
      capa = 1.0 #  set to specific capacitance, Johnston and Wu 1995
      RC = sigma * capa

      # velo um/ms
      # Nauhaus et al, 2009 calculated the propagation speed on average, 0.24 ± 0.20 m/s in
      # monkeys and 0.31 ± 0.23 m/s in cats (mean ± s.d.) ie, 240 um/ms
      time_const = dis / 240.0 
      
      rc_part1 =  exp(-1.0 *(time_const/RC)) * s.area(0.5)

      # for (x,0) goes through segments but the 0 means skip endpoint segments (with locations of 0,1)
      for seg in s:
        if seg.x == 0.0 or seg.x == 1.0: continue
        h.setpointer( seg._ref_i_membrance, 'transmembrane_current', seg.lfp) 
        # setpointer transmembrane_current_lfp(x), i_membrane(x) # lfp transmembrance current observes i_membrane
        # initial_part_point_lfp(x) = point_part1
        # initial_part_line_lfp(x) = line_part1
        # initial_part_rc_lfp(x) = rc_part1

        """
        The hoc setpointer statement is effected in Python as a function call with a syntax for
        POINT_PROCESS and SUFFIX (density)mechanisms respectively of
        
        h.setpointer(_ref_hocvar, 'POINTER_name', point_proces_object)
        h.setpointer(_ref_hocvar, 'POINTER_name', nrn.Mechanism_object)

        See nrn/share/examples/nrniv/nmodl/(tstpnt1.py and tstpnt2.py) for examples of usage. For
        a density mechanism, the 'POINTER_name' cannot have the SUFFIX appended. For example if a
        mechanism with suffix foo has a POINTER bar and you want it to point to t use

        h.setpointer(_ref_t, 'bar', sec(x).foo)

        """


vrec = 0 

# function to sum field potential calculated for PSA schema
def fieldrec_point ():
  sum = 0
  lsec = getallSections()
  for s in lsec:
    if h.ismembrane("lfp",sec=s):
      for seg in s:
        if seg.x == 0.0 or seg.x == 1.0: continue
        sum += seg.lfp.lfp_point
  return sum

# function to sum field potential calculated for LSA schema
def fieldrec_line ():
  sum = 0
  lsec = getallSections()
  for s in lsec:
    if h.ismembrane("lfp",sec=s):
      for seg in s:
        if seg.x == 0.0 or seg.x == 1.0: continue
        sum += seg.lfp.lfp_line
  return sum

# function to sum field potential calculated for RC filter schema
def fieldrec_RC ():
  sum = 0
  lsec = getallSections()
  for s in lsec:
    if h.ismembrane("lfp",sec=s):
      for seg in s:
        if seg.x == 0.0 or seg.x == 1.0: continue
        sum += seg.lfp.lfp_rc
  return sum

def init (): #  Initializing all variables
  h.finitialize(h.v_init)
  h.fcurrent()
  Point_source = fieldrec_point()
  Line_source = fieldrec_line()
  Simple_RC_filter = fieldrec_RC()

def advance ():
  h.fadvance()
  Point_source = fieldrec_point()
  Line_source = fieldrec_line()
  Simple_RC_filter = fieldrec_RC()

# Recording summed LFP using NEURON's record function
total_lfp = h.Vector()
total_lfp.record(&Line_source)

total_point = h.Vector()
total_point.record(&Point_source)

total_RC = h.Vector()
total_RC.record(&Simple_RC_filter)

# h.xopen("move_electrode.hoc")

#  Initializing tool interface 
h.xopen("tool_interface.hoc")

# Function for setting electrode position
def setelec (x,y,z):
  global elec_x, elec_y, elec_z
  elec_x = x
  elec_y = y
  elec_z = z
	
  # Do calculation
  # get_included_comp(xe, ye, ze)
  # drawelec(elec_x, elec_y, elec_z)
  re_insert_elec() # re-define pointers


#  Funtion to display electrode position
def change_electrode_pos (toset, x, y):
  if toset == 2:
    setelec(x, y, 0)	
    print("x, y = ",x,y)
  return (0)

"""
Single electrode location may be set both manually and interactively. To set manually, the user
needs to provide values for x,y,z of electrode location in panel D. Interactive LFP electrode
implemented using NEURON's menu tool. To access this funtionality, the user needs to move the
mouse pointer on "Morphology view" window and right click on the plot, then select
"LFP_electrode" and move mouse pointer to move electrode and click on the point on the plot area
to record the extracellular potential from that point.
"""

MoveElec.menu_tool("LFP_electrode", "change_electrode_pos","1")

#  Write the calculated LFP as files in "LFP_traces" directory
def file_write ():
  f = h.File()
  f.wopen("LFP_traces/Line_source.dat") 
  for i in range(int(total_lfp.size())):
    f.printf("%e",total_lfp.x[i]) 
    f.printf("\n")
  f.close()	

  f.wopen("LFP_traces/Point_source.dat") 
  for i in range(int(total_point.size())):
    f.printf("%e",total_point.x[i]) 
    f.printf("\n")
  f.close()

  f.wopen("LFP_traces/RC.dat") 
  for i in range(int(total_RC.size())):      
    f.printf("%e",total_RC.x[i]) 
    f.printf("\n")
  f.close()
  xpanel("Simulation complete!", 0)
  xlabel("Traces are saved to LFP_traces directory. Run GNU Octave/Matlab scripts to save as .ps for later use.")
  xpanel(494,468)


"""
#  Funtion to set electrode location for Multi Electrode Array simualtion (MEA)
def run_multi_button ():
  if (place_mea_electrode == 1):
    mea_run_control()		
  else:
    xpanel("")
    xlabel("Please set electrode location by clicking on \"Set Multiple Electrodes\". Run MEA simulation!")
    xpanel(494,468)
"""
