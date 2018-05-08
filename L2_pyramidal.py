# L2_pyramidal.py - est class def for layer 2 pyramidal cells
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: removed dep on it.izip)
# last rev: (SL: toward python3, moved cells)

import sys
import os
import numpy as np

from neuron import h
from cell import Pyr
import paramrw
import params_default as p_default

# Units for e: mV
# Units for gbar: S/cm^2 unless otherwise noted

# Layer 2 pyramidal cell class
class L2Pyr(Pyr):

    def __init__(self, gid = -1, pos = -1, p={}):
        # Get default L2Pyr params and update them with any corresponding params in p
        p_all_default = p_default.get_L2Pyr_params_default()
        self.p_all = paramrw.compare_dictionaries(p_all_default, p)

        # Get somatic, dendritic, and synapse properties
        p_soma = self.__get_soma_props(pos)
        p_dend = self.__get_dend_props()
        p_syn = self.__get_syn_props()
        # p_dend_props, dend_names = self.__get_dend_props()

        # usage: Pyr.__init__(self, soma_props)
        Pyr.__init__(self, gid, p_soma)
        self.celltype = 'L2_pyramidal'

        # geometry
        # creates dict of dends: self.dends
        self.create_dends(p_dend)
        self.topol() # sets the connectivity between sections
        self.geom(p_dend) # sets geom properties; adjusted after translation from hoc (2009 model)

        # biophysics
        self.__biophys_soma()
        self.__biophys_dends()

        # dipole_insert() comes from Cell()
        self.yscale = self.get_sectnames()
        self.dipole_insert(self.yscale)

        # create synapses
        self.__synapse_create(p_syn)
        # self.__synapse_create()

        # run record_current_soma(), defined in Cell()
        self.record_current_soma()

    # insert IClamps in all situations
    # temporarily an external function taking the p dict
    def create_all_IClamp(self, p):
        # list of sections for this celltype
        sect_list_IClamp = [
            'soma',
        ]

        # some parameters
        t_delay = p['Itonic_t0_L2Pyr_soma']

        # T = -1 means use h.tstop
        if p['Itonic_T_L2Pyr_soma'] == -1:
            # t_delay = 50.
            t_dur = h.tstop - t_delay

        else:
            t_dur = p['Itonic_T_L2Pyr_soma'] - t_delay

        # t_dur must be nonnegative, I imagine
        if t_dur < 0.:
            t_dur = 0.

        # properties of the IClamp
        props_IClamp = {
            'loc': 0.5,
            'delay': t_delay,
            'dur': t_dur,
            'amp': p['Itonic_A_L2Pyr_soma']
        }

        # iterate through list of sect_list_IClamp to create a persistent IClamp object
        # the insert_IClamp procedure is in Cell() and checks on names
        # so names must be actual section names, or else it will fail silently
        self.list_IClamp = [self.insert_IClamp(sect_name, props_IClamp) for sect_name in sect_list_IClamp]

    # Returns hardcoded somatic properties
    def __get_soma_props(self, pos):
        return {
            'pos': pos,
            'L': self.p_all['L2Pyr_soma_L'],
            'diam': self.p_all['L2Pyr_soma_diam'],
            'cm': self.p_all['L2Pyr_soma_cm'],
            'Ra': self.p_all['L2Pyr_soma_Ra'],
            'name': 'L2Pyr',
        }

    # Returns hardcoded dendritic properties
    def __get_dend_props(self):
        return {
            'apical_trunk': {
                'L': self.p_all['L2Pyr_apicaltrunk_L'] ,
                'diam': self.p_all['L2Pyr_apicaltrunk_diam'],
                'cm': self.p_all['L2Pyr_dend_cm'],
                'Ra': self.p_all['L2Pyr_dend_Ra'],
            },
            'apical_1': {
                'L': self.p_all['L2Pyr_apical1_L'],
                'diam': self.p_all['L2Pyr_apical1_diam'],
                'cm': self.p_all['L2Pyr_dend_cm'],
                'Ra': self.p_all['L2Pyr_dend_Ra'],
            },
            'apical_tuft': {
                'L': self.p_all['L2Pyr_apicaltuft_L'],
                'diam': self.p_all['L2Pyr_apicaltuft_diam'],
                'cm': self.p_all['L2Pyr_dend_cm'],
                'Ra': self.p_all['L2Pyr_dend_Ra'],
            },
            'apical_oblique': {
                'L': self.p_all['L2Pyr_apicaloblique_L'],
                'diam': self.p_all['L2Pyr_apicaloblique_diam'],
                'cm': self.p_all['L2Pyr_dend_cm'],
                'Ra': self.p_all['L2Pyr_dend_Ra'],
            },
            'basal_1': {
                'L': self.p_all['L2Pyr_basal1_L'],
                'diam': self.p_all['L2Pyr_basal1_diam'],
                'cm': self.p_all['L2Pyr_dend_cm'],
                'Ra': self.p_all['L2Pyr_dend_Ra'],
            },
            'basal_2': {
                'L': self.p_all['L2Pyr_basal2_L'],
                'diam': self.p_all['L2Pyr_basal2_diam'],
                'cm': self.p_all['L2Pyr_dend_cm'],
                'Ra': self.p_all['L2Pyr_dend_Ra'],
            },
            'basal_3': {
                'L': self.p_all['L2Pyr_basal3_L'],
                'diam': self.p_all['L2Pyr_basal3_diam'],
                'cm': self.p_all['L2Pyr_dend_cm'],
                'Ra': self.p_all['L2Pyr_dend_Ra'],
            },
        }

        # This order matters!
        # dend_order = ['apical_trunk', 'apical_1', 'apical_tuft', 'apical_oblique',
        #              'basal_1', 'basal_2', 'basal_3']

        # return dend_props, dend_order

    def __get_syn_props(self):
        return {
            'ampa': {
                'e': self.p_all['L2Pyr_ampa_e'],
                'tau1': self.p_all['L2Pyr_ampa_tau1'],
                'tau2': self.p_all['L2Pyr_ampa_tau2'],
            },
            'nmda': {
                'e': self.p_all['L2Pyr_nmda_e'],
                'tau1': self.p_all['L2Pyr_nmda_tau1'],
                'tau2': self.p_all['L2Pyr_nmda_tau2'],
            },
            'gabaa': {
                'e': self.p_all['L2Pyr_gabaa_e'],
                'tau1': self.p_all['L2Pyr_gabaa_tau1'],
                'tau2': self.p_all['L2Pyr_gabaa_tau2'],
            },
            'gabab': {
                'e': self.p_all['L2Pyr_gabab_e'],
                'tau1': self.p_all['L2Pyr_gabab_tau1'],
                'tau2': self.p_all['L2Pyr_gabab_tau2'],
            }
        }

    def geom (self, p_dend):
      soma = self.soma; dend = self.list_dend;
      # increased by 70% for human
      soma.L = 22.1
      dend[0].L = 59.5
      dend[1].L = 340
      dend[2].L = 306
      dend[3].L = 238
      dend[4].L = 85
      dend[5].L = 255
      dend[6].L = 255
      soma.diam = 23.4
      dend[0].diam = 4.25
      dend[1].diam = 3.91
      dend[2].diam = 4.08
      dend[3].diam = 3.4
      dend[4].diam = 4.25
      dend[5].diam = 2.72
      dend[6].diam = 2.72
      self.set_dend_props(p_dend) # resets length,diam,etc. based on param specification

    # Connects sections of THIS cell together
    def topol (self):
        """ original topol
        connect dend(0), soma(1)
        for i = 1, 2 connect dend[i](0), dend(1)
        connect dend[3](0), dend[2](1)
        connect dend[4](0), soma(0) //was soma(1), 0 is correct!
        for i = 5, 6 connect dend[i](0), dend[4](1)

        """

        # child.connect(parent, parent_end, {child_start=0})
        # Distal (Apical)
        self.dends['apical_trunk'].connect(self.soma, 1, 0)
        self.dends['apical_1'].connect(self.dends['apical_trunk'], 1, 0)
        self.dends['apical_tuft'].connect(self.dends['apical_1'], 1, 0)

        # apical_oblique comes off distal end of apical_trunk
        self.dends['apical_oblique'].connect(self.dends['apical_trunk'], 1, 0)

        # Proximal (basal)
        self.dends['basal_1'].connect(self.soma, 0, 0)
        self.dends['basal_2'].connect(self.dends['basal_1'], 1, 0)
        self.dends['basal_3'].connect(self.dends['basal_1'], 1, 0)

        self.basic_shape() # translated from original hoc (2009 model)

    def basic_shape (self):
      # THESE AND LENGHTHS MUST CHANGE TOGETHER!!!
      pt3dclear=h.pt3dclear; pt3dadd=h.pt3dadd; soma = self.soma; dend = self.list_dend
      pt3dclear(sec=soma); pt3dadd(-50, 765, 0, 1,sec=soma); pt3dadd(-50, 778, 0, 1,sec=soma)
      pt3dclear(sec=dend[0]); pt3dadd(-50, 778, 0, 1,sec=dend[0]); pt3dadd(-50, 813, 0, 1,sec=dend[0])
      pt3dclear(sec=dend[1]); pt3dadd(-50, 813, 0, 1,sec=dend[1]); pt3dadd(-250, 813, 0, 1,sec=dend[1])
      pt3dclear(sec=dend[2]); pt3dadd(-50, 813, 0, 1,sec=dend[2]); pt3dadd(-50, 993, 0, 1,sec=dend[2])
      pt3dclear(sec=dend[3]); pt3dadd(-50, 993, 0, 1,sec=dend[3]); pt3dadd(-50, 1133, 0, 1,sec=dend[3])
      pt3dclear(sec=dend[4]); pt3dadd(-50, 765, 0, 1,sec=dend[4]); pt3dadd(-50, 715, 0, 1,sec=dend[4])
      pt3dclear(sec=dend[5]); pt3dadd(-50, 715, 0, 1,sec=dend[5]); pt3dadd(-156, 609, 0, 1,sec=dend[5])
      pt3dclear(sec=dend[6]); pt3dadd(-50, 715, 0, 1,sec=dend[6]); pt3dadd(56, 609, 0, 1,sec=dend[6])

    # Adds biophysics to soma
    def __biophys_soma (self):
        # set soma biophysics specified in Pyr
        # self.pyr_biophys_soma()

        # Insert 'hh2' mechanism
        self.soma.insert('hh2')
        self.soma.gkbar_hh2 = self.p_all['L2Pyr_soma_gkbar_hh2']
        self.soma.gl_hh2 = self.p_all['L2Pyr_soma_gl_hh2']
        self.soma.el_hh2 = self.p_all['L2Pyr_soma_el_hh2']
        self.soma.gnabar_hh2 = self.p_all['L2Pyr_soma_gnabar_hh2']

        # Insert 'km' mechanism
        # Units: pS/um^2
        self.soma.insert('km')
        self.soma.gbar_km = self.p_all['L2Pyr_soma_gbar_km']

    # Defining biophysics for dendrites
    def __biophys_dends (self):
        # set dend biophysics
        # iterate over keys in self.dends and set biophysics for each dend
        for key in self.dends:
            # neuron syntax is used to set values for mechanisms
            # sec.gbar_mech = x sets value of gbar for mech to x for all segs
            # in a section. This method is significantly faster than using
            # a for loop to iterate over all segments to set mech values

            # Insert 'hh' mechanism
            self.dends[key].insert('hh2')
            self.dends[key].gkbar_hh2 = self.p_all['L2Pyr_dend_gkbar_hh2']
            self.dends[key].gl_hh2 = self.p_all['L2Pyr_dend_gl_hh2']
            self.dends[key].gnabar_hh2 = self.p_all['L2Pyr_dend_gnabar_hh2']
            self.dends[key].el_hh2 = self.p_all['L2Pyr_dend_el_hh2']

            # Insert 'km' mechanism
            # Units: pS/um^2
            self.dends[key].insert('km')
            self.dends[key].gbar_km = self.p_all['L2Pyr_dend_gbar_km']

    def __synapse_create (self, p_syn):
        # creates synapses onto this cell
        # Somatic synapses
        self.synapses = {
            'soma_gabaa': self.syn_create(self.soma(0.5), p_syn['gabaa']),
            'soma_gabab': self.syn_create(self.soma(0.5), p_syn['gabab']),
        }

        # Dendritic synapses
        self.apicaloblique_ampa = self.syn_create(self.dends['apical_oblique'](0.5), p_syn['ampa'])
        self.apicaloblique_nmda = self.syn_create(self.dends['apical_oblique'](0.5), p_syn['nmda'])

        self.basal2_ampa = self.syn_create(self.dends['basal_2'](0.5), p_syn['ampa'])
        self.basal2_nmda = self.syn_create(self.dends['basal_2'](0.5), p_syn['nmda'])

        self.basal3_ampa = self.syn_create(self.dends['basal_3'](0.5), p_syn['ampa'])
        self.basal3_nmda = self.syn_create(self.dends['basal_3'](0.5), p_syn['nmda'])

        self.apicaltuft_ampa = self.syn_create(self.dends['apical_tuft'](0.5), p_syn['ampa'])
        self.apicaltuft_nmda = self.syn_create(self.dends['apical_tuft'](0.5), p_syn['nmda'])

        # self.synapses = {
        #     'soma_gabaa': self.syn_gabaa_create(self.soma(0.5)),
        #     'soma_gabab': self.syn_gabab_create(self.soma(0.5)),
        # }

        # Dendritic synapses
        # self.apicaloblique_ampa = self.syn_ampa_create(self.dends['apical_oblique'](0.5), p_syn['ampa'])
        # self.apicaloblique_nmda = self.syn_create(self.dends['apical_oblique'](0.5), p_syn['nmda'])

        # self.basal2_ampa = self.syn_ampa_create(self.dends['basal_2'](0.5))
        # self.basal2_nmda = self.syn_nmda_create(self.dends['basal_2'](0.5))

        # self.basal3_ampa = self.syn_ampa_create(self.dends['basal_3'](0.5))
        # self.basal3_nmda = self.syn_nmda_create(self.dends['basal_3'](0.5))

        # self.apicaltuft_ampa = self.syn_ampa_create(self.dends['apical_tuft'](0.5))
        # self.apicaltuft_nmda = self.syn_nmda_create(self.dends['apical_tuft'](0.5))

    # collect receptor-type-based connections here
    def parconnect (self, gid, gid_dict, pos_dict, p):
        # init dict of dicts
        # nc_dict for ampa and nmda may be the same for this cell type
        nc_dict = {
            'ampa': None,
            'nmda': None,
        }

        # Connections FROM all other L2 Pyramidal cells to this one
        for gid_src, pos in zip(gid_dict['L2_pyramidal'], pos_dict['L2_pyramidal']):
            # don't be redundant, this is only possible for LIKE cells, but it might not hurt to check
            if gid_src != gid:
                nc_dict['ampa'] = {
                    'pos_src': pos,
                    'A_weight': p['gbar_L2Pyr_L2Pyr_ampa'],
                    'A_delay': 1.,
                    'lamtha': 3.,
                    'threshold': p['threshold'],
                    'type_src' : 'L2_pyramidal'
                }

                # parconnect_from_src(gid_presyn, nc_dict, postsyn)
                # ampa connections
                self.ncfrom_L2Pyr.append(self.parconnect_from_src(gid_src, nc_dict['ampa'], self.apicaloblique_ampa))
                self.ncfrom_L2Pyr.append(self.parconnect_from_src(gid_src, nc_dict['ampa'], self.basal2_ampa))
                self.ncfrom_L2Pyr.append(self.parconnect_from_src(gid_src, nc_dict['ampa'], self.basal3_ampa))

                nc_dict['nmda'] = {
                    'pos_src': pos,
                    'A_weight': p['gbar_L2Pyr_L2Pyr_nmda'],
                    'A_delay': 1.,
                    'lamtha': 3.,
                    'threshold': p['threshold'],
                    'type_src' : 'L2_pyramidal'
                }

                # parconnect_from_src(gid_presyn, nc_dict, postsyn)
                # nmda connections
                self.ncfrom_L2Pyr.append(self.parconnect_from_src(gid_src, nc_dict['nmda'], self.apicaloblique_nmda))
                self.ncfrom_L2Pyr.append(self.parconnect_from_src(gid_src, nc_dict['nmda'], self.basal2_nmda))
                self.ncfrom_L2Pyr.append(self.parconnect_from_src(gid_src, nc_dict['nmda'], self.basal3_nmda))

        # connections FROM L2 basket cells TO this L2Pyr cell
        for gid_src, pos in zip(gid_dict['L2_basket'], pos_dict['L2_basket']):
            nc_dict['gabaa'] = {
                'pos_src': pos,
                'A_weight': p['gbar_L2Basket_L2Pyr_gabaa'],
                'A_delay': 1.,
                'lamtha': 50.,
                'threshold': p['threshold'],
                'type_src' : 'L2_basket'
            }

            nc_dict['gabab'] = {
                'pos_src': pos,
                'A_weight': p['gbar_L2Basket_L2Pyr_gabab'],
                'A_delay': 1.,
                'lamtha': 50.,
                'threshold': p['threshold'],
                'type_src' : 'L2_basket'
            }

            self.ncfrom_L2Basket.append(self.parconnect_from_src(gid_src, nc_dict['gabaa'], self.synapses['soma_gabaa']))
            self.ncfrom_L2Basket.append(self.parconnect_from_src(gid_src, nc_dict['gabab'], self.synapses['soma_gabab']))

        # connections FROM L5 basket cells TO this L2Pyr cell
        # for gid_src in gid_dict['L5_basket']:
        #     nc_dict = {
        #         'pos_src': pos_list[gid_src],
        #         'A_weight': 2.5e-2,
        #         'A_delay': 1.,
        #         'lamtha': 70.
        #     }

        #     self.ncfrom_L5Basket.append(self.parconnect_from_src(gid_src, nc_dict, self.synapes['soma_gabaa']))
        #     self.ncfrom_L5Basket.append(self.parconnect_from_src(gid_src, nc_dict, self.synapes['soma_gabab']))

    # may be reorganizable
    def parreceive (self, gid, gid_dict, pos_dict, p_ext):
        for gid_src, p_src, pos in zip(gid_dict['extinput'], p_ext, pos_dict['extinput']):
            # Check if AMPA params defined in p_src
            if 'L2Pyr_ampa' in p_src.keys():
                nc_dict_ampa = {
                    'pos_src': pos,
                    'A_weight': p_src['L2Pyr_ampa'][0],
                    'A_delay': p_src['L2Pyr_ampa'][1],
                    'lamtha': p_src['lamtha'],
                    'threshold': p_src['threshold'],
                    'type_src': 'ext'
                }

                # Proximal feed AMPA synapses
                if p_src['loc'] is 'proximal':
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_ampa, self.basal2_ampa))
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_ampa, self.basal3_ampa))
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_ampa, self.apicaloblique_ampa))
                # Distal feed AMPA synapses
                elif p_src['loc'] is 'distal':
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_ampa, self.apicaltuft_ampa))

            # Check is NMDA params defined in p_src
            if 'L2Pyr_nmda' in p_src.keys():
                nc_dict_nmda = {
                    'pos_src': pos,
                    'A_weight': p_src['L2Pyr_nmda'][0],
                    'A_delay': p_src['L2Pyr_nmda'][1],
                    'lamtha': p_src['lamtha'],
                    'threshold': p_src['threshold'],
                    'type_src': 'ext'
                }

                # Proximal feed NMDA synapses
                if p_src['loc'] is 'proximal':
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_nmda, self.basal2_nmda))
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_nmda, self.basal3_nmda))
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_nmda, self.apicaloblique_nmda))
                # Distal feed NMDA synapses
                elif p_src['loc'] is 'distal':
                    self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_nmda, self.apicaltuft_nmda))

    # one parreceive function to handle all types of external parreceives
    # types must be defined explicitly here
    # this function handles evoked, gaussian, and poisson inputs
    def parreceive_ext (self, type, gid, gid_dict, pos_dict, p_ext):
        if type.startswith(('evprox', 'evdist')):
            if self.celltype in p_ext.keys():
                gid_ev = gid + gid_dict[type][0]

                # separate dictionaries for ampa and nmda evoked inputs
                nc_dict_ampa = {
                    'pos_src': pos_dict[type][gid],
                    'A_weight': p_ext[self.celltype][0], # index 0 for ampa weight
                    'A_delay': p_ext[self.celltype][2], # index 2 for delay
                    'lamtha': p_ext['lamtha_space'],
                    'threshold': p_ext['threshold'],
                    'type_src': type
                }

                nc_dict_nmda = {
                    'pos_src': pos_dict[type][gid],
                    'A_weight': p_ext[self.celltype][1], # index 1 for nmda weight
                    'A_delay': p_ext[self.celltype][2], # index 2 for delay
                    'lamtha': p_ext['lamtha_space'],
                    'threshold': p_ext['threshold'],
                    'type_src': type
                }

                if p_ext['loc'] is 'proximal':
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_ampa, self.basal2_ampa))
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_ampa, self.basal3_ampa))
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_ampa, self.apicaloblique_ampa))

                    # NEW: note that default/original is 0 nmda weight for these proximal dends
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_nmda, self.basal2_nmda))
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_nmda, self.basal3_nmda))
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_nmda, self.apicaloblique_nmda))

                elif p_ext['loc'] is 'distal':
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_ampa, self.apicaltuft_ampa))
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict_nmda, self.apicaltuft_nmda))

        elif type == 'extgauss':
            # gid is this cell's gid
            # gid_dict is the whole dictionary, including the gids of the extgauss
            # pos_list is also the pos of the extgauss (net origin)
            # p_ext_gauss are the params (strength, etc.)

            # gid shift is based on L2_pyramidal cells NOT L5
            # I recognize this is ugly (hack)
            # gid_shift = gid_dict['extgauss'][0] - gid_dict['L2_pyramidal'][0]
            if 'L2_pyramidal' in p_ext.keys():
                gid_extgauss = gid + gid_dict['extgauss'][0]

                nc_dict = {
                    'pos_src': pos_dict['extgauss'][gid],
                    'A_weight': p_ext['L2_pyramidal'][0], # index 0 for ampa weight (nmda not yet used in Gauss)
                    'A_delay': p_ext['L2_pyramidal'][2], # index 2 for delay
                    'lamtha': p_ext['lamtha'],
                    'threshold': p_ext['threshold'],
                    'type_src': type
                }

                self.ncfrom_extgauss.append(self.parconnect_from_src(gid_extgauss,nc_dict,self.basal2_ampa))
                self.ncfrom_extgauss.append(self.parconnect_from_src(gid_extgauss,nc_dict,self.basal3_ampa))
                self.ncfrom_extgauss.append(self.parconnect_from_src(gid_extgauss,nc_dict,self.apicaloblique_ampa))

        elif type == 'extpois':
            if self.celltype in p_ext.keys():
                gid_extpois = gid + gid_dict['extpois'][0]

                nc_dict = {
                    'pos_src': pos_dict['extpois'][gid],
                    'A_weight': p_ext[self.celltype][0], # index 0 for ampa weight
                    'A_delay': p_ext[self.celltype][2], # index 2 for delay
                    'lamtha': p_ext['lamtha_space'],
                    'threshold': p_ext['threshold'],
                    'type_src': type
                }

                self.ncfrom_extpois.append(self.parconnect_from_src(gid_extpois,nc_dict,self.basal2_ampa))
                self.ncfrom_extpois.append(self.parconnect_from_src(gid_extpois,nc_dict,self.basal3_ampa))
                self.ncfrom_extpois.append(self.parconnect_from_src(gid_extpois,nc_dict,self.apicaloblique_ampa))

                if p_ext[self.celltype][1] > 0.0:
                  nc_dict['A_weight'] = p_ext[self.celltype][1] # index 1 for nmda weight
                  self.ncfrom_extpois.append(self.parconnect_from_src(gid_extpois,nc_dict,self.basal2_nmda))
                  self.ncfrom_extpois.append(self.parconnect_from_src(gid_extpois,nc_dict,self.basal3_nmda))
                  self.ncfrom_extpois.append(self.parconnect_from_src(gid_extpois,nc_dict,self.apicaloblique_nmda))

        else:
            print("Warning, ext type def does not exist in L2Pyr")

    # Define 3D shape and position of cell. By default neuron uses xy plane for
    # height and xz plane for depth. This is opposite for model as a whole, but
    # convention is followed in this function for ease use of gui.
    def __set_3Dshape (self):
        # set 3d shape of soma by calling shape_soma from class Cell
        # print("Warning: You are setiing 3d shape geom. You better be doing")
        # print("gui analysis and not numerical analysis!!")
        self.shape_soma()

        # soma proximal coords
        x_prox = 0
        y_prox = 0

        # soma distal coords
        x_distal = 0
        y_distal = self.soma.L

        # dend 0-2 are major axis, dend 3 is branch
        # deal with distal first along major cable axis
        # the way this is assigning variables is ugly/lazy right now
        for i in range(0, 3):
            h.pt3dclear(sec=self.list_dend[i])

            # x_distal and y_distal are the starting points for each segment
            # these are updated at the end of the loop
            h.pt3dadd(0, y_distal, 0, self.dend_diam[i], sec=self.list_dend[i])

            # update x_distal and y_distal after setting them
            # x_distal += dend_dx[i]
            y_distal += self.dend_L[i]

            # add next point
            h.pt3dadd(0, y_distal, 0, self.dend_diam[i], sec=self.list_dend[i])

        # now deal with dend 3
        # dend 3 will ALWAYS be positioned at the end of dend[0]
        h.pt3dclear(sec=self.list_dend[3])

        # activate this section with 'sec =' notation
        # self.list_dend[0].push()
        x_start = h.x3d(1, sec = self.list_dend[0])
        y_start = h.y3d(1, sec = self.list_dend[0])
        # h.pop_section()

        h.pt3dadd(x_start, y_start, 0, self.dend_diam[3], sec=self.list_dend[3])
        # self.dend_L[3] is subtracted because lengths always positive,
        # and this goes to negative x
        h.pt3dadd(x_start-self.dend_L[3], y_start, 0, self.dend_diam[3], sec=self.list_dend[3])

        # now deal with proximal dends
        for i in range(4, 7):
            h.pt3dclear(sec=self.list_dend[i])

        # deal with dend 4, ugly. sorry.
        h.pt3dadd(x_prox, y_prox, 0, self.dend_diam[i], sec=self.list_dend[4])
        y_prox += -self.dend_L[4]

        h.pt3dadd(x_prox, y_prox, 0, self.dend_diam[4], sec=self.list_dend[4])

        # x_prox, y_prox are now the starting points for BOTH last 2 sections

        # dend 5
        # Calculate x-coordinate for end of dend
        dend5_x = -self.dend_L[5] * np.sqrt(2) / 2.
        h.pt3dadd(x_prox, y_prox, 0, self.dend_diam[5], sec=self.list_dend[5])
        h.pt3dadd(dend5_x, y_prox-self.dend_L[5] * np.sqrt(2) / 2.,
                    0, self.dend_diam[5], sec=self.list_dend[5])

        # dend 6
        # Calculate x-coordinate for end of dend
        dend6_x = self.dend_L[6] * np.sqrt(2) / 2.
        h.pt3dadd(x_prox, y_prox, 0, self.dend_diam[6], sec=self.list_dend[6])
        h.pt3dadd(dend6_x, y_prox-self.dend_L[6] * np.sqrt(2) / 2.,
                    0, self.dend_diam[6], sec=self.list_dend[6])

        # set 3D position
        # z grid position used as y coordinate in h.pt3dchange() to satisfy
        # gui convention that y is height and z is depth. In h.pt3dchange()
        # x and z components are scaled by 100 for visualization clarity
        self.soma.push()
        for i in range(0, int(h.n3d())):
            h.pt3dchange(i, self.pos[0]*100 + h.x3d(i), self.pos[2] +
                           h.y3d(i), self.pos[1] * 100 + h.z3d(i),
                           h.diam3d(i))

        h.pop_section()
