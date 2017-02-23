# ac_manu_gamma.py - axes for gamma manuscript paper figs
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: removed izip dep)
# last major: (MS: commented out mpl.use('agg') to prevent conflict ...)

import matplotlib as mpl
import axes_create as ac
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

class FigSimpleSpec(ac.FigBase):
    def __init__(self):
        self.f = plt.figure(figsize=(8, 6))
        font_prop = {'size': 8}
        mpl.rc('font', **font_prop)

        # the right margin is a hack and NOT guaranteed!
        # it's making space for the stupid colorbar that creates a new grid to replace gs1
        # when called, and it doesn't update the params of gs1
        self.gspec = {
            'dpl': gridspec.GridSpec(2, 1, height_ratios=[1, 3], bottom=0.85, top=0.95, left=0.1, right=0.82),
            'spec': gridspec.GridSpec(1, 4, wspace=0.05, hspace=0., bottom=0.10, top=0.80, left=0.1, right=1.),
        }

        self.ax = {}
        self.ax['dipole'] = self.f.add_subplot(self.gspec['dpl'][:, :])
        self.ax['spec'] = self.f.add_subplot(self.gspec['spec'][:, :])

class FigLaminarComparison(ac.FigBase):
    def __init__(self, runtype='debug'):
        # ac.FigBase.__init__()
        self.f = plt.figure(figsize=(9, 7))

        # set_fontsize() is part of FigBase()
        self.set_fontsize(8)

        # various gridspecs
        self.gspec = {
            'left': gridspec.GridSpec(8, 50),
            'middle': gridspec.GridSpec(8, 50),
            'right': gridspec.GridSpec(8, 50),
            'bottom_left': gridspec.GridSpec(1, 50),
            'bottom_middle': gridspec.GridSpec(1, 50),
            'bottom_right': gridspec.GridSpec(1, 50),
        }

        # reposition the gridspecs
        l = np.arange(0.12, 0.80, 0.27)
        r = l + 0.24

        # update the gridspecs
        # um, left is going right ...
        self.gspec['left'].update(wspace=0, hspace=0.30, bottom=0.25, top=0.94, left=l[2], right=r[2])
        self.gspec['middle'].update(wspace=0, hspace=0.30, bottom=0.25, top=0.94, left=l[0], right=r[0])
        self.gspec['right'].update(wspace=0, hspace=0.30, bottom=0.25, top=0.94, left=l[1], right=r[1])

        # bottom are going to mirror the top, despite the names
        self.gspec['bottom_left'].update(wspace=0, hspace=0.0, bottom=0.1, top=0.22, left=l[2], right=r[2])
        self.gspec['bottom_middle'].update(wspace=0, hspace=0.0, bottom=0.1, top=0.22, left=l[0], right=r[0])
        self.gspec['bottom_right'].update(wspace=0, hspace=0.0, bottom=0.1, top=0.22, left=l[1], right=r[1])

        # create axes and handles
        self.ax = {
            'dpl_L': self.f.add_subplot(self.gspec['left'][3:5, :40]),
            'dpl_M': self.f.add_subplot(self.gspec['middle'][3:5, :40]),
            'dpl_R': self.f.add_subplot(self.gspec['right'][3:5, :40]),

            'spk_M': self.f.add_subplot(self.gspec['middle'][:2, :40]),
            'spk_R': self.f.add_subplot(self.gspec['right'][:2, :40]),

            'current_M': self.f.add_subplot(self.gspec['middle'][2:3, :40]),
            'current_R': self.f.add_subplot(self.gspec['right'][2:3, :40]),

            'spec_L': None,
            'spec_M': None,
            'spec_R': self.f.add_subplot(self.gspec['right'][5:7, :]),

            'pgram_L': self.f.add_subplot(self.gspec['bottom_left'][:, :40]),
            'pgram_M': self.f.add_subplot(self.gspec['bottom_middle'][:, :40]),
            'pgram_R': self.f.add_subplot(self.gspec['bottom_right'][:, :40]),
        }

        if runtype in ('debug', 'pub2'):
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][5:7, :])
            self.ax['spec_M'] = self.f.add_subplot(self.gspec['middle'][5:7, :])

        elif runtype == 'pub':
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][5:7, :])
            self.ax['spec_M'] = self.f.add_subplot(self.gspec['middle'][5:7, :])

        # remove xtick labels
        list_ax_noxtick = [ax_handle for ax_handle in self.ax.keys() if ax_handle.startswith(('dpl', 'current', 'spk'))]

        # function defined in FigBase()
        self.remove_tick_labels(list_ax_noxtick, 'x')

        # remove ytick labels
        self.ax['spk_M'].set_yticklabels('')
        self.ax['spk_R'].set_yticklabels('')
        list_ax_noytick = []

        # write list of no y tick axes
        # if runtype == 'pub':
        #     list_ax_noytick.extend([ax_h for ax_h in self.ax.keys() if ax_h.startswith('spk')])
        #     list_ax_noytick.extend(['spec_R', 'spec_L'])

        # function defined in FigBase()
        self.remove_tick_labels(list_ax_noytick, 'y')
        self.create_ax_bounds_dict()
        self.create_y_centers_dict()
        self.__add_labels_subfig(l)
        self.__change_formatting()

    def __change_formatting(self):
        list_axes = ['pgram_L', 'pgram_M', 'pgram_R']
        self.set_notation_scientific(list_axes, 2)

    # add text labels
    def __add_labels_subfig(self, l):
        # top labels
        self.f.text(self.ax_bounds['spk_M'][0], self.ax_bounds['spk_M'][-1] + 0.005, 'A.')
        self.f.text(self.ax_bounds['spk_R'][0], self.ax_bounds['spk_R'][-1] + 0.005, 'B.')
        self.f.text(self.ax_bounds['dpl_L'][0], self.ax_bounds['dpl_L'][-1] + 0.005, 'C.')

        # left labels
        labels_left = {
            'va': 'center',
            'ma': 'center',
            'rotation': 90,
        }
        self.f.text(0.025, self.y_centers['spec_M'], 'Frequency (Hz)', **labels_left)
        self.f.text(0.025, self.y_centers['dpl_M'], 'Current Dipole \n (nAm)', **labels_left)
        self.f.text(0.025, self.y_centers['pgram_M'], 'Welch Spectral \n Power ((nAm)$^2$)', **labels_left)
        self.f.text(0.025, self.y_centers['spk_M'], 'Cells', **labels_left)
        self.f.text(0.025, self.y_centers['current_M'], 'Current \n ($\mu$A)', **labels_left)

        # bottom labels
        self.f.text(self.ax_bounds['spec_M'][0], self.ax_bounds['spec_M'][1] - 0.05, 'Time (ms)', ha='left')
        self.f.text(self.ax_bounds['pgram_M'][0], self.ax_bounds['pgram_M'][1] - 0.05, 'Frequency (Hz)', ha='left')

        # right labels
        self.f.text(0.95, self.y_centers['spec_L'], 'Spectral Power \n ((nAm)$^2$)', rotation=270, ma='center', va='center')

    def set_axes_pingping(self):
        self.ax['current_R'].set_ylim((-2000., 0.))

