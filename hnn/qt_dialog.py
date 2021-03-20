"""Classes for creating the dialog boxes"""

# Authors: Sam Neymotin <samnemo@gmail.com>
#          Blake Caldwell <blake_caldwell@brown.edu>

import os
from collections import OrderedDict

from PyQt5.QtWidgets import (QDialog, QToolTip, QTabWidget, QWidget,
                             QPushButton, QMessageBox, QComboBox, QLabel,
                             QLineEdit, QTextEdit, QFormLayout,
                             QVBoxLayout, QHBoxLayout, QGridLayout)
from PyQt5.QtGui import QFont, QPixmap, QIcon

from hnn_core import read_params, Params

from .paramrw import (usingOngoingInputs, usingEvokedInputs, get_output_dir,
                      legacy_param_str_to_dict)
from .qt_lib import (setscalegeom, setscalegeomcenter, lookupresource,
                     ClickLabel)
from .qt_evoked import EvokedInputParamDialog, OptEvokedInputParamDialog


def bringwintotop(win):
    # bring a pyqt5 window to the top (parents still stay behind children)
    # from https://www.programcreek.com/python/example/
    # 101663/PyQt5.QtCore.Qt.WindowActive
    # win.show()
    # win.setWindowState(win.windowState() & ~Qt.WindowMinimized |
    #                    Qt.WindowActive)
    # win.raise_()
    win.showNormal()
    win.activateWindow()
    # win.setWindowState((win.windowState() & ~Qt.WindowMinimized) |
    #                    Qt.WindowActive)
    # win.activateWindow()
    # win.raise_()
    # win.show()


class DictDialog(QDialog):
    """dictionary-based dialog with tabs

    should make all dialogs specifiable via cfg file format -
    then can customize gui without changing py code
    and can reduce code explosion / overlap between dialogs
    """

    def __init__(self, parent, din):
        super(DictDialog, self).__init__(parent)
        self.ldict = []  # subclasses should override
        self.ltitle = []
        # for translating model variable name to more human-readable form
        self.dtransvar = {}
        self.stitle = ''
        self.initd()
        self.initUI()
        self.initExtra()
        self.setfromdin(din)  # set values from input dictionary
        # self.addtips()

    # TODO: add back tooltips
    # def addtips (self):
    #   for ktip in dconf.keys():
    #     if ktip in self.dqline:
    #       self.dqline[ktip].setToolTip(dconf[ktip])
    #     elif ktip in self.dqextra:
    #       self.dqextra[ktip].setToolTip(dconf[ktip])

    def __str__(self):
        s = ''
        for k, v in self.dqline.items():
            s += k + ': ' + v.text().strip() + os.linesep
        return s

    def saveparams(self):
        self.hide()

    def initd(self):
        pass  # implemented in subclass

    def getval(self, k):
        if k in self.dqline.keys():
            return self.dqline[k].text().strip()

    def lines2val(self, ksearch, val):
        for k in self.dqline.keys():
            if k.count(ksearch) > 0:
                self.dqline[k].setText(str(val))

    def setfromdin(self, din):
        if not din:
            return
        for k, v in din.items():
            if k in self.dqline:
                self.dqline[k].setText(str(v).strip())

    def transvar(self, k):
        if k in self.dtransvar:
            return self.dtransvar[k]
        return k

    def addtransvar(self, k, strans):
        self.dtransvar[k] = strans
        self.dtransvar[strans] = k

    def initExtra(self):
        # extra items not written to param file
        self.dqextra = {}

    def initUI(self):
        self.layout = QVBoxLayout(self)

        # Add stretch to separate the form layout from the button
        self.layout.addStretch(1)

        # Initialize tab screen
        self.ltabs = []
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        for _ in range(len(self.ldict)):
            self.ltabs.append(QWidget())

        self.tabs.resize(575, 200)

        # create tabs and their layouts
        for tab, s in zip(self.ltabs, self.ltitle):
            self.tabs.addTab(tab, s)
            tab.layout = QFormLayout()
            tab.setLayout(tab.layout)

        self.dqline = {}  # QLineEdits dict; key is model variable
        for d, tab in zip(self.ldict, self.ltabs):
            for k, v in d.items():
                self.dqline[k] = QLineEdit(self)
                self.dqline[k].setText(str(v))
                # add label,QLineEdit to the tab
                tab.layout.addRow(self.transvar(k), self.dqline[k])

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        self.setWindowTitle(self.stitle)

    def TurnOff(self):
        pass

    def addOffButton(self):
        """Create a horizontal box layout to hold the button"""
        self.button_box = QHBoxLayout()
        self.btnoff = QPushButton('Turn Off Inputs', self)
        self.btnoff.resize(self.btnoff.sizeHint())
        self.btnoff.clicked.connect(self.TurnOff)
        self.btnoff.setToolTip('Turn Off Inputs')
        self.button_box.addWidget(self.btnoff)
        self.layout.addLayout(self.button_box)

    def addHideButton(self):
        self.bbhidebox = QHBoxLayout()
        self.btnhide = QPushButton('Hide Window', self)
        self.btnhide.resize(self.btnhide.sizeHint())
        self.btnhide.clicked.connect(self.hide)
        self.btnhide.setToolTip('Hide Window')
        self.bbhidebox.addWidget(self.btnhide)
        self.layout.addLayout(self.bbhidebox)


