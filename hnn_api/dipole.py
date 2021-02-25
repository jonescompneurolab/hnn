"""Class to handle the dipoles."""

# Authors: Mainak Jas <mainak.jas@telecom-paristech.fr>
#          Sam Neymotin <samnemo@gmail.com>

import warnings
import numpy as np
from numpy import convolve, hamming

from .viz import plot_dipole


def _hammfilt(x, winsz):
    """Convolve with a hamming window."""
    win = hamming(winsz)
    win /= sum(win)
    return convolve(x, win, 'same')


def read_dipole(fname, units='nAm'):
    """Read dipole values from a file and create a Dipole instance.

    Parameters
    ----------
    fname : str
        Full path to the input file (.txt)

    Returns
    -------
    dpl : Dipole
        The instance of Dipole class
    """
    dpl_data = np.loadtxt(fname, dtype=float)
    dpl = Dipole(dpl_data[:, 0], dpl_data[:, 1:4])
    if units == 'nAm':
        dpl.units = units
    return dpl


def average_dipoles(dpls):
    """Compute dipole averages over a list of Dipole objects.

    Parameters
    ----------
    dpls: list of Dipole objects
        Contains list of dipole objects, each with a `data` member containing
        'L2', 'L5' and 'agg' components

    Returns
    -------
    dpl: instance of Dipole
        A new dipole object with each component of `dpl.data` representing the
        average over the same components in the input list
    """
    # need at least one Dipole to get times
    if len(dpls) < 2:
        raise ValueError("Need at least two dipole object to compute an"
                         " average")

    for dpl_idx, dpl in enumerate(dpls):
        if dpl.nave > 1:
            raise ValueError("Dipole at index %d was already an average of %d"
                             " trials. Cannot reaverage" %
                             (dpl_idx, dpl.nave))

    agg_avg = np.mean(np.array([dpl.data['agg'] for dpl in dpls]), axis=0)
    L2_avg = np.mean(np.array([dpl.data['L2'] for dpl in dpls]), axis=0)
    L5_avg = np.mean(np.array([dpl.data['L5'] for dpl in dpls]), axis=0)

    avg_dpl_data = np.c_[agg_avg,
                         L2_avg,
                         L5_avg]

    avg_dpl = Dipole(dpls[0].times, avg_dpl_data)

    # set nave to the number of trials averaged in this dipole
    avg_dpl.nave = len(dpls)

    return avg_dpl


