# averaging.py - routine to perform averaging
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: using new return_data_dir())
# last major: (SL: pushed for CSM and CB)

import fileio as fio
import dipolefn
import matplotlib.pyplot as plt
import numpy as np
import os

# routine to average the dipoles found in the dsim directory
def average_dipole(dsim):
    dproj = fio.return_data_dir()

    ddata = fio.SimulationPaths()
    ddata.read_sim(dproj, dsim)

    # grab the first experimental group
    expmt_group = ddata.expmt_groups[0]

    flist = ddata.file_match(expmt_group, 'rawdpl')
    N_dpl = len(flist)

    # grab the time and the length
    dpl_time = dipolefn.Dipole(flist[0]).t
    length_dpl = dipolefn.Dipole(flist[0]).N

    # preallocation of the total dipole
    # dpl_agg = np.zeros((N_dpl, length_dpl))
    dpl_sum = np.zeros(length_dpl)

    # the specific dipole to use
    dpl_specific = 'agg'

    for f in flist:
        dpl_f = dipolefn.Dipole(f)
        dpl_sum = dpl_sum + dpl_f.dpl[dpl_specific]

    dpl_scaled = dpl_sum * 1e-6
    dpl_mean = dpl_scaled / N_dpl

    print dpl_sum
    print ' '
    print dpl_scaled
    print ' '
    print dpl_mean

    figure_create(dpl_time, dpl_mean)

# simple plot of the mean dipole
def figure_create(dpl_time, dpl_agg):
    fig = plt.figure()
    ax = {
        'dpl_agg': fig.add_subplot(1, 1, 1),
    }

    # example
    ax['dpl_agg'].plot(dpl_time, dpl_agg, linewidth=0.5, color='k')
    fig.savefig('testing_dpl.png', dpi=200)
    plt.close(fig)

if __name__ == '__main__':
    droot = fio.return_data_dir()
    dsim = os.path.join(droot, '2015-12-02/tonic_L5Pyr-000')
    average_dipole(dsim)