class OngoingInputParamDialog (DictDialog):
    """widget to specify ongoing input params (proximal, distal)"""

    def __init__(self, parent, inty, din=None):
        self.inty = inty
        if self.inty.startswith('Proximal'):
            self.prefix = 'input_prox_A_'
            self.postfix = '_prox'
            self.isprox = True
        else:
            self.prefix = 'input_dist_A_'
            self.postfix = '_dist'
            self.isprox = False
        super(OngoingInputParamDialog, self).__init__(parent, din)
        self.addOffButton()
        self.addImages()
        self.addHideButton()

    def addImages(self):
        """add png cartoons to tabs"""
        if self.isprox:
            self.pix = QPixmap(lookupresource('proxfig'))
        else:
            self.pix = QPixmap(lookupresource('distfig'))
        for tab in self.ltabs:
            pixlbl = ClickLabel(self)
            pixlbl.setPixmap(self.pix)
            tab.layout.addRow(pixlbl)

    def TurnOff(self):
        """ turn off by setting all weights to 0.0"""
        self.lines2val('weight', 0.0)

    def initd(self):
        self.dtiming = OrderedDict([('t0_input' + self.postfix, 1000.),
                                    ('t0_input_stdev' + self.postfix, 0.),
                                    ('tstop_input' + self.postfix, 250.),
                                    ('f_input' + self.postfix, 10.),
                                    ('f_stdev' + self.postfix, 20.),
                                    ('events_per_cycle' + self.postfix, 2),
                                    ('repeats' + self.postfix, 10)])

        self.dL2 = OrderedDict([(self.prefix + 'weight_L2Pyr_ampa', 0.),
                                (self.prefix + 'weight_L2Pyr_nmda', 0.),
                                (self.prefix + 'weight_L2Basket_ampa', 0.),
                                (self.prefix + 'weight_L2Basket_nmda', 0.),
                                (self.prefix + 'delay_L2', 0.1)])

        self.dL5 = OrderedDict([(self.prefix + 'weight_L5Pyr_ampa', 0.),
                                (self.prefix + 'weight_L5Pyr_nmda', 0.)])

        if self.isprox:
            self.dL5[self.prefix + 'weight_L5Basket_ampa'] = 0.0
            self.dL5[self.prefix + 'weight_L5Basket_nmda'] = 0.0
        self.dL5[self.prefix + 'delay_L5'] = 0.1

        self.ldict = [self.dtiming, self.dL2, self.dL5]
        self.ltitle = ['Timing', 'Layer 2/3', 'Layer 5']
        self.stitle = 'Set Rhythmic ' + self.inty + ' Inputs'

        dtmp = {'L2': 'L2/3 ', 'L5': 'L5 '}
        for d in [self.dL2, self.dL5]:
            for k in d.keys():
                lk = k.split('_')
                if k.count('weight') > 0:
                    self.addtransvar(k, dtmp[lk[-2][0:2]] + lk[-2][2:] + ' ' +
                                     lk[-1].upper() + u' weight (µS)')
                else:
                    self.addtransvar(k, 'Delay (ms)')

        self.addtransvar('t0_input' + self.postfix, 'Start time mean (ms)')
        self.addtransvar('t0_input_stdev' + self.postfix,
                         'Start time stdev (ms)')
        self.addtransvar('tstop_input' + self.postfix, 'Stop time (ms)')
        self.addtransvar('f_input' + self.postfix, 'Burst frequency (Hz)')
        self.addtransvar('f_stdev' + self.postfix, 'Burst stdev (ms)')
        self.addtransvar('events_per_cycle' + self.postfix, 'Spikes/burst')
        self.addtransvar('repeats' + self.postfix, 'Number bursts')


class EvokedOrRhythmicDialog (QDialog):
    def __init__(self, parent, distal, evwin, rhythwin):
        super(EvokedOrRhythmicDialog, self).__init__(parent)
        if distal:
            self.prefix = 'Distal'
        else:
            self.prefix = 'Proximal'
        self.evwin = evwin
        self.rhythwin = rhythwin
        self.initUI()
        # TODO: add back tooltips
        # self.addtips()

    def initUI(self):
        self.layout = QVBoxLayout(self)
        # Add stretch to separate the form layout from the button
        self.layout.addStretch(1)

        self.btnrhythmic = QPushButton('Rhythmic ' + self.prefix + ' Inputs',
                                       self)
        self.btnrhythmic.resize(self.btnrhythmic.sizeHint())
        self.btnrhythmic.clicked.connect(self.showrhythmicwin)
        self.layout.addWidget(self.btnrhythmic)

        self.btnevoked = QPushButton('Evoked Inputs', self)
        self.btnevoked.resize(self.btnevoked.sizeHint())
        self.btnevoked.clicked.connect(self.showevokedwin)
        self.layout.addWidget(self.btnevoked)

        self.addHideButton()

        setscalegeom(self, 150, 150, 270, 120)
        self.setWindowTitle("Pick Input Type")

    def showevokedwin(self):
        bringwintotop(self.evwin)
        self.hide()

    def showrhythmicwin(self):
        bringwintotop(self.rhythwin)
        self.hide()

    def addHideButton(self):
        self.bbhidebox = QHBoxLayout()
        self.btnhide = QPushButton('Hide Window', self)
        self.btnhide.resize(self.btnhide.sizeHint())
        self.btnhide.clicked.connect(self.hide)
        self.btnhide.setToolTip('Hide Window')
        self.bbhidebox.addWidget(self.btnhide)
        self.layout.addLayout(self.bbhidebox)


class SynGainParamDialog(QDialog):
    def __init__(self, parent, netparamwin):
        super(SynGainParamDialog, self).__init__(parent)
        self.netparamwin = netparamwin
        self.initUI()

    def scalegain(self, k, fctr):
        oldval = float(self.netparamwin.dqline[k].text().strip())
        newval = oldval * fctr
        self.netparamwin.dqline[k].setText(str(newval))
        return newval

    def isE(self, ty):
        return ty.count('Pyr') > 0

    def isI(self, ty):
        return ty.count('Basket') > 0

    def tounity(self):
        for k in self.dqle.keys():
            self.dqle[k].setText('1.0')

    def scalegains(self):
        for _, k in enumerate(self.dqle.keys()):
            fctr = float(self.dqle[k].text().strip())
            if fctr < 0.:
                fctr = 0.
                self.dqle[k].setText(str(fctr))
            elif fctr == 1.0:
                continue
            for k2 in self.netparamwin.dqline.keys():
                types = k2.split('_')
                ty1, ty2 = types[1], types[2]
                if self.isE(ty1) and self.isE(ty2) and k == 'E -> E':
                    self.scalegain(k2, fctr)
                elif self.isE(ty1) and self.isI(ty2) and k == 'E -> I':
                    self.scalegain(k2, fctr)
                elif self.isI(ty1) and self.isE(ty2) and k == 'I -> E':
                    self.scalegain(k2, fctr)
                elif self.isI(ty1) and self.isI(ty2) and k == 'I -> I':
                    self.scalegain(k2, fctr)

        # go back to unity since pressed OK - next call to this dialog will
        # reset new values
        self.tounity()
        self.hide()

    def initUI(self):
        grid = QGridLayout()
        grid.setSpacing(10)

        self.dqle = {}
        for row, k in enumerate(['E -> E', 'E -> I', 'I -> E', 'I -> I']):
            lbl = QLabel(self)
            lbl.setText(k)
            lbl.adjustSize()
            grid.addWidget(lbl, row, 0)
            qle = QLineEdit(self)
            qle.setText('1.0')
            grid.addWidget(qle, row, 1)
            self.dqle[k] = qle

        row += 1
        self.btnok = QPushButton('OK', self)
        self.btnok.resize(self.btnok.sizeHint())
        self.btnok.clicked.connect(self.scalegains)
        grid.addWidget(self.btnok, row, 0, 1, 1)
        self.btncancel = QPushButton('Cancel', self)
        self.btncancel.resize(self.btncancel.sizeHint())
        self.btncancel.clicked.connect(self.hide)
        grid.addWidget(self.btncancel, row, 1, 1, 1)

        self.setLayout(grid)
        setscalegeom(self, 150, 150, 270, 180)
        self.setWindowTitle("Synaptic Gains")


