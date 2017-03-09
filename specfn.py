# specfn.py - Average time-frequency energy representation using Morlet wavelet method
#
# v 1.10.2-py35
# rev 2017-02-21 (SL: fixed an issue with indexing)
# last major: (SL: more comments on the units of Morlet Spec)

import os
import sys
import numpy as np
import scipy.signal as sps
import matplotlib.pyplot as plt
import paramrw
import fileio as fio
import multiprocessing as mp
from neuron import h as nrn

import fileio as fio
import currentfn
import dipolefn
import spikefn
import axes_create as ac

# MorletSpec class based on a time vec tvec and a time series vec tsvec
class MorletSpec():
    def __init__(self, tvec, tsvec, fparam, f_max=None):
        # Save variable portion of fdata_spec as identifying attribute
        # self.name = fdata_spec

        # Import dipole data and remove extra dimensions from signal array.
        self.tvec = tvec
        self.tsvec = tsvec

        # function is called this way because paramrw.read() returns 2 outputs
        self.p_dict = paramrw.read(fparam)[1]

        # maximum frequency of analysis
        # Add 1 to ensure analysis is inclusive of maximum frequency
        if not f_max:
            self.f_max = self.p_dict['f_max_spec'] + 1
        else:
            self.f_max = f_max + 1

        # cutoff time in ms
        self.tmin = 50.

        # truncate these vectors appropriately based on tmin
        if self.p_dict['tstop'] > self.tmin:
            # must be done in this order! timeseries first!
            self.tsvec = self.tsvec[self.tvec >= self.tmin]
            self.tvec = self.tvec[self.tvec >= self.tmin]

        # Check that tstop is greater than tmin
        if self.p_dict['tstop'] > self.tmin:
            # Array of frequencies over which to sort
            self.f = np.arange(1., self.f_max)

            # Number of cycles in wavelet (>5 advisable)
            self.width = 7.

            # Calculate sampling frequency
            self.fs = 1000. / self.p_dict['dt']

            # Generate Spec data
            self.TFR = self.__traces2TFR()

            # Add time vector as first row of TFR data
            # self.TFR = np.vstack([self.timevec, self.TFR])

        else:
            print("tstop not greater than %4.2f ms. Skipping wavelet analysis." % self.tmin)

    # externally callable save function
    def save(self, fdata_spec):
        write(fdata_spec, self.timevec, self.freqvec, self.TFR)

    # plots spec to axis
    def plot_to_ax(self, ax_spec, dt):
        # pc = ax.imshow(self.TFR, extent=[xmin, xmax, self.freqvec[-1], self.freqvec[0]], aspect='auto', origin='upper')
        pc = ax_spec.imshow(self.TFR, aspect='auto', origin='upper', cmap=plt.get_cmap('jet'))

        return pc

    # get time and freq of max spectral power
    def max(self):
        print("Warning: you are using max() in MorletSpec(). It should be changed from == to np.isclose()")
        max_spec = self.TFR.max()

        t_mask = (self.TFR==max_spec).sum(axis=0)
        t_at_max = self.tvec[t_mask == 1]

        f_mask = (self.TFR==max_spec).sum(axis=1)
        f_at_max = self.f[f_mask == 1]

        return np.array((max_spec, t_at_max, f_at_max))

    # also creates self.timevec
    def __traces2TFR(self):
        self.S_trans = self.tsvec.transpose()
        # self.S_trans = self.S.transpose()

        # range should probably be 0 to len(self.S_trans)
        # shift tvec to reflect change
        # this is in ms
        self.t = 1000. * np.arange(1, len(self.S_trans)+1) / self.fs + self.tmin - self.p_dict['dt']

        # preallocation
        B = np.zeros((len(self.f), len(self.S_trans)))

        if self.S_trans.ndim == 1:
            for j in range(0, len(self.f)):
                s = sps.detrend(self.S_trans[:])

                # += is used here because these were zeros and now it's adding the solution
                B[j, :] += self.__energyvec(self.f[j], s)
                # B[j,:] = B[j,:] + self.__energyvec(self.freqvec[j], self.__lnr50(s))

            return B

        # this code doesn't return anything presently ...
        else:
            for i in range(0, self.S_trans.shape[0]):
                for j in range(0, len(self.f)):
                    s = sps.detrend(self.S_trans[i,:])
                    B[j,:] += self.__energyvec(self.f[j], s)
                    # B[j,:] = B[j,:] + self.__energyvec(self.freqvec[j], self.__lnr50(s))

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
        A = 1. / (st * np.sqrt(2.*np.pi))

        # units: 1/s * (exp (s**2 / s**2)) * exp( 1/ s * s)
        y = A * np.exp(-t**2. / (2. * st**2.)) * np.exp(1.j * 2. * np.pi * f * t)

        return y

    # notch filter for UK
    def __lnr50(self, s):
        """
            presently unused
            Line noise reduction (50 Hz) the amplitude and phase of the line notch is estimate.
            A sinusoid with these characterisitics is then subtracted from the signal.
            s: signal
        """
        fNoise = 50.
        tv = np.arange(0,len(s)) / self.fs

        if np.ndim(s) == 1:
            Sc = np.zeros(s.shape)
            Sft = self.__ft(s[:], fNoise)
            Sc[:] = s[:] - abs(Sft) * np.cos(2. * np.pi * fNoise * tv - np.angle(Sft))

            return Sc

        else:
            s = s.transpose()
            Sc = np.zeros(s.shape)

            for k in range(0, len(s)):
                Sft = ft(s[k,:], fNoise)
                Sc[k,:] = s[k,:] - abs(Sft) * np.cos(2. * np.pi * fNoise * tv - np.angle(Sft))

            return Sc.tranpose()

    def __ft(self, s, f):
        tv = np.arange(0,len(s)) / self.fs
        tmp = np.exp(1.j*2. * np.pi * f * tv)
        S = 2 * sum(s * tmp) / len(s)

        return S

    # Return an array containing the energy as function of time for freq f
    def __energyvec(self, f, s):
        """ Final units of y: signal units squared. For instance, a signal of Am would have Am^2
            The energy is calculated using Morlet's wavelets
            f: frequency
            s: signal
        """
        dt = 1. / self.fs
        sf = f / self.width
        st = 1. / (2. * np.pi * sf)

        t = np.arange(-3.5*st, 3.5*st, dt)

        # calculate the morlet wavelet for this frequency
        # units of m are 1/s
        m = self.__morlet(f, t)

        # convolve wavelet with signal
        y = sps.fftconvolve(s, m)

        # take the power ...
        y = (2. * abs(y) / self.fs)**2.
        i_lower = int(np.ceil(len(m) / 2.))
        i_upper = int(len(y) - np.floor(len(m) / 2.)+1)
        y = y[i_lower:i_upper]

        return y

