# ppsth.py - Plots aggregate psth of all trials in an "experiment"
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: removed it.izip())
# last rev: (SL: changed class names from axes_create.py)

import numpy as np
import itertools as it
import matplotlib.pyplot as plt
import os
import paramrw, spikefn
import fileio as fio
import axes_create as ac
# from axes_create import ac.FigPSTH, ac.FigPSTHGrid

def ppsth_grid(simpaths):
    # get filename lists in dictionaries of experiments
    dict_exp_param = simpaths.exp_files_of_type('param')
    dict_exp_spk = simpaths.exp_files_of_type('rawspk')

    # recreate the ExpParams object used in the simulation
    p_exp = paramrw.ExpParams(simpaths.fparam[0])

    # need number of lambda vals (cols) and number of sigma vals (rows)
    try:
        N_rows = len(p_exp.p_all['L2Pyr_Gauss_A_weight'])
    except TypeError:
        N_rows = 1

    try:
        N_cols = len(p_exp.p_all['L2Basket_Pois_lamtha'])
    except TypeError:
        N_cols = 1

    tstop = p_exp.p_all['tstop']

    print N_rows, N_cols, tstop

    # ugly but slightly less ugly than the index arithmetic i had planned. muahaha
    f = ac.FigGrid(N_rows, N_cols, tstop)

    # create coordinates for axes
    # this is backward-looking for a reason!
    axes_coords = [(j, i) for i, j in it.product(np.arange(N_cols), np.arange(N_rows))]

    if len(simpaths.expnames) != len(axes_coords):
        print "um ... see ppsth.py"

    # assumes a match between expnames and the keys of the previous dicts
    for expname, axis_coord in zip(simpaths.expnames, axes_coords):
        # get the tstop
        exp_param_list = dict_exp_param[expname]
        exp_spk_list = dict_exp_spk[expname]
        gid_dict, p = paramrw.read(exp_param_list[0])
        tstop = p['tstop']
        lamtha = p['L2Basket_Pois_lamtha']
        sigma = p['L2Pyr_Gauss_A_weight']

        # these are total spike dicts for the experiments
        s_L2Pyr_list = []
        # s_L5Pyr_list = []

        # iterate through params and spikes for a given experiment
        for fparam, fspk in zip(dict_exp_param[expname], dict_exp_spk[expname]):
            # get gid dict
            gid_dict, p = paramrw.read(fparam)

            # get spike dict
            s_dict = spikefn.spikes_from_file(gid_dict, fspk)

            # add a new entry to list for each different file assoc with an experiment
            s_L2Pyr_list.append(np.array(list(it.chain.from_iterable(s_dict['L2_pyramidal'].spike_list))))
            # s_L5Pyr_list.append(np.array(list(it.chain.from_iterable(s_dict['L5_pyramidal'].spike_list))))

        # now aggregate over all spikes
        s_L2Pyr = np.array(list(it.chain.from_iterable(s_L2Pyr_list)))
        # s_L5Pyr = np.array(list(it.chain.from_iterable(s_L5Pyr_list)))

        # optimize bins, currently unused for comparison reasons!
        N_trials = len(fparam)
        bin_L2 = 250
        # bin_L5 = 120
        # bin_L2 = spikefn.hist_bin_opt(s_L2Pyr, N_trials)
        # bin_L5 = spikefn.hist_bin_opt(s_L5Pyr, N_trials)

        r = axis_coord[0]
        c = axis_coord[1]
        # create standard fig and axes
        f.ax[r][c].hist(s_L2Pyr, bin_L2, facecolor='g', alpha=0.75)

        if r == 0:
            f.ax[r][c].set_title(r'$\lambda_i$ = %d' % lamtha)

        if c == 0:
            f.ax[r][c].set_ylabel(r'$A_{gauss}$ = %.3e' % sigma)
            # f.ax[r][c].set_ylabel(r'$\sigma_{gauss}$ = %d' % sigma)

        # normalize these axes
        y_L2 = f.ax[r][c].get_ylim()
        # y_L2 = f.ax['L2_psth'].get_ylim()

        print expname, lamtha, sigma, r, c, y_L2[1]

        f.ax[r][c].set_ylim((0, 250.))
        # f.ax['L2_psth'].set_ylim((0, 450.))
        # f.ax['L5_psth'].set_ylim((0, 450.))

        # spikefn.spike_png(f.ax['L2'], s_dict_L2)
        # spikefn.spike_png(f.ax['L5'], s_dict_L5)
        # spikefn.spike_png(f.ax['L2_extpois'], s_dict_L2_extpois)
        # spikefn.spike_png(f.ax['L2_extgauss'], s_dict_L2_extgauss)
        # spikefn.spike_png(f.ax['L5_extpois'], s_dict_L5_extpois)
        # spikefn.spike_png(f.ax['L5_extgauss'], s_dict_L5_extgauss)

    # testfig.ax0.plot(t_vec, dp_total)
    fig_name = os.path.join(simpaths.dsim, 'aggregate.eps')

    plt.savefig(fig_name)
    f.close()

    # run the compression
    fio.epscompress(simpaths.dsim, '.eps', 1)