# widget to specify tonic inputs
class TonicInputParamDialog(DictDialog):
    def __init__(self, parent, din):
        super(TonicInputParamDialog, self).__init__(parent, din)
        self.addOffButton()
        self.addHideButton()

    # turn off by setting all weights to 0.0
    def TurnOff(self):
        self.lines2val('A', 0.0)

    def initd(self):
        self.dL2 = OrderedDict([
            # IClamp params for L2Pyr
            ('Itonic_A_L2Pyr_soma', 0.),
            ('Itonic_t0_L2Pyr_soma', 0.),
            ('Itonic_T_L2Pyr_soma', -1.),
            # IClamp param for L2Basket
            ('Itonic_A_L2Basket', 0.),
            ('Itonic_t0_L2Basket', 0.),
            ('Itonic_T_L2Basket', -1.)])

        self.dL5 = OrderedDict([
            # IClamp params for L5Pyr
            ('Itonic_A_L5Pyr_soma', 0.),
            ('Itonic_t0_L5Pyr_soma', 0.),
            ('Itonic_T_L5Pyr_soma', -1.),
            # IClamp param for L5Basket
            ('Itonic_A_L5Basket', 0.),
            ('Itonic_t0_L5Basket', 0.),
            ('Itonic_T_L5Basket', -1.)])

        # temporary dictionary for string translation
        dtmp = {'L2': 'L2/3 ', 'L5': 'L5 '}
        for d in [self.dL2, self.dL5]:
            for k in d.keys():
                cty = k.split('_')[2]  # cell type
                tcty = dtmp[cty[0:2]] + cty[2:]  # translated cell type
                if k.count('A') > 0:
                    self.addtransvar(k, tcty + ' amplitude (nA)')
                elif k.count('t0') > 0:
                    self.addtransvar(k, tcty + ' start time (ms)')
                elif k.count('T') > 0:
                    self.addtransvar(k, tcty + ' stop time (ms)')

        self.ldict = [self.dL2, self.dL5]
        self.ltitle = ['Layer 2/3', 'Layer 5']
        self.stitle = 'Set Tonic Inputs'


# widget to specify ongoing poisson inputs
class PoissonInputParamDialog(DictDialog):
    def __init__(self, parent, din):
        super(PoissonInputParamDialog, self).__init__(parent, din)
        self.addOffButton()
        self.addHideButton()

    def TurnOff(self):
        """turn off by setting all weights to 0.0"""
        self.lines2val('weight', 0.0)

    def initd(self):
        self.dL2, self.dL5 = {}, {}
        ld = [self.dL2, self.dL5]

        for i, lyr in enumerate(['L2', 'L5']):
            d = ld[i]
            for ty in ['Pyr', 'Basket']:
                for sy in ['ampa', 'nmda']:
                    d[lyr + ty + '_Pois_A_weight' + '_' + sy] = 0.
                d[lyr + ty + '_Pois_lamtha'] = 0.

        self.dtiming = OrderedDict([('t0_pois', 0.),
                                    ('T_pois', -1)])

        self.addtransvar('t0_pois', 'Start time (ms)')
        self.addtransvar('T_pois', 'Stop time (ms)')

        # temporary dictionary for string translation
        dtmp = {'L2': 'L2/3 ', 'L5': 'L5 '}
        for d in [self.dL2, self.dL5]:
            for k in d.keys():
                ks = k.split('_')
                cty = ks[0]  # cell type
                tcty = dtmp[cty[0:2]] + cty[2:]  # translated cell type
                if k.count('weight'):
                    self.addtransvar(k, tcty + ' ' + ks[-1].upper() +
                                     u' weight (µS)')
                elif k.endswith('lamtha'):
                    self.addtransvar(k, tcty + ' freq (Hz)')

        self.ldict = [self.dL2, self.dL5, self.dtiming]
        self.ltitle = ['Layer 2/3', 'Layer 5', 'Timing']
        self.stitle = 'Set Poisson Inputs'