# calculates a phase locking value between 2 time series via morlet wavelets
class PhaseLock():
    """ Based on 4Dtools (deprecated) MATLAB code
        Might be a newer version in fieldtrip
    """
    def __init__(self, tsarray1, tsarray2, fparam, f_max=60.):
        # Save time-series arrays as self variables
        # ohhhh. Do not use 1-indexed keys of a dict!
        self.ts = {
            1: tsarray1,
            2: tsarray2,
        }

        # Get param dict
        self.p = paramrw.read(fparam)[1]

        # Set frequecies over which to sort
        self.f = 1. + np.arange(0., f_max, 1.)

        # Set width of Morlet wavelet (>= 5 suggested)
        self.width = 7.

        # Calculate sampling frequency
        self.fs = 1000. / self.p['dt']

        self.data = self.__traces2PLS()

    def __traces2PLS(self):
        # Not sure what's going on here...
        # nshuffle = 200;
        nshuffle = 1;

        # Construct timevec
        tvec = np.arange(1, self.ts[1].shape[1]) / self.fs

        # Prellocated arrays
        # Check sizes
        B = np.zeros((self.f.size, self.ts[1].shape[1]))
        Bstat = np.zeros((self.f.size, self.ts[1].shape[1]))
        Bplf = np.zeros((self.f.size, self.ts[1].shape[1]))

        # Do the analysis
        for i, freq in enumerate(self.f):
            print('%i Hz' % freq)

            # Get phase of signals for given freq
            # Check sizes
            B1 = self.__phasevec(freq, num_ts=1)
            B2 = self.__phasevec(freq, num_ts=2)

            # Potential conflict here
            # Check size
            B[i, :] = np.mean(B1 / B2, axis=0)
            B[i, :] = abs(B[i, :])

            # Randomly shuffle B2
            for j in range(0, nshuffle):
                # Check size
                idxShuffle = np.random.permutation(B2.shape[0])
                B2shuffle = B2[idxShuffle, :]

                Bshuffle = np.mean(B1 / B2shuffle, axis=0)
                Bplf[i, :] += Bshuffle

                idxSign = (abs(B[i, :]) > abs(Bshuffle))
                Bstat[i, idxSign] += 1

        # Final calculation of Bstat, Bplf
        Bstat = 1. - Bstat / nshuffle
        Bplf /= nshuffle

        # Store data
        return {
            't': tvec,
            'f': self.f,
            'B': B,
            'Bstat': Bstat,
            'Bplf': Bplf,
        }

    def __phasevec(self, f, num_ts=1):
        """ should num_ts here be 0, as an index?
        """
        dt = 1. / self.fs
        sf = f / self.width
        st = 1. / (2. * np.pi * sf)

        # create a time vector for the morlet wavelet
        t = np.arange(-3.5*st, 3.5*st+dt, dt)
        m = self.__morlet(f, t)

        y = np.array([])

        for k in range(0, self.ts[num_ts].shape[0]):
            if k == 0:
                s = sps.detrend(self.ts[num_ts][k, :])
                y = np.array([sps.fftconvolve(s, m)])

            else:
                # convolve kth time series with morlet wavelet
                # might as well let return valid length (not implemented)
                y_tmp = sps.fftconvolve(self.ts[num_ts][k, :], m)
                y = np.vstack((y, y_tmp))

        # Change 0s to 1s to avoid division by 0
        # l is an index
        # y is now complex, so abs(y) is the complex absolute value
        l = (abs(y) == 0)
        y[l] = 1.

        # normalize phase values and return 1s to zeros
        y = y / abs(y)
        y[l] = 0
        y = y[:, np.ceil(len(m)/2.)-1:y.shape[1]-np.floor(len(m)/2.)]

        return y

    def __morlet(self, f, t):
        """ Calculate the morlet wavelet
        """
        sf = f / self.width
        st = 1. / (2. * np.pi * sf)
        A = 1. / np.sqrt(st*np.sqrt(np.pi))

        y = A * np.exp(-t**2./(2.*st**2.)) * np.exp(1.j*2.*np.pi*f*t)

        return y

