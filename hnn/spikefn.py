# spikefn.py - dealing with spikes
#
# v 1.10.0-py35
# rev 2016-05-01 (SL: minor)
# last major: (SL: toward python3)
# 2020-12-1 BC: use hnn-core and remove old code

import numpy as np


# histogram bin optimization
def _hist_bin_opt(x, N_trials):
    """ Shimazaki and Shinomoto, Neural Comput, 2007 """

    bin_checks = np.arange(80, 300, 10)
    # bin_checks = np.linspace(150, 300, 16)
    costs = np.zeros(len(bin_checks))
    i = 0
    # this might be vectorizable in np
    for n_bins in bin_checks:
        # use np.histogram to do the numerical minimization
        pdf, bin_edges = np.histogram(x, n_bins)
        # calculate bin width
        # some discrepancy here but should be fine
        w_bin = np.unique(np.diff(bin_edges))
        if len(w_bin) > 1:
            w_bin = w_bin[0]
        # calc mean and var
        kbar = np.mean(pdf)
        kvar = np.var(pdf)
        # calc cost
        costs[i] = (2. * kbar - kvar) / (N_trials * w_bin)**2.
        i += 1
    # find the bin size corresponding to a minimization of the costs
    bin_opt_list = bin_checks[costs.min() == costs]
    bin_opt = bin_opt_list[0]
    return bin_opt