# widget to specify run params (tstop, dt, etc.) -- not many params here
class RunParamDialog(DictDialog):
    def __init__(self, parent, mainwin, din=None):
        self.mainwin = mainwin
        super(RunParamDialog, self).__init__(parent, din)
        self.addHideButton()
        self.parent = parent

    def initd(self):

        self.drun = OrderedDict([('tstop', 250.),  # simulation end time (ms)
                                 ('dt', 0.025),  # timestep
                                 ('celsius', 37.0),  # temperature
                                 ('N_trials', 1),  # number of trials
                                 ('threshold', 0.0)])  # firing threshold
        # cvode - not currently used by simulation

        # analysis
        self.danalysis = OrderedDict([('save_figs', 0),
                                      ('save_spec_data', 0),
                                      ('f_max_spec', 40),
                                      ('dipole_scalefctr', 30e3),
                                      ('dipole_smooth_win', 15.0),
                                      ('record_vsoma', 0)])

        self.drand = OrderedDict([('prng_seedcore_opt',
                                   self.mainwin.prng_seedcore_opt),
                                  ('prng_seedcore_input_prox', 0),
                                  ('prng_seedcore_input_dist', 0),
                                  ('prng_seedcore_extpois', 0),
                                  ('prng_seedcore_extgauss', 0),
                                  ('prng_seedcore_evprox_1', 0),
                                  ('prng_seedcore_evdist_1', 0),
                                  ('prng_seedcore_evprox_2', 0),
                                  ('prng_seedcore_evdist_2', 0)])

        self.ldict = [self.drun, self.danalysis, self.drand]
        self.ltitle = ['Run', 'Analysis', 'Randomization Seeds']
        self.stitle = 'Run Parameters'

        self.addtransvar('tstop', 'Duration (ms)')
        self.addtransvar('dt', 'Integration Timestep (ms)')
        self.addtransvar('celsius', 'Temperature (C)')
        self.addtransvar('threshold', 'Firing Threshold (mV)')
        self.addtransvar('N_trials', 'Trials')
        self.addtransvar('save_spec_data', 'Save Spectral Data')
        self.addtransvar('save_figs', 'Save Figures')
        self.addtransvar('f_max_spec', 'Max Spectral Frequency (Hz)')
        self.addtransvar('spec_cmap', 'Spectrogram Colormap')
        self.addtransvar('dipole_scalefctr', 'Dipole Scaling')
        self.addtransvar('dipole_smooth_win', 'Dipole Smooth Window (ms)')
        self.addtransvar('record_vsoma', 'Record Somatic Voltages')
        self.addtransvar('prng_seedcore_opt', 'Parameter Optimization')
        self.addtransvar('prng_seedcore_input_prox', 'Ongoing Proximal Input')
        self.addtransvar('prng_seedcore_input_dist', 'Ongoing Distal Input')
        self.addtransvar('prng_seedcore_extpois', 'External Poisson')
        self.addtransvar('prng_seedcore_extgauss', 'External Gaussian')
        self.addtransvar('prng_seedcore_evprox_1', 'Evoked Proximal 1')
        self.addtransvar('prng_seedcore_evdist_1', 'Evoked Distal 1 ')
        self.addtransvar('prng_seedcore_evprox_2', 'Evoked Proximal 2')
        self.addtransvar('prng_seedcore_evdist_2', 'Evoked Distal 2')

    def selectionchange(self, i):
        self.spec_cmap = self.cmaps[i]
        self.parent.update_gui_params({})

    def initExtra(self):
        DictDialog.initExtra(self)
        self.dqextra['NumCores'] = QLineEdit(self)
        self.dqextra['NumCores'].setText(str(self.mainwin.defncore))
        self.addtransvar('NumCores', 'Number Cores')
        self.ltabs[0].layout.addRow('NumCores', self.dqextra['NumCores'])

        self.spec_cmap_cb = None

        self.cmaps = ['jet',
                      'viridis',
                      'plasma',
                      'inferno',
                      'magma',
                      'cividis']

        self.spec_cmap_cb = QComboBox()
        for cmap in self.cmaps:
            self.spec_cmap_cb.addItem(cmap)
        self.spec_cmap_cb.currentIndexChanged.connect(self.selectionchange)
        self.ltabs[1].layout.addRow(
            self.transvar('spec_cmap'), self.spec_cmap_cb)

    def getntrial(self):
        ntrial = int(self.dqline['N_trials'].text().strip())
        if ntrial < 1:
            self.dqline['N_trials'].setText(str(1))
            ntrial = 1
        return ntrial

    def getncore(self):
        ncore = int(self.dqextra['NumCores'].text().strip())
        if ncore < 1:
            self.dqline['NumCores'].setText(str(1))
            ncore = 1

        # update value in HNNGUI for persistence
        self.mainwin.defncore = ncore

        return ncore

    def get_prng_seedcore_opt(self):
        prng_seedcore_opt = self.dqline['prng_seedcore_opt'].text().strip()

        # update value in HNNGUI for persistence
        self.mainwin.prng_seedcore_opt = int(prng_seedcore_opt)

        return int(self.mainwin.prng_seedcore_opt)

    def setfromdin(self, din):
        if not din:
            return

        # number of cores may have changed if the configured number failed
        self.dqextra['NumCores'].setText(str(self.mainwin.defncore))

        # update ordered dict of QLineEdit objects with new parameters
        for k, v in din.items():
            if k in self.dqline:
                self.dqline[k].setText(str(v).strip())
            elif k == 'spec_cmap':
                self.spec_cmap = v

        # for spec_cmap we want the user to be able to change
        # (e.g. 'viridis'), but the default is 'jet' to be consistent with
        # prior publications on HNN
        if 'spec_cmap' not in din:
            self.spec_cmap = 'jet'

        # update the spec_cmap dropdown menu
        self.spec_cmap_cb.setCurrentIndex(self.cmaps.index(self.spec_cmap))

    def __str__(self):
        s = ''
        for k, v in self.dqline.items():
            s += k + ': ' + v.text().strip() + os.linesep
        s += 'spec_cmap: ' + self.spec_cmap + os.linesep
        return s

# widget to specify (pyramidal) cell parameters (geometry, synapses,
# biophysics)