# functions on the aggregate spec data
class Spec():
    def __init__(self, fspec, dtype='dpl'):
        # save dtype
        self.dtype = dtype

        # save details of file
        # may be better ways of doing this...
        self.fspec = fspec
        print('Spec: fspec:',fspec)
        try:
          self.expmt = fspec.split('/')[6].split('.')[0]
        except:
          self.expmt = ''
        self.fname = 'spec.npz' # fspec.split('/')[-1].split('-spec')[0]

        # parse data
        self.__parse_f(fspec)

    # parses the specific data file
    def __parse_f(self, fspec):
        data_spec = np.load(fspec)

        if self.dtype == 'dpl':
            self.spec = {}

            # Try to load aggregate spec data
            try:
                self.spec['agg'] = {
                    't': data_spec['t_agg'],
                    'f': data_spec['f_agg'],
                    'TFR': data_spec['TFR_agg'],
                }

            except KeyError:
                # Try loading aggregate spec data using old keys
                try:
                    self.spec['agg'] = {
                        't': data_spec['time'],
                        'f': data_spec['freq'],
                        'TFR': data_spec['TFR'],
                    }
                except KeyError:
                    print("No aggregate spec data found. Don't use fns that require it...")

            # Try loading Layer specific data
            try:
                self.spec['L2'] = {
                    't': data_spec['t_L2'],
                    'f': data_spec['f_L2'],
                    'TFR': data_spec['TFR_L2'],
                }

                self.spec['L5'] = {
                    't': data_spec['t_L5'],
                    'f': data_spec['f_L5'],
                    'TFR': data_spec['TFR_L5'],
                }

            except KeyError:
                print("All or some layer data is missing. Don't use fns that require it...")

            # Try loading periodigram data
            try:
                self.spec['pgram'] = {
                    'p': data_spec['p_pgram'],
                    'f': data_spec['f_pgram'],
                }

            except KeyError:
                try:
                    self.spec['pgram'] = {
                        'p': data_spec['pgram_p'],
                        'f': data_spec['pgram_f'],
                    }
                except KeyError:
                    print("No periodigram data found. Don't use fns that require it...")

            # Try loading aggregate max spectral data
            try:
                self.spec['max_agg'] = {
                    'p': data_spec['max_agg'][0],
                    't': data_spec['max_agg'][1],
                    'f': data_spec['max_agg'][2],
                }

            except KeyError:
                print("No aggregate max spectral data found. Don't use fns that require it...")

        elif self.dtype == 'current':
            self.spec = {
                'L2': {
                    't': data_spec['t_L2'],
                    'f': data_spec['f_L2'],
                    'TFR': data_spec['TFR_L2'],
                },

                'L5': {
                    't': data_spec['t_L5'],
                    'f': data_spec['f_L5'],
                    'TFR': data_spec['TFR_L5'],
                }
            }

    # Truncate t, f, and TFR for a specific layer over specified t and f intervals
    # Be warned: MODIFIES THE CLASS INTERNALLY
    def truncate(self, layer, t_interval, f_interval):
        self.spec[layer] = self.truncate_ext(layer, t_interval, f_interval)

    # Truncate t, f, and TFR for a specific layer over specified t and f intervals
    # Only returns truncated values. DOES NOT MODIFY THE CLASS INTERNALLY
    def truncate_ext(self, layer, t_interval, f_interval):
        # set f_max and f_min
        if f_interval is None:
            f_min = self.spec[layer]['f'][0]
            f_max = self.spec[layer]['f'][-1]

        else:
            f_min, f_max = f_interval

        # create an f_mask for the bounds of f, inclusive
        f_mask = (self.spec[layer]['f']>=f_min) & (self.spec[layer]['f']<=f_max)

        # do the same for t
        if t_interval is None:
            t_min = self.spec[layer]['t'][0]
            t_max = self.spec[layer]['t'][-1]

        else:
            t_min, t_max = t_interval

        t_mask = (self.spec[layer]['t']>=t_min) & (self.spec[layer]['t']<=t_max)

        # use the masks truncate these appropriately
        TFR_fcut = self.spec[layer]['TFR'][f_mask, :]
        TFR_tfcut = TFR_fcut[:, t_mask]

        f_fcut = self.spec[layer]['f'][f_mask]
        t_tcut = self.spec[layer]['t'][t_mask]

        return {
            't': t_tcut,
            'f': f_fcut,
            'TFR': TFR_tfcut,
        }

    # find the max spectral power over specified time and frequency intervals
    def max(self, layer, t_interval=None, f_interval=None, f_sort=None):
        # If f_sort not provided, sort over all frequencies
        if not f_sort:
            f_sort = (self.spec['agg']['f'][0], self.spec['agg']['f'][-1])

        # If f_sort is -1, assume upper abound is highest frequency
        elif f_sort[1] < 0:
            f_sort[1] = self.spec['agg']['f'][-1]

        # Only continue if absolute max of spectral power occurs at f in range of f_sorted
        # Add +1 to f_sort[0] so range is inclusive
        if self.spec['max_agg']['f'] not in np.arange(f_sort[0], f_sort[1]+1):
            print("%s's absolute max spectral pwr does not occur between %i-%i Hz." %(self.fname, f_sort[0], f_sort[1]))

        else:
            print("Warning: you are using max() in Spec(). It should be changed from == to np.isclose()")
            # truncate data based on specified intervals
            dcut = self.truncate_ext(layer, t_interval, f_interval)

            # find the max power over this new range
            pwr_max = dcut['TFR'].max()
            max_mask = (dcut['TFR'] == pwr_max)

            # find the t and f at max
            # these are slightly crude and do not allow for the possibility of multiple maxes (rare?)
            t_at_max = dcut['t'][max_mask.sum(axis=0) == 1][0]
            f_at_max = dcut['f'][max_mask.sum(axis=1) == 1][0]

            # if f_interval provided and lower bound is not zero, set pd_at_max with lower bound:
            # otherwise set it based on f_at_max
            if f_interval and f_interval[0] > 0:
                pd_at_max = 1000./f_interval[0]
            else:
                pd_at_max = 1000./f_at_max

            t_start = t_at_max - pd_at_max
            t_end = t_at_max + pd_at_max

            # output structure
            data_max = {
                'fname': self.fname,
                'pwr': pwr_max,
                't_int': [t_start, t_end],
                't_at_max': t_at_max,
                'f_at_max': f_at_max,
            }

            return data_max

    # Averages spectral power over specified time interval for specified frequencies
    def stationary_avg(self, layer='agg', t_interval=None, f_interval=None):
        print("Warning: you are using stationary_avg() in Spec(). It should be changed from == to np.isclose()")

        # truncate data based on specified intervals
        dcut = self.truncate_ext(layer, t_interval, f_interval)

        # avg TFR pwr over time
        # axis = 1 sums over columns
        pwr_avg = dcut['TFR'].sum(axis=1) / len(dcut['t'])

        # Get max pwr and freq at which max pwr occurs
        pwr_max = pwr_avg.max()
        f_at_max = dcut['f'][pwr_avg == pwr_max]

        return {
            'p_avg': pwr_avg,
            'p_max': pwr_max,
            'f_max': f_at_max,
            'freq': dcut['f'],
            'expmt': self.expmt,
        }

    def plot_TFR(self, ax, layer='agg', xlim=None, ylim=None):
        # truncate data based on specifed xlim and ylim
        # xlim is a time interval
        # ylim is a frequency interval
        dcut = self.truncate_ext(layer, xlim, ylim)

        # Update xlim to have values guaranteed to exist
        xlim_new = (dcut['t'][0], dcut['t'][-1])
        xmin, xmax = xlim_new

        # Update ylim to have values guaranteed to exist
        ylim_new = (dcut['f'][0], dcut['f'][-1])
        ymin, ymax = ylim_new

        # set extent of plot
        # order is ymax, ymin so y-axis is inverted
        extent_xy = [xmin, xmax, ymax, ymin]

        # plot
        im = ax.imshow(dcut['TFR'], extent=extent_xy, aspect='auto', origin='upper', cmap=plt.get_cmap('jet'))

        return im

    def plot_pgram(self, ax, f_max=None):
        # If f_max is not supplied, set it to highest freq of aggregate analysis
        if f_max is None:
            f_max = self.spec['agg']['f'][-1]

        # plot
        ax.plot(self.spec['pgram']['f'], self.spec['pgram']['p'])
        ax.set_xlim((0., f_max))

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
            # raise an exception for real sometime in the future, for now just say something
            print("in specfn.Welch(), your lengths don't match! Something will fail!")

        # in fact, this will fail (see above)
        # self.N_fft = self.__nextpow2(self.N)

        # grab the dt (in ms) and calc sampling frequency
        self.fs = 1000. / self.dt

        # calculate the actual Welch
        self.f, self.P = sps.welch(self.ts_vec, self.fs, window='hanning', nperseg=self.N, noverlap=0, nfft=self.N, return_onesided=True, scaling='spectrum')

    # simple plot to an axis
    def plot_to_ax(self, ax, f_max=80.):
        ax.plot(self.f, self.P)
        ax.set_xlim((0., f_max))

    def scale(self, scalefactor):
        self.P *= scalefactor
        self.units += ' x%3.4e' % scalefactor

    # return the next power of 2 generally for a given L
    def __nextpow2(self, L):
        n = 2
        # j = 1
        while n < L:
            # j += 1
            n *= 2

        return n
        # return n, j