class Dipole(object):
    """Dipole class.

    Parameters
    ----------
    times : array (n_times,)
        The time vector
    data : array (n_times x 3)
        The data. The first column represents 'agg',
        the second 'L2' and the last one 'L5'
    nave : int
        Number of trials that were averaged to produce this Dipole. Defaults
        to 1

    Attributes
    ----------
    times : array
        The time vector
    data : dict of array
        The dipole with keys 'agg', 'L2' and 'L5'
    nave : int
        Number of trials that were averaged to produce this Dipole
    """

    def __init__(self, times, data, nave=1):  # noqa: D102
        self.units = 'fAm'
        self.N = data.shape[0]
        self.times = times
        self.data = {'agg': data[:, 0], 'L2': data[:, 1], 'L5': data[:, 2]}
        self.nave = nave

    def post_proc(self, N_pyr_x, N_pyr_y, winsz, fctr):
        """ Apply baseline, unit conversion, scaling and smoothing

       Parameters
        ----------
        N_pyr_x : int
            Number of Pyramidal cells in x direction
        N_pyr_y : int
            Number of Pyramidal cells in y direction
        winsz : int
            Smoothing window
        fctr : int
            Scaling factor
        """
        self.baseline_renormalize(N_pyr_x, N_pyr_y)
        self.convert_fAm_to_nAm()
        self.scale(fctr)
        self.smooth(winsz)

    def convert_fAm_to_nAm(self):
        """ must be run after baseline_renormalization()
        """
        for key in self.data.keys():
            self.data[key] *= 1e-6
        self.units = 'nAm'

    def scale(self, fctr):
        for key in self.data.keys():
            self.data[key] *= fctr
        return fctr

    def smooth(self, winsz):
        # XXX: add check to make sure self.times is
        # not smaller than winsz
        if winsz <= 1:
            return
        for key in self.data.keys():
            self.data[key] = _hammfilt(self.data[key], winsz)

    def plot(self, ax=None, layer='agg', show=True):
        """Simple layer-specific plot function.

        Parameters
        ----------
        ax : instance of matplotlib figure | None
            The matplotlib axis
        layer : str
            The layer to plot. Can be one of
            'agg', 'L2', and 'L5'
        show : bool
            If True, show the figure

        Returns
        -------
        fig : instance of plt.fig
            The matplotlib figure handle.
        """
        return plot_dipole(dpl=self, ax=ax, layer=layer, show=show)

    def baseline_renormalize(self, N_pyr_x, N_pyr_y):
        """Only baseline renormalize if the units are fAm.

        Parameters
        ----------
        N_pyr_x : int
            Nr of cells (x)
        N_pyr_y : int
            Nr of cells (y)
        """
        if self.units != 'fAm':
            print("Warning, no dipole renormalization done because units"
                  " were in %s" % (self.units))
            return

        # N_pyr cells in grid. This is PER LAYER
        N_pyr = N_pyr_x * N_pyr_y
        # dipole offset calculation: increasing number of pyr
        # cells (L2 and L5, simultaneously)
        # with no inputs resulted in an aggregate dipole over the
        # interval [50., 1000.] ms that
        # eventually plateaus at -48 fAm. The range over this interval
        # is something like 3 fAm
        # so the resultant correction is here, per dipole
        # dpl_offset = N_pyr * 50.207
        dpl_offset = {
            # these values will be subtracted
            'L2': N_pyr * 0.0443,
            'L5': N_pyr * -49.0502
            # 'L5': N_pyr * -48.3642,
            # will be calculated next, this is a placeholder
            # 'agg': None,
        }
        # L2 dipole offset can be roughly baseline shifted over
        # the entire range of t
        self.data['L2'] -= dpl_offset['L2']
        # L5 dipole offset should be different for interval [50., 500.]
        # and then it can be offset
        # slope (m) and intercept (b) params for L5 dipole offset
        # uncorrected for N_cells
        # these values were fit over the range [37., 750.)
        m = 3.4770508e-3
        b = -51.231085
        # these values were fit over the range [750., 5000]
        t1 = 750.
        m1 = 1.01e-4
        b1 = -48.412078
        # piecewise normalization


        self.data['L2'] = self.data['L2'][:len(self.times)]
        self.data['L5'] = self.data['L5'][:len(self.times)]
        
        self.data['L5'][self.times <= 37.] -= dpl_offset['L5']
        self.data['L5'][(self.times > 37.) & (self.times < t1)] -= N_pyr * \
            (m * self.times[(self.times > 37.) & (self.times < t1)] + b)
        self.data['L5'][self.times >= t1] -= N_pyr * \
            (m1 * self.times[self.times >= t1] + b1)
        # recalculate the aggregate dipole based on the baseline
        # normalized ones
        self.data['agg'] = self.data['L2'] + self.data['L5']

    def write(self, fname):
        """Write dipole values to a file.

        Parameters
        ----------
        fname : str
            Full path to the output file (.txt)

        Outputs
        -------
        A tab separatd txt file where rows correspond
            to samples and columns correspond to
            1) time (s),
            2) aggregate current dipole (scaled nAm),
            3) L2/3 current dipole (scaled nAm), and
            4) L5 current dipole (scaled nAm)
        """

        if self.nave > 1:
            warnings.warn("Saving Dipole to file that is an average of %d"
                          " trials" % self.nave)

        X = np.r_[[self.times, self.data['agg'], self.data['L2'],
                   self.data['L5']]].T
        np.savetxt(fname, X, fmt=['%3.3f', '%5.4f', '%5.4f', '%5.4f'],
                   delimiter='\t')