class CellParamDialog (DictDialog):
    def __init__(self, parent=None, din=None):
        super(CellParamDialog, self).__init__(parent, din)
        self.addHideButton()

    def initd(self):

        self.dL2PyrGeom = OrderedDict([('L2Pyr_soma_L', 22.1),  # Soma
                                       ('L2Pyr_soma_diam', 23.4),
                                       ('L2Pyr_soma_cm', 0.6195),
                                       ('L2Pyr_soma_Ra', 200.),
                                       # Dendrites
                                       ('L2Pyr_dend_cm', 0.6195),
                                       ('L2Pyr_dend_Ra', 200.),
                                       ('L2Pyr_apicaltrunk_L', 59.5),
                                       ('L2Pyr_apicaltrunk_diam', 4.25),
                                       ('L2Pyr_apical1_L', 306.),
                                       ('L2Pyr_apical1_diam', 4.08),
                                       ('L2Pyr_apicaltuft_L', 238.),
                                       ('L2Pyr_apicaltuft_diam', 3.4),
                                       ('L2Pyr_apicaloblique_L', 340.),
                                       ('L2Pyr_apicaloblique_diam', 3.91),
                                       ('L2Pyr_basal1_L', 85.),
                                       ('L2Pyr_basal1_diam', 4.25),
                                       ('L2Pyr_basal2_L', 255.),
                                       ('L2Pyr_basal2_diam', 2.72),
                                       ('L2Pyr_basal3_L', 255.),
                                       ('L2Pyr_basal3_diam', 2.72)])

        self.dL2PyrSyn = OrderedDict([('L2Pyr_ampa_e', 0.),         # Synapses
                                      ('L2Pyr_ampa_tau1', 0.5),
                                      ('L2Pyr_ampa_tau2', 5.),
                                      ('L2Pyr_nmda_e', 0.),
                                      ('L2Pyr_nmda_tau1', 1.),
                                      ('L2Pyr_nmda_tau2', 20.),
                                      ('L2Pyr_gabaa_e', -80.),
                                      ('L2Pyr_gabaa_tau1', 0.5),
                                      ('L2Pyr_gabaa_tau2', 5.),
                                      ('L2Pyr_gabab_e', -80.),
                                      ('L2Pyr_gabab_tau1', 1.),
                                      ('L2Pyr_gabab_tau2', 20.)])

        self.dL2PyrBiophys = OrderedDict([  # Biophysics soma
                                         ('L2Pyr_soma_gkbar_hh2', 0.01),
                                         ('L2Pyr_soma_gnabar_hh2', 0.18),
                                         ('L2Pyr_soma_el_hh2', -65.),
                                         ('L2Pyr_soma_gl_hh2', 4.26e-5),
                                         ('L2Pyr_soma_gbar_km', 250.),
                                         # Biophysics dends
                                         ('L2Pyr_dend_gkbar_hh2', 0.01),
                                         ('L2Pyr_dend_gnabar_hh2', 0.15),
                                         ('L2Pyr_dend_el_hh2', -65.),
                                         ('L2Pyr_dend_gl_hh2', 4.26e-5),
                                         ('L2Pyr_dend_gbar_km', 250.)])

        self.dL5PyrGeom = OrderedDict([('L5Pyr_soma_L', 39.),  # Soma
                                       ('L5Pyr_soma_diam', 28.9),
                                       ('L5Pyr_soma_cm', 0.85),
                                       ('L5Pyr_soma_Ra', 200.),
                                       # Dendrites
                                       ('L5Pyr_dend_cm', 0.85),
                                       ('L5Pyr_dend_Ra', 200.),
                                       ('L5Pyr_apicaltrunk_L', 102.),
                                       ('L5Pyr_apicaltrunk_diam', 10.2),
                                       ('L5Pyr_apical1_L', 680.),
                                       ('L5Pyr_apical1_diam', 7.48),
                                       ('L5Pyr_apical2_L', 680.),
                                       ('L5Pyr_apical2_diam', 4.93),
                                       ('L5Pyr_apicaltuft_L', 425.),
                                       ('L5Pyr_apicaltuft_diam', 3.4),
                                       ('L5Pyr_apicaloblique_L', 255.),
                                       ('L5Pyr_apicaloblique_diam', 5.1),
                                       ('L5Pyr_basal1_L', 85.),
                                       ('L5Pyr_basal1_diam', 6.8),
                                       ('L5Pyr_basal2_L', 255.),
                                       ('L5Pyr_basal2_diam', 8.5),
                                       ('L5Pyr_basal3_L', 255.),
                                       ('L5Pyr_basal3_diam', 8.5)])

        self.dL5PyrSyn = OrderedDict([('L5Pyr_ampa_e', 0.),  # Synapses
                                      ('L5Pyr_ampa_tau1', 0.5),
                                      ('L5Pyr_ampa_tau2', 5.),
                                      ('L5Pyr_nmda_e', 0.),
                                      ('L5Pyr_nmda_tau1', 1.),
                                      ('L5Pyr_nmda_tau2', 20.),
                                      ('L5Pyr_gabaa_e', -80.),
                                      ('L5Pyr_gabaa_tau1', 0.5),
                                      ('L5Pyr_gabaa_tau2', 5.),
                                      ('L5Pyr_gabab_e', -80.),
                                      ('L5Pyr_gabab_tau1', 1.),
                                      ('L5Pyr_gabab_tau2', 20.)])

        self.dL5PyrBiophys = OrderedDict([  # Biophysics soma
                                         ('L5Pyr_soma_gkbar_hh2', 0.01),
                                         ('L5Pyr_soma_gnabar_hh2', 0.16),
                                         ('L5Pyr_soma_el_hh2', -65.),
                                         ('L5Pyr_soma_gl_hh2', 4.26e-5),
                                         ('L5Pyr_soma_gbar_ca', 60.),
                                         ('L5Pyr_soma_taur_cad', 20.),
                                         ('L5Pyr_soma_gbar_kca', 2e-4),
                                         ('L5Pyr_soma_gbar_km', 200.),
                                         ('L5Pyr_soma_gbar_cat', 2e-4),
                                         ('L5Pyr_soma_gbar_ar', 1e-6),
                                         # Biophysics dends
                                         ('L5Pyr_dend_gkbar_hh2', 0.01),
                                         ('L5Pyr_dend_gnabar_hh2', 0.14),
                                         ('L5Pyr_dend_el_hh2', -71.),
                                         ('L5Pyr_dend_gl_hh2', 4.26e-5),
                                         ('L5Pyr_dend_gbar_ca', 60.),
                                         ('L5Pyr_dend_taur_cad', 20.),
                                         ('L5Pyr_dend_gbar_kca', 2e-4),
                                         ('L5Pyr_dend_gbar_km', 200.),
                                         ('L5Pyr_dend_gbar_cat', 2e-4),
                                         ('L5Pyr_dend_gbar_ar', 1e-6)])

        dtrans = {'gkbar': 'Kv', 'gnabar': 'Na', 'km': 'Km', 'gl': 'leak',
                  'ca': 'Ca', 'kca': 'KCa', 'cat': 'CaT', 'ar': 'HCN',
                  'cad': 'Ca decay time', 'dend': 'Dendrite', 'soma': 'Soma',
                  'apicaltrunk': 'Apical Dendrite Trunk',
                  'apical1': 'Apical Dendrite 1',
                  'apical2': 'Apical Dendrite 2',
                  'apical3': 'Apical Dendrite 3',
                  'apicaltuft': 'Apical Dendrite Tuft',
                  'apicaloblique': 'Oblique Apical Dendrite',
                  'basal1': 'Basal Dendrite 1', 'basal2': 'Basal Dendrite 2',
                  'basal3': 'Basal Dendrite 3'}

        for d in [self.dL2PyrGeom, self.dL5PyrGeom]:
            for k in d.keys():
                lk = k.split('_')
                if lk[-1] == 'L':
                    self.addtransvar(
                        k, dtrans[lk[1]] + ' ' + r'length (micron)')
                elif lk[-1] == 'diam':
                    self.addtransvar(
                        k, dtrans[lk[1]] + ' ' + r'diameter (micron)')
                elif lk[-1] == 'cm':
                    self.addtransvar(
                        k, dtrans[lk[1]] + ' ' + r'capacitive density (F/cm2)')
                elif lk[-1] == 'Ra':
                    self.addtransvar(
                        k, dtrans[lk[1]] + ' ' + r'resistivity (ohm-cm)')

        for d in [self.dL2PyrSyn, self.dL5PyrSyn]:
            for k in d.keys():
                lk = k.split('_')
                if k.endswith('e'):
                    self.addtransvar(k, lk[1].upper() + ' ' + ' reversal (mV)')
                elif k.endswith('tau1'):
                    self.addtransvar(k, lk[1].upper() +
                                     ' ' + ' rise time (ms)')
                elif k.endswith('tau2'):
                    self.addtransvar(k, lk[1].upper() +
                                     ' ' + ' decay time (ms)')

        for d in [self.dL2PyrBiophys, self.dL5PyrBiophys]:
            for k in d.keys():
                lk = k.split('_')
                if lk[2].count('g') > 0:
                    if lk[3] == 'km' or lk[3] == 'ca' or lk[3] == 'kca' \
                                or lk[3] == 'cat' or lk[3] == 'ar':
                        nv = dtrans[lk[1]] + ' ' + \
                            dtrans[lk[3]] + ' ' + ' channel density '
                    else:
                        nv = dtrans[lk[1]] + ' ' + \
                            dtrans[lk[2]] + ' ' + ' channel density '
                    if lk[3] == 'hh2' or lk[3] == 'cat' or lk[3] == 'ar':
                        nv += '(S/cm2)'
                    else:
                        nv += '(pS/micron2)'
                elif lk[2].count('el') > 0:
                    nv = dtrans[lk[1]] + ' leak reversal (mV)'
                elif lk[2].count('taur') > 0:
                    nv = dtrans[lk[1]] + ' ' + dtrans[lk[3]] + ' (ms)'
                self.addtransvar(k, nv)

        self.ldict = [self.dL2PyrGeom, self.dL2PyrSyn, self.dL2PyrBiophys,
                      self.dL5PyrGeom, self.dL5PyrSyn, self.dL5PyrBiophys]
        self.ltitle = ['L2/3 Pyr Geometry', 'L2/3 Pyr Synapses',
                       'L2/3 Pyr Biophysics', 'L5 Pyr Geometry',
                       'L5 Pyr Synapses', 'L5 Pyr Biophysics']
        self.stitle = 'Cell Parameters'