# general spec write function
def write(fdata_spec, t_vec, f_vec, TFR):
    np.savez_compressed(fdata_spec, time=t_vec, freq=f_vec, TFR=TFR)

# general spec read function
def read(fdata_spec, type='dpl'):
    if type == 'dpl':
        data_spec = np.load(fdata_spec)
        return data_spec

    elif type == 'current':
        # split this up into 2 spec types
        data_spec = np.load(fdata_spec)
        spec_L2 = {
            't': data_spec['t_L2'],
            'f': data_spec['f_L2'],
            'TFR': data_spec['TFR_L2'],
        }

        spec_L5 = {
            't': data_spec['t_L5'],
            'f': data_spec['f_L5'],
            'TFR': data_spec['TFR_L5'],
        }

        return spec_L2, spec_L5

# average spec data for a given set of files
def average(fname, fspec_list):
    for fspec in fspec_list:
        print(fspec)
        # load spec data
        spec = Spec(fspec)

        # if this is first file, copy spec data structure wholesale to x
        if fspec is fspec_list[0]:
            x = spec.spec

        # else, iterate through spec data and add to x_agg
        # there might be a more 'pythonic' way of doing this...
        else:
            for subdict in x:
                for key in x[subdict]:
                    x[subdict][key] += spec.spec[subdict][key]

    # poor man's mean
    for subdict in x:
        for key in x[subdict]:
            x[subdict][key] /= len(fspec_list)

    # save data
    # if max_agg is a key in x, assume all keys are present
    # else, assume only aggregate data is present
    # Terrible way to save due to how np.savez_compressed works (i.e. must specify key=value)
    if 'max_agg' in x.keys():
        max_agg = (x['max_agg']['p'], x['max_agg']['t'], x['max_agg']['f'])
        # max_agg = (x['max_agg']['p_at_max'], x['max_agg']['t_at_max'], x['max_agg']['f_at_max'])

        np.savez_compressed(fname, t_agg=x['agg']['t'], f_agg=x['agg']['f'], TFR_agg=x['agg']['TFR'], t_L2=x['L2']['t'], f_L2=x['L2']['f'], TFR_L2=x['L2']['TFR'], t_L5=x['L5']['t'], f_L5=x['L5']['f'], TFR_L5=x['L5']['TFR'], max_agg=max_agg, pgram_p=x['pgram']['p'], pgram_f=x['pgram']['f'])

    else:
        np.savez_compressed(fname, t_agg=x['agg']['t'], f_agg=x['agg']['f'], TFR_agg=x['agg']['TFR'])

