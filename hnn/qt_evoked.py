"""Class for creating the optimization configuration window"""

# Authors: Sam Neymotin <samnemo@gmail.com>
#          Blake Caldwell <blake_caldwell@brown.edu>

import os
import numpy as np
from math import isclose
from copy import deepcopy

from PyQt5.QtWidgets import QPushButton, QTabWidget, QWidget, QDialog
from PyQt5.QtWidgets import QGridLayout, QLabel, QFrame, QSpacerItem
from PyQt5.QtWidgets import QCheckBox, QSizePolicy, QLineEdit
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QFormLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from .qt_lib import QRangeSlider, MyLineEdit, ClickLabel, setscalegeom
from .qt_lib import lookupresource
from .paramrw import countEvokedInputs

decay_multiplier = 1.6


def _consolidate_chunks(input_dict):
    # MOVE to hnn-core
    # get a list of sorted chunks
    sorted_inputs = sorted(
        input_dict.items(), key=lambda x: x[1]['user_start'])

    consolidated_chunks = []
    for one_input in sorted_inputs:
        if 'opt_start' not in one_input[1]:
            continue

        # extract info from sorted list
        input_dict = {'inputs': [one_input[0]],
                      'chunk_start': one_input[1]['user_start'],
                      'chunk_end': one_input[1]['user_end'],
                      'opt_start': one_input[1]['opt_start'],
                      'opt_end': one_input[1]['opt_end'],
                      'weights': one_input[1]['weights'],
                      }

        if (len(consolidated_chunks) > 0) and \
                (input_dict['chunk_start'] <=
                 consolidated_chunks[-1]['chunk_end']):
            # update previous chunk
            consolidated_chunks[-1]['inputs'].extend(input_dict['inputs'])
            consolidated_chunks[-1]['chunk_end'] = input_dict['chunk_end']
            consolidated_chunks[-1]['opt_end'] = max(
                consolidated_chunks[-1]['opt_end'], input_dict['opt_end'])
            # average the weights
            consolidated_chunks[-1]['weights'] = (
                consolidated_chunks[-1]['weights'] +
                one_input[1]['weights']) / 2
        else:
            # new chunk
            consolidated_chunks.append(input_dict)

    return consolidated_chunks


def _combine_chunks(input_chunks):
    # MOVE to hnn-core
    # Used for creating the opt params of the last step with all inputs

    final_chunk = {'inputs': [],
                   'opt_start': 0.0,
                   'opt_end': 0.0,
                   'chunk_start': 0.0,
                   'chunk_end': 0.0}

    for evinput in input_chunks:
        final_chunk['inputs'].extend(evinput['inputs'])
        if evinput['opt_end'] > final_chunk['opt_end']:
            final_chunk['opt_end'] = evinput['opt_end']
        if evinput['chunk_end'] > final_chunk['chunk_end']:
            final_chunk['chunk_end'] = evinput['chunk_end']

    # wRMSE with weights of 1's is the same as regular RMSE.
    final_chunk['weights'] = np.ones(len(input_chunks[-1]['weights']))
    return final_chunk


def _chunk_evinputs(opt_params, sim_tstop, sim_dt):
    # MOVE to hnn-core
    """
    Take dictionary (opt_params) sorted by input and
    return a sorted list of dictionaries describing
    chunks with inputs consolidated as determined the
    range between 'user_start' and 'user_end'.

    The keys of the chunks in chunk_list dictionary
    returned are:
    'weights'
    'chunk_start'
    'chunk_end'
    'opt_start'
    'opt_end'
    """

    import scipy.stats as stats
    from math import ceil, floor

    num_step = ceil(sim_tstop / sim_dt) + 1
    times = np.linspace(0, sim_tstop, num_step)

    # input_dict will be passed to consolidate_chunks, so it has
    # keys 'user_start' and 'user_end' instead of chunk_start and
    # 'chunk_start' that will be returned in the dicts returned
    # in chunk_list
    input_dict = {}
    cdfs = {}

    for input_name in opt_params.keys():
        if opt_params[input_name]['user_start'] > sim_tstop or \
           opt_params[input_name]['user_end'] < 0:
            # can't optimize over this input
            continue

        # calculate cdf using start time (minival of optimization range)
        cdf = stats.norm.cdf(times, opt_params[input_name]['user_start'],
                             opt_params[input_name]['sigma'])
        cdfs[input_name] = cdf.copy()

    for input_name in opt_params.keys():
        if opt_params[input_name]['user_start'] > sim_tstop or \
           opt_params[input_name]['user_end'] < 0:
            # can't optimize over this input
            continue
        input_dict[input_name] = \
            {'weights': cdfs[input_name].copy(),
             'user_start': opt_params[input_name]['user_start'],
             'user_end': opt_params[input_name]['user_end']}

        for other_input in opt_params:
            if opt_params[other_input]['user_start'] > sim_tstop or \
               opt_params[other_input]['user_end'] < 0:
                # not optimizing over that input
                continue
            if input_name == other_input:
                # don't subtract our own cdf(s)
                continue
            if opt_params[other_input]['mean'] < \
               opt_params[input_name]['mean']:
                # check ordering to only use inputs after us
                continue
            else:
                decay_factor = \
                        (opt_params[input_name]['decay_multiplier'] *
                         (opt_params[other_input]['mean'] -
                          opt_params[input_name]['mean'])) / sim_tstop
                input_dict[input_name]['weights'] -= cdfs[other_input] * \
                    decay_factor

        # weights should not drop below 0
        input_dict[input_name]['weights'] = np.clip(
            input_dict[input_name]['weights'], a_min=0, a_max=None)

        # start and stop optimization where the weights are insignificant
        good_indices = np.where(input_dict[input_name]['weights'] > 0.01)
        if len(good_indices[0]) > 0:
            input_dict[input_name]['opt_start'] = min(
                opt_params[input_name]['user_start'], times[good_indices][0])
            input_dict[input_name]['opt_end'] = max(
                opt_params[input_name]['user_end'], times[good_indices][-1])
        else:
            input_dict[input_name]['opt_start'] = \
                opt_params[other_input]['user_start']
            input_dict[input_name]['opt_end'] = \
                opt_params[other_input]['user_end']

        # convert to multiples of dt
        input_dict[input_name]['opt_start'] = floor(
            input_dict[input_name]['opt_start']/sim_dt)*sim_dt
        input_dict[input_name]['opt_end'] = ceil(
            input_dict[input_name]['opt_end']/sim_dt)*sim_dt

    # combined chunks that have overlapping ranges
    # opt_params is a dict, turn into a list
    chunk_list = _consolidate_chunks(input_dict)

    # add one last chunk to the end
    if len(chunk_list) > 1:
        chunk_list.append(_combine_chunks(chunk_list))

    return chunk_list


