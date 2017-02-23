#!/usr/bin/env python
# PT_example.py - Plot Template example
#
# v 1.9.4
# rev 2016-02-02 (SL: created)
# last major: ()

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import axes_create as ac

# spec plus dipole
class FigExample(ac.FigBase):
    def __init__(self):
        ac.FigBase.__init__(self)
        self.f = plt.figure(figsize=(8, 6))

        font_prop = {'size': 8}
        mpl.rc('font', **font_prop)

        # the right margin is a hack and NOT guaranteed!
        # it's making space for the stupid colorbar that creates a new grid to replace gs1
        # when called, and it doesn't update the params of gs1
        self.gs = {
            'dpl': gridspec.GridSpec(2, 1, height_ratios=[1, 3], bottom=0.85, top=0.95, left=0.1, right=0.82),
            'spec': gridspec.GridSpec(1, 4, wspace=0.05, hspace=0., bottom=0.30, top=0.80, left=0.1, right=1.),
            'pgram': gridspec.GridSpec(2, 1, height_ratios=[1, 3], bottom=0.05, top=0.25, left=0.1, right=0.82),
        }

        self.ax = {
            'dipole': self.f.add_subplot(self.gs['dpl'][:, :]),
            'spec': self.f.add_subplot(self.gs['spec'][:, :]),
            'pgram': self.f.add_subplot(self.gs['pgram'][:, :]),
        }

if __name__ == '__main__':
    fig = FigExample()
    fig.ax['dipole'].plot(np.random.rand(1000))
    fig.savepng('testing.png')
    fig.close()