# spectral plotting kernel should be simpler and take just a file name and an axis handle
def pspec_ax(ax_spec, fspec, xlim, layer=None):
    """ Spectral plotting kernel for ONE simulation run
        ax_spec is the axis handle. fspec is the file name
    """
    # read is a function in this file to read the fspec
    data_spec = read(fspec)

    if layer in (None, 'agg'):
        TFR = data_spec['TFR']

        if 'f' in data_spec.keys():
            f = data_spec['f']
        else:
            f = data_spec['freq']

    else:
        TFR_layer = 'TFR_%s' % layer
        f_layer = 'f_%s' % layer

        if TFR_layer in data_spec.keys():
            TFR = data_spec[TFR_layer]
            f = data_spec[f_layer]

        else:
            print(data_spec.keys())

    extent_xy = [xlim[0], xlim[1], f[-1], 0.]
    pc = ax_spec.imshow(TFR, extent=extent_xy, aspect='auto', origin='upper', cmap=plt.get_cmap('jet'))
    [vmin, vmax] = pc.get_clim()
    # print(np.min(TFR), np.max(TFR))
    # print(vmin, vmax)
    # ax_spec.colorbar(pc, ax=ax_spec)

    # return (vmin, vmax)
    return pc

# find max spectral power and associated time/freq for individual file
def specmax(fspec, opts):
    print("Warning: you are using specmax(). It should be changed from == to np.isclose()")
    # opts is a dict that includes t_interval and f_interval
    # grab name of file
    fname = fspec.split('/')[-1].split('-spec')[0]

    # load spec data
    data = read(fspec)

    # grab the min and max f
    f_min, f_max = opts['f_interval']

    # set f_max and f_min
    if f_max < 0:
        f_max = data['freq'][-1]

    if f_min < 0:
        f_min = data['freq'][0]

    # create an f_mask for the bounds of f, inclusive
    f_mask = (data['freq']>=f_min) & (data['freq']<=f_max)

    # do the same for t
    t_min, t_max = opts['t_interval']
    if t_max < 0:
        t_max = data['time'][-1]

    if t_min < 0:
        t_min = data['time'][0]

    t_mask = (data['time']>=t_min) & (data['time']<=t_max)

    # use the masks truncate these appropriately
    TFR_fcut = data['TFR'][f_mask, :]
    TFR_tfcut = TFR_fcut[:, t_mask]

    f_fcut = data['freq'][f_mask]
    t_tcut = data['time'][t_mask]

    # find the max power over this new range
    # the max_mask is for the entire TFR
    pwr_max = TFR_tfcut.max()
    max_mask = (TFR_tfcut == pwr_max)

    # find the t and f at max
    # these are slightly crude and do not allow for the possibility of multiple maxes (rare?)
    t_at_max = t_tcut[max_mask.sum(axis=0) == 1]
    f_at_max = f_fcut[max_mask.sum(axis=1) == 1]

    pd_at_max = 1000. / f_at_max
    t_start = t_at_max - pd_at_max
    t_end = t_at_max + pd_at_max

    # output structure
    data_max = {
        'fname': fname,
        'pwr': pwr_max,
        't_int': [t_start, t_end],
        't_at_max': t_at_max,
        'f_at_max': f_at_max,
    }

    return data_max