# strong ping and weak ping examples in Layer 5: Fig 2
class FigL5PingExample(ac.FigBase):
    def __init__(self, runtype='debug'):
        ac.FigBase.__init__(self)
        self.f = plt.figure(figsize=(7, 8))

        # set_fontsize() is part of FigBase()
        self.set_fontsize(8)

        # various gridspecs
        self.gspec = {
            'left': gridspec.GridSpec(7, 50),
            'right': gridspec.GridSpec(7, 50),
            'left_welch': gridspec.GridSpec(1, 50),
            'right_welch': gridspec.GridSpec(1, 50),
        }

        # repositioning the gspec
        l = np.arange(0.125, 0.90, 0.45)
        r = l + 0.33

        # create the gridspec
        if runtype.startswith('pub'):
            hspace_set = 0.30

        else:
            hspace_set = 0.30

        self.gspec['left'].update(wspace=0, hspace=hspace_set, bottom=0.29, top=0.94, left=l[0], right=r[0])
        self.gspec['right'].update(wspace=0, hspace=hspace_set, bottom=0.29, top=0.94, left=l[1], right=r[1])
        self.gspec['left_welch'].update(wspace=0, hspace=0, bottom=0.1, top=0.2, left=l[0], right=r[0])
        self.gspec['right_welch'].update(wspace=0, hspace=0, bottom=0.1, top=0.2, left=l[1], right=r[1])

        # create axes and handles
        # spec_L will be conditional on debug or production
        self.ax = {
            'raster_L': self.f.add_subplot(self.gspec['left'][:2, :40]),
            'hist_L': self.f.add_subplot(self.gspec['left'][2:3, :40]),
            'current_L': self.f.add_subplot(self.gspec['left'][3:4, :40]),
            'dpl_L': self.f.add_subplot(self.gspec['left'][4:5, :40]),
            'spec_L': None,
            'pgram_L': self.f.add_subplot(self.gspec['left_welch'][:, :]),

            'raster_R': self.f.add_subplot(self.gspec['right'][:2, :40]),
            'hist_R': self.f.add_subplot(self.gspec['right'][2:3, :40]),
            'current_R': self.f.add_subplot(self.gspec['right'][3:4, :40]),
            'dpl_R': self.f.add_subplot(self.gspec['right'][4:5, :40]),
            'spec_R': self.f.add_subplot(self.gspec['right'][5:7, :]),
            'pgram_R': self.f.add_subplot(self.gspec['right_welch'][:, :]),
        }

        # different spec_L depending on mode
        if runtype in ('debug', 'pub2'):
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][5:7, :])

        elif runtype == 'pub':
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][5:7, :40])

        # print dir(self.ax['pgram_L'].get_position())
        # print self.ax['pgram_L'].get_position().get_points()
        # print self.ax['pgram_L'].get_position().y0

        # create twinx for the hist
        for key in self.ax.keys():
            if key.startswith('hist_'):
                # this creates an f.ax_twinx dict with the appropriate key names
                self.create_axis_twinx(key)

        # pgram_axes
        list_handles_pgram = [h for h in self.ax.keys() if h.startswith('pgram_')]
        # self.fmt = self.set_notation_scientific(list_handles_pgram)
        self.fmt = None

        # remove ytick labels for the rasters
        for h in [ax for ax in self.ax if ax.startswith('raster_')]:
            self.ax[h].set_yticklabels('')

        if runtype.startswith('pub'):
            self.no_xaxis = ['raster', 'hist', 'dpl', 'current']
            self.no_yaxis = ['raster', 'spec', 'current']
            self.__remove_labels()

        self.__add_labels_subfig(l)

        self.list_sci = ['pgram_L', 'pgram_R']
        self.set_notation_scientific(self.list_sci)

    # add text labels
    # ma is 'multialignment' for multiple lines
    def __add_labels_subfig(self, l):
        self.ax_pos = dict.fromkeys(self.ax)

        # create the ycenter dict
        self.create_y_centers_dict()

        # first get all of the positions
        for ax_h in self.ax.keys():
            self.ax_pos[ax_h] = self.return_axis_bounds(ax_h)

        # raster is on top
        y_pad = 0.005
        label_y = self.ax_pos['raster_L'][-1] + y_pad
        self.f.text(l[0], label_y, 'A.')
        self.f.text(l[1], label_y, 'B.')

        # ylabel x pos
        x_pos = 0.025
        label_props = {
            'fontsize': 7,
            'rotation': 90,
            'va': 'center',
            'ma': 'center',
        }

        # cool, this uses a dict to fill in props. cool, cool, cool.
        self.f.text(x_pos, self.y_centers['raster_L'], 'Cell no.', **label_props)
        self.f.text(x_pos, self.y_centers['hist_L'], 'Spike\nhistogram\n(Left: I, Right: E)', **label_props)
        self.f.text(x_pos, self.y_centers['spec_L'], 'Frequency (Hz)', **label_props)
        self.f.text(x_pos, self.y_centers['dpl_L'], 'Current dipole \n (nAm)', **label_props)
        self.f.text(x_pos, self.y_centers['pgram_L'], 'Welch Spectral \n Power ((nAm)$^2$)', **label_props)
        self.f.text(x_pos, self.y_centers['current_L'], 'Total network \n GABA$_A$ current \n ($\mu$A)', **label_props)

        # xlabels
        self.f.text(l[0], 0.05, 'Frequency (Hz)')
        self.f.text(l[0], 0.25, 'Time (ms)')

        # find the spec_R coords and the associated center
        # and create the text label there
        coords_spec_R = self.return_axis_bounds('spec_R')
        ycenter = coords_spec_R[1] + (coords_spec_R[-1] - coords_spec_R[1]) / 2.
        self.f.text(0.97, ycenter, 'Spectral Power \n ((nAm)$^2$)', rotation=270, va='center', ha='center')

    # function to remove labels when not testing
    def __remove_labels(self):
        for ax in self.ax.keys():
            for label_prefix in self.no_xaxis:
                # if ((ax.startswith('dpl')) or (ax.startswith('current'))):
                if ax.startswith(label_prefix):
                    self.ax[ax].set_xticklabels('')

            if ax.endswith('_R'):
                for label_prefix in self.no_yaxis:
                    if ax.startswith(label_prefix):
                        self.ax[ax].set_yticklabels('')

