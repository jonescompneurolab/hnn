# pmanu_gamma.py - plot functions for gamma manuscript
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: return_data_dir() and it.izip)
# last major: (SL: plot updates)

import numpy as np
import os
import fileio as fio
import currentfn
import dipolefn
import specfn
import spikefn
import paramrw
import ac_manu_gamma as acg
import axes_create as ac

def spec_fig():
    f = acg.FigSimpleSpec()
    dproj = fio.return_data_dir()
    d = os.path.join(dproj, '2013-12-04/ftremor-003')

    ddata = fio.SimulationPaths()
    ddata.read_sim(dproj, d)

    expmt_group = ddata.expmt_groups[0]
    f_dpl = ddata.file_match(expmt_group, 'rawdpl')[0]
    fspec = ddata.file_match(expmt_group, 'rawspec')[0]
    fparam = ddata.file_match(expmt_group, 'param')[0]

    dpl = dipolefn.Dipole(f_dpl)
    dpl.baseline_renormalize(fparam)
    dpl.convert_fAm_to_nAm()

    xlim = (200., 700.)

    dpl.plot(f.ax['dipole'], xlim, layer='L5')
    pc = {
        'spec': specfn.pspec_ax(f.ax['spec'], fspec, (50, 1050), layer='L5'),
    }
    cb = f.f.colorbar(pc['spec'], ax=f.ax['spec'], format='%.1e')

    f.ax['spec'].set_xlim(xlim)
    f.ax['spec'].set_ylabel('Frequency (Hz)')
    f.ax['spec'].set_xlabel('Time (ms)')

    f.set_fontsize(14)

    # fname = os.path.join(d, 'testing.eps')

    f.saveeps(d, 'testing')
    f.close()

# all the data comes from one sim
def hf_epochs(ddata):
    # runtype = 'debug'
    runtype = 'pub'

    # create the figure from the ac template
    f = acg.FigHFEpochs(runtype)

    # hard coded for now
    n_sim = 0
    n_trial = 0

    # and assume just the first expmt for now
    expmt = ddata.expmt_groups[0]

    # hard code the 50 ms epochs that will be used here.
    # centers for the data in tuples (t, f)
    tf_specmax = [
        (79.525, 115.),
        (136.925, 114.),
        (324.350, 109.),
        (418.400, 106.),
    ]

    # these are approximate centers on which to draw sines
    tf_centers = [
        [83.],
        [137.],
        [330.],
        [411., 429.],
    ]

    # these all come from one filename
    f_spec = ddata.return_specific_filename(expmt, 'rawspec', n_sim, n_trial)
    f_dpl = ddata.return_specific_filename(expmt, 'rawdpl', n_sim, n_trial)
    f_spk = ddata.return_specific_filename(expmt, 'rawspk', n_sim, n_trial)
    f_param = ddata.return_specific_filename(expmt, 'param', n_sim, n_trial)
    f_current = ddata.return_specific_filename(expmt, 'rawcurrent', n_sim, n_trial)

    # p_dict is needed for the spike thing.
    _, p_dict = paramrw.read(f_param)

    # figure out the tstop and xlim
    tstop = paramrw.find_param(f_param, 'tstop')
    dt = paramrw.find_param(f_param, 'dt')
    xlim = (50., tstop)

    # grab the dipole data
    dpl = dipolefn.Dipole(f_dpl)
    dpl.baseline_renormalize(f_param)
    dpl.convert_fAm_to_nAm()

    # current data
    I_soma = currentfn.SynapticCurrent(f_current)
    I_soma.convert_nA_to_uA()

    # grab the spike data for histogram
    s = spikefn.spikes_from_file(f_param, f_spk)
    n_bins = 500
    s_list = np.concatenate(s['L5_pyramidal'].spike_list)

    # spikes
    spikes = {
        'L5': spikefn.filter_spike_dict(s, 'L5_'),
    }

    # xrange is just the length of the window, dx is the distance from the center
    xrange = 50.
    dx = xrange / 2.

    # pc will be a list of the colorbar props for each spec (length len(f.gspec))
    pc = []

    # plot the aggregate data too
    specfn.pspec_ax(f.ax['L_spec'], f_spec, xlim, layer='L5')
    dpl.plot(f.ax['L_dpl'], xlim, layer='L5')
    spikefn.spike_png(f.ax['L_spk'], spikes['L5'])

    # change the color
    color_dpl_L5 = '#1e90ff'
    f.set_linecolor('L_dpl', color_dpl_L5)

    # grab a list of the ax handles for the leftmost plot
    ax_L_keys = [ax for ax in f.ax.keys() if ax.startswith('L_')]

    # set all these xlim correctly
    for ax_h in ax_L_keys:
        f.ax[ax_h].set_xlim(xlim)

    list_ylim_dpl = []

    # now plot the individual epochs
    for i in range(len(f.gspec_ex)):
        # for each (t, f) pair, find the xlim_window
        t_center = tf_specmax[i][0]
        f_center = tf_specmax[i][1]
        xlim_window = (t_center - dx, t_center + dx)
        print xlim_window

        # crude setting of vertical lines to denote roi
        for ax_h in ax_L_keys:
            f.ax[ax_h].axvline(x=xlim_window[0], color='b')
            f.ax[ax_h].axvline(x=xlim_window[1], color='k')

        # this is the highlight portion, one fixed
        dx_hl = 0.5 * (1000. / f_center)
        dx_hl_fixed = 10.

        xlim_hl = (t_center - dx_hl, t_center + dx_hl)
        xlim_fixed = (t_center - dx_hl_fixed, t_center + dx_hl_fixed)

        # fix xlim_window in case
        if xlim_window[0] < xlim[0]:
            xlim_window[0] = xlim[0]

        if xlim_window[1] == -1:
            xlim_window[1] = tstop

        I_soma.plot_to_axis(f.ax_twinx['dpl'][i], 'L5')

        # truncate and then plot the dpl
        # dpl_short must be a dict of all the different dipoles
        # so only need here the L5 key
        t_short, dpl_short = dpl.truncate_ext(xlim_hl[0], xlim_hl[1])
        t_fixed, dpl_fixed = dpl.truncate_ext(xlim_fixed[0], xlim_fixed[1])

        # create a sine waveform for this interval
        f_max = tf_specmax[i][1]
        t_half = 0.5 * (1000. / f_max)

        # plot the dipole for the xlim window
        # plot the dipole and the current, either over the appropriate range or the whole window for now
        dpl.plot(f.ax['dpl'][i], xlim_window, layer='L5')
        f.ax['dpl'][i].hold(True)

        for j in range(len(tf_centers[i])):
            t0 = tf_centers[i][j] - t_half
            T = tf_centers[i][j] + t_half

            ylim_dpl = dpl.lim('L5', (t0, T))

            props_dict = {
                't': (t0, T),
                'dt': dt,
                'f': f_max,
                'A': ylim_dpl[1],
            }

            f.add_sine(f.ax['dpl'][i], props_dict)

        f.ax['dpl'][i].set_ylim((-0.025, 0.025))

        # f.ax['dpl'][i].plot(t_fixed, dpl_fixed['L5'], 'g')
        # f.ax['dpl'][i].plot(t_short, dpl_short['L5'], 'r')

        # spec - i think must be plotted as xlim first and then truncated?
        pc.append(specfn.pspec_ax(f.ax['spec'][i], f_spec, xlim, layer='L5'))

        # plot the data
        spikefn.pinput_hist_onesided(f.ax['hist'][i], s_list, n_bins)
        spikefn.spike_png(f.ax['spk'][i], spikes['L5'])

        # set xlim_windows accordingly
        f.ax['hist'][i].set_xlim(xlim_window)
        f.ax['spk'][i].set_xlim(xlim_window)
        f.ax_twinx['dpl'][i].set_xlim(xlim_window)
        f.ax['spec'][i].set_xlim(xlim_window)

        # hist
        f.ax['hist'][i].yaxis.set_ticks(np.arange(0, 9, 4))

        # set the color of the I_soma line
        f.ax['dpl'][i].lines[0].set_color(color_dpl_L5)
        f.ax_twinx['dpl'][i].lines[0].set_color('k')
        f.ysymmetry(f.ax_twinx['dpl'][i])

        # no need for outputs
        if runtype == 'debug':
            f.f.colorbar(pc[i], ax=f.ax['spec'][i], format='%.3e')

    if runtype == 'pub':
        p_ticks = np.arange(0, 9e-5, 2e-5)
        pctest = f.f.colorbar(pc[-1], ax=f.ax['spec'][-1], format='%.2e', ticks=p_ticks)
        pctest.ax.set_yticklabels(p_ticks)
        # pctest.ax.set_ytick(np.arange(0, 8e-5, 2e-5))
        # pctest.ax.locator_params(axis='y', nbins=5)

    # some fig naming stuff
    dfig = os.path.join(ddata.dsim, expmt)
    trial_prefix = ddata.trial_prefix_str % (n_sim, n_trial)
    fprefix_short = trial_prefix + '-hf_epochs'

    # use methods to save figs
    f.savepng_new(dfig, fprefix_short)
    f.saveeps(dfig, fprefix_short)
    f.close()