# return the max spectral power (simple) for a series of files
def spec_max(ddata, expmt_group, layer='agg'):
    # grab the spec list, assumes it exists
    list_spec = ddata.file_match(expmt_group, 'rawspec')

    # really only perform these actions if there are items in the list
    if len(list_spec):
        # simple prealloc
        val_max = np.zeros(len(list_spec))

        # iterate through list_spec
        i = 0
        for fspec in list_spec:
            data_spec = read(fspec)

            # for now only do the TFR for the aggregate data
            val_max[i] = np.max(data_spec['TFR'])
            i += 1

        return spec_max

# common function to generate spec if it appears to be missing
def generate_missing_spec(ddata, f_max=40):
    # just check first expmt_group
    expmt_group = ddata.expmt_groups[0]

    # list of spec data
    l_spec = ddata.file_match(expmt_group, 'rawspec')

    # if this list is empty, assume it is everywhere and run the analysis function
    if not l_spec:
        opts = {
            'type': 'dpl_laminar',
            'f_max': f_max,
            'save_data': 1,
            'runtype': 'parallel',
        }
        analysis_typespecific(ddata, opts)

    else:
        # this is currently incorrect, it should actually return the data that has been referred to
        # as spec_results. such a function to properly get this without analysis (eg. reader to this data)
        # should exist
        spec = []

    # do the one for current, too. Might as well at this point
    l_speccurrent = ddata.file_match(expmt_group, 'rawspeccurrent')

    if not l_speccurrent:
        p_exp = paramrw.ExpParams(ddata.fparam)
        opts = {
            'type': 'current',
            'f_max': 90.,
            'save_data': 1,
            'runtype': 'parallel',
        }
        analysis_typespecific(ddata, opts)
    else:
        spec_current = []

# Kernel for spec analysis of current data
# necessary for parallelization
def spec_current_kernel(fparam, fts, fspec, f_max):
    I_syn = currentfn.SynapticCurrent(fts)

    # Generate spec results
    spec_L2 = MorletSpec(I_syn.t, I_syn.I_soma_L2Pyr, fparam, f_max)
    spec_L5 = MorletSpec(I_syn.t, I_syn.I_soma_L5Pyr, fparam, f_max)

    # Save spec data
    np.savez_compressed(fspec, t_L2=spec_L2.t, f_L2=spec_L2.f, TFR_L2=spec_L2.TFR, t_L5=spec_L5.t, f_L5=spec_L5.f, TFR_L5=spec_L5.TFR)

# Kernel for spec analysis of dipole data
# necessary for parallelization
def spec_dpl_kernel(fparam, fts, fspec, f_max):
    dpl = dipolefn.Dipole(fts)

    # Do the conversion prior to generating these spec
    dpl.convert_fAm_to_nAm()

    # Generate various spec results
    spec_agg = MorletSpec(dpl.t, dpl.dpl['agg'], fparam, f_max)
    spec_L2 = MorletSpec(dpl.t, dpl.dpl['L2'], fparam, f_max)
    spec_L5 = MorletSpec(dpl.t, dpl.dpl['L5'], fparam, f_max)

    # Get max spectral power data
    # for now, only doing this for agg
    max_agg = spec_agg.max()

    # Generate periodogram resutls
    p_dict = paramrw.read(fparam)[1]
    pgram = Welch(dpl.t, dpl.dpl['agg'], p_dict['dt'])

    # Save spec results
    np.savez_compressed(fspec, time=spec_agg.t, freq=spec_agg.f, TFR=spec_agg.TFR, max_agg=max_agg, t_L2=spec_L2.t, f_L2=spec_L2.f, TFR_L2=spec_L2.TFR, t_L5=spec_L5.t, f_L5=spec_L5.f, TFR_L5=spec_L5.TFR, pgram_p=pgram.P, pgram_f=pgram.f)

