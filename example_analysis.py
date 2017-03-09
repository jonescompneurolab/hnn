#!/usr/bin/env python
# example_analysis.py - Example for an analysis workflow
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: changed it.izip())
# last major: (RL: added dipole loading)

import numpy as np
import fileio as fio
import paramrw
import dipolefn
import PT_example

# example simulation
def example_analysis_for_simulation():
    # from these two directories
    droot = fio.return_data_dir()
    dsim = os.path.join(droot, '2016-02-03/beta-sweep-000')

    # create the SimulationPaths() object ddata and read the simulation
    ddata = fio.SimulationPaths()
    ddata.read_sim(droot, dsim)

    # print dir(ddata)
    # print type(np.zeros(5))

    # print ddata.expmt_groups
    # print ddata.fparam
    # for key, val in ddata.dfig['testing'].items():
    #     print key, val
    # print dir({})

    # p_exp = paramrw.ExpParams(ddata.fparam)
    # print p_exp.p_all['dt']
    # # print p_exp.p_all

    # iterate through experimental groups and do the analysis on individual files, etc.
    for expmt_group in ddata.expmt_groups:
        print "experiment group is: %s" % (expmt_group)
        # print ddata.dfig[expmt_group]
        flist_param = ddata.file_match(expmt_group, 'param')
        flist_dpl = ddata.file_match(expmt_group, 'rawdpl')
        # flist_spk = ddata.file_match(expmt_group, 'rawspk')
        # fio.prettyprint(flist_spk)

        # iterate through files in the lists
        for fparam, fdpl in zip(flist_param, flist_dpl):
            # print fparam, fdpl
            gid_dict, p_tr = paramrw.read(fparam)

            # for key, val in p_tr.items():
            #     print key, val
            # fio.prettyprint(p_tr.keys())

            # create and load dipole data structure
            d = dipolefn.Dipole(fdpl)

            # more or less analysis goes here.
            # generate a filename for a dipole plot
            fname_png = ddata.return_filename_example('figdpl', expmt_group, p_tr['Sim_No'], tr=p_tr['Trial'])
            # print p_tr['Trial'], p_tr['Sim_No'], fname_png

            # example figure for this pair of files
            fig = PT_example.FigExample()

            # plot dipole
            fig.ax['dipole'].plot(d.t, d.dpl['agg'])
            fig.ax['dipole'].plot(d.t, d.dpl['L2'])
            fig.ax['dipole'].plot(d.t, d.dpl['L5'])
            fig.savepng(fname_png)
            fig.close()

if __name__ == '__main__':
    example_analysis_for_simulation()