def hf(ddata, xlim_window, n_sim, n_trial):
    # data directories (made up for now)
    # the resultant figure is saved in d0
    # d = os.path.join(dproj, 'pub', '2013-06-28_gamma_weak_L5-000')

    # for now grab the first experiment
    # ddata = fio.SimulationPaths()
    # ddata.read_sim(dproj, d)
    expmt = ddata.expmt_groups[0]

    runtype = 'debug'
    # runtype = 'pub'

    # prints the fig in ddata0
    f = acg.FigHF(runtype)

    # grab the relevant files
    f_spec = ddata.return_specific_filename(expmt, 'rawspec', n_sim, n_trial)
    f_dpl = ddata.return_specific_filename(expmt, 'rawdpl', n_sim, n_trial)
    f_spk = ddata.return_specific_filename(expmt, 'rawspk', n_sim, n_trial)
    f_param = ddata.return_specific_filename(expmt, 'param', n_sim, n_trial)
    f_current = ddata.return_specific_filename(expmt, 'rawcurrent', n_sim, n_trial)

    # p_dict is needed for the spike thing.
    _, p_dict = paramrw.read(f_param)

    # figure out the tstop and xlim
    tstop = paramrw.find_param(f_param, 'tstop')
    dt = paramrw.find_param(f_param, 'dt')
    xlim = (50., tstop)

    # fix xlim_window
    if xlim_window[0] < xlim[0]:
        xlim_window[0] = xlim[0]

    if xlim_window[1] == -1:
        xlim_window[1] = tstop

    # grab the dipole data
    dpl = dipolefn.Dipole(f_dpl)
    dpl.baseline_renormalize(f_param)
    dpl.convert_fAm_to_nAm()
    dpl.plot(f.ax['dpl_L'], xlim, layer='agg')

    # plot currents
    I_soma = currentfn.SynapticCurrent(f_current)
    I_soma.plot_to_axis(f.ax_twinx['dpl_L'], 'L5')

    # spec
    pc = {
        'L': specfn.pspec_ax(f.ax['spec_L'], f_spec, xlim, layer='L5'),
    }

    # no need for outputs
    if runtype == 'debug':
        f.f.colorbar(pc['L'], ax=f.ax['spec_L'], format='%.3e')

    # grab the spike data for histogram
    s = spikefn.spikes_from_file(f_param, f_spk)
    n_bins = 500
    s_list = np.concatenate(s['L5_pyramidal'].spike_list)
    spikefn.pinput_hist_onesided(f.ax['hist_L'], s_list, n_bins)

    # spikes
    spikes = {
        'L5': spikefn.filter_spike_dict(s, 'L5_'),
    }

    # plot the data
    spikefn.spike_png(f.ax['spk'], spikes['L5'])

    # xlim_window
    # xlim_window = (400., 450.)
    f.ax['hist_L'].set_xlim(xlim_window)
    f.ax['dpl_L'].set_xlim(xlim_window)
    f.ax['spec_L'].set_xlim(xlim_window)
    f.ax_twinx['dpl_L'].set_xlim(xlim_window)

    f.ax_twinx['dpl_L'].lines[0].set_color('k')
    f.ysymmetry(f.ax_twinx['dpl_L'])
    f.ax['spk'].set_xlim(xlim_window)

    # # save the fig in ddata0 (arbitrary)
    trial_prefix = ddata.trial_prefix_str % (n_sim, n_trial)
    f_prefix = '%s_hf' % trial_prefix
    dfig = os.path.join(ddata.dsim, expmt)

    f.savepng_new(dfig, f_prefix)
    f.saveeps(dfig, f_prefix)
    f.close()

def laminar(ddata):
    # for now grab the first experiment
    expmt = ddata.expmt_groups[0]

    # runtype = 'debug'
    runtype = 'pub'

    # for now hard code the simulation run
    n_run = 0

    # prints the fig in ddata0
    f = acg.FigLaminarComparison(runtype)

    # grab the relevant files
    f_spec = ddata.file_match(expmt, 'rawspec')[n_run]
    f_dpl = ddata.file_match(expmt, 'rawdpl')[n_run]
    f_spk = ddata.file_match(expmt, 'rawspk')[n_run]
    f_param = ddata.file_match(expmt, 'param')[n_run]
    f_current = ddata.file_match(expmt, 'rawcurrent')[n_run]

    # figure out the tstop and xlim
    tstop = paramrw.find_param(f_param, 'tstop')
    dt = paramrw.find_param(f_param, 'dt')
    xlim = (50., tstop)

    # grab the dipole data
    dpl = dipolefn.Dipole(f_dpl)
    dpl.baseline_renormalize(f_param)
    dpl.convert_fAm_to_nAm()

    # calculate the Welch periodogram
    pgram = {
        'agg': specfn.Welch(dpl.t, dpl.dpl['agg'], dt),
        'L2': specfn.Welch(dpl.t, dpl.dpl['L2'], dt),
        'L5': specfn.Welch(dpl.t, dpl.dpl['L5'], dt),
    }

    # plot periodograms
    pgram['agg'].plot_to_ax(f.ax['pgram_L'])
    pgram['L2'].plot_to_ax(f.ax['pgram_M'])
    pgram['L5'].plot_to_ax(f.ax['pgram_R'])

    # plot currents
    I_soma = currentfn.SynapticCurrent(f_current)
    I_soma.convert_nA_to_uA()
    I_soma.plot_to_axis(f.ax['current_M'], 'L2')
    I_soma.plot_to_axis(f.ax['current_R'], 'L5')
    f.set_linecolor('current_M', 'k')
    f.set_linecolor('current_R', 'k')
    # f.set_axes_pingping()

    # cols have same suffix
    list_cols = ['L', 'M', 'R']

    # create handles list
    list_h_pgram = ['pgram_'+col for col in list_cols]
    list_h_dpl = ['dpl_'+col for col in list_cols]

    # spec
    pc = {
        'L': specfn.pspec_ax(f.ax['spec_L'], f_spec, xlim, layer='agg'),
        'R': specfn.pspec_ax(f.ax['spec_R'], f_spec, xlim, layer='L5'),
    }

    pc2 = {
        'M': specfn.pspec_ax(f.ax['spec_M'], f_spec, xlim, layer='L2'),
    }

    # create a list of spec color handles
    # list_h_spec_cb = ['pc_'+col for col in list_cols]

    # get the vmin, vmax and add them to the master list
    # f.equalize_speclim(pc)
    # list_lim_spec = []

    # no need for outputs
    if runtype == 'debug':
        f.f.colorbar(pc['L'], ax=f.ax['spec_L'], format='%.1e')
        f.f.colorbar(pc2['M'], ax=f.ax['spec_M'], format='%.1e')
        f.f.colorbar(pc['R'], ax=f.ax['spec_R'], format='%.1e')
        # list_spec_handles = [ax for ax in f.ax.keys() if ax.startswith('spec')]
        list_spec_handles = ['spec_M', 'spec_R']
        f.remove_tick_labels(list_spec_handles, ax_xy='y')

    elif runtype == 'pub':
        f.f.colorbar(pc['L'], ax=f.ax['spec_L'], format='%.1e')
        f.f.colorbar(pc2['M'], ax=f.ax['spec_M'], format='%.1e')
        f.f.colorbar(pc['R'], ax=f.ax['spec_R'], format='%.1e')
        list_spec_handles = ['spec_L', 'spec_R']
        f.remove_tick_labels(list_spec_handles, ax_xy='y')

    # grab the spike data
    s = spikefn.spikes_from_file(f_param, f_spk)

    # dipoles
    dpl.plot(f.ax['dpl_L'], xlim, layer='agg')
    # f.set_linecolor('dpl_L', 'k')
    f.ax['dpl_L'].hold(True)
    dpl.plot(f.ax['dpl_L'], xlim, layer='L5')
    dpl.plot(f.ax['dpl_L'], xlim, layer='L2')

    color_dpl_L5 = '#1e90ff'

    # these colors mirror below, should be vars
    f.ax['dpl_L'].lines[0].set_color('k')
    f.ax['dpl_L'].lines[1].set_color(color_dpl_L5)
    f.ax['dpl_L'].lines[2].set_color('#b22222')

    # plot and color
    dpl.plot(f.ax['dpl_M'], xlim, layer='L2')
    f.set_linecolor('dpl_M', '#b22222')

    # plot and color
    dpl.plot(f.ax['dpl_R'], xlim, layer='L5')
    f.set_linecolor('dpl_R', color_dpl_L5)

    # equalize the ylim
    # f.equalize_ylim(list_h_pgram)
    f.equalize_speclim(pc)
    f.equalize_ylim(['dpl_L', 'dpl_R'])
    ylim_dpl_M = dpl.lim('L2', xlim)
    # f.ysymmetry(f.ax['dpl_M'])
    # f.ax['dpl_M'].set_ylim(ylim_dpl_M)
    f.ax['dpl_M'].set_ylim((-0.01, 0.01))
    for ax in f.ax.keys():
        if ax.startswith('dpl'):
            f.ax[ax].locator_params(axis='y', nbins=7)

    # spikes
    spikes = {
        'L2': spikefn.filter_spike_dict(s, 'L2_'),
        'L5': spikefn.filter_spike_dict(s, 'L5_'),
    }

    # plot the data
    spikefn.spike_png(f.ax['spk_M'], spikes['L2'])
    spikefn.spike_png(f.ax['spk_R'], spikes['L5'])
    f.ax['spk_M'].set_xlim(xlim)
    f.ax['spk_R'].set_xlim(xlim)

    # thin the yaxis
    # function defined in FigBase()
    # f.thin_yaxis(f.ax['current_M'], 5)
    f.ax['current_M'].locator_params(axis='y', nbins=5)
    f.ax['current_M'].set_ylim((-0.20, 0))
    f.ax['current_R'].locator_params(axis='y', nbins=5)
    f.ax['current_R'].set_ylim((-0.8, 0))

    # Welch number of labels
    f.ax['pgram_M'].locator_params(axis='y', nbins=5)
    f.ax['pgram_R'].locator_params(axis='y', nbins=5)
    f.ax['pgram_L'].locator_params(axis='y', nbins=5)

    # set the colors
    f.set_linecolor('pgram_L', 'k')
    f.set_linecolor('pgram_R', 'k')
    f.set_linecolor('pgram_M', 'k')

    # save the fig in ddata0 (arbitrary)
    f_prefix = '%s_laminar' % ddata.sim_prefix
    dfig = os.path.join(ddata.dsim, expmt)

    f.savepng_new(dfig, f_prefix)
    f.saveeps(dfig, f_prefix)
    f.close()

