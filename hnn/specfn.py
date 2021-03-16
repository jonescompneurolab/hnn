# specfn.py - Average time-frequency energy representation using Morlet
# wavelet method
#
# v 1.10.2-py35
# rev 2017-02-21 (SL: fixed an issue with indexing)
# last major: (SL: more comments on the units of Morlet Spec)
# 11-29-2020: BC removed code that no longer uses in preparation for
# hnn-core integration

import numpy as np
import scipy.signal as sps
from copy import deepcopy
import matplotlib.pyplot as plt

fontsize = plt.rcParams['font.size'] = 10


# MorletSpec class based on a time vec tvec and a time series vec tsvec
class MorletSpec():
    def __init__(self, tvec, tsvec, f_max, dt, tstop, tmin=50.0,
                 f_min=1.):
        # Save variable portion of fdata_spec as identifying attribute
        # self.name = fdata_spec

        # Import dipole data and remove extra dimensions from signal array.
        self.tvec = tvec
        self.tsvec = tsvec

        self.f_min = f_min
        self.tstop = tstop
        self.dt = dt

        # maximum frequency of analysis
        # Add 1 to ensure analysis is inclusive of maximum frequency
        self.f_max = f_max + 1

        # cutoff time in ms
        self.tmin = tmin

        # truncate these vectors appropriately based on tmin
        if self.tstop > self.tmin:
            # must be done in this order! timeseries first!
            self.tsvec = self.tsvec[self.tvec >= self.tmin]
            self.tvec = self.tvec[self.tvec >= self.tmin]

        # Check that tstop is greater than tmin
        if self.tstop > self.tmin:
            # Array of frequencies over which to sort
            self.f = np.arange(self.f_min, self.f_max)

            # Number of cycles in wavelet (>5 advisable)
            self.width = 7.

            # Calculate sampling frequency
            self.fs = 1000. / self.dt

            # Generate Spec data
            self.TFR = self.__traces2TFR()
        else:
            print("tstop not greater than %4.2f ms. " % self.tmin +
                  "Skipping wavelet analysis.")

    # also creates self.timevec
    def __traces2TFR(self):
        self.S_trans = self.tsvec.transpose()
        # self.S_trans = self.S.transpose()

        # range should probably be 0 to len(self.S_trans)
        # shift tvec to reflect change
        # this is in ms
        self.t = 1000. * np.arange(1, len(self.S_trans) + 1) / self.fs + \
            self.tmin - self.dt

        # preallocation
        B = np.zeros((len(self.f), len(self.S_trans)))

        if self.S_trans.ndim == 1:
            for j in range(0, len(self.f)):
                s = sps.detrend(self.S_trans[:])

                # += is used here because these were zeros and now it's adding
                # the solution
                B[j, :] += self.__energyvec(self.f[j], s)

            return B

        # this code doesn't return anything presently ...
        else:
            for i in range(0, self.S_trans.shape[0]):
                for j in range(0, len(self.f)):
                    s = sps.detrend(self.S_trans[i, :])
                    B[j, :] += self.__energyvec(self.f[j], s)

    # calculate the morlet wavelet for central frequency f
    def __morlet(self, f, t):
        """ Morlet's wavelet for frequency f and time t
            Wavelet normalized so total energy is 1
            f: specific frequency
            y: final units are 1/s
        """
        # sf in Hz
        sf = f / self.width

        # st in s
        st = 1. / (2. * np.pi * sf)

        # A in 1 / s
        A = 1. / (st * np.sqrt(2. * np.pi))

        # units: 1/s * (exp (s**2 / s**2)) * exp( 1/ s * s)
        y = A * np.exp(-t**2. / (2. * st**2.)) * np.exp(1.j * 2. * np.pi * f *
                                                        t)

        return y

    # Return an array containing the energy as function of time for freq f
    def __energyvec(self, f, s):
        """ Final units of y: signal units squared.

            For instance, a signal of Am would have Am^2
            The energy is calculated using Morlet's wavelets
            f: frequency
            s: signal
        """
        dt = 1. / self.fs
        sf = f / self.width
        st = 1. / (2. * np.pi * sf)

        t = np.arange(-3.5 * st, 3.5 * st, dt)

        # calculate the morlet wavelet for this frequency
        # units of m are 1/s
        m = self.__morlet(f, t)

        # convolve wavelet with signal
        y = sps.fftconvolve(s, m)

        # take the power ...
        y = (2. * abs(y) / self.fs)**2.
        i_lower = int(np.ceil(len(m) / 2.))
        i_upper = int(len(y) - np.floor(len(m) / 2.) + 1)
        y = y[i_lower:i_upper]

        return y


