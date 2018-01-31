# L2_basket.py - establish class def for layer 2 basket cells
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: removed dependence on it.izip)
# last rev: (SL: toward python3)

from neuron import h as nrn
from cell import BasketSingle

# Units for e: mV
# Units for gbar: S/cm^2 unless otherwise noted

# Layer 2 basket cell class
class L2Basket(BasketSingle):
    def __init__(self, gid = -1, pos = -1):
        # BasketSingle.__init__(self, pos, L, diam, Ra, cm)
        # Note: Basket cell properties set in BasketSingle())
        BasketSingle.__init__(self, gid, pos, 'L2Basket')
        self.celltype = 'L2_basket'

        self.__synapse_create()
        self.__biophysics()

    # creation of synapses
    def __synapse_create(self):
        # creates synapses onto this cell
        self.soma_ampa = self.syn_ampa_create(self.soma(0.5))
        self.soma_gabaa = self.syn_gabaa_create(self.soma(0.5))
        self.soma_nmda = self.syn_nmda_create(self.soma(0.5))

    def __biophysics(self):
        self.soma.insert('hh2')

    # insert IClamps in all situations
    def create_all_IClamp(self, p):
        # list of sections for this celltype
        sect_list_IClamp = [
            'soma',
        ]

        # some parameters
        t_delay = p['Itonic_t0_L2Basket']

        # T = -1 means use nrn.tstop
        if p['Itonic_T_L2Basket'] == -1:
            t_dur = nrn.tstop - t_delay

        else:
            t_dur = p['Itonic_T_L2Basket'] - t_delay

        # t_dur must be nonnegative, I imagine
        if t_dur < 0.:
            t_dur = 0.

        # properties of the IClamp
        props_IClamp = {
            'loc': 0.5,
            'delay': t_delay,
            'dur': t_dur,
            'amp': p['Itonic_A_L2Basket']
        }

        # iterate through list of sect_list_IClamp to create a persistent IClamp object
        # the insert_IClamp procedure is in Cell() and checks on names
        # so names must be actual section names, or else it will fail silently
        # self.list_IClamp as a variable is guaranteed in Cell()
        self.list_IClamp = [self.insert_IClamp(sect_name, props_IClamp) for sect_name in sect_list_IClamp]

    # par connect between all presynaptic cells
    # no connections from L5Pyr or L5Basket to L2Baskets
    def parconnect(self, gid, gid_dict, pos_dict, p):
        # FROM L2 pyramidals TO this cell
        for gid_src, pos in zip(gid_dict['L2_pyramidal'], pos_dict['L2_pyramidal']):
            nc_dict = {
                'pos_src': pos,
                'A_weight': p['gbar_L2Pyr_L2Basket'],
                'A_delay': 1.,
                'lamtha': 3.,
                'threshold': p['threshold']
            }

            self.ncfrom_L2Pyr.append(self.parconnect_from_src(gid_src, nc_dict, self.soma_ampa))

        # FROM other L2Basket cells
        for gid_src, pos in zip(gid_dict['L2_basket'], pos_dict['L2_basket']):
            # no autapses
            # if gid_src != gid:
            nc_dict = {
                'pos_src': pos,
                'A_weight': p['gbar_L2Basket_L2Basket'],
                'A_delay': 1.,
                'lamtha': 20.,
                'threshold': p['threshold']
            }

            self.ncfrom_L2Basket.append(self.parconnect_from_src(gid_src, nc_dict, self.soma_gabaa))

    # this function might make more sense as a method of net?
    # par: receive from external inputs
    def parreceive(self, gid, gid_dict, pos_dict, p_ext):
        # for some gid relating to the input feed:
        for gid_src, p_src, pos in zip(gid_dict['extinput'], p_ext, pos_dict['extinput']):
            # check if AMPA params are defined in the p_src
            if 'L2Basket_ampa' in p_src.keys():
                # create an nc_dict
                nc_dict_ampa = {
                    'pos_src': pos,
                    'A_weight': p_src['L2Basket_ampa'][0],
                    'A_delay': p_src['L2Basket_ampa'][1],
                    'lamtha': p_src['lamtha'],
                    'threshold': p_src['threshold']
                }

                # AMPA synapse
                self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_ampa, self.soma_ampa))

            # Check if NMDA params are defined in p_src
            if 'L2Basket_nmda' in p_src.keys():
                nc_dict_nmda = {
                    'pos_src': pos,
                    'A_weight': p_src['L2Basket_nmda'][0],
                    'A_delay': p_src['L2Basket_nmda'][1],
                    'lamtha': p_src['lamtha'],
                    'threshold': p_src['threshold']
                }

                # NMDA synapse
                self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_nmda, self.soma_nmda))

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
                    'lamtha': p_ext['lamtha_space'],
                    'threshold': p_ext['threshold']
                }

                # connections depend on location of input
                if p_ext['loc'] is 'proximal':
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict, self.soma_ampa))

                elif p_ext['loc'] is 'distal':
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict, self.soma_ampa))
                    self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict, self.soma_nmda))

        elif type == 'extgauss':
            # gid is this cell's gid
            # gid_dict is the whole dictionary, including the gids of the extgauss
            # pos_list is also the pos of the extgauss (net origin)
            # p_ext_gauss are the params (strength, etc.)
            # I recognize this is ugly (hack)
            if self.celltype in p_ext.keys():
                # since gid ids are unique, then these will all be shifted.
                # if order of extgauss random feeds ever matters (likely)
                # then will have to preserve order
                # of creation based on gid ids of the cells
                # this is a dumb place to put this information
                gid_extgauss = gid + gid_dict['extgauss'][0]

                # gid works here because there are as many pos items in pos_dict['extgauss'] as there are cells
                nc_dict = {
                    'pos_src': pos_dict['extgauss'][gid],
                    'A_weight': p_ext[self.celltype][0],
                    'A_delay': p_ext[self.celltype][1],
                    'lamtha': p_ext['lamtha'],
                    'threshold': p_ext['threshold']
                }

                self.ncfrom_extgauss.append(self.parconnect_from_src(gid_extgauss, nc_dict, self.soma_ampa))

        elif type == 'extpois':
            if self.celltype in p_ext.keys():
                gid_extpois = gid + gid_dict['extpois'][0]

                nc_dict = {
                    'pos_src': pos_dict['extpois'][gid],
                    'A_weight': p_ext[self.celltype][0],
                    'A_delay': p_ext[self.celltype][1],
                    'lamtha': p_ext['lamtha_space'],
                    'threshold': p_ext['threshold']
                }

                self.ncfrom_extpois.append(self.parconnect_from_src(gid_extpois, nc_dict, self.soma_ampa))

        else:
            print("Warning, type def not specified in L2Basket")