# compares PING regimes for two different trial runs
def compare_ping():
    dproj = fio.return_data_dir()
    runtype = 'pub2'
    # runtype = 'debug'

    # data directories (made up for now)
    # the resultant figure is saved in d0
    d0 = os.path.join(dproj, 'pub', '2013-06-28_gamma_ping_L5-000')
    d1 = os.path.join(dproj, 'pub', '2013-07-31_gamma_weak_L5-000')
    # d1 = os.path.join(dproj, 'pub', '2013-06-28_gamma_weak_L5-000')

    # hard code the data for now
    ddata0 = fio.SimulationPaths()
    ddata1 = fio.SimulationPaths()

    # use read_sim() to read the simulations
    ddata0.read_sim(dproj, d0)
    ddata1.read_sim(dproj, d1)

    # for now grab the first experiment in each
    expmt0 = ddata0.expmt_groups[0]
    expmt1 = ddata1.expmt_groups[0]

    # for now hard code the simulation run
    run0 = 0
    run1 = 0

    # prints the fig in ddata0
    f = acg.FigL5PingExample(runtype)

    # first panel data
    f_spec0 = ddata0.file_match(expmt0, 'rawspec')[run0]
    f_dpl0 = ddata0.file_match(expmt0, 'rawdpl')[run0]
    f_spk0 = ddata0.file_match(expmt0, 'rawspk')[run0]
    f_param0 = ddata0.file_match(expmt0, 'param')[run0]
    f_current0 = ddata0.file_match(expmt0, 'rawcurrent')[run0]

    # figure out the tstop and xlim
    tstop0 = paramrw.find_param(f_param0, 'tstop')
    dt = paramrw.find_param(f_param0, 'dt')
    xlim0 = (50., tstop0)

    # grab the dipole data
    dpl0 = dipolefn.Dipole(f_dpl0)
    dpl0.baseline_renormalize(f_param0)
    dpl0.convert_fAm_to_nAm()

    # calculate the Welch periodogram
    f_max = 150.
    pgram0 = specfn.Welch(dpl0.t, dpl0.dpl['L5'], dt)
    pgram0.plot_to_ax(f.ax['pgram_L'], f_max)

    # grab the spike data
    s0 = spikefn.spikes_from_file(f_param0, f_spk0)
    s0_L5 = spikefn.filter_spike_dict(s0, 'L5_')

    # plot the spike histogram data
    icell0_spikes = np.concatenate(s0_L5['L5_basket'].spike_list)
    ecell0_spikes = np.concatenate(s0_L5['L5_pyramidal'].spike_list)

    # 1 ms bins
    n_bins = int(tstop0)

    f.ax['hist_L'].hist(icell0_spikes, n_bins, facecolor='r', histtype='stepfilled', alpha=0.75, edgecolor='none')
    f.ax_twinx['hist_L'].hist(ecell0_spikes, n_bins, facecolor='k')

    # based on number of cells
    f.ax['hist_L'].set_ylim((0, 20))
    f.ax_twinx['hist_L'].set_ylim((0, 100))

    f.ax_twinx['hist_L'].set_xlim(xlim0)
    f.ax['hist_L'].set_xlim(xlim0)

    # hack
    labels = f.ax['hist_L'].yaxis.get_ticklocs()
    labels_text = [str(label) for label in labels[:-1]]
    for i in range(len(labels_text)):
        labels_text[i] = ''

    labels_text.append('20')
    f.ax['hist_L'].set_yticklabels(labels_text)

    labels_twinx = f.ax_twinx['hist_L'].yaxis.get_ticklocs()
    labels_text = [str(label) for label in labels_twinx[:-1]]
    for i in range(len(labels_text)):
        labels_text[i] = ''

    labels_text.append('100')
    f.ax_twinx['hist_L'].set_yticklabels(labels_text)

    # grab the current data
    I_soma0 = currentfn.SynapticCurrent(f_current0)
    I_soma0.convert_nA_to_uA()

    # plot the data
    dpl0.plot(f.ax['dpl_L'], xlim0, layer='L5')
    spikefn.spike_png(f.ax['raster_L'], s0_L5)
    f.ax['raster_L'].set_xlim(xlim0)

    # second panel data
    f_spec1 = ddata1.file_match(expmt1, 'rawspec')[run1]
    f_dpl1 = ddata1.file_match(expmt1, 'rawdpl')[run1]
    f_spk1 = ddata1.file_match(expmt1, 'rawspk')[run1]
    f_param1 = ddata1.file_match(expmt1, 'param')[run1]
    f_current1 = ddata1.file_match(expmt1, 'rawcurrent')[run1]

    # figure out the tstop and xlim
    tstop1 = paramrw.find_param(f_param1, 'tstop')
    xlim1 = (50., tstop1)

    # grab the dipole data
    dpl1 = dipolefn.Dipole(f_dpl1)
    dpl1.baseline_renormalize(f_param1)
    dpl1.convert_fAm_to_nAm()

    # calculate the Welch periodogram
    pgram1 = specfn.Welch(dpl1.t, dpl1.dpl['L5'], dt)
    pgram1.plot_to_ax(f.ax['pgram_R'], f_max)

    # grab the spike data
    s1 = spikefn.spikes_from_file(f_param1, f_spk1)
    s1_L5 = spikefn.filter_spike_dict(s1, 'L5_')
    # s1_L2 = spikefn.filter_spike_dict(s1, 'L2_')

    # plot the spike histogram data
    icell1_spikes = np.concatenate(s1_L5['L5_basket'].spike_list)
    ecell1_spikes = np.concatenate(s1_L5['L5_pyramidal'].spike_list)

    # 1 ms bins
    n_bins = int(tstop1)

    f.ax['hist_R'].hist(icell1_spikes, n_bins, facecolor='r', histtype='stepfilled', alpha=0.75, edgecolor='none')
    f.ax_twinx['hist_R'].hist(ecell1_spikes, n_bins, facecolor='k')

    # based on number of cells
    f.ax['hist_R'].set_ylim((0, 12))
    f.ax_twinx['hist_R'].set_ylim((0, 12))

    f.ax_twinx['hist_R'].set_xlim(xlim0)
    f.ax['hist_R'].set_xlim(xlim0)

    # hack
    labels = f.ax['hist_R'].yaxis.get_ticklocs()
    labels_text = [str(label) for label in labels[:-1]]
    for i in range(len(labels_text)):
        labels_text[i] = ''

    labels_text.append('12')
    f.ax['hist_R'].set_yticklabels(labels_text)

    labels_twinx = f.ax_twinx['hist_R'].yaxis.get_ticklocs()
    labels_text = [str(label) for label in labels_twinx[:-1]]
    for i in range(len(labels_text)):
        labels_text[i] = ''

    labels_text.append('12')
    f.ax_twinx['hist_R'].set_yticklabels(labels_text)

    # grab the current data
    I_soma1 = currentfn.SynapticCurrent(f_current1)
    I_soma1.convert_nA_to_uA()

    # plot the data
    dpl1.plot(f.ax['dpl_R'], xlim1, layer='L5')
    f.ysymmetry(f.ax['dpl_R'])
    spikefn.spike_png(f.ax['raster_R'], s1_L5)
    f.ax['raster_R'].set_xlim(xlim1)

    # plot the spec data
    pc = {
        'L': specfn.pspec_ax(f.ax['spec_L'], f_spec0, xlim0, layer='L5'),
        'R': specfn.pspec_ax(f.ax['spec_R'], f_spec1, xlim1, layer='L5'),
    }

    # f.equalize_speclim(pc)

    # grab the dipole figure handles
    list_h_dpl = [h for h in f.ax.keys() if h.startswith('dpl')]
    for ax_h in list_h_dpl:
        f.ax[ax_h].locator_params(axis='y', nbins=5)
    # f.equalize_ylim(list_h_dpl)

    # and the pgrams
    # list_h_pgram = [h for h in f.ax.keys() if h.startswith('pgram')]
    # test = f.equalize_ylim(list_h_pgram)

    # plot current and do lims
    I_soma0.plot_to_axis(f.ax['current_L'], 'L5')
    I_soma1.plot_to_axis(f.ax['current_R'], 'L5')
    list_h_current = [ax_h for ax_h in f.ax.keys() if ax_h.startswith('current')]
    f.equalize_ylim(list_h_current)

    # this is a hack
    # now in uA instead of nA
    for ax_handle in f.ax.keys():
        if ax_handle.startswith('current_'):
            f.ax[ax_handle].set_ylim((-2, 0.))

    # testing something
    # f.ax['pgram_L'].set_yscale('log')
    # f.ax['pgram_R'].set_yscale('log')
    # f.ax['pgram_L'].set_ylim((1e-12, 1e-3))
    # f.ax['pgram_R'].set_ylim((1e-12, 1e-3))

    # save the fig in ddata0 (arbitrary)
    f_prefix = 'gamma_L5ping_L5weak'
    dfig = os.path.join(ddata0.dsim, expmt0)

    # create the colorbars
    cb = dict.fromkeys(pc)

    if runtype in ('debug', 'pub2'):
        for key in pc.keys():
            key_ax = 'spec_' + key
            cb[key] = f.f.colorbar(pc[key], ax=f.ax[key_ax], format='%.1e')

    elif runtype == 'pub':
        cb['R'] = f.f.colorbar(pc['R'], ax=f.ax['spec_R'], format='%.1e')

    f.savepng_new(dfig, f_prefix)
    f.saveeps(dfig, f_prefix)
    f.close()