def _get_param_inputs(params):
    import re
    input_list = []

    # first pass through all params to get mu and sigma for each
    for k in params.keys():
        input_mu = re.match('^t_ev(prox|dist)_([0-9]+)', k)
        if input_mu:
            id_str = 'ev' + input_mu.group(1) + '_' + input_mu.group(2)
            input_list.append(id_str)

    return input_list


def _trans_input(input_var):
    import re

    input_str = input_var
    input_match = re.match('^ev(prox|dist)_([0-9]+)', input_var)
    if input_match:
        if input_match.group(1) == "prox":
            input_str = 'Proximal ' + input_match.group(2)
        if input_match.group(1) == "dist":
            input_str = 'Distal ' + input_match.group(2)

    return input_str


def _format_range_str(value):
    if value == 0:
        value_str = "0.000"
    elif value < 0.1:
        value_str = ("%6f" % value)
    else:
        value_str = ("%.3f" % value)

    return value_str


def _get_prox_dict(nprox):
    # evprox feed strength

    dprox = {
        't_evprox_' + str(nprox): 0.,
        'sigma_t_evprox_' + str(nprox): 2.5,
        'numspikes_evprox_' + str(nprox): 1,
        'gbar_evprox_' + str(nprox) + '_L2Pyr_ampa': 0.,
        'gbar_evprox_' + str(nprox) + '_L2Pyr_nmda': 0.,
        'gbar_evprox_' + str(nprox) + '_L2Basket_ampa': 0.,
        'gbar_evprox_' + str(nprox) + '_L2Basket_nmda': 0.,
        'gbar_evprox_' + str(nprox) + '_L5Pyr_ampa': 0.,
        'gbar_evprox_' + str(nprox) + '_L5Pyr_nmda': 0.,
        'gbar_evprox_' + str(nprox) + '_L5Basket_ampa': 0.,
        'gbar_evprox_' + str(nprox) + '_L5Basket_nmda': 0.
    }
    return dprox


def _get_dist_dict(ndist):
    # evdist feed strength

    ddist = {
        't_evdist_' + str(ndist): 0.,
        'sigma_t_evdist_' + str(ndist): 6.,
        'numspikes_evdist_' + str(ndist): 1,
        'gbar_evdist_' + str(ndist) + '_L2Pyr_ampa': 0.,
        'gbar_evdist_' + str(ndist) + '_L2Pyr_nmda': 0.,
        'gbar_evdist_' + str(ndist) + '_L2Basket_ampa': 0.,
        'gbar_evdist_' + str(ndist) + '_L2Basket_nmda': 0.,
        'gbar_evdist_' + str(ndist) + '_L5Pyr_ampa': 0.,
        'gbar_evdist_' + str(ndist) + '_L5Pyr_nmda': 0.,
    }
    return ddist


class EvokedInputBaseDialog(QDialog):
    def __init__(self):
        super(EvokedInputBaseDialog, self).__init__()

        self.nprox = self.ndist = 0  # number of proximal,distal inputs
        self.ld = []  # list of dictionaries for proximal/distal inputs
        self.dqline = {}
        # for translating model variable name to more human-readable form
        self.dtransvar = {}
        # TODO: add back tooltips
        # self.addtips()

    def transvar(self, k):
        if k in self.dtransvar:
            return self.dtransvar[k]
        return k

    def addtransvarfromdict(self, d):
        dtmp = {'L2': 'L2/3 ', 'L5': 'L5 '}
        for k in d.keys():
            if k.startswith('gbar'):
                ks = k.split('_')
                stmp = ks[-2]
                self.addtransvar(k, dtmp[stmp[0:2]] + stmp[2:] + ' ' +
                                 ks[-1].upper() + u' weight (µS)')
            elif k.startswith('t'):
                self.addtransvar(k, 'Start time mean (ms)')
            elif k.startswith('sigma'):
                self.addtransvar(k, 'Start time stdev (ms)')
            elif k.startswith('numspikes'):
                self.addtransvar(k, 'Number spikes')

    def addtransvar(self, k, strans):
        self.dtransvar[k] = strans
        self.dtransvar[strans] = k

    def IsProx(self, idx):
        d = self.ld[idx]
        for k in d.keys():
            if k.count('evprox'):
                return True

        return False

    def getInputID(self, idx):
        """get evoked input number associated with idx"""
        d = self.ld[idx]
        for k in d.keys():
            lk = k.split('_')
            if len(lk) >= 3:
                return int(lk[2])

    def downShift(self, idx):
        """downshift the evoked input ID, keys, values"""
        d = self.ld[idx]
        dnew = {}  # new dictionary
        newidx = 0  # new evoked input ID
        for k, v in d.items():
            lk = k.split('_')
            if len(lk) >= 3:
                if lk[0] == 'sigma':
                    newidx = int(lk[3]) - 1
                    lk[3] = str(newidx)
                else:
                    newidx = int(lk[2]) - 1
                    lk[2] = str(newidx)
            newkey = '_'.join(lk)
            dnew[newkey] = v
            if k in self.dqline:
                self.dqline[newkey] = self.dqline[k]
                del self.dqline[k]
        self.ld[idx] = dnew
        currtxt = self.tabs.tabText(idx)
        newtxt = currtxt.split(' ')[0] + ' ' + str(newidx)
        self.tabs.setTabText(idx, newtxt)

    def removeInput(self, idx):
        # remove the evoked input specified by idx
        if idx < 0 or idx > len(self.ltabs):
            return
        self.tabs.removeTab(idx)
        tab = self.ltabs[idx]
        self.ltabs.remove(tab)
        d = self.ld[idx]

        isprox = self.IsProx(idx)  # is it a proximal input?
        isdist = not isprox  # is it a distal input?

        # what's the proximal/distal input number?
        inputID = self.getInputID(idx)

        for k in d.keys():
            if k in self.dqline:
                del self.dqline[k]
        self.ld.remove(d)
        tab.setParent(None)

        # now downshift the evoked inputs (only proximal or only distal) that
        # came after this one.
        # first get the IDs of the evoked inputs to downshift
        lds = []  # list of inputs to downshift
        for jdx in range(len(self.ltabs)):
            if isprox and self.IsProx(jdx) and self.getInputID(jdx) > inputID:
                lds.append(jdx)
            elif isdist and not self.IsProx(jdx):
                if self.getInputID(jdx) > inputID:
                    lds.append(jdx)
        for jdx in lds:
            self.downShift(jdx)  # then do the downshifting

    def removeCurrentInput(self):
        """ removes currently selected input"""
        idx = self.tabs.currentIndex()
        if idx < 0:
            return
        self.removeInput(idx)

    def removeAllInputs(self):
        for _ in range(len(self.ltabs)):
            self.removeCurrentInput()
        self.nprox = self.ndist = 0


