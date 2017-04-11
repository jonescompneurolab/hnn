# L5_pyramidal.py - establish class def for layer 5 pyramidal cells
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: removed it.izip dep)
# last rev: (SL: toward python3, moved cells)

import sys
import numpy as np

from neuron import h
from cell import Pyr
import paramrw
import params_default as p_default

# Units for e: mV
# Units for gbar: S/cm^2 unless otherwise noted
# units for taur: ms

class L5Pyr(Pyr):

    def basic_shape (self):
        # THESE AND LENGHTHS MUST CHANGE TOGETHER!!!
        pt3dclear=h.pt3dclear; pt3dadd=h.pt3dadd; dend = self.list_dend
        pt3dclear(sec=self.soma); pt3dadd(0, 0, 0, 1, sec=self.soma); pt3dadd(0, 23, 0, 1, sec=self.soma)
        pt3dclear(sec=dend[0]); pt3dadd(0, 23, 0, 1,sec=dend[0]); pt3dadd(0, 83, 0, 1,sec=dend[0])
        pt3dclear(sec=dend[1]); pt3dadd(0, 83, 0, 1,sec=dend[1]); pt3dadd(-150, 83, 0, 1,sec=dend[1])
        pt3dclear(sec=dend[2]); pt3dadd(0, 83, 0, 1,sec=dend[2]); pt3dadd(0, 483, 0, 1,sec=dend[2])
        pt3dclear(sec=dend[3]); pt3dadd(0, 483, 0, 1,sec=dend[3]); pt3dadd(0, 883, 0, 1,sec=dend[3])
        pt3dclear(sec=dend[4]); pt3dadd(0, 883, 0, 1,sec=dend[4]); pt3dadd(0, 1133, 0, 1,sec=dend[4])
        pt3dclear(sec=dend[5]); pt3dadd(0, 0, 0, 1,sec=dend[5]); pt3dadd(0, -50, 0, 1,sec=dend[5])
        pt3dclear(sec=dend[6]); pt3dadd(0, -50, 0, 1,sec=dend[6]); pt3dadd(-106, -156, 0, 1,sec=dend[6])
        pt3dclear(sec=dend[7]); pt3dadd(0, -50, 0, 1,sec=dend[7]); pt3dadd(106, -156, 0, 1,sec=dend[7])

    def geom (self):
      soma = self.soma; dend = self.list_dend;
      # soma.L = 13 # BUSH 1999 spike amp smaller
      soma.L=39 # Bush 1993
      dend[0].L = 102
      dend[1].L = 255
      dend[2].L = 680 # default 400
      dend[3].L = 680 # default 400
      dend[4].L = 425
      dend[5].L = 85
      dend[6].L = 255 #  default 150
      dend[7].L = 255 #  default 150
      # soma.diam = 18.95 # Bush 1999
      soma.diam = 28.9 # Bush 1993
      dend[0].diam = 10.2
      dend[1].diam = 5.1
      dend[2].diam = 7.48 # default 4.4
      dend[3].diam = 4.93 # default 2.9
      dend[4].diam = 3.4
      dend[5].diam = 6.8
      dend[6].diam = 8.5
      dend[7].diam = 8.5

    def __init__(self, pos, p={}):
        # Get default L5Pyr params and update them with corresponding params in p
        p_all_default = p_default.get_L5Pyr_params_default()
        self.p_all = paramrw.compare_dictionaries(p_all_default, p)

        # Get somatic, dendirtic, and synapse properties
        p_soma = self.__get_soma_props(pos)
        p_dend = self.__get_dend_props()
        p_syn = self.__get_syn_props()

        # Set morphology properties
        # p_soma_props = self.__get_soma_props(pos)
        # p_dend_props = self.__get_dend_props()
        # dend_props, dend_names = self.__set_dend_props()

        # Pyr.__init__(self, soma_props)
        Pyr.__init__(self, p_soma)
        self.celltype = 'L5_pyramidal'

        # Geometry
        # dend Cm and dend Ra set using soma Cm and soma Ra
        self.create_dends_new(p_dend)
        self.topol()
        self.geom() # adjusted after translation from original hoc (2009 model)

        # biophysics
        self.__biophys_soma()
        self.__biophys_dends()

        # Dictionary of length scales to calculate dipole without 3d shape. Comes from Pyr().
        # dipole_insert() comes from Cell()
        self.yscale = self.get_sectnames()
        self.dipole_insert(self.yscale)

        # create synapses
        self.__synapse_create(p_syn)

        # insert iclamp
        self.list_IClamp = []

        # run record current soma, defined in Cell()
        self.record_current_soma()

    # insert IClamps in all situations
    # temporarily an external function taking the p dict
    def create_all_IClamp(self, p):
        # list of sections for this celltype
        sect_list_IClamp = [
            'soma',
        ]

        # some parameters
        t_delay = p['Itonic_t0_L5Pyr_soma']

        # T = -1 means use h.tstop
        if p['Itonic_T_L5Pyr_soma'] == -1:
            # t_delay = 50.
            t_dur = h.tstop - t_delay
        else:
            t_dur = p['Itonic_T_L5Pyr_soma'] - t_delay

        # t_dur must be nonnegative, I imagine
        if t_dur < 0.:
            t_dur = 0.

        # properties of the IClamp
        props_IClamp = {
            'loc': 0.5,
            'delay': t_delay,
            'dur': t_dur,
            'amp': p['Itonic_A_L5Pyr_soma']
        }

        # iterate through list of sect_list_IClamp to create a persistent IClamp object
        # the insert_IClamp procedure is in Cell() and checks on names
        # so names must be actual section names, or else it will fail silently
        self.list_IClamp = [self.insert_IClamp(sect_name, props_IClamp) for sect_name in sect_list_IClamp]

    # Sets somatic properties. Returns dictionary.
    def __get_soma_props(self, pos):
         return {
            'pos': pos,
            'L': self.p_all['L5Pyr_soma_L'],
            'diam': self.p_all['L5Pyr_soma_diam'],
            'cm': self.p_all['L5Pyr_soma_cm'],
            'Ra': self.p_all['L5Pyr_soma_Ra'],
            'name': 'L5Pyr',
        }

    # Returns dictionary of dendritic properties and list of dendrite names
    def __get_dend_props(self):
        # def __set_dend_props(self):
        # Hard coded dend properties
        # dend_props =  {
        return {
            'apical_trunk': {
                'L': self.p_all['L5Pyr_apicaltrunk_L'] ,
                'diam': self.p_all['L5Pyr_apicaltrunk_diam'],
                'cm': self.p_all['L5Pyr_dend_cm'],
                'Ra': self.p_all['L5Pyr_dend_Ra'],
            },
            'apical_1': {
                'L': self.p_all['L5Pyr_apical1_L'],
                'diam': self.p_all['L5Pyr_apical1_diam'],
                'cm': self.p_all['L5Pyr_dend_cm'],
                'Ra': self.p_all['L5Pyr_dend_Ra'],
            },
            'apical_2': {
                'L': self.p_all['L5Pyr_apical2_L'],
                'diam': self.p_all['L5Pyr_apical2_diam'],
                'cm': self.p_all['L5Pyr_dend_cm'],
                'Ra': self.p_all['L5Pyr_dend_Ra'],
            },
            'apical_tuft': {
                'L': self.p_all['L5Pyr_apicaltuft_L'],
                'diam': self.p_all['L5Pyr_apicaltuft_diam'],
                'cm': self.p_all['L5Pyr_dend_cm'],
                'Ra': self.p_all['L5Pyr_dend_Ra'],
            },
            'apical_oblique': {
                'L': self.p_all['L5Pyr_apicaloblique_L'],
                'diam': self.p_all['L5Pyr_apicaloblique_diam'],
                'cm': self.p_all['L5Pyr_dend_cm'],
                'Ra': self.p_all['L5Pyr_dend_Ra'],
            },
            'basal_1': {
                'L': self.p_all['L5Pyr_basal1_L'],
                'diam': self.p_all['L5Pyr_basal1_diam'],
                'cm': self.p_all['L5Pyr_dend_cm'],
                'Ra': self.p_all['L5Pyr_dend_Ra'],
            },
            'basal_2': {
                'L': self.p_all['L5Pyr_basal2_L'],
                'diam': self.p_all['L5Pyr_basal2_diam'],
                'cm': self.p_all['L5Pyr_dend_cm'],
                'Ra': self.p_all['L5Pyr_dend_Ra'],
            },
            'basal_3': {
                'L': self.p_all['L5Pyr_basal3_L'],
                'diam': self.p_all['L5Pyr_basal3_diam'],
                'cm': self.p_all['L5Pyr_dend_cm'],
                'Ra': self.p_all['L5Pyr_dend_Ra'],
            },
        }

        # These MUST match order the above keys in exact order!
        # dend_names = [
        #     'apical_trunk', 'apical_1', 'apical_2',
        #     'apical_tuft', 'apical_oblique', 'basal_1',
        #     'basal_2', 'basal_3'
        # ]

        # return dend_props, dend_names

        # self.dend_L = [102, 680, 680, 425, 255, 85, 255, 255]
        # self.dend_diam = [10.2, 7.48, 4.93, 3.4, 5.1, 6.8, 8.5, 8.5]

        # # check lengths for congruity
        # if len(self.dend_L) == len(self.dend_diam):
        #     # Zip above lists together
        #     self.dend_props = zip(self.dend_names, self.dend_L, self.dend_diam)
        # else:
        #     print "self.dend_L and self.dend_diam are not the same length"
        #     print "please fix in L5_pyramidal.py"
        #     sys.exit()

    def __get_syn_props(self):
        return {
            'ampa': {
                'e': self.p_all['L5Pyr_ampa_e'],
                'tau1': self.p_all['L5Pyr_ampa_tau1'],
                'tau2': self.p_all['L5Pyr_ampa_tau2'],
            },
            'nmda': {
                'e': self.p_all['L5Pyr_nmda_e'],
                'tau1': self.p_all['L5Pyr_nmda_tau1'],
                'tau2': self.p_all['L5Pyr_nmda_tau2'],
            },
            'gabaa': {
                'e': self.p_all['L5Pyr_gabaa_e'],
                'tau1': self.p_all['L5Pyr_gabaa_tau1'],
                'tau2': self.p_all['L5Pyr_gabaa_tau2'],
            },
            'gabab': {
                'e': self.p_all['L5Pyr_gabab_e'],
                'tau1': self.p_all['L5Pyr_gabab_tau1'],
                'tau2': self.p_all['L5Pyr_gabab_tau2'],
            }
        }

    # connects sections of this cell together
    def topol (self):

        """ original topol
        connect dend(0), soma(1) // dend[0] is apical trunk
        for i = 1, 2 connect dend[i](0), dend(1) // dend[1] is oblique, dend[2] is apic1
        for i = 3, 4 connect dend[i](0), dend[i-1](1) // dend[3],dend[4] are apic2,apic tuft
        connect dend[5](0), soma(0) //was soma(1)this is correct! 
        for i = 6, 7 connect dend[i](0), dend[5](1)
        """

        # child.connect(parent, parent_end, {child_start=0})
        # Distal (apical)
        self.dends['apical_trunk'].connect(self.soma, 1, 0)
        self.dends['apical_1'].connect(self.dends['apical_trunk'], 1, 0)
        self.dends['apical_2'].connect(self.dends['apical_1'], 1, 0)
        self.dends['apical_tuft'].connect(self.dends['apical_2'], 1, 0)

        # apical_oblique comes off distal end of apical_trunk
        self.dends['apical_oblique'].connect(self.dends['apical_trunk'], 1, 0)

        # Proximal (basal)
        self.dends['basal_1'].connect(self.soma, 0, 0)
        self.dends['basal_2'].connect(self.dends['basal_1'], 1, 0)
        self.dends['basal_3'].connect(self.dends['basal_1'], 1, 0)

        self.basic_shape() # translated from original hoc (2009 model)

        # # Distal
        # self.list_dend[0].connect(self.soma, 1, 0)
        # self.list_dend[1].connect(self.list_dend[0], 1, 0)

        # self.list_dend[2].connect(self.list_dend[1], 1, 0)
        # self.list_dend[3].connect(self.list_dend[2], 1, 0)

        # # dend[4] comes off of dend[0](1)
        # self.list_dend[4].connect(self.list_dend[0], 1, 0)

        # # Proximal
        # self.list_dend[5].connect(self.soma, 0, 0)
        # self.list_dend[6].connect(self.list_dend[5], 1, 0)
        # self.list_dend[7].connect(self.list_dend[5], 1, 0)

    # adds biophysics to soma
    def __biophys_soma(self):
        # set soma biophysics specified in Pyr
        # self.pyr_biophys_soma()

        # Insert 'hh' mechanism
        self.soma.insert('hh')
        self.soma.gkbar_hh = self.p_all['L5Pyr_soma_gkbar_hh']
        self.soma.gnabar_hh = self.p_all['L5Pyr_soma_gnabar_hh']
        self.soma.gl_hh = self.p_all['L5Pyr_soma_gl_hh']
        self.soma.el_hh = self.p_all['L5Pyr_soma_el_hh']

        # insert 'ca' mechanism
        # Units: pS/um^2
        self.soma.insert('ca')
        self.soma.gbar_ca = self.p_all['L5Pyr_soma_gbar_ca']

        # insert 'cad' mechanism
        # units of tau are ms
        self.soma.insert('cad')
        self.soma.taur_cad = self.p_all['L5Pyr_soma_taur_cad']

        # insert 'kca' mechanism
        # units are S/cm^2?
        self.soma.insert('kca')
        self.soma.gbar_kca = self.p_all['L5Pyr_soma_gbar_kca']

        # Insert 'km' mechanism
        # Units: pS/um^2
        self.soma.insert('km')
        self.soma.gbar_km = self.p_all['L5Pyr_soma_gbar_km']

        # insert 'cat' mechanism
        self.soma.insert('cat')
        self.soma.gbar_cat = self.p_all['L5Pyr_soma_gbar_cat']

        # insert 'ar' mechanism
        self.soma.insert('ar')
        self.soma.gbar_ar = self.p_all['L5Pyr_soma_gbar_ar']

        # self.soma.gkbar_hh = 0.01
        # self.soma.gnabar_hh = 0.16
        # self.soma.gl_hh = 4.26e-5
        # self.soma.el_hh = -65.
        # self.soma.gbar_ca = 60.
        # self.soma.taur_cad = 20.
        # self.soma.gbar_kca = 2e-4
        # self.soma.gbar_km = 200.
        # self.soma.gbar_cat = 2e-4
        # self.soma.gbar_ar = 1e-6

    def __biophys_dends(self):
        # set dend biophysics specified in Pyr()
        # self.pyr_biophys_dends()

        # set dend biophysics not specified in Pyr()
        for key in self.dends:
            # Insert 'hh' mechanism
            self.dends[key].insert('hh')
            self.dends[key].gkbar_hh = self.p_all['L5Pyr_dend_gkbar_hh']
            self.dends[key].gl_hh = self.p_all['L5Pyr_dend_gl_hh']
            self.dends[key].gnabar_hh = self.p_all['L5Pyr_dend_gnabar_hh']
            self.dends[key].el_hh = self.p_all['L5Pyr_dend_el_hh']

            # Insert 'ca' mechanims
            # Units: pS/um^2
            self.dends[key].insert('ca')
            self.dends[key].gbar_ca = self.p_all['L5Pyr_dend_gbar_ca']

            # Insert 'cad' mechanism
            self.dends[key].insert('cad')
            self.dends[key].taur_cad = self.p_all['L5Pyr_dend_taur_cad']

            # Insert 'kca' mechanism
            self.dends[key].insert('kca')
            self.dends[key].gbar_kca = self.p_all['L5Pyr_dend_gbar_kca']

            # Insert 'km' mechansim
            # Units: pS/um^2
            self.dends[key].insert('km')
            self.dends[key].gbar_km = self.p_all['L5Pyr_dend_gbar_km']

            # insert 'cat' mechanism
            self.dends[key].insert('cat')
            self.dends[key].gbar_cat = self.p_all['L5Pyr_dend_gbar_cat']

            # insert 'ar' mechanism
            self.dends[key].insert('ar')

        # set gbar_ar
        # Value depends on distance from the soma. Soma is set as
        # origin by passing self.soma as a sec argument to h.distance()
        # Then iterate over segment nodes of dendritic sections
        # and set gbar_ar depending on h.distance(seg.x), which returns
        # distance from the soma to this point on the CURRENTLY ACCESSED
        # SECTION!!!
        h.distance(sec=self.soma)

        for key in self.dends:
            self.dends[key].push()
            for seg in self.dends[key]:
                seg.gbar_ar = 1e-6 * np.exp(3e-3 * h.distance(seg.x))

            h.pop_section()

            # self.dends[key].gkbar_hh = 0.01
            # self.dends[key].gl_hh = 4.26e-5
            # self.dends[key].gnabar_hh = 0.14
            # self.dends[key].el_hh = -71
            # self.dends[key].gbar_ca = 60.
            # self.dends[key].taur_cad = 20.
            # self.dends[key].gbar_kca = 2e-4
            # self.dends[key].gbar_km = 200.
            #     seg.gbar_ar = 1e-6 * np.exp(3e-3 * h.distance(seg.x))
            #     seg.gbar_cat = 2e-4 * np.exp(0 * h.distance(seg.x))

        # for sec in self.list_dend:
        #     # Insert 'hh' mechanism
        #     sec.insert('hh')
        #     sec.gkbar_hh = 0.01
        #     sec.gl_hh = 4.26e-5
        #     sec.gnabar_hh = 0.14
        #     sec.el_hh = -71

        #     # Insert 'ca' mechanims
        #     # Units: pS/um^2
        #     sec.insert('ca')
        #     sec.gbar_ca = 60.

        #     # Insert 'cad' mechanism
        #     sec.insert('cad')
        #     sec.taur_cad = 20.

        #     # Insert 'kca' mechanism
        #     sec.insert('kca')
        #     sec.gbar_kca = 2e-4

        #     # Insert 'km' mechansim
        #     # Units: pS/um^2
        #     sec.insert('km')
        #     sec.gbar_km = 200.

        #     # insert 'cat' and 'ar' mechanisms
        #     sec.insert('cat')
        #     sec.insert('ar')

        # h.distance(sec=self.soma)

        # for sec in self.list_dend:
        #     sec.push()
        #     for seg in sec:
        #         seg.gbar_ar = 1e-6 * np.exp(3e-3 * h.distance(seg.x))

        #         # this should always evaluate to 2e-4
        #         sec.gbar_cat = 2e-4 * np.exp(0 * h.distance(seg.x))

        #     h.pop_section()

    def __synapse_create(self, p_syn):
        # creates synapses onto this cell
        # Somatic synapses
        self.synapses = {
            'soma_gabaa': self.syn_create(self.soma(0.5), p_syn['gabaa']),
            'soma_gabab': self.syn_create(self.soma(0.5), p_syn['gabab']),
        }

        # Dendritic synapses
        self.apicaltuft_gabaa = self.syn_create(self.dends['apical_tuft'](0.5), p_syn['gabaa'])
        self.apicaltuft_ampa = self.syn_create(self.dends['apical_tuft'](0.5), p_syn['ampa'])
        self.apicaltuft_nmda = self.syn_create(self.dends['apical_tuft'](0.5), p_syn['nmda'])

        self.apicaloblique_ampa = self.syn_create(self.dends['apical_oblique'](0.5), p_syn['ampa'])
        self.apicaloblique_nmda = self.syn_create(self.dends['apical_oblique'](0.5), p_syn['nmda'])

        self.basal2_ampa = self.syn_create(self.dends['basal_2'](0.5), p_syn['ampa'])
        self.basal2_nmda = self.syn_create(self.dends['basal_2'](0.5), p_syn['nmda'])

        self.basal3_ampa = self.syn_create(self.dends['basal_3'](0.5), p_syn['ampa'])
        self.basal3_nmda = self.syn_create(self.dends['basal_3'](0.5), p_syn['nmda'])

    # parallel connection function FROM all cell types TO here
    def parconnect(self, gid, gid_dict, pos_dict, p):
        # init dict of dicts
        # nc_dict for ampa and nmda may be the same for this cell type
        nc_dict = {
            'ampa': None,
            'nmda': None,
        }

        # connections FROM L5Pyr TO here
        for gid_src, pos in zip(gid_dict['L5_pyramidal'], pos_dict['L5_pyramidal']):
            # no autapses
            if gid_src != gid:
                nc_dict['ampa'] = {
                    'pos_src': pos,
                    'A_weight': p['gbar_L5Pyr_L5Pyr_ampa'],
                    'A_delay': 1.,
                    'lamtha': 3.,
                }

                # ampa connections
                self.ncfrom_L5Pyr.append(self.parconnect_from_src(gid_src, nc_dict['ampa'], self.apicaloblique_ampa))
                self.ncfrom_L5Pyr.append(self.parconnect_from_src(gid_src, nc_dict['ampa'], self.basal2_ampa))
                self.ncfrom_L5Pyr.append(self.parconnect_from_src(gid_src, nc_dict['ampa'], self.basal3_ampa))

                nc_dict['nmda'] = {
                    'pos_src': pos,
                    'A_weight': p['gbar_L5Pyr_L5Pyr_nmda'],
                    'A_delay': 1.,
                    'lamtha': 3.,
                }

                # nmda connections
                self.ncfrom_L5Pyr.append(self.parconnect_from_src(gid_src, nc_dict['nmda'], self.apicaloblique_nmda))
                self.ncfrom_L5Pyr.append(self.parconnect_from_src(gid_src, nc_dict['nmda'], self.basal2_nmda))
                self.ncfrom_L5Pyr.append(self.parconnect_from_src(gid_src, nc_dict['nmda'], self.basal3_nmda))

        # connections FROM L5Basket TO here
        for gid_src, pos in zip(gid_dict['L5_basket'], pos_dict['L5_basket']):
            nc_dict['gabaa'] = {
                'pos_src': pos,
                'A_weight': p['gbar_L5Basket_L5Pyr_gabaa'],
                'A_delay': 1.,
                'lamtha': 70.,
            }

            nc_dict['gabab'] = {
                'pos_src': pos,
                'A_weight': p['gbar_L5Basket_L5Pyr_gabab'],
                'A_delay': 1.,
                'lamtha': 70.,
            }

            # soma synapses are defined in Pyr()
            self.ncfrom_L5Basket.append(self.parconnect_from_src(gid_src, nc_dict['gabaa'], self.synapses['soma_gabaa']))
            self.ncfrom_L5Basket.append(self.parconnect_from_src(gid_src, nc_dict['gabab'], self.synapses['soma_gabab']))

        # connections FROM L2Pyr TO here
        for gid_src, pos in zip(gid_dict['L2_pyramidal'], pos_dict['L2_pyramidal']):
            # this delay is longer than most
            nc_dict = {
                'pos_src': pos,
                'A_weight': p['gbar_L2Pyr_L5Pyr'],
                'A_delay': 1.,
                'lamtha': 3.,
            }

            self.ncfrom_L2Pyr.append(self.parconnect_from_src(gid_src, nc_dict, self.basal2_ampa))
            self.ncfrom_L2Pyr.append(self.parconnect_from_src(gid_src, nc_dict, self.basal3_ampa))
            self.ncfrom_L2Pyr.append(self.parconnect_from_src(gid_src, nc_dict, self.apicaltuft_ampa))
            self.ncfrom_L2Pyr.append(self.parconnect_from_src(gid_src, nc_dict, self.apicaloblique_ampa))

        # connections FROM L2Basket TO here
        for gid_src, pos in zip(gid_dict['L2_basket'], pos_dict['L2_basket']):
            nc_dict = {
                'pos_src': pos,
                'A_weight': p['gbar_L2Basket_L5Pyr'],
                'A_delay': 1.,
                'lamtha': 50.,
            }

            self.ncfrom_L2Basket.append(self.parconnect_from_src(gid_src, nc_dict, self.apicaltuft_gabaa))

    # receive from external inputs
    def parreceive(self, gid, gid_dict, pos_dict, p_ext):
        for gid_src, p_src, pos in zip(gid_dict['extinput'], p_ext, pos_dict['extinput']):
            # Check if AMPA params defined in p_src
            if 'L5Pyr_ampa' in p_src.keys():
                nc_dict_ampa = {
                    'pos_src': pos,
                    'A_weight': p_src['L5Pyr_ampa'][0],
                    'A_delay': p_src['L5Pyr_ampa'][1],
                    'lamtha': p_src['lamtha']
                }

                # Proximal feed AMPA synapses
                if p_src['loc'] is 'proximal':
                    # basal2_ampa, basal3_ampa, apicaloblique_ampa
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_ampa, self.basal2_ampa))
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_ampa, self.basal3_ampa))
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_ampa, self.apicaloblique_ampa))

                # Distal feed AMPA synsapes
                elif p_src['loc'] is 'distal':
                    # apical tuft
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_ampa, self.apicaltuft_ampa))

            # Check if NMDA params defined in p_src
            if 'L5Pyr_nmda' in p_src.keys():
                nc_dict_nmda = {
                    'pos_src': pos,
                    'A_weight': p_src['L5Pyr_nmda'][0],
                    'A_delay': p_src['L5Pyr_nmda'][1],
                    'lamtha': p_src['lamtha']
                }

                # Proximal feed NMDA synapses
                if p_src['loc'] is 'proximal':
                    # basal2_nmda, basal3_nmda, apicaloblique_nmda
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_nmda, self.basal2_nmda))
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_nmda, self.basal3_nmda))
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_nmda, self.apicaloblique_nmda))

                # Distal feed NMDA synsapes
                elif p_src['loc'] is 'distal':
                    # apical tuft
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_nmda, self.apicaltuft_nmda))

    # one parreceive function to handle all types of external parreceives
    # types must be defined explicitly here
    def parreceive_ext(self, type, gid, gid_dict, pos_dict, p_ext):
        if type.startswith(('evprox', 'evdist')):
            if self.celltype in p_ext.keys():
                gid_ev = gid + gid_dict[type][0]

                nc_dict = {
                    'pos_src': pos_dict[type][gid],
                    'A_weight': p_ext[self.celltype][0],
                    'A_delay': p_ext[self.celltype][1],
                    'lamtha': p_ext['lamtha_space']
                }

                if p_ext['loc'] is 'proximal':
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict, self.basal2_ampa))
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict, self.basal3_ampa))
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict, self.apicaloblique_ampa))

                elif p_ext['loc'] is 'distal':
                    # apical tuft
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict, self.apicaltuft_ampa))
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict, self.apicaltuft_nmda))

        elif type == 'extgauss':
            # gid is this cell's gid
            # gid_dict is the whole dictionary, including the gids of the extgauss
            # pos_dict is also the pos of the extgauss (net origin)
            # p_ext_gauss are the params (strength, etc.)
            # doesn't matter if this doesn't do anything

            # gid shift is based on L2_pyramidal cells NOT L5
            # I recognize this is ugly (hack)
            # gid_shift = gid_dict['extgauss'][0] - gid_dict['L2_pyramidal'][0]
            if 'L5_pyramidal' in p_ext.keys():
                gid_extgauss = gid + gid_dict['extgauss'][0]

                nc_dict = {
                    'pos_src': pos_dict['extgauss'][gid],
                    'A_weight': p_ext['L5_pyramidal'][0],
                    'A_delay': p_ext['L5_pyramidal'][1],
                    'lamtha': p_ext['lamtha']
                }

                self.ncfrom_extgauss.append(self.parconnect_from_src(gid_extgauss, nc_dict, self.basal2_ampa))
                self.ncfrom_extgauss.append(self.parconnect_from_src(gid_extgauss, nc_dict, self.basal3_ampa))
                self.ncfrom_extgauss.append(self.parconnect_from_src(gid_extgauss, nc_dict, self.apicaloblique_ampa))

        elif type == 'extpois':
            if self.celltype in p_ext.keys():
                gid_extpois = gid + gid_dict['extpois'][0]

                nc_dict = {
                    'pos_src': pos_dict['extpois'][gid],
                    'A_weight': p_ext[self.celltype][0],
                    'A_delay': p_ext[self.celltype][1],
                    'lamtha': p_ext['lamtha_space']
                }

                self.ncfrom_extpois.append(self.parconnect_from_src(gid_extpois, nc_dict, self.basal2_ampa))
                self.ncfrom_extpois.append(self.parconnect_from_src(gid_extpois, nc_dict, self.basal3_ampa))
                self.ncfrom_extpois.append(self.parconnect_from_src(gid_extpois, nc_dict, self.apicaloblique_ampa))

    # Define 3D shape and position of cell. By default neuron uses xy plane for
    # height and xz plane for depth. This is opposite for model as a whole, but
    # convention is followed in this function for ease use of gui.
    def __set_3Dshape(self):
        # set 3D shape of soma by calling shape_soma from class Cell
        # print "WARNING: You are setting 3d shape geom. You better be doing"
        # print "gui analysis and not numerical analysis!!"
        self.shape_soma()

        # soma proximal coords
        x_prox = 0
        y_prox = 0

        # soma distal coords
        x_distal = 0
        y_distal = self.soma.L

        # dend 0-3 are major axis, dend 4 is branch
        # deal with distal first along major cable axis
        # the way this is assigning variables is ugly/lazy right now
        for i in range(0, 4):
            h.pt3dclear(sec=self.list_dend[i])

            # x_distal and y_distal are the starting points for each segment
            # these are updated at the end of the loop
            sec=self.list_dend[i]
            h.pt3dadd(0, y_distal, 0, sec.diam, sec=sec)

            # update x_distal and y_distal after setting them
            # x_distal += dend_dx[i]
            y_distal += sec.L

            # add next point
            h.pt3dadd(0, y_distal, 0, sec.diam, sec=sec)

        # now deal with dend 4
        # dend 4 will ALWAYS be positioned at the end of dend[0]
        h.pt3dclear(sec=self.list_dend[4])

        # activate this section with 'sec=self.list_dend[i]' notation
        x_start = h.x3d(1, sec=self.list_dend[0])
        y_start = h.y3d(1, sec=self.list_dend[0])

        sec=self.list_dend[4]
        h.pt3dadd(x_start, y_start, 0, sec.diam, sec=sec)
        # self.dend_L[4] is subtracted because lengths always positive,
        # and this goes to negative x
        h.pt3dadd(x_start-sec.L, y_start, 0, sec.diam, sec=sec)

        # now deal with proximal dends
        for i in range(5, 8):
            h.pt3dclear(sec=self.list_dend[i])

        # deal with dend 5, ugly. sorry.
        sec=self.list_dend[5]
        h.pt3dadd(x_prox, y_prox, 0, sec.diam, sec=sec)
        y_prox += -sec.L

        h.pt3dadd(x_prox, y_prox, 0, sec.diam,sec=sec)

        # x_prox, y_prox are now the starting points for BOTH of last 2 sections
        # dend 6
        # Calculate x-coordinate for end of dend
        sec=self.list_dend[6]
        dend6_x = -sec.L * np.sqrt(2) / 2.
        h.pt3dadd(x_prox, y_prox, 0, sec.diam, sec=sec)
        h.pt3dadd(dend6_x, y_prox-sec.L * np.sqrt(2) / 2.,
                    0, sec.diam, sec=sec)

        # dend 7
        # Calculate x-coordinate for end of dend
        sec=self.list_dend[7]
        dend7_x = sec.L * np.sqrt(2) / 2.
        h.pt3dadd(x_prox, y_prox, 0, sec.diam, sec=sec)
        h.pt3dadd(dend7_x, y_prox-sec.L * np.sqrt(2) / 2.,
                    0, sec.diam, sec=sec)

        # set 3D position
        # z grid position used as y coordinate in h.pt3dchange() to satisfy
        # gui convention that y is height and z is depth. In h.pt3dchange()
        # x and z components are scaled by 100 for visualization clarity
        self.soma.push()
        for i in range(0, int(h.n3d())):
            h.pt3dchange(i, self.pos[0]*100 + h.x3d(i), -self.pos[2] + h.y3d(i),
                           self.pos[1] * 100 + h.z3d(i), h.diam3d(i))

        h.pop_section()