def sub_dist_examples():
    dproj = fio.return_data_dir()
    # runtype = 'pub2'
    runtype = 'debug'

    # data directories (made up for now)
    # the resultant figure is saved in d0
    d0 = os.path.join(dproj, 'pub', '2013-07-01_gamma_sub_50Hz-002')
    d1 = os.path.join(dproj, 'pub', '2013-07-18_gamma_sub_100Hz-000')

    # hard code the data for now
    ddata0 = fio.SimulationPaths()
    ddata1 = fio.SimulationPaths()

    # use read_sim() to read the simulations
    ddata0.read_sim(dproj, d0)
    ddata1.read_sim(dproj, d1)

    # for now grab the first experiment in each
    expmt0 = ddata0.expmt_groups[0]
    expmt1 = ddata1.expmt_groups[0]

    # for now hard code the simulation run
    run0 = 0
    run1 = 0

    # number of bins for the spike histograms
    n_bins = 500

    # prints the fig in ddata0
    f = acg.FigSubDistExample(runtype)

    # first panel data
    f_spec0 = ddata0.file_match(expmt0, 'rawspec')[run0]
    f_dpl0 = ddata0.file_match(expmt0, 'rawdpl')[run0]
    f_spk0 = ddata0.file_match(expmt0, 'rawspk')[run0]
    f_param0 = ddata0.file_match(expmt0, 'param')[run0]
    # f_current0 = ddata0.file_match(expmt0, 'rawcurrent')[run0]

    # figure out the tstop and xlim
    tstop0 = paramrw.find_param(f_param0, 'tstop')
    dt = paramrw.find_param(f_param0, 'dt')
    xlim0 = (50., tstop0)

    # grab the dipole data
    dpl0 = dipolefn.Dipole(f_dpl0)
    dpl0.baseline_renormalize(f_param0)
    dpl0.convert_fAm_to_nAm()

    # grab the current data
    # I_soma0 = currentfn.SynapticCurrent(f_current0)

    # grab the spike data
    _, p_dict0 = paramrw.read(f_param0)
    s0 = spikefn.spikes_from_file(f_param0, f_spk0)
    s0 = spikefn.alpha_feed_verify(s0, p_dict0)
    sp_list = s0['alpha_feed_prox'].spike_list[0]
    sd_list = s0['alpha_feed_dist'].spike_list[0]
    spikefn.pinput_hist(f.ax['hist_L'], f.ax_twinx['hist_L'], sp_list, sd_list, n_bins, xlim0)

    # plot the data
    dpl0.plot(f.ax['dpl_L'], xlim0, layer='L5')

    # second panel data
    f_spec1 = ddata1.file_match(expmt1, 'rawspec')[run1]
    f_dpl1 = ddata1.file_match(expmt1, 'rawdpl')[run1]
    f_spk1 = ddata1.file_match(expmt1, 'rawspk')[run1]
    f_param1 = ddata1.file_match(expmt1, 'param')[run1]
    # f_current1 = ddata1.file_match(expmt1, 'rawcurrent')[run1]

    # figure out the tstop and xlim
    tstop1 = paramrw.find_param(f_param1, 'tstop')
    xlim1 = (50., tstop1)

    # grab the dipole data
    dpl1 = dipolefn.Dipole(f_dpl1)
    dpl1.baseline_renormalize(f_param1)
    dpl1.convert_fAm_to_nAm()

    # # calculate the Welch periodogram
    # pgram1 = specfn.Welch(dpl1.t, dpl1.dpl['L5'], dt)
    # pgram1.plot_to_ax(f.ax['pgram_R'], f_max)

    # grab the spike data
    _, p_dict1 = paramrw.read(f_param1)
    s1 = spikefn.spikes_from_file(f_param1, f_spk1)
    s1 = spikefn.alpha_feed_verify(s1, p_dict1)
    sp_list = s1['alpha_feed_prox'].spike_list[0]
    sd_list = s1['alpha_feed_dist'].spike_list[0]
    spikefn.pinput_hist(f.ax['hist_R'], f.ax_twinx['hist_R'], sp_list, sd_list, n_bins, xlim1)

    # grab the current data
    # I_soma1 = currentfn.SynapticCurrent(f_current1)

    # plot the data
    dpl1.plot(f.ax['dpl_R'], xlim1, layer='L5')
    # spikefn.spike_png(f.ax['raster_R'], s1_L5)
    # f.ax['raster_R'].set_xlim(xlim1)

    # plot the spec data
    pc = {
        'L': specfn.pspec_ax(f.ax['spec_L'], f_spec0, xlim0, layer='L5'),
        'R': specfn.pspec_ax(f.ax['spec_R'], f_spec1, xlim1, layer='L5'),
    }

    # f.equalize_speclim(pc)

    # # grab the dipole figure handles
    # # list_h_dpl = [h for h in f.ax.keys() if h.startswith('dpl')]
    # # f.equalize_ylim(list_h_dpl)

    # # and the pgrams
    # # list_h_pgram = [h for h in f.ax.keys() if h.startswith('pgram')]
    # # test = f.equalize_ylim(list_h_pgram)

    # # plot current and do lims
    # I_soma0.plot_to_axis(f.ax['current_L'], 'L5')
    # I_soma1.plot_to_axis(f.ax['current_R'], 'L5')
    # for ax_handle in f.ax.keys():
    #     if ax_handle.startswith('current_'):
    #         f.ax[ax_handle].set_ylim((-2000, 0.))

    # # testing something
    # # f.ax['pgram_L'].set_yscale('log')
    # # f.ax['pgram_R'].set_yscale('log')
    # # f.ax['pgram_L'].set_ylim((1e-12, 1e-3))
    # # f.ax['pgram_R'].set_ylim((1e-12, 1e-3))

    # save the fig in ddata0 (arbitrary)
    f_prefix = 'gamma_sub_examples'
    dfig = os.path.join(ddata0.dsim, expmt0)

    # create the colorbars
    cb = dict.fromkeys(pc)

    if runtype == 'debug':
        for key in pc.keys():
            key_ax = 'spec_' + key
            cb[key] = f.f.colorbar(pc[key], ax=f.ax[key_ax])

    elif runtype == 'pub':
        cb['R'] = f.f.colorbar(pc['R'], ax=f.ax['spec_R'])

    f.savepng_new(dfig, f_prefix)
    f.saveeps(dfig, f_prefix)
    f.close()

