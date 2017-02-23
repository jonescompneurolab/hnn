# ptest.py - plot test function
#
# v 1.7.11a
# rev 2012-08-23 (SL: created)
# last major:

import matplotlib as mpl
mpl.use("Agg")

import matplotlib.pyplot as plt
from neuron import h as nrn
from axes_create import FigStd

def ptest(t_vec, v_e, v_i):
    testfig = FigStd()
    testfig.ax0.hold(True)

    testfig.ax0.plot(t_vec, v_e)
    testfig.ax0.plot(t_vec, v_i)

    plt.savefig('outputspikes.png')
    testfig.close()