# 3 examples of different phases and the aggregate spectral power as a function of delay
class FigDistalPhase(ac.FigBase):
    def __init__(self):
        ac.FigBase.__init__(self)
        self.f = plt.figure(figsize=(15, 4))

        # set_fontsize() is part of FigBase()
        self.set_fontsize(8)

        # various gridspecs
        self.gspec = {
            'left0': gridspec.GridSpec(4, 50),
            'left1': gridspec.GridSpec(4, 50),
            'middle': gridspec.GridSpec(4, 50),
            'right': gridspec.GridSpec(1, 1),
        }

        # number of cols are the number of gridspecs
        n_cols = len(self.gspec.keys())

        # find the start values by making a linspace from L margin to R margin
        # and then remove the R margin's element
        # this is why you need n_cols+1
        l = np.linspace(0.1, 0.95, n_cols+1)[:-1]

        # ensure first element of the unique on the diff of l to find
        # the width of each panel
        # remove the width of some margin
        w_margin = 0.05
        w = np.unique(np.diff(l))[0] - w_margin

        # to find the right position, just add w to the l
        r = l + w

        # create the gridspecs
        self.gspec['left0'].update(wspace=0, hspace=0.15, bottom=0.1, top=0.91, left=l[0], right=r[0])
        self.gspec['left1'].update(wspace=0, hspace=0.15, bottom=0.1, top=0.91, left=l[1], right=r[1])
        self.gspec['middle'].update(wspace=0, hspace=0.15, bottom=0.1, top=0.91, left=l[2], right=r[2])
        self.gspec['right'].update(wspace=0, hspace=0.15, bottom=0.1, top=0.91, left=l[3], right=r[3])

        # create axes and handles
        self.ax = {
            'spec_L': self.f.add_subplot(self.gspec['left0'][:2, :]),
            'spec_M': self.f.add_subplot(self.gspec['left1'][:2, :]),
            'spec_R': self.f.add_subplot(self.gspec['middle'][:2, :]),

            'dpl_L': self.f.add_subplot(self.gspec['left0'][2:3, :40]),
            'dpl_M': self.f.add_subplot(self.gspec['left1'][2:3, :40]),
            'dpl_R': self.f.add_subplot(self.gspec['middle'][2:3, :40]),

            'hist_L': self.f.add_subplot(self.gspec['left0'][3:, :40]),
            'hist_M': self.f.add_subplot(self.gspec['left1'][3:, :40]),
            'hist_R': self.f.add_subplot(self.gspec['middle'][3:, :40]),

            'aggregate': self.f.add_subplot(self.gspec['right'][:, :]),
        }

        self.__create_hist_twinx()
        self.__add_labels_subfig(l)

    def __create_hist_twinx(self):
        # ax_handles_hist = [ax for ax in self.ax.keys() if ax.startswith('hist')]
        for ax in self.ax.keys():
            if ax.startswith('hist'):
                self.create_axis_twinx(ax)

    # add text labels
    def __add_labels_subfig(self, l):
        self.f.text(l[0], 0.95, 'A.')
        self.f.text(l[1], 0.95, 'B.')
        self.f.text(l[2], 0.95, 'C.')
        self.f.text(l[3], 0.95, 'D.')