def sub_dist_example2():
    dproj = fio.return_data_dir()
    runtype = 'pub2'
    # runtype = 'debug'

    # data directories (made up for now)
    # the resultant figure is saved in d0
    d0 = os.path.join(dproj, 'pub', '2013-08-07_gamma_sub_50Hz-000')

    # hard code the data for now
    ddata0 = fio.SimulationPaths()

    # use read_sim() to read the simulations
    ddata0.read_sim(dproj, d0)

    # for now grab the first experiment in each
    expmt0 = ddata0.expmt_groups[0]

    # for now hard code the simulation run
    run0 = 0
    run1 = 1

    # number of bins for the spike histograms
    n_bins = 500

    # prints the fig in ddata0
    f = acg.FigSubDistExample(runtype)

    # first panel data
    f_spec0 = ddata0.file_match(expmt0, 'rawspec')[run0]
    f_dpl0 = ddata0.file_match(expmt0, 'rawdpl')[run0]
    f_spk0 = ddata0.file_match(expmt0, 'rawspk')[run0]
    f_param0 = ddata0.file_match(expmt0, 'param')[run0]
    # f_current0 = ddata0.file_match(expmt0, 'rawcurrent')[run0]

    # figure out the tstop and xlim
    tstop0 = paramrw.find_param(f_param0, 'tstop')
    dt = paramrw.find_param(f_param0, 'dt')
    xlim0 = (50., tstop0)

    # grab the dipole data
    dpl0 = dipolefn.Dipole(f_dpl0)
    dpl0.baseline_renormalize(f_param0)
    dpl0.convert_fAm_to_nAm()

    # grab the current data
    # I_soma0 = currentfn.SynapticCurrent(f_current0)

    # grab the spike data
    _, p_dict0 = paramrw.read(f_param0)
    s0 = spikefn.spikes_from_file(f_param0, f_spk0)
    s0 = spikefn.alpha_feed_verify(s0, p_dict0)
    sp_list = s0['alpha_feed_prox'].spike_list[0]
    sd_list = s0['alpha_feed_dist'].spike_list[0]
    spikefn.pinput_hist(f.ax['hist_L'], f.ax_twinx['hist_L'], sp_list, sd_list, n_bins, xlim0)

    # plot the data
    dpl0.plot(f.ax['dpl_L'], xlim0, layer='L5')

    # second panel data
    f_spec1 = ddata0.file_match(expmt0, 'rawspec')[run1]
    f_dpl1 = ddata0.file_match(expmt0, 'rawdpl')[run1]
    f_spk1 = ddata0.file_match(expmt0, 'rawspk')[run1]
    f_param1 = ddata0.file_match(expmt0, 'param')[run1]
    # f_current1 = ddata1.file_match(expmt1, 'rawcurrent')[run1]

    # figure out the tstop and xlim
    tstop1 = paramrw.find_param(f_param1, 'tstop')
    xlim1 = (50., tstop1)

    # grab the dipole data
    dpl1 = dipolefn.Dipole(f_dpl1)
    dpl1.baseline_renormalize(f_param1)
    dpl1.convert_fAm_to_nAm()

    # # calculate the Welch periodogram
    # pgram1 = specfn.Welch(dpl1.t, dpl1.dpl['L5'], dt)
    # pgram1.plot_to_ax(f.ax['pgram_R'], f_max)

    # grab the spike data
    _, p_dict1 = paramrw.read(f_param1)
    s1 = spikefn.spikes_from_file(f_param1, f_spk1)
    s1 = spikefn.alpha_feed_verify(s1, p_dict1)
    sp_list = s1['alpha_feed_prox'].spike_list[0]
    sd_list = s1['alpha_feed_dist'].spike_list[0]
    spikefn.pinput_hist(f.ax['hist_R'], f.ax_twinx['hist_R'], sp_list, sd_list, n_bins, xlim1)
    f.ax['hist_R'].set_ylim((0., 20.))
    f.ax_twinx['hist_R'].set_ylim((20., 0.))

    # grab the current data
    # I_soma1 = currentfn.SynapticCurrent(f_current1)

    # plot the data
    dpl1.plot(f.ax['dpl_R'], xlim1, layer='L5')
    # spikefn.spike_png(f.ax['raster_R'], s1_L5)
    # f.ax['raster_R'].set_xlim(xlim1)

    # plot the spec data
    pc = {
        'L': specfn.pspec_ax(f.ax['spec_L'], f_spec0, xlim0, layer='L5'),
        'R': specfn.pspec_ax(f.ax['spec_R'], f_spec1, xlim1, layer='L5'),
    }

    # change the xlim format
    f.set_notation_scientific([ax for ax in f.ax.keys() if ax.startswith('dpl')], n=2)

    # f.equalize_speclim(pc)

    # # grab the dipole figure handles
    list_h_dpl = [h for h in f.ax.keys() if h.startswith('dpl')]
    f.equalize_ylim(list_h_dpl)

    # hack.
    f.ax['dpl_R'].set_yticklabels('')

    # and the pgrams
    # list_h_pgram = [h for h in f.ax.keys() if h.startswith('pgram')]
    # test = f.equalize_ylim(list_h_pgram)

    # # plot current and do lims
    # I_soma0.plot_to_axis(f.ax['current_L'], 'L5')
    # I_soma1.plot_to_axis(f.ax['current_R'], 'L5')
    # for ax_handle in f.ax.keys():
    #     if ax_handle.startswith('current_'):
    #         f.ax[ax_handle].set_ylim((-2000, 0.))

    # # testing something
    # # f.ax['pgram_L'].set_yscale('log')
    # # f.ax['pgram_R'].set_yscale('log')
    # # f.ax['pgram_L'].set_ylim((1e-12, 1e-3))
    # # f.ax['pgram_R'].set_ylim((1e-12, 1e-3))

    # save the fig in ddata0 (arbitrary)
    f_prefix = 'gamma_sub_examples'
    dfig = os.path.join(ddata0.dsim, expmt0)

    # create the colorbars
    cb = dict.fromkeys(pc)

    if runtype in ('debug', 'pub2'):
        for key in pc.keys():
            key_ax = 'spec_' + key
            cb[key] = f.f.colorbar(pc[key], ax=f.ax[key_ax])

        f.remove_twinx_labels()

    elif runtype == 'pub':
        cb['R'] = f.f.colorbar(pc['R'], ax=f.ax['spec_R'])

    f.savepng_new(dfig, f_prefix)
    f.saveeps(dfig, f_prefix)
    f.close()

