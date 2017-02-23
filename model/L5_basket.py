# L5_basket.py - establish class def for layer 5 basket cells
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: removed izip dep)
# last rev: (SL: toward python3)

from neuron import h as nrn
from cell import BasketSingle

# Units for e: mV
# Units for gbar: S/cm^2 unless otherwise noted

# Layer 5 basket cell class
class L5Basket(BasketSingle):
    def __init__(self, pos):
        # Note: Cell properties are set in BasketSingle()
        BasketSingle.__init__(self, pos, 'L5Basket')
        self.celltype = 'L5_basket'

        self.__synapse_create()
        self.__biophysics()

    # creates synapses
    def __synapse_create(self):
        # creates synapses onto this cell
        self.soma_ampa = self.syn_ampa_create(self.soma(0.5))
        self.soma_nmda = self.syn_nmda_create(self.soma(0.5))
        self.soma_gabaa = self.syn_gabaa_create(self.soma(0.5))

    # insert IClamps in all situations
    def create_all_IClamp(self, p):
        """ temporarily an external function taking the p dict
        """
        # list of sections for this celltype
        sect_list_IClamp = [
            'soma',
        ]

        # some parameters
        t_delay = p['Itonic_t0_L5Basket']

        # T = -1 means use nrn.tstop
        if p['Itonic_T_L5Basket'] == -1:
            t_dur = nrn.tstop - t_delay

        else:
            t_dur = p['Itonic_T_L5Basket'] - t_delay

        # t_dur must be nonnegative, I imagine
        if t_dur < 0.:
            t_dur = 0.

        # properties of the IClamp
        props_IClamp = {
            'loc': 0.5,
            'delay': t_delay,
            'dur': t_dur,
            'amp': p['Itonic_A_L5Basket']
        }

        # iterate through list of sect_list_IClamp to create a persistent IClamp object
        # the insert_IClamp procedure is in Cell() and checks on names
        # so names must be actual section names, or else it will fail silently
        self.list_IClamp = [self.insert_IClamp(sect_name, props_IClamp) for sect_name in sect_list_IClamp]

    # defines biophysics
    def __biophysics(self):
        self.soma.insert('hh')

    # connections FROM other cells TO this cell
    # there are no connections from the L2Basket cells. congrats!
    def parconnect(self, gid, gid_dict, pos_dict, p):
        # FROM other L5Basket cells TO this cell
        for gid_src, pos in zip(gid_dict['L5_basket'], pos_dict['L5_basket']):
            if gid_src != gid:
                nc_dict = {
                    'pos_src': pos,
                    'A_weight': p['gbar_L5Basket_L5Basket'],
                    'A_delay': 1.,
                    'lamtha': 20.,
                }

                self.ncfrom_L5Basket.append(self.parconnect_from_src(gid_src, nc_dict, self.soma_gabaa))

        # FROM other L5Pyr cells TO this cell
        for gid_src, pos in zip(gid_dict['L5_pyramidal'], pos_dict['L5_pyramidal']):
            nc_dict = {
                'pos_src': pos,
                'A_weight': p['gbar_L5Pyr_L5Basket'],
                'A_delay': 1.,
                'lamtha': 3.,
            }

            self.ncfrom_L5Pyr.append(self.parconnect_from_src(gid_src, nc_dict, self.soma_ampa))

        # FROM other L2Pyr cells TO this cell
        for gid_src, pos in zip(gid_dict['L2_pyramidal'], pos_dict['L2_pyramidal']):
            nc_dict = {
                'pos_src': pos,
                'A_weight': p['gbar_L2Pyr_L5Basket'],
                'A_delay': 1.,
                'lamtha': 3.,
            }

            self.ncfrom_L2Pyr.append(self.parconnect_from_src(gid_src, nc_dict, self.soma_ampa))

    # parallel receive function parreceive()
    def parreceive(self, gid, gid_dict, pos_dict, p_ext):
        for gid_src, p_src, pos in zip(gid_dict['extinput'], p_ext, pos_dict['extinput']):
            # Check if AMPA params are define in p_src
            if 'L5Basket_ampa' in p_src.keys():
                nc_dict_ampa = {
                    'pos_src': pos,
                    'A_weight': p_src['L5Basket_ampa'][0],
                    'A_delay': p_src['L5Basket_ampa'][1],
                    'lamtha': p_src['lamtha']
                }

                # AMPA synapse
                self.ncfrom_extinput.append(self.parconnect_from_src(gid_src, nc_dict_ampa, self.soma_ampa))

            # Check if nmda params are define in p_src
            if 'L5Basket_nmda' in p_src.keys():
                nc_dict_nmda = {
                    'pos_src': pos,
                    'A_weight': p_src['L5Basket_nmda'][0],
                    'A_delay': p_src['L5Basket_nmda'][1],
                    'lamtha': p_src['lamtha']
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
                    'lamtha': p_ext['lamtha_space']
                }

                self.ncfrom_ev.append(self.parconnect_from_src(gid_ev, nc_dict, self.soma_ampa))

        elif type == 'extgauss':
            # gid is this cell's gid
            # gid_dict is the whole dictionary, including the gids of the extgauss
            # pos_dict is also the pos of the extgauss (net origin)
            # p_ext_gauss are the params (strength, etc.)
            if 'L5_basket' in p_ext.keys():
                gid_extgauss = gid + gid_dict['extgauss'][0]

                nc_dict = {
                    'pos_src': pos_dict['extgauss'][gid],
                    'A_weight': p_ext['L5_basket'][0],
                    'A_delay': p_ext['L5_basket'][1],
                    'lamtha': p_ext['lamtha']
                }

                self.ncfrom_extgauss.append(self.parconnect_from_src(gid_extgauss, nc_dict, self.soma_ampa))

        elif type == 'extpois':
            if self.celltype in p_ext.keys():
                gid_extpois = gid + gid_dict['extpois'][0]

                nc_dict = {
                    'pos_src': pos_dict['extpois'][gid],
                    'A_weight': p_ext[self.celltype][0],
                    'A_delay': p_ext[self.celltype][1],
                    'lamtha': p_ext['lamtha_space']
                }

                self.ncfrom_extpois.append(self.parconnect_from_src(gid_extpois, nc_dict, self.soma_ampa))

        else:
            print("Warning, type def not specified in L2Basket")