class EvokedInputParamDialog (EvokedInputBaseDialog):
    """ Evoked Input Dialog
    allows adding/removing arbitrary number of evoked inputs"""

    def __init__(self, parent, din):
        super(EvokedInputParamDialog, self).__init__()
        self.initUI()
        self.setfromdin(din)

    def transvar(self, k):
        if k in self.dtransvar:
            return self.dtransvar[k]
        return k

    def set_qline_float(self, key_str, value):
        try:
            new_value = float(value)
        except ValueError:
            print("WARN: bad value for param %s: %s. Unable to convert"
                  " to a floating point number" % (key_str, value))
            return

        # Enforce no sci. not. + limit field len + remove trailing 0's
        self.dqline[key_str].setText(
            ("%7f" % new_value).rstrip('0').rstrip('.'))

    def setfromdin(self, din):
        if not din:
            return

        if 'dt' in din:

            # Optimization feature introduces the case where din just contains
            # optimization relevant parameters. In that case, we don't want to
            # remove all inputs, just modify existing inputs.
            self.removeAllInputs()  # turn off any previously set inputs

            nprox, ndist = countEvokedInputs(din)
            for i in range(nprox+ndist):
                if i % 2 == 0:
                    if self.nprox < nprox:
                        self.addProx()
                    elif self.ndist < ndist:
                        self.addDist()
                else:
                    if self.ndist < ndist:
                        self.addDist()
                    elif self.nprox < nprox:
                        self.addProx()

        for k, v in din.items():
            if k == 'sync_evinput':
                try:
                    new_value = bool(int(v))
                except ValueError:
                    print("WARN: bad value for param %s: %s. Unable to"
                          " convert to a boolean value" % (k, v))
                    continue
                if new_value:
                    self.chksync.setChecked(True)
                else:
                    self.chksync.setChecked(False)
            elif k == 'inc_evinput':
                try:
                    new_value = float(v)
                except ValueError:
                    print("WARN: bad value for param %s: %s. Unable to"
                          " convert to a floating point number" % (k, v))
                    continue
                self.incedit.setText(str(new_value).strip())
            elif k in self.dqline:
                if k.startswith('numspikes'):
                    try:
                        new_value = int(v)
                    except ValueError:
                        print("WARN: bad value for param %s: %s. Unable to"
                              " convert to a integer" % (k, v))
                        continue
                    self.dqline[k].setText(str(new_value))
                else:
                    self.set_qline_float(k, v)
            elif k.count('gbar') > 0 and \
                (k.count('evprox') > 0 or
                 k.count('evdist') > 0):
                # NOTE: will be deprecated in future release
                # for back-compat with old-style specification which didn't
                # have ampa,nmda in evoked gbar
                lks = k.split('_')
                eloc = lks[1]
                enum = lks[2]
                base_key_str = 'gbar_' + eloc + '_' + enum + '_'
                if eloc == 'evprox':
                    for ct in ['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket']:
                        # ORIGINAL MODEL/PARAM: only ampa for prox evoked
                        # inputs
                        key_str = base_key_str + ct + '_ampa'
                        self.set_qline_float(key_str, v)
                elif eloc == 'evdist':
                    for ct in ['L2Pyr', 'L2Basket', 'L5Pyr']:
                        # ORIGINAL MODEL/PARAM: both ampa and nmda for distal
                        # evoked inputs
                        key_str = base_key_str + ct + '_ampa'
                        self.set_qline_float(key_str, v)
                        key_str = base_key_str + ct + '_nmda'
                        self.set_qline_float(key_str, v)

    def initUI(self):
        self.layout = QVBoxLayout(self)

        # Add stretch to separate the form layout from the button
        self.layout.addStretch(1)

        self.ltabs = []
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.button_box = QVBoxLayout()
        self.btnprox = QPushButton('Add Proximal Input', self)
        self.btnprox.resize(self.btnprox.sizeHint())
        self.btnprox.clicked.connect(self.addProx)
        self.btnprox.setToolTip('Add Proximal Input')
        self.button_box.addWidget(self.btnprox)

        self.btndist = QPushButton('Add Distal Input', self)
        self.btndist.resize(self.btndist.sizeHint())
        self.btndist.clicked.connect(self.addDist)
        self.btndist.setToolTip('Add Distal Input')
        self.button_box.addWidget(self.btndist)

        self.chksync = QCheckBox('Synchronous Inputs', self)
        self.chksync.resize(self.chksync.sizeHint())
        self.chksync.setChecked(True)
        self.button_box.addWidget(self.chksync)

        self.incbox = QHBoxLayout()
        self.inclabel = QLabel(self)
        self.inclabel.setText('Increment start time (ms)')
        self.inclabel.adjustSize()
        self.inclabel.setToolTip(
            'Increment mean evoked input start time(s) by this amount on each'
            ' trial.')
        self.incedit = QLineEdit(self)
        self.incedit.setText('0.0')
        self.incbox.addWidget(self.inclabel)
        self.incbox.addWidget(self.incedit)

        self.layout.addLayout(self.button_box)
        self.layout.addLayout(self.incbox)

        self.tabs.resize(425, 200)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        self.setWindowTitle('Evoked Inputs')

        self.addRemoveInputButton()
        self.addHideButton()
        # self.addtips()

    def lines2val(self, ksearch, val):
        for k in self.dqline.keys():
            if k.count(ksearch) > 0:
                self.dqline[k].setText(str(val))

    def __str__(self):
        s = ''
        for k, v in self.dqline.items():
            s += k + ': ' + v.text().strip() + os.linesep
        if self.chksync.isChecked():
            s += 'sync_evinput: 1' + os.linesep
        else:
            s += 'sync_evinput: 0' + os.linesep
        s += 'inc_evinput: ' + self.incedit.text().strip() + os.linesep
        return s

    def addRemoveInputButton(self):
        self.bbremovebox = QHBoxLayout()
        self.btnremove = QPushButton('Remove Input', self)
        self.btnremove.resize(self.btnremove.sizeHint())
        self.btnremove.clicked.connect(self.removeCurrentInput)
        self.btnremove.setToolTip('Remove This Input')
        self.bbremovebox.addWidget(self.btnremove)
        self.layout.addLayout(self.bbremovebox)

    def addHideButton(self):
        self.bbhidebox = QHBoxLayout()
        self.btnhide = QPushButton('Hide Window', self)
        self.btnhide.resize(self.btnhide.sizeHint())
        self.btnhide.clicked.connect(self.hide)
        self.btnhide.setToolTip('Hide Window')
        self.bbhidebox.addWidget(self.btnhide)
        self.layout.addLayout(self.bbhidebox)

    def addTab(self, s):
        tab = QWidget()
        self.ltabs.append(tab)
        self.tabs.addTab(tab, s)
        tab.layout = QFormLayout()
        tab.setLayout(tab.layout)
        return tab

    def addFormToTab(self, d, tab):
        for k, v in d.items():
            self.dqline[k] = QLineEdit(self)
            self.dqline[k].setText(str(v))
            # adds label,QLineEdit to the tab
            tab.layout.addRow(self.transvar(k), self.dqline[k])

    def makePixLabel(self, fn):
        pix = QPixmap(fn)
        pixlbl = ClickLabel(self)
        pixlbl.setPixmap(pix)
        return pixlbl

    def addProx(self):
        self.nprox += 1  # starts at 1
        dprox = _get_prox_dict(self.nprox)
        self.ld.append(dprox)
        self.addtransvarfromdict(dprox)
        self.addFormToTab(dprox, self.addTab('Proximal ' + str(self.nprox)))
        self.ltabs[-1].layout.addRow(
            self.makePixLabel(lookupresource('proxfig')))
        # print('index to', len(self.ltabs)-1)
        self.tabs.setCurrentIndex(len(self.ltabs)-1)
        # print('index now', self.tabs.currentIndex(), ' of ',
        #       self.tabs.count())
        # self.addtips()

    def addDist(self):
        self.ndist += 1
        ddist = _get_dist_dict(self.ndist)
        self.ld.append(ddist)
        self.addtransvarfromdict(ddist)
        self.addFormToTab(ddist, self.addTab('Distal ' + str(self.ndist)))
        self.ltabs[-1].layout.addRow(
            self.makePixLabel(lookupresource('distfig')))
        # print('index to', len(self.ltabs)-1)
        self.tabs.setCurrentIndex(len(self.ltabs)-1)
        # print('index now', self.tabs.currentIndex(),
        #       ' of ',self.tabs.count())
        # self.addtips()