# plots a histogram of e cell spikes relative to I cell spikes
def spikephase():
    dproj = fio.return_data_dir()
    # runtype = 'pub2'
    runtype = 'debug'

    # data directories (made up for now)
    # the resultant figure is saved in d0
    d0 = os.path.join(dproj, 'pub', '2013-06-28_gamma_weak_L5-000')

    # hard code the data for now
    ddata0 = fio.SimulationPaths()

    # use read_sim() to read the simulations
    ddata0.read_sim(dproj, d0)

    # for now grab the first experiment in each
    expmt0 = ddata0.expmt_groups[0]

    # for now hard code the simulation run
    run0 = 0

    # prints the fig in ddata0
    f = ac.FigStd()

    # create a twin axis
    f.create_axis_twinx('ax0')

    # first panel data
    f_spec0 = ddata0.file_match(expmt0, 'rawspec')[run0]
    f_dpl0 = ddata0.file_match(expmt0, 'rawdpl')[run0]
    f_spk0 = ddata0.file_match(expmt0, 'rawspk')[run0]
    f_param0 = ddata0.file_match(expmt0, 'param')[run0]
    # f_current0 = ddata0.file_match(expmt0, 'rawcurrent')[run0]

    # figure out the tstop and xlim
    tstop0 = paramrw.find_param(f_param0, 'tstop')
    dt = paramrw.find_param(f_param0, 'dt')
    xlim0 = (0., tstop0)

    # grab the spike data
    _, p_dict0 = paramrw.read(f_param0)
    s0 = spikefn.spikes_from_file(f_param0, f_spk0)
    icell_spikes = s0['L5_basket'].spike_list
    ecell_spikes = s0['L5_pyramidal'].spike_list

    ispike_counts = [len(slist) for slist in icell_spikes]
    espike_counts = [len(slist) for slist in ecell_spikes]

    # let's try a sort ...
    icell_spikes_agg = np.concatenate(icell_spikes)
    ecell_spikes_agg = np.concatenate(ecell_spikes)

    # lop off the first 50 ms
    icell_spikes_agg = icell_spikes_agg[icell_spikes_agg >= 50]
    icell_spikes_agg_sorted = np.sort(icell_spikes_agg)

    n_bins = int(tstop0 - 50)

    f.ax['ax0'].hist(icell_spikes_agg, n_bins, facecolor='r', histtype='stepfilled', alpha=0.75, edgecolor='none')
    f.ax_twinx['ax0'].hist(ecell_spikes_agg, n_bins, facecolor='k')
    # f.ax_twinx['ax0'].hist(ecell_spikes_agg, n_bins, facecolor='k', alpha=0.75)

    # sets these lims to the MAX number of possible events per bin (n_celltype limited)
    f.ax['ax0'].set_ylim((0, 35))
    f.ax_twinx['ax0'].set_ylim((0, 100))

    f.ax_twinx['ax0'].set_xlim((50, tstop0))
    f.ax['ax0'].set_xlim((50, tstop0))

    f.savepng_new(d0, 'testing')
    f.close()

    # save the fig in ddata0 (arbitrary)
    f_prefix = 'gamma_spikephase'
    dfig = os.path.join(ddata0.dsim, expmt0)

def peaks():
    dproj = fio.return_data_dir()
    # runtype = 'pub2'
    runtype = 'debug'

    # data directories (made up for now)
    # the resultant figure is saved in d0
    d0 = os.path.join(dproj, 'pub', '2013-07-01_gamma_sub_50Hz-002')
    # d1 = os.path.join(dproj, 'pub', '2013-07-18_gamma_sub_100Hz-000')

    # hard code the data for now
    ddata0 = fio.SimulationPaths()

    # use read_sim() to read the simulations
    ddata0.read_sim(dproj, d0)

    # for now grab the first experiment in each
    expmt0 = ddata0.expmt_groups[0]

    # for now hard code the simulation run
    run0 = 0

    # prints the fig in ddata0
    f = acg.FigPeaks(runtype)

    # first panel data
    f_spec0 = ddata0.file_match(expmt0, 'rawspec')[run0]
    f_dpl0 = ddata0.file_match(expmt0, 'rawdpl')[run0]
    f_spk0 = ddata0.file_match(expmt0, 'rawspk')[run0]
    f_param0 = ddata0.file_match(expmt0, 'param')[run0]
    # f_current0 = ddata0.file_match(expmt0, 'rawcurrent')[run0]

    # figure out the tstop and xlim
    tstop0 = paramrw.find_param(f_param0, 'tstop')
    dt = paramrw.find_param(f_param0, 'dt')
    xlim0 = (0., tstop0)

    # grab the dipole data
    dpl0 = dipolefn.Dipole(f_dpl0)
    dpl0.baseline_renormalize(f_param0)
    dpl0.convert_fAm_to_nAm()

    # grab the current data
    # I_soma0 = currentfn.SynapticCurrent(f_current0)

    # grab the spike data
    _, p_dict0 = paramrw.read(f_param0)
    s0 = spikefn.spikes_from_file(f_param0, f_spk0)
    s0 = spikefn.alpha_feed_verify(s0, p_dict0)
    sp_list = s0['alpha_feed_prox'].spike_list[0]
    sd_list = s0['alpha_feed_dist'].spike_list[0]
    # spikefn.pinput_hist(f.ax['hist_L'], f.ax_twinx['hist_L'], sp_list, sd_list, n_bins, xlim0)

    # plot the data
    dpl0.plot(f.ax['dpl_L'], xlim0, layer='L5')

    # plot the spec data
    pc = {
        'L': specfn.pspec_ax(f.ax['spec_L'], f_spec0, xlim0, layer='L5'),
    }

    # save the fig in ddata0 (arbitrary)
    f_prefix = 'gamma_peaks'
    dfig = os.path.join(ddata0.dsim, expmt0)

    # create the colorbars
    cb = dict.fromkeys(pc)

    if runtype == 'debug':
        for key in pc.keys():
            key_ax = 'spec_' + key
            cb[key] = f.f.colorbar(pc[key], ax=f.ax[key_ax])

    elif runtype == 'pub':
        cb['R'] = f.f.colorbar(pc['L'], ax=f.ax['spec_L'])

    f.savepng_new(dfig, f_prefix)
    f.saveeps(dfig, f_prefix)
    f.close()

# needs spec for multiple experiments, will plot 2 examples and aggregate
def pgamma_distal_phase(ddata, data_L=0, data_M=1, data_R=2):
    layer_specific = 'agg'

    for expmt in ddata.expmt_groups:
        f = acg.FigDistalPhase()

        # grab file lists
        list_spec = ddata.file_match(expmt, 'rawspec')
        list_dpl = ddata.file_match(expmt, 'rawdpl')
        list_spk = ddata.file_match(expmt, 'rawspk')
        list_param = ddata.file_match(expmt, 'param')

        # grab the tstop and make an xlim
        T = paramrw.find_param(list_param[0], 'tstop')
        xlim = (50., T)

        # grab the input frequency, try prox before dist
        f_max = paramrw.find_param(list_param[0], 'f_input_prox')

        # only try dist if prox is 0, otherwise, use prox
        if not f_max:
            f_max = paramrw.find_param(list_param[0], 'f_input_dist')

        # dealing with the left panel
        dpl_L = dipolefn.Dipole(list_dpl[data_L])
        dpl_L.baseline_renormalize(list_param[data_L])
        dpl_L.convert_fAm_to_nAm()
        dpl_L.plot(f.ax['dpl_L'], xlim, layer='agg')

        # middle data panel
        dpl_M = dipolefn.Dipole(list_dpl[data_M])
        dpl_M.baseline_renormalize(list_param[data_M])
        dpl_M.convert_fAm_to_nAm()
        dpl_M.plot(f.ax['dpl_M'], xlim, layer='agg')

        # dealing with right panel
        dpl_R = dipolefn.Dipole(list_dpl[data_R])
        dpl_R.baseline_renormalize(list_param[data_R])
        dpl_R.convert_fAm_to_nAm()
        dpl_R.plot(f.ax['dpl_R'], xlim, layer='agg')

        # get the vmin, vmax and add them to the master list
        pc = {
            'L': specfn.pspec_ax(f.ax['spec_L'], list_spec[data_L], xlim, layer=layer_specific),
            'M': specfn.pspec_ax(f.ax['spec_M'], list_spec[data_M], xlim, layer=layer_specific),
            'R': specfn.pspec_ax(f.ax['spec_R'], list_spec[data_R], xlim, layer=layer_specific),
        }

        # use the equalize function
        f.equalize_speclim(pc)

        # create colorbars
        f.f.colorbar(pc['L'], ax=f.ax['spec_L'])
        f.f.colorbar(pc['M'], ax=f.ax['spec_M'])
        f.f.colorbar(pc['R'], ax=f.ax['spec_R'])

        # hist data
        xlim_hist = (50., 100.)

        # get the data for the left panel
        _, p_dict = paramrw.read(list_param[data_L])
        s_L = spikefn.spikes_from_file(list_param[data_L], list_spk[data_L])
        s_L = spikefn.alpha_feed_verify(s_L, p_dict)
        # n_bins = spikefn.hist_bin_opt(s_L['alpha_feed_prox'].spike_list, 10)
        n_bins = 500

        # prox and dist spike lists
        sp_list = spike_list_truncate(s_L['alpha_feed_prox'].spike_list[0])
        sd_list = spike_list_truncate(s_L['alpha_feed_dist'].spike_list[0])
        spikefn.pinput_hist(f.ax['hist_L'], f.ax_twinx['hist_L'], sp_list, sd_list, n_bins, xlim_hist)

        # same motif as previous lines, I'm tired.
        _, p_dict = paramrw.read(list_param[data_M])
        s_M = spikefn.spikes_from_file(list_param[data_M], list_spk[data_M])
        s_M = spikefn.alpha_feed_verify(s_M, p_dict)
        sp_list = spike_list_truncate(s_M['alpha_feed_prox'].spike_list[0])
        sd_list = spike_list_truncate(s_M['alpha_feed_dist'].spike_list[0])
        spikefn.pinput_hist(f.ax['hist_M'], f.ax_twinx['hist_M'], sp_list, sd_list, n_bins, xlim_hist)

        # same motif as previous lines, I'm tired.
        _, p_dict = paramrw.read(list_param[data_R])
        s_R = spikefn.spikes_from_file(list_param[data_R], list_spk[data_R])
        s_R = spikefn.alpha_feed_verify(s_R, p_dict)
        sp_list = spike_list_truncate(s_R['alpha_feed_prox'].spike_list[0])
        sd_list = spike_list_truncate(s_R['alpha_feed_dist'].spike_list[0])
        spikefn.pinput_hist(f.ax['hist_R'], f.ax_twinx['hist_R'], sp_list, sd_list, n_bins, xlim_hist)

        # now do the aggregate data
        # theta is the normalized phase
        list_spec_max = np.zeros(len(list_spec))
        list_theta = np.zeros(len(list_spec))
        list_delay = np.zeros(len(list_spec))

        i = 0
        for fspec, fparam in zip(list_spec, list_param):
            # f_max comes from the input f
            # f_max = 50.
            t_pd = 1000. / f_max

            # read the data
            data_spec = specfn.read(fspec)

            # use specpwr_stationary() to get an aggregate measure of power over the entire time
            p_stat = specfn.specpwr_stationary(data_spec['time'], data_spec['freq'], data_spec['TFR'])

            # this is ONLY for aggregate and NOT for individual layers right now
            # here, f_max is the hard coded one and NOT the calculated one from specpwr_stationary()
            list_spec_max[i] = p_stat['p'][p_stat['f']==f_max]

            # get the relevant param's value
            t0_prox = paramrw.find_param(fparam, 't0_input_prox')
            t0_dist = paramrw.find_param(fparam, 't0_input_dist')

            # calculating these two together BUT don't need to. Cleanness beats efficiency here
            list_delay[i] = t0_dist - t0_prox
            list_theta[i] = list_delay[i] / t_pd

            i += 1

        f.ax['aggregate'].plot(list_delay, list_spec_max, marker='o')

        # deal with names
        f_prefix = 'gamma_%s_distal_phase' % expmt
        dfig = os.path.join(ddata.dsim, expmt)

        f.savepng_new(dfig, f_prefix)
        f.saveeps(dfig, f_prefix)
        f.close()