class FigStDev(ac.FigBase):
    def __init__(self, runtype='debug'):
        ac.FigBase.__init__(self)
        self.f = plt.figure(figsize=(8, 3))

        # set_fontsize() is part of FigBase()
        self.set_fontsize(8)

        # various gridspecs
        self.gspec = {
            'left': gridspec.GridSpec(4, 50),
            'middle': gridspec.GridSpec(4, 50),
            'right': gridspec.GridSpec(4, 50),
            'farright': gridspec.GridSpec(4, 50),
        }

        # reposition the gridspecs
        l = np.arange(0.1, 0.9, 0.2)
        # l = np.arange(0.05, 0.95, 0.3)
        r = l + 0.175

        # create the gridspecs
        self.gspec['left'].update(wspace=0, hspace=0.30, bottom=0.15, top=0.94, left=l[0], right=r[0])
        self.gspec['middle'].update(wspace=0, hspace=0.30, bottom=0.15, top=0.94, left=l[1], right=r[1])
        self.gspec['right'].update(wspace=0, hspace=0.30, bottom=0.15, top=0.94, left=l[2], right=r[2])
        self.gspec['farright'].update(wspace=0, hspace=0.30, bottom=0.15, top=0.94, left=l[3], right=r[3])

        self.ax = {
            'hist_L': self.f.add_subplot(self.gspec['left'][:1, :40]),
            'hist_M': self.f.add_subplot(self.gspec['middle'][:1, :40]),
            'hist_R': self.f.add_subplot(self.gspec['right'][:1, :40]),
            'hist_FR': self.f.add_subplot(self.gspec['farright'][:1, :40]),

            'dpl_L': self.f.add_subplot(self.gspec['left'][1:2, :40]),
            'dpl_M': self.f.add_subplot(self.gspec['middle'][1:2, :40]),
            'dpl_R': self.f.add_subplot(self.gspec['right'][1:2, :40]),
            'dpl_FR': self.f.add_subplot(self.gspec['farright'][1:2, :40]),

            # these are set differently depending on runtype, below
            'spec_L': None,
            'spec_M': None,
            'spec_R': None,
            'spec_FR': None,
        }

        if runtype in ('debug', 'pub2'):
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][2:, :])
            self.ax['spec_M'] = self.f.add_subplot(self.gspec['middle'][2:, :])
            self.ax['spec_R'] = self.f.add_subplot(self.gspec['right'][2:, :])
            self.ax['spec_FR'] = self.f.add_subplot(self.gspec['farright'][2:, :])

        elif runtype == 'pub':
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][2:, :40])
            self.ax['spec_M'] = self.f.add_subplot(self.gspec['middle'][2:, :40])
            self.ax['spec_R'] = self.f.add_subplot(self.gspec['right'][2:, :40])
            self.ax['spec_FR'] = self.f.add_subplot(self.gspec['farright'][2:, :])

        if runtype.startswith('pub'):
            self.__remove_labels()

        self.__create_twinx()

        # methods come from the FigBase()
        self.create_ax_bounds_dict()
        self.create_y_centers_dict()
        self.__add_labels_subfig(l)

    def __create_twinx(self):
        for ax_handle in self.ax.keys():
            if ax_handle.startswith('hist'):
                self.create_axis_twinx(ax_handle)

    # function to remove labels when not testing
    def __remove_labels(self):
        for ax in self.ax.keys():
            if ax.startswith(('dpl', 'hist')):
                self.ax[ax].set_xticklabels('')

            if ax.endswith(('_M', '_R', '_FR')):
                self.ax[ax].set_yticklabels('')

    def remove_twinx_labels(self):
        for ax in self.ax_twinx.keys():
            self.ax_twinx[ax].set_yticklabels('')

    # add text labels
    def __add_labels_subfig(self, l):
        self.f.text(self.ax_bounds['hist_L'][0], 0.95, 'A.')
        self.f.text(self.ax_bounds['hist_M'][0], 0.95, 'B.')
        self.f.text(self.ax_bounds['hist_R'][0], 0.95, 'C.')
        self.f.text(self.ax_bounds['hist_FR'][0], 0.95, 'D.')

        labels_left = {
            'va': 'center',
            'ma': 'center',
            'rotation': 90,
        }
        self.f.text(0.025, self.y_centers['spec_L'], 'Frequency \n (Hz)', **labels_left)
        self.f.text(0.025, self.y_centers['dpl_L'], 'Current dipole \n (nAm)', **labels_left)
        self.f.text(0.025, self.y_centers['hist_L'], 'EPSPs', **labels_left)

        self.f.text(self.ax_bounds['spec_L'][0], 0.025, 'Time (ms)', ha='left')
        self.f.text(self.ax_bounds['spec_FR'][2] + 0.05, self.y_centers['spec_FR'], 'Power spectral density \n ((nAm)$^2$/Hz)', rotation=270, va='center', ma='center')

class FigPanel4(ac.FigBase):
    def __init__(self, runtype='debug'):
        ac.FigBase.__init__(self)
        self.f = plt.figure(figsize=(8, 3))

        # set_fontsize() is part of FigBase()
        self.set_fontsize(8)

        # various gridspecs
        self.gspec = {
            'left': gridspec.GridSpec(4, 50),
            'middle': gridspec.GridSpec(4, 50),
            'right': gridspec.GridSpec(4, 50),
            'farright': gridspec.GridSpec(4, 50),
        }

        # reposition the gridspecs
        l = np.arange(0.1, 0.9, 0.2)
        # l = np.arange(0.05, 0.95, 0.3)
        r = l + 0.175

        # create the gridspecs
        self.gspec['left'].update(wspace=0, hspace=0.30, bottom=0.15, top=0.94, left=l[0], right=r[0])
        self.gspec['middle'].update(wspace=0, hspace=0.30, bottom=0.15, top=0.94, left=l[1], right=r[1])
        self.gspec['right'].update(wspace=0, hspace=0.30, bottom=0.15, top=0.94, left=l[2], right=r[2])
        self.gspec['farright'].update(wspace=0, hspace=0.30, bottom=0.15, top=0.94, left=l[3], right=r[3])

        self.ax = {
            'hist_L': self.f.add_subplot(self.gspec['left'][:1, :40]),
            'hist_M': self.f.add_subplot(self.gspec['middle'][:1, :40]),
            'hist_R': self.f.add_subplot(self.gspec['right'][:1, :40]),
            'hist_FR': self.f.add_subplot(self.gspec['farright'][:1, :40]),

            'dpl_L': self.f.add_subplot(self.gspec['left'][1:2, :40]),
            'dpl_M': self.f.add_subplot(self.gspec['middle'][1:2, :40]),
            'dpl_R': self.f.add_subplot(self.gspec['right'][1:2, :40]),
            'dpl_FR': self.f.add_subplot(self.gspec['farright'][1:2, :40]),

            # these are set differently depending on runtype, below
            'spec_L': None,
            'spec_M': None,
            'spec_R': None,
            'spec_FR': None,
        }

        if runtype in ('debug', 'pub2'):
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][2:, :])
            self.ax['spec_M'] = self.f.add_subplot(self.gspec['middle'][2:, :])
            self.ax['spec_R'] = self.f.add_subplot(self.gspec['right'][2:, :])
            self.ax['spec_FR'] = self.f.add_subplot(self.gspec['farright'][2:, :])

        elif runtype == 'pub':
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][2:, :40])
            self.ax['spec_M'] = self.f.add_subplot(self.gspec['middle'][2:, :40])
            self.ax['spec_R'] = self.f.add_subplot(self.gspec['right'][2:, :40])
            self.ax['spec_FR'] = self.f.add_subplot(self.gspec['farright'][2:, :])

        if runtype.startswith('pub'):
            self.__remove_labels()

        self.__create_twinx()

        # methods come from the FigBase()
        self.create_ax_bounds_dict()
        self.create_y_centers_dict()
        self.__add_labels_subfig(l)

    def __create_twinx(self):
        for ax_handle in self.ax.keys():
            if ax_handle.startswith('hist'):
                self.create_axis_twinx(ax_handle)

    # function to remove labels when not testing
    def __remove_labels(self):
        for ax in self.ax.keys():
            if ax.startswith(('dpl', 'hist')):
                self.ax[ax].set_xticklabels('')

            if ax.endswith(('_M', '_R', '_FR')):
                self.ax[ax].set_yticklabels('')

    def remove_twinx_labels(self):
        for ax in self.ax_twinx.keys():
            self.ax_twinx[ax].set_yticklabels('')

    # add text labels
    def __add_labels_subfig(self, l):
        self.f.text(self.ax_bounds['hist_L'][0], 0.95, 'A.')
        self.f.text(self.ax_bounds['hist_M'][0], 0.95, 'B.')
        self.f.text(self.ax_bounds['hist_R'][0], 0.95, 'C.')
        self.f.text(self.ax_bounds['hist_FR'][0], 0.95, 'D.')

        labels_left = {
            'va': 'center',
            'ma': 'center',
            'rotation': 90,
        }
        self.f.text(0.025, self.y_centers['spec_L'], 'Frequency \n (Hz)', **labels_left)
        self.f.text(0.025, self.y_centers['dpl_L'], 'Current dipole \n (nAm)', **labels_left)
        self.f.text(0.025, self.y_centers['hist_L'], 'EPSPs', **labels_left)

        self.f.text(self.ax_bounds['spec_L'][0], 0.025, 'Time (ms)', ha='left')
        self.f.text(self.ax_bounds['spec_FR'][2] + 0.05, self.y_centers['spec_FR'], 'Power spectral density \n ((nAm)$^2$/Hz)', rotation=270, va='center', ma='center')