# widget to specify network parameters (number cells, weights, etc.)
class NetworkParamDialog (DictDialog):
    def __init__(self, parent=None, din=None):
        super(NetworkParamDialog, self).__init__(parent, din)
        self.addHideButton()

    def initd(self):
        # number of cells
        self.dcells = OrderedDict([('N_pyr_x', 10),
                                   ('N_pyr_y', 10)])

        # max conductances TO L2Pyr
        self.dL2Pyr = OrderedDict([('gbar_L2Pyr_L2Pyr_ampa', 0.),
                                   ('gbar_L2Pyr_L2Pyr_nmda', 0.),
                                   ('gbar_L2Basket_L2Pyr_gabaa', 0.),
                                   ('gbar_L2Basket_L2Pyr_gabab', 0.)])

        # max conductances TO L2Baskets
        self.dL2Bas = OrderedDict([('gbar_L2Pyr_L2Basket', 0.),
                                   ('gbar_L2Basket_L2Basket', 0.)])

        # max conductances TO L5Pyr
        self.dL5Pyr = OrderedDict([('gbar_L2Pyr_L5Pyr', 0.),
                                   ('gbar_L2Basket_L5Pyr', 0.),
                                   ('gbar_L5Pyr_L5Pyr_ampa', 0.),
                                   ('gbar_L5Pyr_L5Pyr_nmda', 0.),
                                   ('gbar_L5Basket_L5Pyr_gabaa', 0.),
                                   ('gbar_L5Basket_L5Pyr_gabab', 0.)])

        # max conductances TO L5Baskets
        self.dL5Bas = OrderedDict([('gbar_L2Pyr_L5Basket', 0.),
                                   ('gbar_L5Pyr_L5Basket', 0.),
                                   ('gbar_L5Basket_L5Basket', 0.)])

        self.ldict = [self.dcells, self.dL2Pyr,
                      self.dL5Pyr, self.dL2Bas, self.dL5Bas]
        self.ltitle = ['Cells', 'Layer 2/3 Pyr',
                       'Layer 5 Pyr', 'Layer 2/3 Bas', 'Layer 5 Bas']
        self.stitle = 'Local Network Parameters'

        self.addtransvar('N_pyr_x', 'Num Pyr Cells (X direction)')
        self.addtransvar('N_pyr_y', 'Num Pyr Cells (Y direction)')

        dtmp = {'L2': 'L2/3 ', 'L5': 'L5 '}

        for d in [self.dL2Pyr, self.dL5Pyr, self.dL2Bas, self.dL5Bas]:
            for k in d.keys():
                lk = k.split('_')
                sty1 = dtmp[lk[1][0:2]] + lk[1][2:]
                sty2 = dtmp[lk[2][0:2]] + lk[2][2:]
                if len(lk) == 3:
                    self.addtransvar(k, sty1 + ' -> ' + sty2 + u' weight (µS)')
                else:
                    self.addtransvar(k, sty1 + ' -> ' + sty2 + ' ' +
                                     lk[3].upper() + u' weight (µS)')