def spike_list_truncate(s_list):
    return s_list[(s_list > 55.) & (s_list < 100.)]

# needs spec for 3 experiments
# really a generic comparison of the top 3 sims in a given exp
# the list is naturally truncated by the length of ax_suffices
def pgamma_stdev(ddata):
    for expmt in ddata.expmt_groups:
        # runtype = 'debug'
        # runtype = 'pub2'
        runtype = 'pub'

        f = acg.Fig3PanelPlusAgg(runtype)

        # data types
        list_spec = ddata.file_match(expmt, 'rawspec')
        list_dpl = ddata.file_match(expmt, 'rawdpl')
        list_param = ddata.file_match(expmt, 'param')
        list_spk = ddata.file_match(expmt, 'rawspk')

        # time info
        T = paramrw.find_param(list_param[0], 'tstop')
        xlim = (50., T)

        # assume only the first 3 files are the ones we care about
        ax_suffices = [
            '_L',
            '_M',
            '_R',
            '_FR',
        ]

        # dpl handles list
        list_handles_dpl = []

        # spec handles
        pc = {}

        # lists in zip are naturally truncated by the shortest list
        for ax_end, fdpl, fspec, fparam, fspk in zip(ax_suffices, list_dpl, list_spec, list_param, list_spk):
            # create axis handle names
            ax_dpl = 'dpl%s' % ax_end
            ax_spec = 'spec%s' % ax_end
            ax_hist = 'hist%s' % ax_end

            # add to my terrible list
            list_handles_dpl.append(ax_dpl)

            # grab the dipole and convert
            dpl = dipolefn.Dipole(fdpl)
            dpl.baseline_renormalize(fparam)
            dpl.convert_fAm_to_nAm()

            # plot relevant data
            dpl.plot(f.ax[ax_dpl], xlim, layer='L5')
            pc[ax_spec] = specfn.pspec_ax(f.ax[ax_spec], fspec, xlim, layer='L5')

            # only set the colorbar for all axes in debug mode
            # otherwise set only for the rightmost spec axis
            if runtype in ('debug', 'pub2'):
                f.f.colorbar(pc[ax_spec], ax=f.ax[ax_spec])

            elif runtype == 'pub':
                if ax_end == '_FR':
                    f.f.colorbar(pc[ax_spec], ax=f.ax[ax_spec])

            # histogram stuff
            _, p_dict = paramrw.read(fparam)
            s = spikefn.spikes_from_file(fparam, fspk)
            s = spikefn.alpha_feed_verify(s, p_dict)

            # result of the optimization function, for the right 2 panels. 100
            # was the value returned for the L panel for f plot
            # result for stdev plot was 290, 80, 110
            # n_bins = spikefn.hist_bin_opt(s['alpha_feed_prox'][0].spike_list, 10)
            # print n_bins
            n_bins = 110

            # plot the hist
            spikefn.pinput_hist_onesided(f.ax[ax_hist], s['alpha_feed_prox'][0].spike_list, n_bins)
            f.ax[ax_hist].set_xlim(xlim)

        # equalize ylim on hists
        list_ax_hist = [ax for ax in f.ax.keys() if ax.startswith('hist')]
        f.equalize_ylim(list_ax_hist)

        # normalize the spec
        f.equalize_speclim(pc)
        f.remove_twinx_labels()

        # normalize the dpl with that hack
        # centers c and lim l
        # c = [1e-3, 1.2e-3, 1.8e-3]
        # l = 2e-3
        # for h in list_handles_dpl:
        #      f.ax[h].set_ylim((-3e-3, 3e-3))
        f.ysymmetry(f.ax['dpl_L'])
        f.set_notation_scientific(['dpl_L'])
        list_ax_dpl = [ax for ax in f.ax.keys() if ax.startswith('dpl')]
        f.equalize_ylim(list_ax_dpl)

        # some fig naming stuff
        fprefix_short = 'gamma_%s_compare3' % expmt
        dfig = os.path.join(ddata.dsim, expmt)

        # use methods to save figs
        f.savepng_new(dfig, fprefix_short)
        f.saveeps(dfig, fprefix_short)
        f.close()

def pgamma_stdev_new(ddata, p):
    for expmt in ddata.expmt_groups:
        # runtype = 'debug'
        runtype = 'pub2'
        # runtype = 'pub'

        f = acg.Fig3PanelPlusAgg(runtype)

        # data types
        list_spec = ddata.file_match(expmt, 'rawspec')
        list_dpl = ddata.file_match(expmt, 'rawdpl')
        list_param = ddata.file_match(expmt, 'param')
        list_spk = ddata.file_match(expmt, 'rawspk')

        # time info
        T = paramrw.find_param(list_param[0], 'tstop')
        xlim = (50., T)

        # assume only the first 3 files are the ones we care about
        ax_suffices = [
            '_L',
            '_M',
            '_R',
            '_FR',
        ]

        # dpl handles list
        list_handles_dpl = []

        # spec handles
        pc = {}

        # pgram_list
        list_pgram = []

        # lists in zip are naturally truncated by the shortest list
        for ax_end, fdpl, fspec, fparam, fspk in zip(ax_suffices, list_dpl, list_spec, list_param, list_spk):
            # create axis handle names
            ax_dpl = 'dpl%s' % ax_end
            ax_spec = 'spec%s' % ax_end
            ax_hist = 'hist%s' % ax_end

            # add to my terrible list
            list_handles_dpl.append(ax_dpl)

            # grab the dipole and convert
            dpl = dipolefn.Dipole(fdpl)
            dpl.baseline_renormalize(fparam)
            dpl.convert_fAm_to_nAm()

            # find the dpl lim
            ylim_dpl = dpl.lim('L5', xlim)

            # plot relevant data
            dpl.plot(f.ax[ax_dpl], xlim, layer='L5')
            f.ax[ax_dpl].set_ylim(ylim_dpl)
            pc[ax_spec] = specfn.pspec_ax(f.ax[ax_spec], fspec, xlim, layer='L5')

            # only set the colorbar for all axes in debug mode
            # otherwise set only for the rightmost spec axis
            if runtype in ('debug', 'pub2'):
                f.f.colorbar(pc[ax_spec], ax=f.ax[ax_spec])

            elif runtype == 'pub':
                if ax_end == '_FR':
                    f.f.colorbar(pc[ax_spec], ax=f.ax[ax_spec])

            # histogram stuff
            _, p_dict = paramrw.read(fparam)
            s = spikefn.spikes_from_file(fparam, fspk)
            s = spikefn.alpha_feed_verify(s, p_dict)

            # result of the optimization function, for the right 2 panels. 100
            # was the value returned for the L panel for f plot
            # result for stdev plot was 290, 80, 110
            # n_bins = spikefn.hist_bin_opt(s['alpha_feed_prox'][0].spike_list, 10)
            # print n_bins
            n_bins = 110

            # plot the hist
            spikefn.pinput_hist_onesided(f.ax[ax_hist], s['alpha_feed_prox'][0].spike_list, n_bins)
            # print s['alpha_feed_prox']
            f.ax[ax_hist].set_xlim(xlim)

            # run the Welch and plot it
            # get the dt, for the welch
            dt = paramrw.find_param(fparam, 'dt')
            list_pgram.append(specfn.Welch(dpl.t, dpl.dpl['L5'], dt))
            list_pgram[-1].scale(1e7)
            # f.ax['pgram'].plot(list_pgram[-1].f, list_pgram[-1].P)
            list_pgram[-1].plot_to_ax(f.ax['pgram'], p['f_max_welch'])
            print list_pgram[-1].units

        # equalize ylim on hists
        list_ax_hist = [ax for ax in f.ax.keys() if ax.startswith('hist')]
        f.equalize_ylim(list_ax_hist)
        for ax_h in list_ax_hist:
            f.ax[ax_h].set_ylim((0, 10))
            f.ax[ax_h].locator_params(axis='y', nbins=3)

        # f.ax['pgram'].yaxis.tick_right()

        # normalize the spec
        # f.equalize_speclim(pc)
        f.remove_twinx_labels()

        # normalize the dpl with that hack
        # centers c and lim l
        # c = [1e-3, 1.2e-3, 1.8e-3]
        # l = 2e-3
        # for h in list_handles_dpl:
        #      f.ax[h].set_ylim((-3e-3, 3e-3))
        # f.ysymmetry(f.ax['dpl_L'])
        # f.set_notation_scientific(['dpl_L'])
        list_ax_dpl = [ax for ax in f.ax.keys() if ax.startswith('dpl')]
        f.equalize_ylim(list_ax_dpl)
        for ax_h in list_ax_dpl:
            f.ax[ax_h].locator_params(axis='y', nbins=5)

        # some fig naming stuff
        fprefix_short = 'gamma_%s_compare3' % expmt
        dfig = os.path.join(ddata.dsim, expmt)

        # use methods to save figs
        f.savepng_new(dfig, fprefix_short)
        f.saveeps(dfig, fprefix_short)
        f.close()