def analysis_simp (datdir, ddata, opts):
  opts_run = {
    'type': 'dpl_laminar',
    'f_max': 100.,
    'save_data': 0,
    'runtype': 'parallel',
  }
  if opts:
    for key, val in opts.items():
      if key in opts_run.keys():
        opts_run[key] = val
  expmt_group = ddata.expmt_groups[0]
  fparam  = ddata.file_match(expmt_group, 'param')[0]
  print('fparam:',fparam)
  fts = os.path.join(datdir,'dpl.txt')
  fspec = os.path.join(datdir,'rawspec.npz')
  #spec_current_kernel(fparam, fts, fspec, opts_run['f_max'])
  spec_dpl_kernel(fparam, fts, fspec, opts_run['f_max'])

# Does spec analysis for all files in simulation directory
# ddata comes from fileio
def analysis_typespecific(ddata, opts=None):
    # def analysis_typespecific(ddata, p_exp, opts=None):
    # 'opts' input are the options in a dictionary
    # if opts is defined, then make it well formed
    # the valid keys of opts are in list_opts
    opts_run = {
        'type': 'dpl_laminar',
        'f_max': 100.,
        'save_data': 0,
        'runtype': 'parallel',
    }
    # check if opts is supplied
    if opts:
        # assume opts is a dict
        # iterate through provided opts and assign if the key is present
        # otherwise, ignore
        for key, val in opts.items():
            if key in opts_run.keys():
                opts_run[key] = val
    # preallocate lists for use below
    list_param, list_ts, list_spec = [], [], []

    # aggregrate all files from individual expmts into lists
    expmt_group = ddata.expmt_groups[0]
    # get the list of params
    # returns an alpha SORTED list
    # add to list of all param files
    param_tmp = ddata.file_match(expmt_group, 'param')
    print('param_tmp:',param_tmp)
    list_param.extend(param_tmp)
    # get exp prefix for each trial in this expmt group
    list_exp_prefix = [fio.strip_extprefix(fparam) for fparam in param_tmp]
    # get the list of dipoles and create spec output filenames
    if opts_run['type'] in ('dpl', 'dpl_laminar'):
        list_ts.extend(ddata.file_match(expmt_group, 'rawdpl'))
        list_spec.extend([ddata.create_filename(expmt_group, 'rawspec', exp_prefix) for exp_prefix in list_exp_prefix])
    elif opts_run['type'] == 'current':
        list_ts.extend(ddata.file_match(expmt_group, 'rawcurrent'))
        list_spec.extend(ddata.create_filename(expmt_group, 'rawspeccurrent', list_exp_prefix[-1]))
    # create list of spec output names
    # this is sorted because of file_match
    # exp_prefix_list = [fio.strip_extprefix(fparam) for fparam in list_param]

    # perform analysis on all runs from all exmpts at same time
    if opts_run['type'] == 'current':
        # list_spec.extend([ddata.create_filename(expmt_group, 'rawspeccurrent', exp_prefix) for exp_prefix in exp_prefix_list])
        if opts_run['runtype'] == 'parallel':
            pl = mp.Pool()
            for fparam, fts, fspec in zip(list_param, list_ts, list_spec):
                pl.apply_async(spec_current_kernel, (fparam, fts, fspec, opts_run['f_max']))
            pl.close()
            pl.join()
        elif opts_run['runtype'] == 'debug':
            for fparam, fts, fspec in zip(list_param, list_ts, list_spec):
                spec_current_kernel(fparam, fts, fspec, opts_run['f_max'])
    elif opts_run['type'] == 'dpl_laminar':
        # these should be OUTPUT filenames that are being generated
        # list_spec.extend([ddata.create_filename(expmt_group, 'rawspec', exp_prefix) for exp_prefix in exp_prefix_list])
        # also in this case, the original spec results will be overwritten
        # and replaced by laminar specific ones and aggregate ones
        # in this case, list_ts is a list of dipole
        if opts_run['runtype'] == 'parallel':
            pl = mp.Pool()
            for fparam, fts, fspec in zip(list_param, list_ts, list_spec):
                pl.apply_async(spec_dpl_kernel, (fparam, fts, fspec, opts_run['f_max']))
            pl.close()
            pl.join()
        elif opts_run['runtype'] == 'debug':
            # spec_results_L2 and _L5
            for fparam, fts, fspec in zip(list_param, list_ts, list_spec):
                spec_dpl_kernel(fparam, fts, fspec, opts_run['f_max'])
    # else:
    #     print('Type %s not recognized. Try again later.' %(opts_run['type']))