class HelpDialog (QDialog):
    def __init__(self, parent):
        super(HelpDialog, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)
        # Add stretch to separate the form layout from the button
        self.layout.addStretch(1)

        setscalegeom(self, 100, 100, 300, 100)
        self.setWindowTitle('Help')


class SchematicDialog (QDialog):
    # class for holding model schematics (and parameter shortcuts)
    def __init__(self, parent):
        super(SchematicDialog, self).__init__(parent)
        self.initUI()

    def initUI(self):

        self.setWindowTitle('Model Schematics')
        QToolTip.setFont(QFont('SansSerif', 10))

        self.grid = grid = QGridLayout()
        grid.setSpacing(10)

        gRow = 0

        self.locbtn = QPushButton(
            'Local Network' + os.linesep + 'Connections', self)
        self.locbtn.setIcon(QIcon(lookupresource('connfig')))
        self.locbtn.clicked.connect(self.parent().shownetparamwin)
        self.grid.addWidget(self.locbtn, gRow, 0, 1, 1)

        self.proxbtn = QPushButton(
            'Proximal Drive' + os.linesep + 'Thalamus', self)
        self.proxbtn.setIcon(QIcon(lookupresource('proxfig')))
        self.proxbtn.clicked.connect(self.parent().showproxparamwin)
        self.grid.addWidget(self.proxbtn, gRow, 1, 1, 1)

        self.distbtn = QPushButton(
            'Distal Drive NonLemniscal' + os.linesep +
            'Thal./Cortical Feedback', self)
        self.distbtn.setIcon(QIcon(lookupresource('distfig')))
        self.distbtn.clicked.connect(self.parent().showdistparamwin)
        self.grid.addWidget(self.distbtn, gRow, 2, 1, 1)

        gRow = 1

        # for schematic dialog box
        self.pixConn = QPixmap(lookupresource('connfig'))
        self.pixConnlbl = ClickLabel(self)
        self.pixConnlbl.setScaledContents(True)
        # self.pixConnlbl.resize(self.pixConnlbl.size())
        self.pixConnlbl.setPixmap(self.pixConn)
        # self.pixConnlbl.clicked.connect(self.shownetparamwin)
        self.grid.addWidget(self.pixConnlbl, gRow, 0, 1, 1)

        self.pixProx = QPixmap(lookupresource('proxfig'))
        self.pixProxlbl = ClickLabel(self)
        self.pixProxlbl.setScaledContents(True)
        self.pixProxlbl.setPixmap(self.pixProx)
        # self.pixProxlbl.clicked.connect(self.showproxparamwin)
        self.grid.addWidget(self.pixProxlbl, gRow, 1, 1, 1)

        self.pixDist = QPixmap(lookupresource('distfig'))
        self.pixDistlbl = ClickLabel(self)
        self.pixDistlbl.setScaledContents(True)
        self.pixDistlbl.setPixmap(self.pixDist)
        # self.pixDistlbl.clicked.connect(self.showdistparamwin)
        self.grid.addWidget(self.pixDistlbl, gRow, 2, 1, 1)

        self.setLayout(grid)