class Fig3PanelPlusAgg(ac.FigBase):
    def __init__(self, runtype='debug'):
        ac.FigBase.__init__(self)
        self.f = plt.figure(figsize=(10, 3))

        # set_fontsize() is part of FigBase()
        self.set_fontsize(6)

        # various gridspecs
        self.gspec = {
            'left': gridspec.GridSpec(5, 50),
            'middle': gridspec.GridSpec(5, 50),
            'right': gridspec.GridSpec(5, 50),
            'farright': gridspec.GridSpec(5, 50),
        }

        # reposition the gridspecs
        # l = np.arange(0.075, 0.8, 0.22)
        l = np.array([0.075, 0.295, 0.515, 0.740])
        # l = np.arange(0.05, 0.95, 0.3)
        r = l + 0.2
        # r[-1] += 0.025

        # create the gridspecs
        self.gspec['left'].update(wspace=0, hspace=0.30, bottom=0.15, top=0.94, left=l[0], right=r[0])
        self.gspec['middle'].update(wspace=0, hspace=0.30, bottom=0.15, top=0.94, left=l[1], right=r[1])
        self.gspec['right'].update(wspace=0, hspace=0.30, bottom=0.15, top=0.94, left=l[2], right=r[2])
        self.gspec['farright'].update(wspace=0, hspace=0.30, bottom=0.15, top=0.94, left=l[3], right=r[3])

        self.ax = {
            'hist_L': self.f.add_subplot(self.gspec['left'][:1, :40]),
            'hist_M': self.f.add_subplot(self.gspec['middle'][:1, :40]),
            'hist_R': self.f.add_subplot(self.gspec['right'][:1, :40]),

            'dpl_L': self.f.add_subplot(self.gspec['left'][1:3, :40]),
            'dpl_M': self.f.add_subplot(self.gspec['middle'][1:3, :40]),
            'dpl_R': self.f.add_subplot(self.gspec['right'][1:3, :40]),

            # aggregate welch
            'pgram': self.f.add_subplot(self.gspec['farright'][:, :]),

            # these are set differently depending on runtype, below
            'spec_L': None,
            'spec_M': None,
            'spec_R': None,
        }

        if runtype in ('debug', 'pub2'):
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][3:, :])
            self.ax['spec_M'] = self.f.add_subplot(self.gspec['middle'][3:, :])
            self.ax['spec_R'] = self.f.add_subplot(self.gspec['right'][3:, :])

        elif runtype == 'pub':
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][3:, :40])
            self.ax['spec_M'] = self.f.add_subplot(self.gspec['middle'][3:, :40])
            self.ax['spec_R'] = self.f.add_subplot(self.gspec['right'][3:, :])

        if runtype.startswith('pub'):
            self.__remove_labels()

        # periodogram hold on
        self.ax['pgram'].hold(True)
        self.ax['pgram'].yaxis.tick_right()

        self.__create_twinx()
        self.create_ax_bounds_dict()
        self.create_y_centers_dict()
        self.__add_labels_subfig(l)

    def __create_twinx(self):
        for ax_handle in self.ax.keys():
            if ax_handle.startswith('hist'):
                self.create_axis_twinx(ax_handle)

    # function to remove labels when not testing
    def __remove_labels(self):
        for ax in self.ax.keys():
            if ax.startswith(('dpl', 'hist')):
                self.ax[ax].set_xticklabels('')

            if ax.endswith(('_M', '_R')):
                self.ax[ax].set_yticklabels('')

    def remove_twinx_labels(self):
        for ax in self.ax_twinx.keys():
            self.ax_twinx[ax].set_yticklabels('')

    # add text labels
    def __add_labels_subfig(self, l):
        self.f.text(l[0], 0.95, 'A.')
        self.f.text(l[1], 0.95, 'B.')
        self.f.text(l[2], 0.95, 'C.')
        self.f.text(l[3], 0.95, 'D.')

        ylabel_props = {
            'rotation': 90,
            'va': 'center',
            'ma': 'center',
        }

        ylabel_right_props = {
            'rotation': 270,
            'va': 'center',
            'ma': 'center',
            'ha': 'center',
        }

        xoffset = 0.0675

        # y labels
        self.f.text(l[0] - xoffset, self.y_centers['hist_L'], 'EPSP \n Count', **ylabel_props)
        self.f.text(l[0] - xoffset, self.y_centers['dpl_L'], 'Current Dipole \n (nAm)', **ylabel_props)
        self.f.text(l[0] - xoffset, self.y_centers['spec_L'], 'Frequency \n (Hz)', **ylabel_props)

        # self.ax['spec_L'].set_ylabel('Frequency (Hz)')
        # self.ax['dpl_L'].set_ylabel('Current dipole (nAm)')
        # self.ax['hist_L'].set_ylabel('EPSP count')

        self.f.text(l[0], 0.025, 'Time (ms)')
        self.f.text(l[-1], 0.025, 'Frequency (Hz)')
        self.f.text(0.975, self.y_centers['pgram'], 'Welch Spectral Power \n ((nAm)$^2$ x10$^{-7}$)', **ylabel_right_props)
        self.f.text(self.ax_bounds['spec_R'][2] + 0.005, self.y_centers['spec_R'], 'Spectral Power \n ((nAm)$^2$)', fontsize=5, **ylabel_right_props)
        # self.f.text(self.ax_bounds['hist_L'][-2]+0.05, self.y_centers['hist_L'], 'Distal EPSP Count', rotation=270, va='center', ma='center', ha='center')
        # self.f.text(0.925, 0.40, 'Power spectral density ((nAm)$^2$/Hz)', rotation=270)

