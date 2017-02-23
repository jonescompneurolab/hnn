# praw.py - all of the raw data types on one fig
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: updated for it.izip() and return_data_dir())
# last major: (SL: minor)

import fileio as fio
import numpy as np
import multiprocessing as mp
import ast
import os
import paramrw
import dipolefn
import spikefn
import specfn
import currentfn
import matplotlib.pyplot as plt
from neuron import h as nrn
import axes_create as ac

def pkernel(dfig_dpl, f_dpl, f_spk, f_spec, f_current, f_spec_current, f_param, ax_handles):
    T = paramrw.find_param(f_param, 'tstop')
    xlim = (50., T)

    # into the pdipole directory, this will plot dipole, spec, and spikes
    # create the axis handle
    f = ac.FigDipoleExp(ax_handles)

    # create the figure name
    fprefix = fio.strip_extprefix(f_dpl) + '-dpl'
    fname = os.path.join(dfig_dpl, fprefix + '.png')

    # grab the dipole
    dpl = dipolefn.Dipole(f_dpl)
    dpl.convert_fAm_to_nAm()

    # plot the dipole to the agg axes
    dpl.plot(f.ax['dpl_agg'], xlim)
    dpl.plot(f.ax['dpl_agg_L5'], xlim)
    # f.ax['dpl_agg_L5'].hold(True)
    # dpl.plot(f.ax['dpl_agg_L5'], xlim, 'L5')

    # plot individual dipoles
    dpl.plot(f.ax['dpl'], xlim, 'L2')
    dpl.plot(f.ax['dpl_L5'], xlim, 'L5')

    # f.ysymmetry(f.ax['dpl'])
    # print dpl.max('L5', (0., -1)), dpl.max('L5', (50., -1))
    # print f.ax['dpl_L5'].get_ylim()
    # f.ax['dpl_L5'].set_ylim((-1e5, 1e5))
    # f.ysymmetry(f.ax['dpl_L5'])

    # plot the current
    I_soma = currentfn.SynapticCurrent(f_current)
    I_soma.plot_to_axis(f.ax['I_soma'], 'L2')
    I_soma.plot_to_axis(f.ax['I_soma_L5'], 'L5')

    # plot the dipole-based spec data
    pc = specfn.pspec_ax(f.ax['spec_dpl'], f_spec, xlim, 'L2')
    f.f.colorbar(pc, ax=f.ax['spec_dpl'])

    pc = specfn.pspec_ax(f.ax['spec_dpl_L5'], f_spec, xlim, 'L5')
    f.f.colorbar(pc, ax=f.ax['spec_dpl_L5'])

    # grab the current spec and plot them
    spec_L2, spec_L5 = data_spec_current = specfn.read(f_spec_current, type='current')
    pc_L2 = f.ax['spec_I'].imshow(spec_L2['TFR'], aspect='auto', origin='upper')
    pc_L5 = f.ax['spec_I_L5'].imshow(spec_L5['TFR'], aspect='auto', origin='upper')

    # plot the current-based spec data
    # pci = specfn.pspec_ax(f.ax['spec_I'], f_spec_current, type='current')
    f.f.colorbar(pc_L2, ax=f.ax['spec_I'])
    f.f.colorbar(pc_L5, ax=f.ax['spec_I_L5'])

    # get all spikes
    s = spikefn.spikes_from_file(f_param, f_spk)

    # these work primarily because of how the keys are done
    # in the spike dict s (consequence of spikefn.spikes_from_file())
    s_L2 = spikefn.filter_spike_dict(s, 'L2_')
    s_L5 = spikefn.filter_spike_dict(s, 'L5_')

    # resize xlim based on our 50 ms cutoff thingy
    xlim = (50., xlim[1])

    # plot the spikes
    spikefn.spike_png(f.ax['spk'], s_L2)
    spikefn.spike_png(f.ax['spk_L5'], s_L5)

    f.ax['dpl'].set_xlim(xlim)
    # f.ax['dpl_L5'].set_xlim(xlim)
    # f.ax['spec_dpl'].set_xlim(xlim)
    f.ax['spk'].set_xlim(xlim)
    f.ax['spk_L5'].set_xlim(xlim)

    f.savepng(fname)
    f.close()

    return 0

# dummy function for callback
def cb(r):
    pass

# For a given ddata (SimulationPaths object), find the mean dipole
# over ALL trials in ALL conditions in EACH experiment
def praw(ddata):
    # grab the original dipole from a specific dir
    dproj = fio.return_data_dir()

    runtype = 'parallel'
    # runtype = 'debug'

    # check on spec data
    # generates both spec because both are needed here
    specfn.generate_missing_spec(ddata)

    # test experiment
    # expmt_group = ddata.expmt_groups[0]

    ax_handles = [
        'dpl_agg',
        'dpl',
        'spec_dpl',
        'spk',
        'I_soma',
        'spec_I',
    ]

    # iterate over exmpt groups
    for expmt_group in ddata.expmt_groups:
        dfig_dpl = ddata.dfig[expmt_group]['figdpl']

        # grab lists of files (l_)
        l_dpl = ddata.file_match(expmt_group, 'rawdpl')
        l_spk = ddata.file_match(expmt_group, 'rawspk')
        l_param = ddata.file_match(expmt_group, 'param')
        l_spec = ddata.file_match(expmt_group, 'rawspec')
        l_current = ddata.file_match(expmt_group, 'rawcurrent')
        l_spec_current = ddata.file_match(expmt_group, 'rawspeccurrent')

        if runtype == 'parallel':
            pl = mp.Pool()

            for f_dpl, f_spk, f_spec, f_current, f_spec_current, f_param \
            in zip(l_dpl, l_spk, l_spec, l_current, l_spec_current, l_param):
                pl.apply_async(pkernel, (dfig_dpl, f_dpl, f_spk, f_spec, f_current, f_spec_current, f_param, ax_handles), callback=cb)
            pl.close()
            pl.join()

        elif runtype == 'debug':
            for f_dpl, f_spk, f_spec, f_current, f_spec_current, f_param \
            in zip(l_dpl, l_spk, l_spec, l_current, l_spec_current, l_param):
                pkernel(dfig_dpl, f_dpl, f_spk, f_spec, f_current, f_spec_current, f_param, ax_handles)