class OptEvokedInputParamDialog (EvokedInputBaseDialog):
    def __init__(self, parent, mainwin):
        super(OptEvokedInputParamDialog, self).__init__()
        self.nprox = self.ndist = 0  # number of proximal,distal inputs
        self.ld = []  # list of dictionaries for proximal/distal inputs
        self.dqline = {}  # not used, prevents failure in removeInput

        self.dtab_idx = {}  # for translating input names to tab indices
        self.dtab_names = {}  # for translating tab indices to input names
        self.dparams = {}  # actual values

        # these store values used in grid
        self.dqchkbox = {}  # optimize
        self.dqparam_name = {}  # parameter name
        self.dqinitial_label = {}  # initial
        self.dqopt_label = {}  # optimtized
        self.dqdiff_label = {}  # delta
        self.dqrange_multiplier = {}  # user-defined multiplier
        self.dqrange_mode = {}  # range mode (stdev, %, absolute)
        self.dqrange_slider = {}  # slider
        self.dqrange_label = {}  # defined range
        self.dqrange_max = {}
        self.dqrange_min = {}

        self.chunk_list = []
        self.lqnumsim = []
        self.lqnumparams = []
        self.lqinputs = []
        self.opt_params = {}
        self.initial_opt_ranges = []
        self.dtabdata = []
        self.simlength = 0.0
        self.sim_dt = 0.0
        self.default_num_step_sims = 30
        self.default_num_total_sims = 50
        self.mainwin = mainwin
        self.optimization_running = False
        self.initUI()
        self.parent = parent
        self.old_num_steps = 0

    def initUI(self):
        # start with a reasonable size
        setscalegeom(self, 150, 150, 475, 300)

        self.ltabs = []
        self.ltabkeys = []
        self.tabs = QTabWidget()
        self.din = {}

        self.grid = QGridLayout()

        row = 0
        self.sublayout = QGridLayout()
        self.old_numsims = []
        self.grid.addLayout(self.sublayout, row, 0)

        row += 1
        self.grid.addWidget(self.tabs, row, 0)

        row += 1
        self.btnrunop = QPushButton('Run Optimization', self)
        self.btnrunop.resize(self.btnrunop.sizeHint())
        self.btnrunop.setToolTip('Run Optimization')
        self.btnrunop.clicked.connect(self.runOptimization)
        self.grid.addWidget(self.btnrunop, row, 0)

        row += 1
        self.btnreset = QPushButton('Reset Ranges', self)
        self.btnreset.resize(self.btnreset.sizeHint())
        self.btnreset.clicked.connect(self.updateOptRanges)
        self.btnreset.setToolTip('Reset Ranges')
        self.grid.addWidget(self.btnreset, row, 0)

        row += 1
        btnhide = QPushButton('Hide Window', self)
        btnhide.resize(btnhide.sizeHint())
        btnhide.clicked.connect(self.hide)
        btnhide.setToolTip('Hide Window')
        self.grid.addWidget(btnhide, row, 0)

        self.setLayout(self.grid)

        self.setWindowTitle("Configure Optimization")

        # the largest horizontal component will be column 0 (headings)
        self.resize(self.minimumSizeHint())

    def toggle_enable_param(self, label):

        widget_dict_list = [self.dqinitial_label, self.dqopt_label,
                            self.dqdiff_label, self.dqparam_name,
                            self.dqrange_mode, self.dqrange_multiplier,
                            self.dqrange_label, self.dqrange_slider]

        if self.dqchkbox[label].isChecked():
            # set all other fields in the row to enabled
            for widget_dict in widget_dict_list:
                widget_dict[label].setEnabled(True)
            toEnable = True
        else:
            # disable all other fields in the row
            for widget_dict in widget_dict_list:
                widget_dict[label].setEnabled(False)
            toEnable = False

        self.changeParamEnabledStatus(label, toEnable)

    def addTab(self, id_str):
        tab = QWidget()
        self.ltabs.append(tab)

        name_str = _trans_input(id_str)
        self.tabs.addTab(tab, name_str)

        tab_index = len(self.ltabs)-1
        self.dtab_idx[id_str] = tab_index
        self.dtab_names[tab_index] = id_str

        return tab

    def cleanLabels(self):
        """
        To avoid memory leaks we need to delete all widgets when we recreate
        grid. Go through all tabs and check for each var name (k)
        """
        for idx in range(len(self.ltabs)):
            for k in self.ld[idx].keys():
                if k in self.dqinitial_label:
                    del self.dqinitial_label[k]
                if k in self.dqopt_label:
                    del self.dqopt_label[k]
                if k in self.dqdiff_label:
                    del self.dqdiff_label[k]
                if k in self.dqparam_name:
                    del self.dqparam_name[k]
                if not self.optimization_running:
                    if k in self.dqrange_mode:
                        del self.dqrange_mode[k]
                    if k in self.dqrange_multiplier:
                        del self.dqrange_multiplier[k]
                    if k in self.dqrange_label:
                        del self.dqrange_label[k]
                    if k in self.dqrange_slider:
                        del self.dqrange_slider[k]
                    if k in self.dqrange_min:
                        del self.dqrange_min[k]
                    if k in self.dqrange_max:
                        del self.dqrange_max[k]

    def addGridToTab(self, d, tab):
        from functools import partial

        current_tab = len(self.ltabs)-1
        tab.layout = QGridLayout()
        # tab.layout.setSpacing(10)

        self.ltabkeys.append([])

        # The first row has column headings
        row = 0
        self.ltabkeys[current_tab].append("")
        for column_index, column_name in enumerate(["Optimize",
                                                    "Parameter name",
                                                    "Initial", "Optimized",
                                                    "Delta"]):
            widget = QLabel(column_name)
            widget.resize(widget.sizeHint())
            tab.layout.addWidget(widget, row, column_index)

        column_index += 1
        widget = QLabel("Range specifier")
        widget.setMinimumWidth(100)
        tab.layout.addWidget(widget, row, column_index, 1, 2)

        column_index += 2
        widget = QLabel("Range slider")
        # widget.setMinimumWidth(160)
        tab.layout.addWidget(widget, row, column_index)

        column_index += 1
        widget = QLabel("Defined range")
        tab.layout.addWidget(widget, row, column_index)

        # The second row is a horizontal line
        row = 1
        self.ltabkeys[current_tab].append("")
        qthline = QFrame()
        qthline.setFrameShape(QFrame.HLine)
        qthline.setFrameShadow(QFrame.Sunken)
        tab.layout.addWidget(qthline, row, 0, 1, 9)

        # The rest are the parameters
        row = 2
        for k, v in d.items():
            self.ltabkeys[current_tab].append(k)

            # create and format widgets
            self.dparams[k] = float(v)
            self.dqchkbox[k] = QCheckBox()
            self.dqchkbox[k].setStyleSheet("""
      .QCheckBox {
            spacing: 20px;
          }
      .QCheckBox::unchecked {
            color: grey;
          }
      .QCheckBox::checked {
            color: black;
          }
      """)
            self.dqchkbox[k].setChecked(True)
            # use partial instead of lamda (so args won't be evaluated ahead
            # of time?)
            self.dqchkbox[k].clicked.connect(
                partial(self.toggle_enable_param, k))
            self.dqparam_name[k] = QLabel(self)
            self.dqparam_name[k].setText(self.transvar(k))
            self.dqinitial_label[k] = QLabel()
            self.dqopt_label[k] = QLabel()
            self.dqdiff_label[k] = QLabel()

            # add widgets to grid
            tab.layout.addWidget(
                self.dqchkbox[k], row, 0,
                alignment=Qt.AlignBaseline | Qt.AlignCenter)
            tab.layout.addWidget(self.dqparam_name[k], row, 1)
            tab.layout.addWidget(
                self.dqinitial_label[k], row, 2)  # initial value
            tab.layout.addWidget(
                self.dqopt_label[k], row, 3)  # optimized value
            tab.layout.addWidget(self.dqdiff_label[k], row, 4)  # delta

            if k.startswith('t'):
                range_mode = "(stdev)"
                range_multiplier = "3.0"
            elif k.startswith('sigma'):
                range_mode = "(%)"
                range_multiplier = "50.0"
            else:
                range_mode = "(%)"
                range_multiplier = "500.0"

            if not self.optimization_running:
                self.dqrange_slider[k] = QRangeSlider(k, self)
                self.dqrange_slider[k].setMinimumWidth(140)
                self.dqrange_label[k] = QLabel()
                self.dqrange_multiplier[k] = MyLineEdit(range_multiplier, k)
                self.dqrange_multiplier[k].textModified.connect(
                    self.updateRange)
                self.dqrange_multiplier[k].setSizePolicy(
                    QSizePolicy.Ignored, QSizePolicy.Preferred)
                self.dqrange_multiplier[k].setMinimumWidth(50)
                self.dqrange_multiplier[k].setMaximumWidth(50)
                self.dqrange_mode[k] = QLabel(range_mode)
                tab.layout.addWidget(
                    self.dqrange_multiplier[k], row, 5)  # range specifier
                tab.layout.addWidget(
                    self.dqrange_mode[k], row, 6)  # range mode
                tab.layout.addWidget(
                    self.dqrange_slider[k], row, 7)  # range slider
                # calculated range
                tab.layout.addWidget(self.dqrange_label[k], row, 8)

            row += 1

        # A spacer in the last row stretches to fill remaining space.
        # For inputs with fewer parameters than the rest, this pushes
        # parameters to the top with the same spacing as the other inputs.
        tab.layout.addItem(QSpacerItem(0, 0), row, 0, 1, 9)
        tab.layout.setRowStretch(row, 1)
        tab.setLayout(tab.layout)

    def addProx(self):
        self.nprox += 1
        dprox = _get_prox_dict(self.nprox)
        self.ld.append(dprox)
        self.addtransvarfromdict(dprox)
        tab = self.addTab('evprox_' + str(self.nprox))
        self.addGridToTab(dprox, tab)

    def addDist(self):
        self.ndist += 1
        ddist = _get_dist_dict(self.ndist)
        self.ld.append(ddist)
        self.addtransvarfromdict(ddist)
        tab = self.addTab('evdist_' + str(self.ndist))
        self.addGridToTab(ddist, tab)

    def changeParamEnabledStatus(self, label, toEnable):
        import re

        label_match = re.search('(evprox|evdist)_([0-9]+)', label)
        if label_match:
            my_input_name = label_match.group(1) + '_' + label_match.group(2)
        else:
            print("ERR: can't determine input name from parameter: %s" %
                  label)
            return

        # decrease the count of num params
        for chunk_index in range(self.old_num_steps):
            for input_name in self.chunk_list[chunk_index]['inputs']:
                if input_name == my_input_name:
                    try:
                        num_params = int(self.lqnumparams[chunk_index].text())
                    except ValueError:
                        print(
                            "ERR: could not get number of params for step %d"
                            % chunk_index)

                    if toEnable:
                        num_params += 1
                    else:
                        num_params -= 1
                    self.lqnumparams[chunk_index].setText(str(num_params))
                    ranges = self.opt_params[input_name]['ranges']
                    ranges[label]['enabled'] = toEnable

    def updateRange(self, label, save_slider=True):
        import re

        max_width = 0

        label_match = re.search('(evprox|evdist)_([0-9]+)', label)
        if label_match:
            tab_name = label_match.group(1) + '_' + label_match.group(2)
        else:
            print("ERR: can't determine input name from parameter: %s" %
                  label)
            return

        if self.dqchkbox[label].isChecked():
            self.opt_params[tab_name]['ranges'][label]['enabled'] = True
        else:
            self.opt_params[tab_name]['ranges'][label]['enabled'] = False

        if tab_name not in self.initial_opt_ranges or \
                label not in self.initial_opt_ranges[tab_name]:
            value = self.dparams[label]
        else:
            value = float(self.initial_opt_ranges[tab_name][label]['initial'])

        range_type = self.dqrange_mode[label].text()
        if range_type == "(%)" and value == 0.0:
            # change to range from 0 to 1
            range_type = "(max)"
            self.dqrange_mode[label].setText(range_type)
            self.dqrange_multiplier[label].setText("1.0")
        elif range_type == "(max)" and value > 0.0:
            # change back to %
            range_type = "(%)"
            self.dqrange_mode[label].setText(range_type)
            self.dqrange_multiplier[label].setText("500.0")

        try:
            range_multiplier = float(self.dqrange_multiplier[label].text())
        except ValueError:
            range_multiplier = 0.0
        self.dqrange_multiplier[label].setText(str(range_multiplier))

        if range_type == "(max)":
            range_min = 0
            try:
                range_max = float(self.dqrange_multiplier[label].text())
            except ValueError:
                range_max = 1.0
        elif range_type == "(stdev)":  # timing
            timing_sigma = self.get_input_timing_sigma(tab_name)
            timing_bound = timing_sigma * range_multiplier
            range_min = max(0, value - timing_bound)
            range_max = min(self.simlength, value + timing_bound)
        else:  # range_type == "(%)"
            range_min = max(0, value - (value * range_multiplier / 100.0))
            range_max = value + (value * range_multiplier / 100.0)

        # set up the slider
        self.dqrange_slider[label].setLine(value)
        self.dqrange_slider[label].setMin(range_min)
        self.dqrange_slider[label].setMax(range_max)

        if not save_slider:
            self.dqrange_min.pop(label, None)
            self.dqrange_max.pop(label, None)

        self.opt_params[tab_name]['ranges'][label]['initial'] = value
        if label in self.dqrange_min and label in self.dqrange_max:
            range_min = self.dqrange_min[label]
            range_max = self.dqrange_max[label]

        self.opt_params[tab_name]['ranges'][label]['minval'] = range_min
        self.opt_params[tab_name]['ranges'][label]['maxval'] = range_max
        self.dqrange_slider[label].setRange(range_min, range_max)

        if range_min == range_max:
            self.dqrange_label[label].setText(
                _format_range_str(range_min))  # use the exact value
            self.dqrange_label[label].setEnabled(False)
            # uncheck because invalid range
            self.dqchkbox[label].setChecked(False)
            # disable slider
            self.dqrange_slider[label].setEnabled(False)
            self.changeParamEnabledStatus(label, False)
        else:
            self.dqrange_label[label].setText(_format_range_str(range_min) +
                                              " - " +
                                              _format_range_str(range_max))

        if self.dqrange_label[label].sizeHint().width() > max_width:
            max_width = self.dqrange_label[label].sizeHint().width() + 15
        # fix the size for the defined range so that changing the slider
        # doesn't change the dialog's width
        self.dqrange_label[label].setMinimumWidth(max_width)
        self.dqrange_label[label].setMaximumWidth(max_width)

    def prepareOptimization(self):
        self.updateOptParams()
        self.rebuildOptStepInfo()
        self.updateOptDeltas()
        self.updateOptRanges(save_sliders=True)
        self.btnreset.setEnabled(True)
        self.btnrunop.setText('Run Optimization')
        self.btnrunop.clicked.disconnect()
        self.btnrunop.clicked.connect(self.runOptimization)

    def runOptimization(self):
        # update the ranges to find which parameters have been disabled
        # (unchecked)
        self.updateOptRanges(save_sliders=True)

        # update the opt info dict to capture num_sims from GUI
        self.rebuildOptStepInfo()
        self.optimization_running = True
        self.populate_initial_opt_ranges()

        # run the actual optimization
        num_steps = self.get_num_chunks()
        self.mainwin.startoptmodel(num_steps)

    def get_chunk_start(self, step):
        return self.chunk_list[step]['opt_start']

    def get_chunk_end(self, step):
        return self.chunk_list[step]['opt_end']

    def get_chunk_weights(self, step):
        return self.chunk_list[step]['weights']

    def get_num_chunks(self):
        return len(self.chunk_list)

    def get_sims_for_chunk(self, step):
        try:
            num_sims = int(self.lqnumsim[step].text())
        except KeyError:
            print("ERR: number of sims not found for step %d" % step)
            num_sims = 0
        except ValueError:
            if step == self.old_num_steps - 1:
                num_sims = self.default_num_total_sims
            else:
                num_sims = self.default_num_step_sims

        return num_sims

    def get_chunk_ranges(self, step):
        ranges = {}
        for input_name in self.chunk_list[step]['inputs']:
            # make sure initial value is between minval or maxval before
            # returning ranges to the optimization
            ranges = self.opt_params[input_name]['ranges']
            for label in ranges.keys():
                if not ranges[label]['enabled']:
                    continue
                range_min = ranges[label]['minval']
                range_max = ranges[label]['maxval']
                if range_min > ranges[label]['initial']:
                    ranges[label]['initial'] = range_min
                if range_max < ranges[label]['initial']:
                    ranges[label]['initial'] = range_max

                # copy the values to the ranges dict to be returned
                # to optimization
                ranges[label] = ranges[label].copy()

        return ranges

    def get_initial_params(self):
        initial_params = {}
        for input_name in self.opt_params.keys():
            for label in self.opt_params[input_name]['ranges'].keys():
                initial_params[label] = \
                    self.opt_params[input_name]['ranges'][label]['initial']

        return initial_params

    def get_num_params(self, step):
        num_params = 0

        for input_name in self.chunk_list[step]['inputs']:
            for label in self.opt_params[input_name]['ranges'].keys():
                if self.opt_params[input_name]['ranges'][label]['enabled']:
                    num_params += 1
                else:
                    continue

        return num_params

    def push_chunk_ranges(self, ranges):
        for label, value in ranges.items():
            for tab_name in self.opt_params.keys():
                if label in self.opt_params[tab_name]['ranges']:
                    self.opt_params[tab_name]['ranges'][label]['initial'] = \
                        float(value)

    def clean_opt_grid(self):
        # This is the top part of the Configure Optimization dialog.

        column_count = self.sublayout.columnCount()
        row = 0
        while True:
            try:
                self.sublayout.itemAtPosition(row, 0).widget()
            except AttributeError:
                # no more rows
                break

            for column in range(column_count):
                try:
                    # Use deleteLater() to avoid memory leaks.
                    self.sublayout.itemAtPosition(
                        row, column).widget().deleteLater()
                except AttributeError:
                    # if item wasn't found
                    pass
            row += 1

        # reset data for number of sims per chunk (step)
        self.lqnumsim = []
        self.lqnumparams = []
        self.lqinputs = []
        self.old_num_steps = 0

    def rebuildOptStepInfo(self):
        # split chunks from paramter file
        self.chunk_list = _chunk_evinputs(
            self.opt_params, self.simlength, self.sim_dt)

        if len(self.chunk_list) == 0:
            self.clean_opt_grid()

            qlabel = QLabel("No valid evoked inputs to optimize!")
            qlabel.setAlignment(Qt.AlignBaseline | Qt.AlignLeft)
            qlabel.resize(qlabel.minimumSizeHint())
            self.sublayout.addWidget(qlabel, 0, 0)
            self.btnrunop.setEnabled(False)
            self.btnreset.setEnabled(False)
        else:
            self.btnrunop.setEnabled(True)
            self.btnreset.setEnabled(True)

            if len(self.chunk_list) < self.old_num_steps or \
                    self.old_num_steps == 0:
                # clean up the old grid sublayout
                self.clean_opt_grid()

        # keep track of inputs to optimize over (check against
        # self.opt_params later)
        all_inputs = []

        # create a new grid sublayout with a row for each optimization step
        for chunk_index, chunk in enumerate(self.chunk_list):
            chunk['num_params'] = self.get_num_params(chunk_index)

            inputs = []
            for input_name in chunk['inputs']:
                all_inputs.append(input_name)
                inputs.append(_trans_input(input_name))

            if chunk_index >= self.old_num_steps:
                qlabel = QLabel("Optimization step %d:" % (chunk_index+1))
                qlabel.setAlignment(Qt.AlignBaseline | Qt.AlignLeft)
                qlabel.resize(qlabel.minimumSizeHint())
                self.sublayout.addWidget(qlabel, chunk_index, 0)

                self.lqinputs.append(QLabel("Inputs: %s" % ', '.join(inputs)))
                self.lqinputs[chunk_index].setAlignment(
                    Qt.AlignBaseline | Qt.AlignLeft)
                self.lqinputs[chunk_index].resize(
                    self.lqinputs[chunk_index].minimumSizeHint())
                self.sublayout.addWidget(
                    self.lqinputs[chunk_index], chunk_index, 1)

                # spacer here for readability of input names and reduce size
                # of "Num simulations:"
                self.sublayout.addItem(QSpacerItem(
                    0, 0, hPolicy=QSizePolicy.MinimumExpanding), chunk_index,
                    2)

                qlabel_params = QLabel("Num params:")
                qlabel_params.setAlignment(Qt.AlignBaseline | Qt.AlignLeft)
                qlabel_params.resize(qlabel_params.minimumSizeHint())
                self.sublayout.addWidget(qlabel_params, chunk_index, 3)

                self.lqnumparams.append(QLabel(str(chunk['num_params'])))
                self.lqnumparams[chunk_index].setAlignment(
                    Qt.AlignBaseline | Qt.AlignLeft)
                self.lqnumparams[chunk_index].resize(
                    self.lqnumparams[chunk_index].minimumSizeHint())
                self.sublayout.addWidget(
                    self.lqnumparams[chunk_index], chunk_index, 4)

                qlabel_sims = QLabel("Num simulations:")
                qlabel_sims.setAlignment(Qt.AlignBaseline | Qt.AlignLeft)
                qlabel_sims.resize(qlabel_sims.minimumSizeHint())
                self.sublayout.addWidget(qlabel_sims, chunk_index, 5)

                if chunk_index == len(self.chunk_list) - 1:
                    chunk['num_sims'] = self.default_num_total_sims
                else:
                    chunk['num_sims'] = self.default_num_step_sims
                self.lqnumsim.append(QLineEdit(str(chunk['num_sims'])))
                self.lqnumsim[chunk_index].resize(
                    self.lqnumsim[chunk_index].minimumSizeHint())
                self.sublayout.addWidget(self.lqnumsim[chunk_index],
                                         chunk_index, 6)
            else:
                self.lqinputs[chunk_index].setText(
                    "Inputs: %s" % ', '.join(inputs))
                self.lqnumparams[chunk_index].setText(
                        str(chunk['num_params']))

        self.old_num_steps = len(self.chunk_list)

        remove_list = []
        # remove a tab if necessary
        for input_name in self.opt_params.keys():
            if input_name not in all_inputs and input_name in self.dtab_idx:
                remove_list.append(input_name)

        while len(remove_list) > 0:
            tab_name = remove_list.pop()
            tab_index = self.dtab_idx[tab_name]

            self.removeInput(tab_index)
            del self.dtab_idx[tab_name]
            del self.dtab_names[tab_index]
            self.ltabkeys.pop(tab_index)

            # rebuild dtab_idx and dtab_names
            temp_dtab_names = {}
            temp_dtab_idx = {}
            for new_tab_index, old_tab_index in enumerate(
                    self.dtab_idx.values()):
                # self.dtab_idx[id_str] = tab_index
                id_str = self.dtab_names[old_tab_index]
                temp_dtab_names[new_tab_index] = id_str
                temp_dtab_idx[id_str] = new_tab_index
            self.dtab_names = temp_dtab_names
            self.dtab_idx = temp_dtab_idx

    def toggle_enable_user_fields(self, step, enable=True):
        for input_name in self.chunk_list[step]['inputs']:
            tab_index = self.dtab_idx[input_name]
            tab = self.ltabs[tab_index]

            # last row is a spacer
            for row_index in range(2, tab.layout.rowCount() - 1):
                label = self.ltabkeys[tab_index][row_index]
                self.dqchkbox[label].setEnabled(enable)
                self.dqrange_slider[label].setEnabled(enable)
                self.dqrange_multiplier[label].setEnabled(enable)

    def get_input_timing_sigma(self, tab_name):
        """ get timing_sigma from already loaded values """

        label = 'sigma_t_' + tab_name
        try:
            timing_sigma = self.dparams[label]
        except KeyError:
            timing_sigma = 3.0
            print("ERR: Couldn't fing %s. Using default %f" %
                  (label, timing_sigma))

        if timing_sigma == 0.0:
            # sigma of 0 will not produce a CDF
            timing_sigma = 0.01

        return timing_sigma

    def updateOptParams(self):
        global decay_multiplier

        # iterate through tabs. data is contained in grid layout
        for tab_index, tab in enumerate(self.ltabs):
            tab_name = self.dtab_names[tab_index]

            # before optimization has started update 'mean', 'sigma',
            # 'start', and 'user_end'
            start_time_label = 't_' + tab_name
            try:
                try:
                    range_multiplier = float(
                        self.dqrange_multiplier[start_time_label].text())
                except ValueError:
                    range_multiplier = 0.0
                value = self.dparams[start_time_label]
            except KeyError:
                print("ERR: could not find start time parameter: %s" %
                      start_time_label)
                continue

            timing_sigma = self.get_input_timing_sigma(tab_name)
            if tab_name not in self.opt_params:
                self.opt_params[tab_name] = {'ranges': {}}
            self.opt_params[tab_name]['mean'] = value
            self.opt_params[tab_name]['sigma'] = timing_sigma
            self.opt_params[tab_name]['decay_multiplier'] = decay_multiplier

            timing_bound = timing_sigma * range_multiplier
            self.opt_params[tab_name]['user_start'] = max(
                0, value - timing_bound)
            self.opt_params[tab_name]['user_end'] = min(
                self.simlength, value + timing_bound)

            # last row is a spacer
            for row_index in range(2, tab.layout.rowCount() - 1):
                label = self.ltabkeys[tab_index][row_index]
                if label not in self.opt_params[tab_name]['ranges']:
                    # add an empty dictionary so that rebuildOptStepInfo() can
                    # determine how many parameters
                    self.opt_params[tab_name]['ranges'][label] = {}

                if 'enabled' not in \
                        self.opt_params[tab_name]['ranges'][label]:
                    # set the enable status for the first time
                    enabled = True
                    if label.startswith('numspikes'):
                        enabled = False
                    self.opt_params[tab_name]['ranges'][label]['enabled'] = \
                        enabled
                    self.dqchkbox[label].setChecked(enabled)

    def clear_initial_opt_ranges(self):
        self.initial_opt_ranges = {}

    def populate_initial_opt_ranges(self):
        self.initial_opt_ranges = {}

        for input_name in self.opt_params.keys():
            self.initial_opt_ranges[input_name] = deepcopy(
                self.opt_params[input_name]['ranges'])

    def updateOptDeltas(self):
        # iterate through tabs. data is contained in grid layout
        for tab_index, tab in enumerate(self.ltabs):
            tab_name = self.dtab_names[tab_index]

            # update the initial value (last row is a spacer)
            for row_index in range(2, tab.layout.rowCount()-1):
                label = self.ltabkeys[tab_index][row_index]
                value = self.dparams[label]

                # Calculate value to put in "Delta" column. When possible, use
                # percentages, but when initial value is 0, use absolute
                # changes
                if tab_name not in self.initial_opt_ranges or \
                   not self.dqchkbox[label].isChecked():
                    self.dqdiff_label[label].setEnabled(False)
                    self.dqinitial_label[label].setText(
                        ("%6f" % self.dparams[label]).rstrip('0').rstrip('.'))
                    text = '--'
                    color_fmt = "QLabel { color : black; }"
                    self.dqopt_label[label].setText(text)
                    self.dqopt_label[label].setStyleSheet(color_fmt)
                    self.dqopt_label[label].setAlignment(Qt.AlignHCenter)
                    self.dqdiff_label[label].setAlignment(Qt.AlignHCenter)
                else:
                    initial_value = float(
                        self.initial_opt_ranges[tab_name][label]['initial'])
                    self.dqinitial_label[label].setText(
                        ("%6f" % initial_value).rstrip('0').rstrip('.'))
                    self.dqopt_label[label].setText(
                        ("%6f" % self.dparams[label]).rstrip('0').rstrip('.'))
                    self.dqopt_label[label].setAlignment(
                        Qt.AlignVCenter | Qt.AlignLeft)
                    self.dqdiff_label[label].setAlignment(
                        Qt.AlignVCenter | Qt.AlignLeft)

                    if isclose(value, initial_value, abs_tol=1e-7):
                        diff = 0
                        text = "0.0"
                        color_fmt = "QLabel { color : black; }"
                    else:
                        diff = value - initial_value

                    if initial_value == 0:
                        # can't calculate %
                        if diff < 0:
                            text = ("%6f" % diff).rstrip('0').rstrip('.')
                            color_fmt = "QLabel { color : red; }"
                        elif diff > 0:
                            text = ("+%6f" % diff).rstrip('0').rstrip('.')
                            color_fmt = "QLabel { color : green; }"
                    else:
                        # calculate percent difference
                        percent_diff = 100 * diff/abs(initial_value)
                        if percent_diff < 0:
                            text = ("%2.2f %%" % percent_diff)
                            color_fmt = "QLabel { color : red; }"
                        elif percent_diff > 0:
                            text = ("+%2.2f %%" % percent_diff)
                            color_fmt = "QLabel { color : green; }"

                self.dqdiff_label[label].setStyleSheet(color_fmt)
                self.dqdiff_label[label].setText(text)

    def updateRangeFromSlider(self, label, range_min, range_max):
        import re

        label_match = re.search('(evprox|evdist)_([0-9]+)', label)
        if label_match:
            tab_name = label_match.group(1) + '_' + label_match.group(2)
        else:
            print("ERR: can't determine input name from parameter: %s" %
                  label)
            return

        self.dqrange_min[label] = range_min
        self.dqrange_max[label] = range_max
        self.dqrange_label[label].setText(_format_range_str(range_min) +
                                          " - " +
                                          _format_range_str(range_max))
        self.opt_params[tab_name]['ranges'][label]['minval'] = range_min
        self.opt_params[tab_name]['ranges'][label]['maxval'] = range_max

    def updateOptRanges(self, save_sliders=False):
        # iterate through tabs. data is contained in grid layout
        for tab_index, tab in enumerate(self.ltabs):
            # now update the ranges (last row is a spacer)
            for row_index in range(2, tab.layout.rowCount()-1):
                label = self.ltabkeys[tab_index][row_index]
                self.updateRange(label, save_sliders)

    def setfromdin(self, din):
        if not din:
            return

        if 'dt' in din:
            # din proivdes a complete parameter set
            self.din = din
            self.simlength = float(din['tstop'])
            self.sim_dt = float(din['dt'])

            self.cleanLabels()
            self.removeAllInputs()  # turn off any previously set inputs
            self.ltabkeys = []
            self.dtab_idx = {}
            self.dtab_names = {}

            for evinput in _get_param_inputs(din):
                if 'evprox_' in evinput:
                    self.addProx()
                elif 'evdist_' in evinput:
                    self.addDist()

        for k, v in din.items():
            if k in self.dparams:
                if k.startswith('numspikes'):
                    try:
                        new_value = int(v)
                    except ValueError:
                        print("WARN: bad value for param %s: %s. Unable to"
                              " convert to a integer" % (k, v))
                        continue
                    self.dparams[k] = new_value
                else:
                    try:
                        new_value = float(v)
                    except ValueError:
                        print("WARN: bad value for param %s: %s. Unable to"
                              " convert to a floating point number" % (k, v))
                        continue
                    self.dparams[k] = new_value
            elif k.count('gbar') > 0 and \
                (k.count('evprox') > 0 or
                 k.count('evdist') > 0):
                # NOTE: will be deprecated in future release
                # for back-compat with old-style specification which didn't
                # have ampa,nmda in evoked gbar
                try:
                    new_value = float(v)
                except ValueError:
                    print("WARN: bad value for param %s: %s. Unable to"
                          " convert to a floating point number" % (k, v))
                    continue
                lks = k.split('_')
                eloc = lks[1]
                enum = lks[2]
                base_key_str = 'gbar_' + eloc + '_' + enum + '_'
                if eloc == 'evprox':
                    for ct in ['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket']:
                        # ORIGINAL MODEL/PARAM: only ampa for prox evoked
                        # inputs
                        key_str = base_key_str + ct + '_ampa'
                        self.dparams[key_str] = new_value
                elif eloc == 'evdist':
                    for ct in ['L2Pyr', 'L2Basket', 'L5Pyr']:
                        # ORIGINAL MODEL/PARAM: both ampa and nmda for distal
                        # evoked inputs
                        key_str = base_key_str + ct + '_ampa'
                        self.dparams[key_str] = new_value
                        key_str = base_key_str + ct + '_nmda'
                        self.dparams[key_str] = new_value

        if not self.optimization_running:
            self.updateOptParams()
            self.rebuildOptStepInfo()
            self.updateOptRanges(save_sliders=True)

        self.updateOptDeltas()

    def __str__(self):
        # don't write any values to param file
        return ''