class FigSubDistExample(ac.FigBase):
    def __init__(self, runtype='debug'):
        ac.FigBase.__init__(self)
        self.f = plt.figure(figsize=(6, 5))

        # set_fontsize() is part of FigBase()
        self.set_fontsize(8)

        # various gridspecs
        self.gspec = {
            'left': gridspec.GridSpec(4, 50),
            'right': gridspec.GridSpec(4, 50),
        }

        # reposition the gridspecs
        l = np.array([0.1, 0.52])
        # l = np.arange(0.1, 0.9, 0.45)
        r = l + 0.39

        # create the gridspecs
        self.gspec['left'].update(wspace=0, hspace=0.30, bottom=0.1, top=0.94, left=l[0], right=r[0])
        self.gspec['right'].update(wspace=0, hspace=0.30, bottom=0.1, top=0.94, left=l[1], right=r[1])

        self.ax = {
            'hist_L': self.f.add_subplot(self.gspec['left'][:1, :40]),
            'hist_R': self.f.add_subplot(self.gspec['right'][:1, :40]),

            'dpl_L': self.f.add_subplot(self.gspec['left'][1:2, :40]),
            'dpl_R': self.f.add_subplot(self.gspec['right'][1:2, :40]),

            # these are set differently depending on runtype, below
            'spec_L': None,
            'spec_R': None,
        }

        if runtype in ('debug', 'pub2'):
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][2:, :])
            self.ax['spec_R'] = self.f.add_subplot(self.gspec['right'][2:, :])

        elif runtype == 'pub':
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][2:, :40])
            self.ax['spec_R'] = self.f.add_subplot(self.gspec['right'][2:, :])

        if runtype.startswith('pub'):
            self.__remove_labels()

        self.__create_twinx()
        self.create_ax_bounds_dict()
        self.create_y_centers_dict()
        self.__add_labels_subfig(l)

    def __create_twinx(self):
        for ax_handle in self.ax.keys():
            if ax_handle.startswith('hist'):
                self.create_axis_twinx(ax_handle)

    # function to remove labels when not testing
    def __remove_labels(self):
        for ax in self.ax.keys():
            if ax.startswith(('dpl', 'hist')):
                self.ax[ax].set_xticklabels('')

            if ax.endswith('_R'):
                self.ax[ax].set_yticklabels('')

    def remove_twinx_labels(self):
        for ax in self.ax_twinx.keys():
            if ax.endswith('_R'):
                self.ax_twinx[ax].set_yticklabels('')

    # add text labels
    def __add_labels_subfig(self, l):
        # left labels
        labels_left = {
            'va': 'center',
            'ma': 'center',
            'rotation': 90,
        }
        self.f.text(0.02, self.y_centers['spec_L'], 'Frequency (Hz)', **labels_left)
        self.f.text(0.02, self.y_centers['dpl_L'], 'Current Dipole \n (nAm)', **labels_left)
        self.f.text(0.02, self.y_centers['hist_L'], 'Proximal EPSP Count', **labels_left)
        # self.f.text(self.ax_bounds['spec_M'][0], self.ax_bounds['spec_M'][1] - 0.05, 'Time (ms)', ha='left')
        self.f.text(self.ax_bounds['hist_L'][-2]+0.05, self.y_centers['hist_L'], 'Distal EPSP Count', rotation=270, va='center', ma='center', ha='center')
        self.f.text(0.95, self.y_centers['spec_R'], 'Power spectral density \n ((nAm)$^2$/Hz)', rotation=270, ha='center', ma='center', va='center')

        self.f.text(l[0], 0.95, 'A.')
        self.f.text(l[1], 0.95, 'B.')

        # self.ax['spec_L'].set_ylabel('Frequency (Hz)')
        # self.ax['dpl_L'].set_ylabel('Current dipole (nAm)')
        # self.ax['hist_L'].set_ylabel('Proximal EPSP count')
        # self.ax_twinx['hist_L'].set_ylabel('Distal EPSP count')

        self.f.text(l[0], 0.025, 'Time (ms)')

class FigPeaks(ac.FigBase):
    def __init__(self, runtype='debug'):
        ac.FigBase.__init__(self)
        self.f = plt.figure(figsize=(4, 5))

        # set_fontsize() is part of FigBase()
        self.set_fontsize(8)

        # various gridspecs
        self.gspec = {
            'left': gridspec.GridSpec(4, 50),
            'right': gridspec.GridSpec(4, 50),
        }

        # reposition the gridspecs
        l = np.arange(0.1, 0.9, 0.45)
        r = l + 0.8

        # create the gridspecs
        self.gspec['left'].update(wspace=0, hspace=0.30, bottom=0.1, top=0.94, left=l[0], right=r[0])
        self.gspec['right'].update(wspace=0, hspace=0.30, bottom=0.1, top=0.94, left=l[1], right=r[1])

        self.ax = {
            'dpl_L': self.f.add_subplot(self.gspec['left'][:1, :40]),
            'hist_L': self.f.add_subplot(self.gspec['left'][1:2, :40]),

            # these are set differently depending on runtype, below
            'spec_L': None,
        }

        if runtype in ('debug', 'pub2'):
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][2:, :])

        elif runtype == 'pub':
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][2:, :40])

        if runtype.startswith('pub'):
            self.__remove_labels()

        # self.__create_twinx()
        # self.__add_labels_subfig(l)

    def __create_twinx(self):
        for ax_handle in self.ax.keys():
            if ax_handle.startswith('hist'):
                self.create_axis_twinx(ax_handle)

    # function to remove labels when not testing
    def __remove_labels(self):
        for ax in self.ax.keys():
            if ax.startswith(('dpl', 'hist')):
                self.ax[ax].set_xticklabels('')

            if ax.endswith('_R'):
                self.ax[ax].set_yticklabels('')

    def remove_twinx_labels(self):
        for ax in self.ax_twinx.keys():
            self.ax_twinx[ax].set_yticklabels('')

    # add text labels
    def __add_labels_subfig(self, l):
        self.f.text(l[0], 0.95, 'A.')
        self.f.text(l[1], 0.95, 'B.')

        self.ax['spec_L'].set_ylabel('Frequency (Hz)')
        self.ax['dpl_L'].set_ylabel('Current dipole (nAm)')
        self.ax['hist_L'].set_ylabel('EPSP count')

        self.f.text(l[0], 0.025, 'Time (ms)')
        self.f.text(0.95, 0.40, 'Power spectral density ((nAm)$^2$/Hz)', rotation=270)