class BaseParamDialog (QDialog):
    """Base widget for specifying params

    The params dictionary is stored within this class. Other Dialogs access it
    here.
    """
    def __init__(self, parent, paramfn):
        super(BaseParamDialog, self).__init__(parent)
        self.proxparamwin = None
        self.distparamwin = None
        self.netparamwin = None
        self.syngainparamwin = None
        self.runparamwin = RunParamDialog(self, parent)
        self.cellparamwin = CellParamDialog(self)
        self.netparamwin = NetworkParamDialog(self)
        self.syngainparamwin = SynGainParamDialog(self, self.netparamwin)
        self.proxparamwin = OngoingInputParamDialog(self, 'Proximal')
        self.distparamwin = OngoingInputParamDialog(self, 'Distal')
        self.evparamwin = EvokedInputParamDialog(self, None)
        self.optparamwin = OptEvokedInputParamDialog(self, parent)
        self.poisparamwin = PoissonInputParamDialog(self, None)
        self.tonicparamwin = TonicInputParamDialog(self, None)
        self.lsubwin = [self.runparamwin, self.cellparamwin, self.netparamwin,
                        self.proxparamwin, self.distparamwin, self.evparamwin,
                        self.poisparamwin, self.tonicparamwin,
                        self.optparamwin]
        self.paramfn = paramfn
        self.parent = parent

        self.params = read_params(self.paramfn)
        self.initUI()  # requires self.params
        self.updateDispParam(self.params)

    def updateDispParam(self, params=None):
        global drawavgdpl

        if params is None:
            try:
                params = read_params(self.paramfn)
            except ValueError:
                QMessageBox.information(self, "HNN", "WARNING: could not"
                                        "retrieve parameters from %s" %
                                        self.paramfn)
                return

        self.params = params

        if usingEvokedInputs(self.params):
            # default for evoked is to show average dipole
            drawavgdpl = True
        elif usingOngoingInputs(self.params):
            # default for ongoing is NOT to show average dipole
            drawavgdpl = False

        for dlg in self.lsubwin:
            dlg.setfromdin(self.params)  # update to values from file
        self.qle.setText(self.params['sim_prefix'])  # update simulation name

    def setrunparam(self):
        bringwintotop(self.runparamwin)

    def setcellparam(self):
        bringwintotop(self.cellparamwin)

    def setnetparam(self):
        bringwintotop(self.netparamwin)

    def setsyngainparam(self):
        bringwintotop(self.syngainparamwin)

    def setproxparam(self):
        bringwintotop(self.proxparamwin)

    def setdistparam(self):
        bringwintotop(self.distparamwin)

    def setevparam(self):
        bringwintotop(self.evparamwin)

    def setpoisparam(self):
        bringwintotop(self.poisparamwin)

    def settonicparam(self):
        bringwintotop(self.tonicparamwin)

    def initUI(self):
        grid = QGridLayout()
        grid.setSpacing(10)

        row = 1

        self.lbl = QLabel(self)
        self.lbl.setText('Simulation Name:')
        self.lbl.adjustSize()
        self.lbl.setToolTip(
            'Simulation Name used to save parameter file and simulation data')
        grid.addWidget(self.lbl, row, 0)
        self.qle = QLineEdit(self)
        self.qle.setText(self.params['sim_prefix'])
        grid.addWidget(self.qle, row, 1)
        row += 1

        self.btnrun = QPushButton('Run', self)
        self.btnrun.resize(self.btnrun.sizeHint())
        self.btnrun.setToolTip('Set Run Parameters')
        self.btnrun.clicked.connect(self.setrunparam)
        grid.addWidget(self.btnrun, row, 0, 1, 1)

        self.btncell = QPushButton('Cell', self)
        self.btncell.resize(self.btncell.sizeHint())
        self.btncell.setToolTip(
            'Set Cell (Geometry, Synapses, Biophysics) Parameters')
        self.btncell.clicked.connect(self.setcellparam)
        grid.addWidget(self.btncell, row, 1, 1, 1)
        row += 1

        self.btnnet = QPushButton('Local Network', self)
        self.btnnet.resize(self.btnnet.sizeHint())
        self.btnnet.setToolTip('Set Local Network Parameters')
        self.btnnet.clicked.connect(self.setnetparam)
        grid.addWidget(self.btnnet, row, 0, 1, 1)

        self.btnsyngain = QPushButton('Synaptic Gains', self)
        self.btnsyngain.resize(self.btnsyngain.sizeHint())
        self.btnsyngain.setToolTip('Set Local Network Synaptic Gains')
        self.btnsyngain.clicked.connect(self.setsyngainparam)
        grid.addWidget(self.btnsyngain, row, 1, 1, 1)

        row += 1

        self.btnprox = QPushButton('Rhythmic Proximal Inputs', self)
        self.btnprox.resize(self.btnprox.sizeHint())
        self.btnprox.setToolTip('Set Rhythmic Proximal Inputs')
        self.btnprox.clicked.connect(self.setproxparam)
        grid.addWidget(self.btnprox, row, 0, 1, 2)
        row += 1

        self.btndist = QPushButton('Rhythmic Distal Inputs', self)
        self.btndist.resize(self.btndist.sizeHint())
        self.btndist.setToolTip('Set Rhythmic Distal Inputs')
        self.btndist.clicked.connect(self.setdistparam)
        grid.addWidget(self.btndist, row, 0, 1, 2)
        row += 1

        self.btnev = QPushButton('Evoked Inputs', self)
        self.btnev.resize(self.btnev.sizeHint())
        self.btnev.setToolTip('Set Evoked Inputs')
        self.btnev.clicked.connect(self.setevparam)
        grid.addWidget(self.btnev, row, 0, 1, 2)
        row += 1

        self.btnpois = QPushButton('Poisson Inputs', self)
        self.btnpois.resize(self.btnpois.sizeHint())
        self.btnpois.setToolTip('Set Poisson Inputs')
        self.btnpois.clicked.connect(self.setpoisparam)
        grid.addWidget(self.btnpois, row, 0, 1, 2)
        row += 1

        self.btntonic = QPushButton('Tonic Inputs', self)
        self.btntonic.resize(self.btntonic.sizeHint())
        self.btntonic.setToolTip('Set Tonic (Current Clamp) Inputs')
        self.btntonic.clicked.connect(self.settonicparam)
        grid.addWidget(self.btntonic, row, 0, 1, 2)
        row += 1

        self.btnsave = QPushButton('Save Parameters To File', self)
        self.btnsave.resize(self.btnsave.sizeHint())
        self.btnsave.setToolTip(
            'Save All Parameters to File (Specified by Simulation Name)')
        self.btnsave.clicked.connect(self.saveparams)
        grid.addWidget(self.btnsave, row, 0, 1, 2)
        row += 1

        self.btnhide = QPushButton('Hide Window', self)
        self.btnhide.resize(self.btnhide.sizeHint())
        self.btnhide.clicked.connect(self.hide)
        self.btnhide.setToolTip('Hide Window')
        grid.addWidget(self.btnhide, row, 0, 1, 2)

        self.setLayout(grid)

        self.setWindowTitle('Set Parameters')

    def saveparams(self, checkok=True):
        param_dir = os.path.join(get_output_dir(), 'param')
        tmpf = os.path.join(param_dir, self.qle.text() + '.param')

        oktosave = True
        if os.path.isfile(tmpf) and checkok:
            self.show()
            msg = QMessageBox()
            ret = msg.warning(self, 'Over-write file(s)?',
                              tmpf + ' already exists. Over-write?',
                              QMessageBox.Ok | QMessageBox.Cancel,
                              QMessageBox.Ok)
            if ret == QMessageBox.Cancel:
                oktosave = False

        if oktosave:
            # update params dict with values from GUI
            self.params = Params(legacy_param_str_to_dict(str(self)))

            os.makedirs(param_dir, exist_ok=True)
            with open(tmpf, 'w') as fp:
                fp.write(str(self))

            self.paramfn = tmpf
            data_dir = os.path.join(get_output_dir(), 'data')
            sim_dir = os.path.join(data_dir, self.qle.text())
            os.makedirs(sim_dir, exist_ok=True)

        return oktosave

    def update_gui_params(self, dtest):
        """ Update parameter values in GUI

        So user can see and so GUI will save these param values
        """
        for win in self.lsubwin:
            win.setfromdin(dtest)

    def __str__(self):
        s = 'sim_prefix: ' + self.qle.text() + os.linesep
        s += 'expmt_groups: {' + self.qle.text() + '}' + os.linesep
        for win in self.lsubwin:
            s += str(win)
        return s


class WaitSimDialog (QDialog):
    def __init__(self, parent):
        super(WaitSimDialog, self).__init__(parent)
        self.initUI()
        self.txt = ''  # text for display

    def updatetxt(self, txt):
        self.qtxt.append(txt)

    def initUI(self):
        self.layout = QVBoxLayout(self)
        self.layout.addStretch(1)

        self.qtxt = QTextEdit(self)
        self.layout.addWidget(self.qtxt)

        self.stopbtn = stopbtn = QPushButton('Stop All Simulations', self)
        stopbtn.setToolTip('Stop All Simulations')
        stopbtn.resize(stopbtn.sizeHint())
        stopbtn.clicked.connect(self.stopsim)
        self.layout.addWidget(stopbtn)

        setscalegeomcenter(self, 500, 250)
        self.setWindowTitle("Simulation Log")

    def stopsim(self):
        self.parent().stopsim()
        self.hide()