# returns spec results *only* for a given experimental group
def from_expmt(spec_result_list, expmt_group):
    return [spec_result for spec_result in spec_result_list if expmt_group in spec_result.name]

# Averages spec power over time, returning an array of average pwr per frequency
def specpwr_stationary_avg(fspec):
    print("Warning: you are using specpwr_stationary_avg(). It should be changed from == to np.isclose()")

    # Load data from file
    data_spec = np.load(fspec)

    timevec = data_spec['time']
    freqvec = data_spec['freq']
    TFR = data_spec['TFR']

    # get experiment name
    expmt = fspec.split('/')[6].split('.')[0]

    # axis = 1 sums over columns
    pwr_avg = TFR.sum(axis=1) / len(timevec)
    pwr_max = pwr_avg.max()
    f_at_max = freqvec[pwr_avg == pwr_max]

    return {
        'p_avg': pwr_avg,
        'p_max': pwr_max,
        'f_max': f_at_max,
        'freq': freqvec,
        'expmt': expmt,
    }

def specpwr_stationary(t, f, TFR):
    print("Warning: you are using specpwr_stationary(). It should be changed from == to np.isclose()")

    # aggregate sum of power of all calculated frequencies
    p = TFR.sum(axis=1)

    # calculate max power
    p_max = p.max()

    # calculate max f
    f_max = f[p == p_max]

    return {
        'p': p,
        'f': f,
        'p_max': p_max,
        'f_max': f_max,
    }

def calc_stderror(data_list):
    # np.std returns standard deviation
    # axis=0 performs standard deviation over rows
    error_vec = np.std(data_list, axis=0)

    return error_vec

def pfreqpwr_with_hist(file_name, freqpwr_result, f_spk, gid_dict, p_dict, key_types):
    f = ac.FigFreqpwrWithHist()
    f.ax['hist'].hold(True)

    xmin = 50.
    xmax = p_dict['tstop']

    f.ax['freqpwr'].plot(freqpwr_result['freq'], freqpwr_result['avgpwr'])

    # grab alpha feed data. spikes_from_file() from spikefn.py
    s_dict = spikefn.spikes_from_file(gid_dict, f_spk)

    # check for existance of alpha feed keys in s_dict.
    s_dict = spikefn.alpha_feed_verify(s_dict, p_dict)

    # Account for possible delays
    s_dict = spikefn.add_delay_times(s_dict, p_dict)

    # set number of bins (150 bins/1000ms)
    bins = 150. * (xmax - xmin) / 1000.
    hist_data = []

    # Proximal feed
    hist_data.extend(f.ax['hist'].hist(s_dict['alpha_feed_prox'].spike_list, bins, range=[xmin, xmax], color='red', label='Proximal feed')[0])

    # Distal feed
    hist_data.extend(f.ax['hist'].hist(s_dict['alpha_feed_dist'].spike_list, bins, range=[xmin, xmax], color='green', label='Distal feed')[0])

    # set hist axis props
    f.set_hist_props(hist_data)

    # axis labels
    f.ax['freqpwr'].set_xlabel('freq (Hz)')
    f.ax['freqpwr'].set_ylabel('power')
    f.ax['hist'].set_xlabel('time (ms)')
    f.ax['hist'].set_ylabel('# spikes')

    # create title
    title_str = ac.create_title(p_dict, key_types)
    f.f.suptitle(title_str)
    # title_str = [key + ': %2.1f' % p_dict[key] for key in key_types['dynamic_keys']]

    f.savepng(file_name)
    f.close()

def pmaxpwr(file_name, results_list, fparam_list):
    f = ac.FigStd()
    f.ax0.hold(True)

    # instantiate lists for storing x and y data
    x_data = []
    y_data = []

    # plot points
    for result, fparam in zip(results_list, fparam_list):
        p = paramrw.read(fparam)[1]

        x_data.append(p['f_input_prox'])
        y_data.extend(result['freq_at_max'])

        f.ax0.plot(x_data[-1], y_data[-1], 'kx')

    # add trendline
    fit = np.polyfit(x_data, y_data, 1)
    fit_fn = np.poly1d(fit)

    f.ax0.plot(x_data, fit_fn(x_data), 'k-')

    # Axis stuff
    f.ax0.set_xlabel('Proximal/Distal Input Freq (Hz)')
    f.ax0.set_ylabel('Freq at which max avg power occurs (Hz)')

    f.save(file_name)

if __name__ == '__main__':
    x = np.arange(0, 10.1, 0.1)
    s1 = np.array([np.sin(x)])
    s2 = np.array([np.sin(2*x)])
    dt = 0.1

    p = PhaseLock(s1, s2, dt)