class FigHF(ac.FigBase):
    def __init__(self, runtype='debug'):
        ac.FigBase.__init__(self)
        self.f = plt.figure(figsize=(5, 7))

        # set_fontsize() is part of FigBase()
        self.set_fontsize(8)

        # various gridspecs
        self.gspec = {
            'left': gridspec.GridSpec(5, 50),
        }

        # reposition the gridspecs
        # l = np.arange(0.1, 0.9, 0.28)
        # l = np.arange(0.05, 0.95, 0.3)
        # r = l + 0.275

        # create the gridspecs
        self.gspec['left'].update(wspace=0, hspace=0.30, bottom=0.1, top=0.94, left=0.2, right=0.95)
        l = 0.1

        self.ax = {
            'spk': self.f.add_subplot(self.gspec['left'][:1, :40]),
            'hist_L': self.f.add_subplot(self.gspec['left'][1:2, :40]),
            'dpl_L': self.f.add_subplot(self.gspec['left'][2:4, :40]),

            # these are set differently depending on runtype, below
            'spec_L': None,
        }

        if runtype in ('debug', 'pub2'):
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][4:, :])

        elif runtype == 'pub':
            self.ax['spec_L'] = self.f.add_subplot(self.gspec['left'][4:, :40])

        # if runtype.startswith('pub'):
        #     self.__remove_labels()

        self.__create_twinx()
        self.__add_labels_subfig(l)

    def __create_twinx(self):
        for ax_handle in self.ax.keys():
            if ax_handle.startswith('dpl'):
                self.create_axis_twinx(ax_handle)

    # function to remove labels when not testing
    def __remove_labels(self):
        for ax in self.ax.keys():
            if ax.startswith(('dpl', 'hist')):
                self.ax[ax].set_xticklabels('')

            if ax.endswith(('_M', '_R')):
                self.ax[ax].set_yticklabels('')

    def remove_twinx_labels(self):
        for ax in self.ax_twinx.keys():
            self.ax_twinx[ax].set_yticklabels('')

    # add text labels
    def __add_labels_subfig(self, l):
        # self.f.text(l, 0.95, 'A.')

        self.ax['spk'].set_ylabel('Cells')
        self.ax['spec_L'].set_ylabel('Frequency (Hz)')
        self.ax['spec_L'].set_xlabel('Time (ms)')
        self.ax['dpl_L'].set_ylabel('Current dipole (nAm)')
        self.ax['hist_L'].set_ylabel('L5 Pyramidal Spikes')
        self.ax_twinx['dpl_L'].set_ylabel('Current (nA)', rotation=270)

        # self.f.text(l, 0.025, 'Time (ms)')
        # self.f.text(0.925, 0.40, 'Power spectral density ((nAm)$^2$/Hz)', rotation=270)