class ExtInputs(object):
    """Class for extracting gids and times from external inputs"""

    def __init__(self, spikes, gid_ranges, trials, params):
        self.p_dict = params
        self.gid_ranges = gid_ranges

        if 'common' in self.gid_ranges:
            # hnn-core
            extinput_key = 'common'
        elif 'extinput' in self.gid_ranges:
            # hnn legacy
            extinput_key = 'extinput'
        else:
            print(self.gid_ranges)
            raise ValueError("Unable to find key for external inputs")

        # parse evoked prox and dist input gids from gid_ranges
        self.gid_evprox, self.gid_evdist = self._get_evokedinput_gids()

        # parse ongoing prox and dist input gids from gid_ranges
        self.gid_prox, self.gid_dist = self._get_extinput_gids(extinput_key)

        # poisson input gids
        self.gid_pois = self._get_poisinput_gids()

        # self.inputs is dict of input times with keys 'prox' and 'dist'
        self.inputs = self._get_extinput_times(spikes, trials)

        self._add_delay_times()

    def _get_extinput_gids(self, extinput_key):
        """Determine if both feeds exist in this sim

        If they do, self.gid_ranges[extinput_key] has length 2
        If so, first gid is guaraneteed to be prox feed, second to be dist
        feed
        """

        if len(self.gid_ranges[extinput_key]) == 2:
            return self.gid_ranges[extinput_key]
        elif len(self.gid_ranges[extinput_key]) > 0:
            # Otherwise, only one feed exists in this sim
            # Must use param file to figure out which one...
            if self.p_dict['t0_input_prox'] < self.p_dict['tstop']:
                return self.gid_ranges[extinput_key][0], None
            elif self.p_dict['t0_input_dist'] < self.p_dict['tstop']:
                return None, self.gid_ranges[extinput_key][0]
        else:
            return None, None

    def _get_poisinput_gids(self):
        """get Poisson input gids"""

        gids = []
        if len(self.gid_ranges['extpois']) > 0:
            if self.p_dict['t0_pois'] < self.p_dict['tstop']:
                gids = np.array(self.gid_ranges['extpois'])
                self.pois_gid_range = (min(gids), max(gids))
        return gids

    def countevinputs(self, ty):
        # count number of evoked inputs
        num_inputs = 0
        for key in self.gid_ranges.keys():
            if key.startswith(ty) and len(self.gid_ranges[key]) > 0:
                num_inputs += 1
        return num_inputs

    def countevprox(self):
        return self.countevinputs('evprox')

    def countevdist(self):
        return self.countevinputs('evdist')

    def _get_evokedinput_gids(self):
        gid_prox, gid_dist = None, None
        nprox, ndist = self.countevprox(), self.countevdist()

        if nprox > 0:
            gid_prox = []
            for i in range(nprox):
                if len(self.gid_ranges['evprox' + str(i + 1)]) > 0:
                    gid_prox += list(self.gid_ranges['evprox' + str(i + 1)])
            gid_prox = np.array(gid_prox)
            self.evprox_gid_range = (min(gid_prox), max(gid_prox))
        if ndist > 0:
            gid_dist = []
            for i in range(ndist):
                if len(self.gid_ranges['evdist' + str(i + 1)]) > 0:
                    gid_dist += list(self.gid_ranges['evdist' + str(i + 1)])
            gid_dist = np.array(gid_dist)
            self.evdist_gid_range = (min(gid_dist), max(gid_dist))

        return gid_prox, gid_dist

    def _filter(self, spikes, trials, filter_range):
        """returns spike_list, a list of lists of spikes.

        Each list corresponds to a cell, counted by range
        """

        filtered_spike_times = []
        for trial_idx in trials:
            indices = np.where(np.in1d(spikes.spike_gids[trial_idx],
                                       filter_range))[0]
            matches = np.array(spikes.spike_times[trial_idx])[indices]
            filtered_spike_times += list(matches)

        return np.array(filtered_spike_times)

    def _get_times(self, spikes, trials, filter_range):
        return self._filter(spikes, trials, filter_range)

    def _unique_times(self, spikes, trials, filter_range):
        filtered_spike_times = self._get_times(spikes, trials, filter_range)

        return np.unique(filtered_spike_times)

    def _get_extinput_times(self, spikes, trials):
        """load all spike times from file"""

        inputs = {k: np.array([]) for k in ['prox', 'dist', 'evprox', 'evdist',
                                            'pois']}
        if self.gid_prox is not None:
            inputs['prox'] = self._get_times(spikes, trials, [self.gid_prox])
        if self.gid_dist is not None:
            inputs['dist'] = self._get_times(spikes, trials, [self.gid_dist])
        if self.gid_evprox is not None:
            inputs['evprox'] = self._unique_times(spikes, trials,
                                                  self.gid_evprox)
        if self.gid_evdist is not None:
            inputs['evdist'] = self._unique_times(spikes, trials,
                                                  self.gid_evdist)
        if self.gid_pois is not None:
            inputs['pois'] = self._unique_times(spikes, trials, self.gid_pois)

        return inputs

    def is_prox_gid(self, gid):
        """check if gid is associated with a proximal input"""

        if gid == self.gid_prox:
            return True
        if len(self.inputs['evprox']) > 0:
            return self.evprox_gid_range[0] <= gid <= self.evprox_gid_range[1]

        return False

    def is_dist_gid(self, gid):
        """check if gid is associated with a distal input"""

        if gid == self.gid_dist:
            return True
        if len(self.inputs['evdist']) > 0:
            return self.evdist_gid_range[0] <= gid <= self.evdist_gid_range[1]

        return False

    def is_pois_gid(self, gid):
        """check if gid is associated with a Poisson input"""
        if len(self.inputs['pois']) > 0:
            return self.pois_gid_range[0] <= gid <= self.pois_gid_range[1]

        return False

    def _add_delay_times(self):
        # if same prox delay to both layers, add it to the prox input times
        if self.p_dict['input_prox_A_delay_L2'] == \
                self.p_dict['input_prox_A_delay_L5']:
            self.inputs['prox'] += self.p_dict['input_prox_A_delay_L2']

        # if same dist delay to both layers, add it to the dist input times
        if self.p_dict['input_dist_A_delay_L2'] == \
                self.p_dict['input_dist_A_delay_L5']:
            self.inputs['dist'] += self.p_dict['input_dist_A_delay_L2']

    def plot_hist(self, ax, extinput, tvec, bins='auto', xlim=None,
                  color='green', hty='bar', lw=4):
        # extinput is either 'dist' or 'prox'

        if bins == 'auto':
            bins = _hist_bin_opt(self.inputs[extinput], 1)
        if not xlim:
            xlim = (0., self.p_dict['tstop'])
        if len(self.inputs[extinput]):
            hist = ax.hist(self.inputs[extinput], bins, range=xlim,
                           color=color, label=extinput, histtype=hty,
                           linewidth=lw)
            ax.set_xticklabels([])
            ax.tick_params(bottom=False, left=False)
        else:
            hist = None

        return hist