# will take a directory, find the files bin all the psth's, plot a representative spike raster
def ppsth(simpaths):
    # get filename lists in dictionaries of experiments
    dict_exp_param = simpaths.exp_files_of_type('param')
    dict_exp_spk = simpaths.exp_files_of_type('rawspk')

    # assumes a match between expnames and the keys of the previous dicts
    for expname in simpaths.expnames:
        # get the tstop
        exp_param_list = dict_exp_param[expname]
        exp_spk_list = dict_exp_spk[expname]
        gid_dict, p = paramrw.read(exp_param_list[0])
        # gid_dict, p = paramrw.read(dict_exp_param[expname][0])
        tstop = p['tstop']

        # get representative spikes
        s_dict = spikefn.spikes_from_file(gid_dict, exp_spk_list[0])

        s_dict_L2 = {}
        s_dict_L5 = {}
        s_dict_L2_extgauss = {}
        s_dict_L2_extpois = {}
        s_dict_L5_extgauss = {}
        s_dict_L5_extpois = {}

        # clean out s_dict destructively
        # borrowed from praster
        for key in s_dict.keys():
            # do this first to remove all extgauss feeds
            if 'extgauss' in key:
                if 'L2_' in key:
                    s_dict_L2_extgauss[key] = s_dict.pop(key)

                elif 'L5_' in key:
                    s_dict_L5_extgauss[key] = s_dict.pop(key)

            elif 'extpois' in key:
                # s_dict_extpois[key] = s_dict.pop(key)
                if 'L2_' in key:
                    s_dict_L2_extpois[key] = s_dict.pop(key)

                elif 'L5_' in key:
                    s_dict_L5_extpois[key] = s_dict.pop(key)

            # L2 next
            elif 'L2_' in key:
                s_dict_L2[key] = s_dict.pop(key)

            elif 'L5_' in key:
                s_dict_L5[key] = s_dict.pop(key)

        # these are total spike dicts for the experiments
        s_L2Pyr_list = []
        s_L5Pyr_list = []

        # iterate through params and spikes for a given experiment
        for fparam, fspk in zip(dict_exp_param[expname], dict_exp_spk[expname]):
            # get gid dict
            gid_dict, p = paramrw.read(fparam)

            # get spike dict
            s_dict = spikefn.spikes_from_file(gid_dict, fspk)

            # add a new entry to list for each different file assoc with an experiment
            s_L2Pyr_list.append(np.array(list(it.chain.from_iterable(s_dict['L2_pyramidal'].spike_list))))
            s_L5Pyr_list.append(np.array(list(it.chain.from_iterable(s_dict['L5_pyramidal'].spike_list))))

        # now aggregate over all spikes
        s_L2Pyr = np.array(list(it.chain.from_iterable(s_L2Pyr_list)))
        s_L5Pyr = np.array(list(it.chain.from_iterable(s_L5Pyr_list)))

        # optimize bins, currently unused for comparison reasons!
        N_trials = len(fparam)
        # bin_L2 = 120
        # bin_L5 = 120
        bin_L2 = spikefn.hist_bin_opt(s_L2Pyr, N_trials)
        bin_L5 = spikefn.hist_bin_opt(s_L5Pyr, N_trials)

        # create standard fig and axes
        f = ac.FigPSTH(400.)
        f.ax['L2_psth'].hist(s_L2Pyr, bin_L2, facecolor='g', alpha=0.75)
        f.ax['L5_psth'].hist(s_L5Pyr, bin_L5, facecolor='g', alpha=0.75)

        # normalize these axes
        y_L2 = f.ax['L2_psth'].get_ylim()
        y_L5 = f.ax['L5_psth'].get_ylim()

        print y_L2, y_L5

        # f.ax['L2_psth'].set_ylim((0, 450.))
        # f.ax['L5_psth'].set_ylim((0, 450.))

        spikefn.spike_png(f.ax['L2'], s_dict_L2)
        spikefn.spike_png(f.ax['L5'], s_dict_L5)
        spikefn.spike_png(f.ax['L2_extpois'], s_dict_L2_extpois)
        spikefn.spike_png(f.ax['L2_extgauss'], s_dict_L2_extgauss)
        spikefn.spike_png(f.ax['L5_extpois'], s_dict_L5_extpois)
        spikefn.spike_png(f.ax['L5_extgauss'], s_dict_L5_extgauss)

        # # testfig.ax0.plot(t_vec, dp_total)
        fig_name = os.path.join(simpaths.dsim, expname+'.eps')

        plt.savefig(fig_name)
        f.close()

    # run the compression
    fio.epscompress(simpaths.dsim, '.eps', 1)