# high frequency epochs fig
class FigHFEpochs(ac.FigBase):
    def __init__(self, runtype='pub'):
        ac.FigBase.__init__(self)
        self.f = plt.figure(figsize=(9.5, 7))

        # set_fontsize() is part of FigBase()
        self.set_fontsize(9)

        # called L_gspec so the ax keys can be (a) sortably grouped and (b) congruent with gspec
        # I want it to be called gspec_L, but you can't have everything you want in life.
        self.L_gspec = gridspec.GridSpec(5, 50)
        self.L_gspec.update(wspace=0, hspace=0.1, bottom=0.1, top=0.95, left=0.07, right=0.32)

        self.gspec_ex = [
            gridspec.GridSpec(7, 50),
            gridspec.GridSpec(7, 50),
            gridspec.GridSpec(7, 50),
            gridspec.GridSpec(7, 50),
        ]

        # reposition the gridspecs. there are cleverer ways of doing this
        w = 0.25
        l_split = np.array([0.05, 0.36, 0.63])
        # l_split = np.arange(0.05, 0.95, 0.3)
        self.l_ex = np.array([l_split[1], l_split[2], l_split[1], l_split[2]])
        self.r_ex = self.l_ex + w

        # bottom and tops
        h = 0.4
        b_ex = np.array([0.55, 0.55, 0.10, 0.10])
        # b_ex = np.array([0.1, 0.1, 0.55, 0.55])
        t_ex = b_ex + h

        # l = np.arange(0.25, 0.9, 0.2)
        # r = l + 0.1
        # r = l + 0.275

        # create the gridspecs
        for i in range(len(self.gspec_ex)):
            self.gspec_ex[i].update(wspace=0, hspace=0.30, bottom=b_ex[i], top=t_ex[i], left=self.l_ex[i], right=self.r_ex[i])

        self.ax = {
            'L_spk': self.f.add_subplot(self.L_gspec[:2, :40]),
            'L_dpl': self.f.add_subplot(self.L_gspec[2:3, :40]),
            'L_spec': self.f.add_subplot(self.L_gspec[3:, :40]),
            'hist': [
                self.f.add_subplot(self.gspec_ex[0][:1, :40]),
                self.f.add_subplot(self.gspec_ex[1][:1, :40]),
                self.f.add_subplot(self.gspec_ex[2][:1, :40]),
                self.f.add_subplot(self.gspec_ex[3][:1, :40]),
            ],

            'spk': [
                self.f.add_subplot(self.gspec_ex[0][1:3, :40]),
                self.f.add_subplot(self.gspec_ex[1][1:3, :40]),
                self.f.add_subplot(self.gspec_ex[2][1:3, :40]),
                self.f.add_subplot(self.gspec_ex[3][1:3, :40]),
            ],

            'dpl': [
                self.f.add_subplot(self.gspec_ex[0][3:5, :40]),
                self.f.add_subplot(self.gspec_ex[1][3:5, :40]),
                self.f.add_subplot(self.gspec_ex[2][3:5, :40]),
                self.f.add_subplot(self.gspec_ex[3][3:5, :40]),
            ],

            # these are set differently depending on runtype, below
            'spec': None,
        }

        if runtype in ('debug', 'pub2'):
            self.ax['spec'] = [
                self.f.add_subplot(self.gspec_ex[0][5:, :]),
                self.f.add_subplot(self.gspec_ex[1][5:, :]),
                self.f.add_subplot(self.gspec_ex[2][5:, :]),
                self.f.add_subplot(self.gspec_ex[3][5:, :]),
            ]

        elif runtype == 'pub':
            self.ax['spec'] = [
                self.f.add_subplot(self.gspec_ex[0][5:, :40]),
                self.f.add_subplot(self.gspec_ex[1][5:, :40]),
                self.f.add_subplot(self.gspec_ex[2][5:, :40]),
                self.f.add_subplot(self.gspec_ex[3][5:, :]),
            ]

        self.__create_twinx()

        if runtype.startswith('pub'):
            self.__remove_labels()

        self.create_ax_bounds_dict()
        self.create_y_centers_dict()
        self.__add_labels_left()
        self.__add_labels_subfig()

    # takes a specific ax and a well-formed props_dict
    def add_sine(self, ax, props_dict):
        # will create fake sine waves with various properties
        # t_center = props_dict['t_center']
        f = props_dict['f']
        # t_half = 0.5 * (1000. / f)
        t0 = props_dict['t'][0]
        T = props_dict['t'][1]
        # t0 = t_center - t_half
        # T = t_center + t_half
        t = np.arange(t0, T, props_dict['dt'])
        x = props_dict['A'] * np.sin(2 * np.pi * f * (t - t0) / 1000.)
        # x = 0.01 * np.sin(2 * np.pi * f * (t - t0) / 1000.)
        ax.plot(t, x, 'r--')

    # the general twinx function cannot be used, due to the structure of the axes here
    def __create_twinx(self):
        # just create the twinx list for the dipole
        self.ax_twinx['dpl'] = [ax_h.twinx() for ax_h in self.ax['dpl']]

    # function to remove labels when not testing
    def __remove_labels(self):
        for ax_h in self.ax.keys():
            if ax_h.startswith('L_'):
                if ax_h.endswith(('spk', 'dpl')):
                    self.ax[ax_h].set_xticklabels('')

                if ax_h.endswith('spk'):
                    self.ax[ax_h].set_yticklabels('')

            for ax_h in self.ax.keys():
                if not ax_h.startswith(('L', 'spec')):
                    for i in range(1, 4):
                        self.ax[ax_h][i].set_xticklabels('')

                if not ax_h.startswith('L'):
                    if not ax_h.startswith('spec'):
                        for i in range(0, 2):
                            self.ax[ax_h][i].set_xticklabels('')

                    for i in range(1, 4):
                        self.ax[ax_h][i].set_yticklabels('')

                # remove the spk ones
                if ax_h == 'spk':
                    self.ax[ax_h][0].set_yticklabels('')

            for i in range(1, 4):
                self.ax_twinx['dpl'][i].set_yticklabels('')

    def remove_twinx_labels(self):
        for ax in self.ax_twinx.keys():
            self.ax_twinx[ax].set_yticklabels('')

    # add text labels
    def __add_labels_left(self):
        label_props = {
            'rotation': 90,
            'va': 'center',
            'ma': 'center',
        }
        self.f.text(0.018, self.y_centers['L_spec'], 'Frequency (Hz)', **label_props)
        self.f.text(0.018, self.y_centers['L_dpl'], 'Current Dipole (nAm)', **label_props)
        self.f.text(0.018, self.y_centers['L_spk'], 'Cells', **label_props)
        self.f.text(0.07, 0.04, 'Time (ms)', ha='left')

        x = self.ax_bounds['L_spk'][0]
        y = self.ax_bounds['L_spk'][-1] + 0.005
        self.f.text(x, y, 'A.', ha='left')

    def __add_labels_subfig(self):
        list_labels = ['B.', 'C.', 'D.', 'E.']

        label_props = {
            'ha': 'left',
        }

        # for ax_h, lbl in zip(self.ax['hist'], list_labels):
        for i in range(len(self.ax['hist'])):
            # get the x coord
            x = self.ax_bounds['hist'][i][0]
            y = self.ax_bounds['hist'][i][-1] + 0.005
            self.f.text(x, y, list_labels[i], **label_props)

        # for x_l, lbl in zip(self.l_ex, list_labels):
        #     self.f.text(x_l, 0.95, lbl+'.')

        ylabel_props = {
            'rotation': 90,
            'va': 'center',
            'ma': 'center',
        }

        xoffset = 0.0675

        # y labels
        self.f.text(self.l_ex[0] - xoffset, self.y_centers['spec'][0], 'Frequency \n (Hz)', **ylabel_props)
        self.f.text(self.l_ex[0] - xoffset, self.y_centers['dpl'][0], 'Current Dipole \n (nAm)', **ylabel_props)
        self.f.text(self.l_ex[0] - xoffset, self.y_centers['hist'][0], 'L5 Pyramidal \n Spike Count', **ylabel_props)
        self.f.text(self.l_ex[0] - xoffset, self.y_centers['spk'][0], 'Cells', **ylabel_props)
        self.f.text(self.r_ex[0] - 0.02, self.y_centers['dpl'][0], 'Somatic current \n ($\mu$A)', rotation=270, ma='center', va='center')
        self.f.text(0.925, self.y_centers['spec'][-1], 'Spectral Power \n ((nAm)$^2$)', rotation=270, ma='center', va='center')

        # time label
        self.f.text(self.l_ex[0], 0.04, 'Time (ms)')

if __name__ == '__main__':
    x = np.random.rand(100)

    f_test = 'testing.png'

    print mpl.get_backend()

    # testfig for FigDipoleExp()
    # testfig = ac.FigDipoleExp(ax_handles)
    # testfig.create_colorbar_axis('spec')
    # testfig.ax['spec'].plot(x)

    # testfig = FigTest()
    # testfig = FigStDev()
    # testfig = FigL5PingExample()
    # testfig = FigSubDistExample()
    # testfig = FigLaminarComparison()
    # testfig = FigDistalPhase()
    # testfig = FigPeaks()
    testfig = FigSimpleSpec()
    testfig.savepng(f_test)
    testfig.close()
