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

# MorletSpec class based on a time vec tvec and a time series vec tsvec
class MorletSpec():
    def __init__(self, tvec, tsvec, f_max=None, p_dict=None, tmin = 50.0, f_min = 1.):
        # Save variable portion of fdata_spec as identifying attribute
        # self.name = fdata_spec

        # Import dipole data and remove extra dimensions from signal array.
        self.tvec = tvec
        self.tsvec = tsvec

        self.f_min = f_min

        self.params = p_dict

        # maximum frequency of analysis
        # Add 1 to ensure analysis is inclusive of maximum frequency
        if not f_max:
            self.f_max = self.params['f_max_spec'] + 1
        else:
            self.f_max = f_max + 1

        # cutoff time in ms
        self.tmin = tmin

        # truncate these vectors appropriately based on tmin
        if self.params['tstop'] > self.tmin:
            # must be done in this order! timeseries first!
            self.tsvec = self.tsvec[self.tvec >= self.tmin]
            self.tvec = self.tvec[self.tvec >= self.tmin]

        # Check that tstop is greater than tmin
        if self.params['tstop'] > self.tmin:
            # Array of frequencies over which to sort
            self.f = np.arange(self.f_min, self.f_max)

            # Number of cycles in wavelet (>5 advisable)
            self.width = 7.

            # Calculate sampling frequency
            self.fs = 1000. / self.params['dt']

            # Generate Spec data
            self.TFR = self.__traces2TFR()

            # Add time vector as first row of TFR data
            # self.TFR = np.vstack([self.timevec, self.TFR])

        else:
            print("tstop not greater than %4.2f ms. Skipping wavelet analysis." % self.tmin)

    # externally callable save function
    def save(self, fdata_spec):
        raise DeprecationWarning
        write(fdata_spec, self.timevec, self.freqvec, self.TFR)

    # plots spec to axis
    def plot_to_ax(self, ax_spec, dt):
        # pc = ax.imshow(self.TFR, extent=[xmin, xmax, self.freqvec[-1], self.freqvec[0]], aspect='auto', origin='upper')
        pc = ax_spec.imshow(self.TFR, aspect='auto', origin='upper', cmap=plt.get_cmap(self.params['spec_cmap']))

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
        self.t = 1000. * np.arange(1, len(self.S_trans)+1) / self.fs + self.tmin - self.params['dt']

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
        raise DeprecationWarning
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

# functions on the aggregate spec data
class Spec():
    def __init__(self, fspec, spec_cmap='jet', dtype='dpl'):
        raise DeprecationWarning

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

        self.spec_cmap = spec_cmap

        # parse data
        self.__parse_f(fspec)

    # parses the specific data file
    def __parse_f(self, fspec):
        data_spec = np.load(fspec, allow_pickle=True)

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
        im = ax.imshow(dcut['TFR'], extent=extent_xy, aspect='auto', origin='upper', cmap=plt.get_cmap(self.spec_cmap))

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

# Kernel for spec analysis of dipole data
# necessary for parallelization
def spec_dpl_kernel(params, dpl, fspec, opts):

    # Do the conversion prior to generating these spec
    # dpl.convert_fAm_to_nAm()

    # Generate various spec results
    spec_agg = MorletSpec(dpl.times, dpl.data['agg'], opts['f_max'], p_dict=params)
    spec_L2 = MorletSpec(dpl.times, dpl.data['L2'], opts['f_max'], p_dict=params)
    spec_L5 = MorletSpec(dpl.times, dpl.data['L5'], opts['f_max'], p_dict=params)

    # Get max spectral power data
    # for now, only doing this for agg
    max_agg = spec_agg.max()

    # Generate periodogram resutls
    pgram = Welch(dpl.times, dpl.data['agg'], params['dt'])

    # Save spec results
    np.savez_compressed(fspec, time=spec_agg.t, freq=spec_agg.f, TFR=spec_agg.TFR, max_agg=max_agg, t_L2=spec_L2.t, f_L2=spec_L2.f, TFR_L2=spec_L2.TFR, t_L5=spec_L5.t, f_L5=spec_L5.f, TFR_L5=spec_L5.TFR, pgram_p=pgram.P, pgram_f=pgram.f)

def analysis_simp (opts, params, fdpl, fspec):
  opts_run = {'type': 'dpl_laminar',
              'f_max': 100.,
              'save_data': 0,
              'runtype': 'parallel',
            }
  if opts:
    for key, val in opts.items():
      if key in opts_run.keys(): opts_run[key] = val
  spec_dpl_kernel(params, fdpl, fspec, opts_run)