# core class for frequency analysis assuming stationary time series
class Welch():
    def __init__(self, t_vec, ts_vec, dt):
        # assign data internally
        self.t_vec = t_vec
        self.ts_vec = ts_vec
        self.dt = dt
        self.units = 'tsunits^2'

        # only assign length if same
        if len(self.t_vec) == len(self.ts_vec):
            self.N = len(ts_vec)

        else:
            # raise an exception for real sometime in the future, for now
            # just say something
            print("in specfn.Welch(), your lengths don't match! Something"
                  " will fail!")

        # grab the dt (in ms) and calc sampling frequency
        self.fs = 1000. / self.dt

        # calculate the actual Welch
        self.f, self.P = sps.welch(self.ts_vec, self.fs, window='hanning',
                                   nperseg=self.N, noverlap=0, nfft=self.N,
                                   return_onesided=True, scaling='spectrum')


def spec_dpl_kernel(dpl, f_max, dt, tstop):
    # Do the conversion prior to generating these spec
    # dpl.convert_fAm_to_nAm()

    print("Extracting spectrogram from dipole")
    # Generate various spec results
    spec_agg = MorletSpec(dpl.times, dpl.data['agg'], f_max, dt, tstop)
    spec_L2 = MorletSpec(dpl.times, dpl.data['L2'], f_max, dt, tstop)
    spec_L5 = MorletSpec(dpl.times, dpl.data['L5'], f_max, dt, tstop)

    # Get max spectral power data
    # BC (11/29/2020): no longer calculating this
    max_agg = []

    # Generate periodogram resutls
    pgram = Welch(dpl.times, dpl.data['agg'], dt)

    spec_results = {'time': spec_agg.t, 'freq': spec_agg.f,
                    'TFR': spec_agg.TFR, 'max_agg': max_agg,
                    't_L2': spec_L2.t, 'f_L2': spec_L2.f,
                    'TFR_L2': spec_L2.TFR, 't_L5': spec_L5.t,
                    'f_L5': spec_L5.f, 'TFR_L5': spec_L5.TFR,
                    'pgram_p': pgram.P, 'pgram_f': pgram.f}

    return spec_results


def save_spec_data(fspec, spec):
    # Save spec results
    print("Saving %s" % fspec)
    np.savez_compressed(fspec, time=spec['time'], freq=spec['freq'],
                        TFR=spec['TFR'], max_agg=spec['max_agg'],
                        t_L2=spec['t_L2'], f_L2=spec['f_L2'],
                        TFR_L2=spec['TFR_L2'], t_L5=spec['t_L5'],
                        f_L5=spec['f_L5'], TFR_L5=spec['TFR_L5'],
                        pgram_p=spec['pgram_p'], pgram_f=spec['pgram_f'])


def plot_spec(ax, spec_data, ntrial, spec_cmap, xlim, fontsize=fontsize):
    """Plot spectrogram"""

    # calculate TFR from spec trial data
    # start with data from the first trial, but make deepcopy
    # we will be modifying it in place
    spec_TFR = deepcopy(spec_data[0])
    spec_list = [spec_data[i]['TFR'] for i in range(ntrial)]
    spec_TFR['TFR'] = np.mean(np.array(spec_list), axis=0)

    # Plot TFR data and add colorbar
    plot = ax.imshow(spec_TFR['TFR'],
                     extent=(spec_TFR['time'][0],
                             spec_TFR['time'][-1],
                             spec_TFR['freq'][-1],
                             spec_TFR['freq'][0]),
                     aspect='auto', origin='upper',
                     cmap=plt.get_cmap(spec_cmap))
    ax.set_ylabel('Frequency (Hz)', fontsize=fontsize)
    ax.set_xlabel('Time (ms)', fontsize=fontsize)
    ax.set_xlim(xlim)
    ax.set_ylim(spec_TFR['freq'][-1], spec_TFR['freq'][0])

    return plot


def extract_spec(dpls, f_max_spec):
    """Extract Mortlet spectrograms from dipoles

    Parameters
    ----------
    dpls: list of Dipole objects
        List containing Dipoles of each trial
    f_max_spec: float
        Maximum frequency of analysis

    Returns
    ----------
    specs: list of MortletSpec objects
        List containing spectrograms of each trial

    """

    specs = []
    for dpltrial in dpls:
        dt = dpltrial.times[1] - dpltrial.times[0]
        tstop = dpltrial.times[-1]

        spec_results = spec_dpl_kernel(dpltrial, f_max_spec, dt, tstop)
        specs.append(spec_results)

    return specs