def prox_dist_new(ddata, p):
    for expmt in ddata.expmt_groups:
        # runtype = 'debug'
        runtype = 'pub2'
        # runtype = 'pub'

        f = acg.Fig3PanelPlusAgg(runtype)

        # data types
        list_spec = ddata.file_match(expmt, 'rawspec')
        list_dpl = ddata.file_match(expmt, 'rawdpl')
        list_param = ddata.file_match(expmt, 'param')
        list_spk = ddata.file_match(expmt, 'rawspk')

        # time info
        T = paramrw.find_param(list_param[0], 'tstop')
        xlim = (50., T)

        # assume only the first 3 files are the ones we care about
        ax_suffices = [
            '_L',
            '_M',
            '_R',
            '_FR',
        ]

        # dpl handles list
        list_handles_dpl = []

        # spec handles
        pc = {}

        # pgram_list
        list_pgram = []

        # lists in zip are naturally truncated by the shortest list
        for ax_end, fdpl, fspec, fparam, fspk in zip(ax_suffices, list_dpl, list_spec, list_param, list_spk):
            # create axis handle names
            ax_dpl = 'dpl%s' % ax_end
            ax_spec = 'spec%s' % ax_end
            ax_hist = 'hist%s' % ax_end

            # add to my terrible list
            list_handles_dpl.append(ax_dpl)

            # grab the dipole and convert
            dpl = dipolefn.Dipole(fdpl)
            dpl.baseline_renormalize(fparam)
            dpl.convert_fAm_to_nAm()

            # find the dpl lim
            ylim_dpl = dpl.lim('L5', xlim)

            # plot relevant data
            dpl.plot(f.ax[ax_dpl], xlim, layer='L5')
            f.ax[ax_dpl].set_ylim(ylim_dpl)
            pc[ax_spec] = specfn.pspec_ax(f.ax[ax_spec], fspec, xlim, layer='L5')

            # only set the colorbar for all axes in debug mode
            # otherwise set only for the rightmost spec axis
            if runtype in ('debug', 'pub2'):
                f.f.colorbar(pc[ax_spec], ax=f.ax[ax_spec])

            elif runtype == 'pub':
                if ax_end == '_FR':
                    f.f.colorbar(pc[ax_spec], ax=f.ax[ax_spec])

            # histogram stuff
            n_bins = 110
            _, p_dict = paramrw.read(fparam)
            s = spikefn.spikes_from_file(fparam, fspk)
            s = spikefn.alpha_feed_verify(s, p_dict)
            sp_list = s['alpha_feed_prox'].spike_list[0]
            sd_list = s['alpha_feed_dist'].spike_list[0]
            spikefn.pinput_hist(f.ax[ax_hist], f.ax_twinx[ax_hist], sp_list, sd_list, n_bins, xlim)

            # result of the optimization function, for the right 2 panels. 100
            # was the value returned for the L panel for f plot
            # result for stdev plot was 290, 80, 110
            # n_bins = spikefn.hist_bin_opt(s['alpha_feed_prox'][0].spike_list, 10)
            # print n_bins

            # plot the hist
            # spikefn.pinput_hist_onesided(f.ax[ax_hist], s['alpha_feed_prox'][0].spike_list, n_bins)
            # print s['alpha_feed_prox']
            f.ax[ax_hist].set_xlim(xlim)

            # run the Welch and plot it
            # get the dt, for the welch
            dt = paramrw.find_param(fparam, 'dt')
            list_pgram.append(specfn.Welch(dpl.t, dpl.dpl['L5'], dt))
            list_pgram[-1].scale(1e7)
            # f.ax['pgram'].plot(list_pgram[-1].f, list_pgram[-1].P)
            list_pgram[-1].plot_to_ax(f.ax['pgram'], p['f_max_welch'])
            print list_pgram[-1].units

        # equalize ylim on hists
        list_ax_hist = [ax for ax in f.ax.keys() if ax.startswith('hist')]
        f.equalize_ylim(list_ax_hist)

        for ax_h in list_ax_hist:
            f.ax[ax_h].set_ylim((0, 20))
            f.ax_twinx[ax_h].set_ylim((20, 0))

            f.ax[ax_h].locator_params(axis='y', nbins=3)
            f.ax_twinx[ax_h].locator_params(axis='y', nbins=3)

        f.ax_twinx['hist_M'].set_yticklabels('')
        f.ax_twinx['hist_R'].set_yticklabels('')
        # f.ax['pgram'].yaxis.tick_right()

        # normalize the spec
        # f.equalize_speclim(pc)
        # f.remove_twinx_labels()

        # normalize the dpl with that hack
        # centers c and lim l
        # c = [1e-3, 1.2e-3, 1.8e-3]
        # l = 2e-3
        # for h in list_handles_dpl:
        #      f.ax[h].set_ylim((-3e-3, 3e-3))
        # f.ysymmetry(f.ax['dpl_L'])
        # f.set_notation_scientific(['dpl_L'])
        list_ax_dpl = [ax for ax in f.ax.keys() if ax.startswith('dpl')]
        f.equalize_ylim(list_ax_dpl)
        for ax_h in list_ax_dpl:
            f.ax[ax_h].locator_params(axis='y', nbins=5)

        # some fig naming stuff
        fprefix_short = 'gamma_%s_compare3' % expmt
        dfig = os.path.join(ddata.dsim, expmt)

        # use methods to save figs
        f.savepng_new(dfig, fprefix_short)
        f.saveeps(dfig, fprefix_short)
        f.close()

# manual setting of ylims
def ylim_hack(f, list_handles, ylim_centers, ylim_limit):
    # ylim_centers = [1.5e-5, 2e-5, 2.5e-5]
    # ylim_limit = 1.5e-5

    # gross
    for h, c in zip(list_handles, ylim_centers):
        f.ax[h].grid(True, which='minor')
        ylim = (c - ylim_limit, c + ylim_limit)
        f.ax[h].set_ylim(ylim)
        f.f.canvas.draw()
        # labels = [tick.get_text() for tick in f.ax[list_handles[1]].get_yticklabels()]
        labels = f.ax[h].yaxis.get_ticklocs()
        labels_text = [str(label) for label in labels[:-1]]
        labels_text[0] = ''
        f.ax[h].set_yticklabels(labels_text)
        # print labels_text

if __name__ == '__main__':
    hf_epochs()
