"""Classes for creating the main HNN GUI"""

# Authors: Sam Neymotin <samnemo@gmail.com>
#          Blake Caldwell <blake_caldwell@brown.edu>
#          Shane Lee

# Python builtins
import sys
import os
import multiprocessing
from subprocess import Popen
from collections import namedtuple, OrderedDict
import numpy as np
import traceback
from psutil import cpu_count

# External libraries
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication
from PyQt5.QtWidgets import QFileDialog, QComboBox, QTabWidget
from PyQt5.QtWidgets import QToolTip, QPushButton, QFormLayout
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QDialog, QGridLayout
from PyQt5.QtWidgets import QLineEdit, QLabel, QTextEdit, QInputDialog
from PyQt5.QtWidgets import QMenu, QMessageBox, QWidget, QDialog
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
import matplotlib.pyplot as plt
from hnn_core import read_params

# HNN modules
from .paramrw import usingOngoingInputs, usingEvokedInputs, get_output_dir
from .simdat import SIMCanvas, getinputfiles
from .simdat import updatelsimdat, ddat, lsimdat, lsimidx
from .run import RunSimThread, ParamSignal
from .qt_lib import setscalegeom, setscalegeomcenter, getmplDPI, getscreengeom
from .qt_lib import lookupresource, ClickLabel
from .qt_evoked import EvokedInputParamDialog, OptEvokedInputParamDialog

# TODO: These globals should be made configurable via the GUI
drawindivrast = 0
drawavgdpl = 0
fontsize = plt.rcParams['font.size'] = 10


def isWindows():
    # are we on windows? or linux/mac ?
    return sys.platform.startswith('win')


def getPyComm():
    """get the python command"""

    # check python command interpreter path - if available
    if sys.executable is not None:
        pyc = sys.executable
        if pyc.count('python') > 0 and len(pyc) > 0:
            return pyc  # full path to python
    if isWindows():
        return 'python'
    return 'python3'


def _add_missing_frames(tb):
    fake_tb = namedtuple(
        'fake_tb', ('tb_frame', 'tb_lasti', 'tb_lineno', 'tb_next')
    )
    result = fake_tb(tb.tb_frame, tb.tb_lasti, tb.tb_lineno, tb.tb_next)
    frame = tb.tb_frame.f_back
    while frame:
        result = fake_tb(frame, frame.f_lasti, frame.f_lineno, result)
        frame = frame.f_back
    return result


def _get_defncore():
    """get default number of cores """

    try:
        defncore = len(os.sched_getaffinity(0))
    except AttributeError:
        defncore = cpu_count(logical=False)

    if defncore is None or defncore == 0:
        # in case psutil is not supported (e.g. BSD)
        defncore = multiprocessing.cpu_count()

    return defncore


class DoneSignal(QObject):
    finishSim = pyqtSignal(bool, str)


def bringwintobot(win):
    # win.show()
    # win.lower()
    win.hide()


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
  def __init__(self, parent, din = None):
    super(RunParamDialog, self).__init__(parent,din)
    self.addHideButton()
    self.parent = parent

  def initd(self):

    self.drun = OrderedDict([('tstop', 250.), # simulation end time (ms)
                             ('dt', 0.025), # timestep
                             ('celsius',37.0), # temperature
                             ('N_trials',1), # number of trials
                             ('threshold',0.0)]) # firing threshold
                             # cvode - not currently used by simulation

    # analysis    
    self.danalysis = OrderedDict([('save_figs',0),
                                  ('save_spec_data', 0),
                                  ('f_max_spec', 40),
                                  ('dipole_scalefctr',30e3),
                                  ('dipole_smooth_win',15.0),
                                  ('save_vsoma',0)])

    self.drand = OrderedDict([('prng_seedcore_opt', 0),
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

    self.addtransvar('tstop','Duration (ms)')
    self.addtransvar('dt','Integration Timestep (ms)')
    self.addtransvar('celsius','Temperature (C)')
    self.addtransvar('threshold','Firing Threshold (mV)')
    self.addtransvar('N_trials','Trials')
    self.addtransvar('save_spec_data','Save Spectral Data')
    self.addtransvar('save_figs','Save Figures')
    self.addtransvar('f_max_spec', 'Max Spectral Frequency (Hz)')
    self.addtransvar('spec_cmap', 'Spectrogram Colormap')
    self.addtransvar('dipole_scalefctr','Dipole Scaling')
    self.addtransvar('dipole_smooth_win','Dipole Smooth Window (ms)')
    self.addtransvar('save_vsoma','Save Somatic Voltages')
    self.addtransvar('prng_seedcore_opt','Parameter Optimization')
    self.addtransvar('prng_seedcore_input_prox','Ongoing Proximal Input')
    self.addtransvar('prng_seedcore_input_dist','Ongoing Distal Input')
    self.addtransvar('prng_seedcore_extpois','External Poisson')
    self.addtransvar('prng_seedcore_extgauss','External Gaussian')
    self.addtransvar('prng_seedcore_evprox_1','Evoked Proximal 1')
    self.addtransvar('prng_seedcore_evdist_1','Evoked Distal 1 ')
    self.addtransvar('prng_seedcore_evprox_2','Evoked Proximal 2')
    self.addtransvar('prng_seedcore_evdist_2','Evoked Distal 2')

  def selectionchange(self,i):
    self.spec_cmap = self.cmaps[i]
    self.parent.updatesaveparams({})

  def initExtra (self):
    DictDialog.initExtra(self)
    self.dqextra['NumCores'] = QLineEdit(self)
    self.defncore = _get_defncore()
    self.dqextra['NumCores'].setText(str(self.defncore))
    self.addtransvar('NumCores','Number Cores')
    self.ltabs[0].layout.addRow('NumCores',self.dqextra['NumCores'])

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
    self.ltabs[1].layout.addRow(self.transvar('spec_cmap'),self.spec_cmap_cb)

  def getntrial (self):
    ntrial = int(self.dqline['N_trials'].text().strip())
    if ntrial < 1:
      self.dqline['N_trials'].setText(str(1))
      ntrial = 1
    return ntrial

  def getncore (self):
    ncore = int(self.dqextra['NumCores'].text().strip())
    if ncore < 1:
      self.dqline['NumCores'].setText(str(1))
      ncore = 1
    return ncore

  def setfromdin (self,din):
    if not din: return

    # number of cores may have changed if the configured number failed
    self.dqextra['NumCores'].setText(str(self.defncore))

    # update ordered dict of QLineEdit objects with new parameters
    for k,v in din.items():
      if k in self.dqline:
        self.dqline[k].setText(str(v).strip())
      elif k == 'spec_cmap':
        self.spec_cmap = v

    # for spec_cmap we want the user to be able to change (e.g. 'viridis'), but the
    # default is 'jet' to be consistent with prior publications on HNN
    if 'spec_cmap' not in din:
      self.spec_cmap = 'jet'

    # update the spec_cmap dropdown menu
    self.spec_cmap_cb.setCurrentIndex(self.cmaps.index(self.spec_cmap))

  def __str__ (self):
    s = ''
    for k,v in self.dqline.items(): s += k + ': ' + v.text().strip() + os.linesep
    s += 'spec_cmap: ' + self.spec_cmap + os.linesep
    return s

# widget to specify (pyramidal) cell parameters (geometry, synapses, biophysics)
class CellParamDialog (DictDialog):
  def __init__ (self, parent = None, din = None):
    super(CellParamDialog, self).__init__(parent,din)
    self.addHideButton()

  def initd (self):
    
    self.dL2PyrGeom = OrderedDict([('L2Pyr_soma_L', 22.1), # Soma
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

    self.dL2PyrBiophys = OrderedDict([('L2Pyr_soma_gkbar_hh2', 0.01), # Biophysics soma
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

    self.dL5PyrSyn = OrderedDict([('L5Pyr_ampa_e', 0.), # Synapses
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

    self.dL5PyrBiophys = OrderedDict([('L5Pyr_soma_gkbar_hh2', 0.01), # Biophysics soma
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

    dtrans = {'gkbar':'Kv', 'gnabar':'Na', 'km':'Km', 'gl':'leak',\
              'ca':'Ca', 'kca':'KCa','cat':'CaT','ar':'HCN','cad':'Ca decay time',\
              'dend':'Dendrite','soma':'Soma','apicaltrunk':'Apical Dendrite Trunk',\
              'apical1':'Apical Dendrite 1','apical2':'Apical Dendrite 2',\
              'apical3':'Apical Dendrite 3','apicaltuft':'Apical Dendrite Tuft',\
              'apicaloblique':'Oblique Apical Dendrite','basal1':'Basal Dendrite 1',\
              'basal2':'Basal Dendrite 2','basal3':'Basal Dendrite 3'}

    for d in [self.dL2PyrGeom, self.dL5PyrGeom]:
      for k in d.keys():
        lk = k.split('_')
        if lk[-1] == 'L':
          self.addtransvar(k,dtrans[lk[1]] + ' ' + r'length (micron)')
        elif lk[-1] == 'diam':
          self.addtransvar(k,dtrans[lk[1]] + ' ' + r'diameter (micron)')
        elif lk[-1] == 'cm':
          self.addtransvar(k,dtrans[lk[1]] + ' ' + r'capacitive density (F/cm2)')
        elif lk[-1] == 'Ra':
          self.addtransvar(k,dtrans[lk[1]] + ' ' + r'resistivity (ohm-cm)')

    for d in [self.dL2PyrSyn, self.dL5PyrSyn]:
      for k in d.keys():
        lk = k.split('_')
        if k.endswith('e'):
          self.addtransvar(k,lk[1].upper() + ' ' + ' reversal (mV)')
        elif k.endswith('tau1'):
          self.addtransvar(k,lk[1].upper() + ' ' + ' rise time (ms)')
        elif k.endswith('tau2'):
          self.addtransvar(k,lk[1].upper() + ' ' + ' decay time (ms)')

    for d in [self.dL2PyrBiophys, self.dL5PyrBiophys]:
      for k in d.keys():
        lk = k.split('_')
        if lk[2].count('g') > 0:
          if lk[3]=='km' or lk[3]=='ca' or lk[3]=='kca' or lk[3]=='cat' or lk[3]=='ar':
            nv = dtrans[lk[1]] + ' ' + dtrans[lk[3]] + ' ' + ' channel density '
          else:
            nv = dtrans[lk[1]] + ' ' + dtrans[lk[2]] + ' ' + ' channel density '
          if lk[3] == 'hh2' or lk[3] == 'cat' or lk[3] == 'ar' : nv += '(S/cm2)'
          else: nv += '(pS/micron2)'
        elif lk[2].count('el') > 0: 
          nv = dtrans[lk[1]] + ' leak reversal (mV)'
        elif lk[2].count('taur') > 0:
          nv = dtrans[lk[1]] + ' ' + dtrans[lk[3]] + ' (ms)'
        self.addtransvar(k,nv)

    self.ldict = [self.dL2PyrGeom, self.dL2PyrSyn, self.dL2PyrBiophys,\
                  self.dL5PyrGeom, self.dL5PyrSyn, self.dL5PyrBiophys]
    self.ltitle = [ 'L2/3 Pyr Geometry', 'L2/3 Pyr Synapses', 'L2/3 Pyr Biophysics',\
                    'L5 Pyr Geometry', 'L5 Pyr Synapses', 'L5 Pyr Biophysics']
    self.stitle = 'Cell Parameters'


# widget to specify network parameters (number cells, weights, etc.)
class NetworkParamDialog (DictDialog):
  def __init__ (self, parent = None, din = None):
    super(NetworkParamDialog, self).__init__(parent,din)
    self.addHideButton()

  def initd (self):
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

    self.ldict = [self.dcells, self.dL2Pyr, self.dL5Pyr, self.dL2Bas, self.dL5Bas]
    self.ltitle = ['Cells', 'Layer 2/3 Pyr', 'Layer 5 Pyr', 'Layer 2/3 Bas', 'Layer 5 Bas']
    self.stitle = 'Local Network Parameters'

    self.addtransvar('N_pyr_x', 'Num Pyr Cells (X direction)')
    self.addtransvar('N_pyr_y', 'Num Pyr Cells (Y direction)')

    dtmp = {'L2':'L2/3 ','L5':'L5 '}

    for d in [self.dL2Pyr, self.dL5Pyr, self.dL2Bas, self.dL5Bas]:
      for k in d.keys():
        lk = k.split('_')
        sty1 = dtmp[lk[1][0:2]] + lk[1][2:]
        sty2 = dtmp[lk[2][0:2]] + lk[2][2:]
        if len(lk) == 3:
          self.addtransvar(k,sty1+' -> '+sty2+u' weight (µS)')
        else:
          self.addtransvar(k,sty1+' -> '+sty2+' '+lk[3].upper()+u' weight (µS)')

class HelpDialog (QDialog):
  def __init__ (self, parent):
    super(HelpDialog, self).__init__(parent)
    self.initUI()

  def initUI (self):
    self.layout = QVBoxLayout(self)
    # Add stretch to separate the form layout from the button
    self.layout.addStretch(1)

    setscalegeom(self, 100, 100, 300, 100)
    self.setWindowTitle('Help')    

class SchematicDialog (QDialog):
  # class for holding model schematics (and parameter shortcuts)
  def __init__ (self, parent):
    super(SchematicDialog, self).__init__(parent)
    self.initUI()

  def initUI (self):

    self.setWindowTitle('Model Schematics')
    QToolTip.setFont(QFont('SansSerif', 10))

    self.grid = grid = QGridLayout()
    grid.setSpacing(10)

    gRow = 0

    self.locbtn = QPushButton('Local Network'+os.linesep+'Connections',self)
    self.locbtn.setIcon(QIcon(lookupresource('connfig')))
    self.locbtn.clicked.connect(self.parent().shownetparamwin)
    self.grid.addWidget(self.locbtn,gRow,0,1,1)

    self.proxbtn = QPushButton('Proximal Drive'+os.linesep+'Thalamus',self)
    self.proxbtn.setIcon(QIcon(lookupresource('proxfig')))
    self.proxbtn.clicked.connect(self.parent().showproxparamwin)
    self.grid.addWidget(self.proxbtn,gRow,1,1,1)

    self.distbtn = QPushButton('Distal Drive NonLemniscal'+os.linesep+'Thal./Cortical Feedback',self)
    self.distbtn.setIcon(QIcon(lookupresource('distfig')))
    self.distbtn.clicked.connect(self.parent().showdistparamwin)
    self.grid.addWidget(self.distbtn,gRow,2,1,1)

    gRow = 1

    # for schematic dialog box
    self.pixConn = QPixmap(lookupresource('connfig'))
    self.pixConnlbl = ClickLabel(self)
    self.pixConnlbl.setScaledContents(True)
    #self.pixConnlbl.resize(self.pixConnlbl.size())
    self.pixConnlbl.setPixmap(self.pixConn)    
    # self.pixConnlbl.clicked.connect(self.shownetparamwin)
    self.grid.addWidget(self.pixConnlbl,gRow,0,1,1)

    self.pixProx = QPixmap(lookupresource('proxfig'))
    self.pixProxlbl = ClickLabel(self)
    self.pixProxlbl.setScaledContents(True)
    self.pixProxlbl.setPixmap(self.pixProx)
    # self.pixProxlbl.clicked.connect(self.showproxparamwin)
    self.grid.addWidget(self.pixProxlbl,gRow,1,1,1)

    self.pixDist = QPixmap(lookupresource('distfig'))
    self.pixDistlbl = ClickLabel(self)
    self.pixDistlbl.setScaledContents(True)
    self.pixDistlbl.setPixmap(self.pixDist)
    # self.pixDistlbl.clicked.connect(self.showdistparamwin)
    self.grid.addWidget(self.pixDistlbl,gRow,2,1,1)

    self.setLayout(grid)

class BaseParamDialog (QDialog):
  # base widget for specifying params (contains buttons to create other widgets
  def __init__ (self, parent, paramfn, optrun_func):
    super(BaseParamDialog, self).__init__(parent)
    self.proxparamwin = self.distparamwin = self.netparamwin = self.syngainparamwin = None
    self.runparamwin = RunParamDialog(self)
    self.cellparamwin = CellParamDialog(self)
    self.netparamwin = NetworkParamDialog(self)    
    self.syngainparamwin = SynGainParamDialog(self,self.netparamwin)
    self.proxparamwin = OngoingInputParamDialog(self,'Proximal')
    self.distparamwin = OngoingInputParamDialog(self,'Distal')
    self.evparamwin = EvokedInputParamDialog(self,None)
    self.optparamwin = OptEvokedInputParamDialog(self,optrun_func)
    self.poisparamwin = PoissonInputParamDialog(self,None)
    self.tonicparamwin = TonicInputParamDialog(self,None)
    self.lsubwin = [self.runparamwin, self.cellparamwin, self.netparamwin,
                    self.proxparamwin, self.distparamwin, self.evparamwin,
                    self.poisparamwin, self.tonicparamwin, self.optparamwin]
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
      dlg.setfromdin(self.params) # update to values from file
    self.qle.setText(self.params['sim_prefix']) # update simulation name

  def setrunparam (self): bringwintotop(self.runparamwin)
  def setcellparam (self): bringwintotop(self.cellparamwin)
  def setnetparam (self): bringwintotop(self.netparamwin)
  def setsyngainparam (self): bringwintotop(self.syngainparamwin)
  def setproxparam (self): bringwintotop(self.proxparamwin)
  def setdistparam (self): bringwintotop(self.distparamwin)
  def setevparam (self): bringwintotop(self.evparamwin)
  def setpoisparam (self): bringwintotop(self.poisparamwin)
  def settonicparam (self): bringwintotop(self.tonicparamwin)

  def initUI (self):
    grid = QGridLayout()
    grid.setSpacing(10)

    row = 1

    self.lbl = QLabel(self)
    self.lbl.setText('Simulation Name:')
    self.lbl.adjustSize()
    self.lbl.setToolTip('Simulation Name used to save parameter file and simulation data')
    grid.addWidget(self.lbl, row, 0)
    self.qle = QLineEdit(self)
    self.qle.setText(self.params['sim_prefix'])
    grid.addWidget(self.qle, row, 1)
    row+=1

    self.btnrun = QPushButton('Run',self)
    self.btnrun.resize(self.btnrun.sizeHint())
    self.btnrun.setToolTip('Set Run Parameters')
    self.btnrun.clicked.connect(self.setrunparam)
    grid.addWidget(self.btnrun, row, 0, 1, 1)

    self.btncell = QPushButton('Cell',self)
    self.btncell.resize(self.btncell.sizeHint())
    self.btncell.setToolTip('Set Cell (Geometry, Synapses, Biophysics) Parameters')
    self.btncell.clicked.connect(self.setcellparam)
    grid.addWidget(self.btncell, row, 1, 1, 1)
    row+=1

    self.btnnet = QPushButton('Local Network',self)
    self.btnnet.resize(self.btnnet.sizeHint())
    self.btnnet.setToolTip('Set Local Network Parameters')
    self.btnnet.clicked.connect(self.setnetparam)
    grid.addWidget(self.btnnet, row, 0, 1, 1)

    self.btnsyngain = QPushButton('Synaptic Gains',self)
    self.btnsyngain.resize(self.btnsyngain.sizeHint())
    self.btnsyngain.setToolTip('Set Local Network Synaptic Gains')
    self.btnsyngain.clicked.connect(self.setsyngainparam)
    grid.addWidget(self.btnsyngain, row, 1, 1, 1)

    row+=1

    self.btnprox = QPushButton('Rhythmic Proximal Inputs',self)
    self.btnprox.resize(self.btnprox.sizeHint())
    self.btnprox.setToolTip('Set Rhythmic Proximal Inputs')
    self.btnprox.clicked.connect(self.setproxparam)
    grid.addWidget(self.btnprox, row, 0, 1, 2); row+=1

    self.btndist = QPushButton('Rhythmic Distal Inputs',self)
    self.btndist.resize(self.btndist.sizeHint())
    self.btndist.setToolTip('Set Rhythmic Distal Inputs')
    self.btndist.clicked.connect(self.setdistparam)
    grid.addWidget(self.btndist, row, 0, 1, 2)
    row+=1

    self.btnev = QPushButton('Evoked Inputs',self)
    self.btnev.resize(self.btnev.sizeHint())
    self.btnev.setToolTip('Set Evoked Inputs')
    self.btnev.clicked.connect(self.setevparam)
    grid.addWidget(self.btnev, row, 0, 1, 2)
    row+=1

    self.btnpois = QPushButton('Poisson Inputs',self)
    self.btnpois.resize(self.btnpois.sizeHint())
    self.btnpois.setToolTip('Set Poisson Inputs')
    self.btnpois.clicked.connect(self.setpoisparam)
    grid.addWidget(self.btnpois, row, 0, 1, 2)
    row+=1

    self.btntonic = QPushButton('Tonic Inputs',self)
    self.btntonic.resize(self.btntonic.sizeHint())
    self.btntonic.setToolTip('Set Tonic (Current Clamp) Inputs')
    self.btntonic.clicked.connect(self.settonicparam)
    grid.addWidget(self.btntonic, row, 0, 1, 2)
    row+=1

    self.btnsave = QPushButton('Save Parameters To File',self)
    self.btnsave.resize(self.btnsave.sizeHint())
    self.btnsave.setToolTip('Save All Parameters to File (Specified by Simulation Name)')
    self.btnsave.clicked.connect(self.saveparams)
    grid.addWidget(self.btnsave, row, 0, 1, 2)
    row+=1

    self.btnhide = QPushButton('Hide Window',self)
    self.btnhide.resize(self.btnhide.sizeHint())
    self.btnhide.clicked.connect(self.hide)
    self.btnhide.setToolTip('Hide Window')
    grid.addWidget(self.btnhide, row, 0, 1, 2)

    self.setLayout(grid) 
        
    self.setWindowTitle('Set Parameters')    

  def saveparams (self, checkok = True):
    tmpf = os.path.join(get_output_dir(), 'param',
                        self.qle.text() + '.param')
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
      with open(tmpf,'w') as fp:
        fp.write(str(self))

      self.paramfn = tmpf
      data_dir = os.path.join(get_output_dir(), 'data')
      sim_dir = os.path.join(data_dir, self.params['sim_prefix'])
      os.makedirs(sim_dir, exist_ok=True)

    return oktosave

  def updatesaveparams (self, dtest):
    # update parameter values in GUI (so user can see and so GUI will save these param values)
    for win in self.lsubwin: win.setfromdin(dtest)
    # save parameters - do not ask if can over-write the param file
    self.saveparams(checkok = False)

  def __str__ (self):
    s = 'sim_prefix: ' + self.qle.text() + os.linesep
    s += 'expmt_groups: {' + self.qle.text() + '}' + os.linesep
    for win in self.lsubwin: s += str(win)
    return s

class WaitSimDialog (QDialog):
  def __init__ (self, parent):
    super(WaitSimDialog, self).__init__(parent)
    self.initUI()
    self.txt = '' # text for display

  def updatetxt (self,txt):
    self.qtxt.append(txt)

  def initUI (self):
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

  def stopsim (self):
    self.parent().stopsim()
    self.hide()


class HNNGUI (QMainWindow):
  # main HNN GUI class
  def __init__ (self):
    # initialize the main HNN GUI

    super().__init__()   
    sys.excepthook = self.excepthook

    global fontsize

    hnn_root_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))

    self.runningsim = False
    self.runthread = None
    self.fontsize = fontsize
    self.linewidth = plt.rcParams['lines.linewidth'] = 1
    self.markersize = plt.rcParams['lines.markersize'] = 5
    self.dextdata = {} # external data
    self.schemwin = SchematicDialog(self)
    self.m = self.toolbar = None
    paramfn = os.path.join(hnn_root_dir, 'param', 'default.param')
    self.baseparamwin = BaseParamDialog(self, paramfn, self.startoptmodel)
    self.optMode = False
    self.initUI()
    self.helpwin = HelpDialog(self)
    self.erselectdistal = EvokedOrRhythmicDialog(self, True, self.baseparamwin.evparamwin, self.baseparamwin.distparamwin)
    self.erselectprox = EvokedOrRhythmicDialog(self, False, self.baseparamwin.evparamwin, self.baseparamwin.proxparamwin)
    self.waitsimwin = WaitSimDialog(self)
    default_param = os.path.join(get_output_dir(), 'data', 'default')
    first_load = not (os.path.exists(default_param))

    if first_load:
      QMessageBox.information(self, "HNN", "Welcome to HNN! Default parameter file loaded. "
                              "Press 'Run Simulation' to display simulation output")
    else:
      self.statusBar().showMessage("Loaded %s"%default_param)
    # successful initialization, catch all further exceptions

  def excepthook(self, exc_type, exc_value, exc_tb):
    enriched_tb = _add_missing_frames(exc_tb) if exc_tb else exc_tb
    # Note: sys.__excepthook__(...) would not work here.
    # We need to use print_exception(...):
    traceback.print_exception(exc_type, exc_value, enriched_tb)
    msgBox = QMessageBox(self)
    msgBox.information(self, "Exception", "WARNING: an exception occurred! "
                      "Details can be found in the console output. Please "
                      "include this output when opening an issue on GitHub: "
                      "<a href=https://github.com/jonescompneurolab/hnn/issues>"
                      "https://github.com/jonescompneurolab/hnn/issues</a>")


  def redraw (self):
    # redraw simulation & external data
    self.m.plot()
    self.m.draw()

  def changeFontSize (self):
    # bring up window to change font sizes
    global fontsize

    i, ok = QInputDialog.getInt(self, "Set Font Size","Font Size:", plt.rcParams['font.size'], 1, 100, 1)
    if ok:
      self.fontsize = plt.rcParams['font.size'] = fontsize = i
      self.redraw()

  def changeLineWidth (self):
    # bring up window to change line width(s)
    i, ok = QInputDialog.getInt(self, "Set Line Width","Line Width:", plt.rcParams['lines.linewidth'], 1, 20, 1)
    if ok:
      self.linewidth = plt.rcParams['lines.linewidth'] = i
      self.redraw()

  def changeMarkerSize (self):
    # bring up window to change marker size
    i, ok = QInputDialog.getInt(self, "Set Marker Size","Font Size:", self.markersize, 1, 100, 1)
    if ok:
      self.markersize = plt.rcParams['lines.markersize'] = i
      self.redraw()
    
  def selParamFileDialog (self):
    # bring up window to select simulation parameter file

    hnn_root_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))

    qfd = QFileDialog()
    qfd.setHistory([os.path.join(get_output_dir(), 'param'),
                    os.path.join(hnn_root_dir, 'param')])
    fn = qfd.getOpenFileName(self, 'Open param file',
                             os.path.join(hnn_root_dir,'param'),
                             "Param files (*.param)")
    if len(fn) > 0 and fn[0] == '':
      # no file selected in dialog
      return

    tmpfn = os.path.abspath(fn[0])

    try:
      params = read_params(tmpfn)
    except ValueError:
      QMessageBox.information(self, "HNN", "WARNING: could not"
                              "retrieve parameters from %s" %
                              tmpfn)
      return

    self.baseparamwin.paramfn = tmpfn

    # now update the GUI components to reflect the param file selected
    self.baseparamwin.updateDispParam(params)
    self.initSimCanvas() # recreate canvas
    # self.m.plot() # replot data
    self.setWindowTitle(self.baseparamwin.paramfn)

    # store the sim just loaded in simdat's list - is this the desired behavior? or should we first erase prev sims?
    if 'dpl' in ddat:
      # update lsimdat and its current sim index
      updatelsimdat(self.baseparamwin.paramfn, self.baseparamwin.params, ddat['dpl'])

    self.populateSimCB() # populate the combobox

    if len(self.dextdata) > 0:
      self.toggleEnableOptimization(True)

  def loadDataFile (self, fn):
    # load a dipole data file

    try:
      self.dextdata[fn] = np.loadtxt(fn)
    except ValueError:
      # possible that data file is comma delimted instead of whitespace delimted
      try:
        self.dextdata[fn] = np.loadtxt(fn, delimiter=',')
      except ValueError:
        QMessageBox.information(self, "HNN", "WARNING: could not load data file %s" % fn)
        return False
    except IsADirectoryError:
      QMessageBox.information(self, "HNN", "WARNING: could not load data file %s" % fn)
      return False

    ddat['dextdata'] = self.dextdata
    print('Loaded data in ', fn)

    self.m.plot()
    self.m.draw() # make sure new lines show up in plot

    if self.baseparamwin.paramfn:
      self.toggleEnableOptimization(True)
    return True

  def loadDataFileDialog (self):
    # bring up window to select/load external dipole data file
    hnn_root_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))

    qfd = QFileDialog()
    qfd.setHistory([os.path.join(get_output_dir(), 'data'),
                   os.path.join(hnn_root_dir, 'data')])
    fn = qfd.getOpenFileName(self, 'Open data file',
                                    os.path.join(hnn_root_dir,'data'),
                                    "Data files (*.txt)")
    if len(fn) > 0 and fn[0] == '':
      # no file selected in dialog
      return

    self.loadDataFile(os.path.abspath(fn[0])) # use abspath to make sure have right path separators

  def clearDataFile (self):
    # clear external dipole data
    self.m.clearlextdatobj()
    self.dextdata = ddat['dextdata'] = {}
    self.toggleEnableOptimization(False)
    self.m.plot()  # recreate canvas
    self.m.draw()

  def setparams (self):
    # show set parameters dialog window
    if self.baseparamwin:
      for win in self.baseparamwin.lsubwin: bringwintobot(win)
      bringwintotop(self.baseparamwin)

  def showAboutDialog (self):
    # show HNN's about dialog box
    from hnn import __version__
    msgBox = QMessageBox(self)
    msgBox.setTextFormat(Qt.RichText)
    msgBox.setWindowTitle('About')
    msgBox.setText("Human Neocortical Neurosolver (HNN) v" + __version__ + "<br>"+\
                   "<a href=https://hnn.brown.edu>https://hnn.brown.edu</a><br>"+\
                   "<a href=https://github.com/jonescompneurolab/hnn>HNN On Github</a><br>"+\
                   "© 2017-2019 <a href=http://brown.edu>Brown University, Providence, RI</a><br>"+\
                   "<a href=https://github.com/jonescompneurolab/hnn/blob/master/LICENSE>Software License</a>")
    msgBox.setStandardButtons(QMessageBox.Ok)
    msgBox.exec_()

  def showOptWarnDialog (self):
    # TODO : not implemented yet
    msgBox = QMessageBox(self)
    msgBox.setTextFormat(Qt.RichText)
    msgBox.setWindowTitle('Warning')
    msgBox.setText("")
    msgBox.setStandardButtons(QMessageBox.Ok)
    msgBox.exec_()

  def showHelpDialog (self):
    # show the help dialog box
    bringwintotop(self.helpwin)

  def showSomaVPlot (self): 
    # start the somatic voltage visualization process (separate window)
    if not float(self.baseparamwin.runparamwin.getval('save_vsoma')):
      smsg='In order to view somatic voltages you must first rerun the simulation with saving somatic voltages. To do so from the main GUI, click on Set Parameters -> Run -> Analysis -> Save Somatic Voltages, enter a 1 and then rerun the simulation.'
      msg = QMessageBox()
      msg.setIcon(QMessageBox.Information)
      msg.setText(smsg)
      msg.setWindowTitle('Rerun simulation')
      msg.setStandardButtons(QMessageBox.Ok)      
      msg.exec_()
    else:
      outdir = os.path.join(get_output_dir(), 'data', self.baseparamwin.params['sim_prefix'])
      outparamf = os.path.join(outdir,
                               self.baseparamwin.params['sim_prefix'] +
                               '.param')
      lcmd = [getPyComm(), 'visvolt.py',outparamf]
      Popen(lcmd) # nonblocking

  def showPSDPlot (self):
    # start the PSD visualization process (separate window)
    outdir = os.path.join(get_output_dir(), 'data', self.baseparamwin.params['sim_prefix'])
    outparamf = os.path.join(outdir,
                             self.baseparamwin.params['sim_prefix'] +
                             '.param')
    lcmd = [getPyComm(), 'vispsd.py',outparamf]
    Popen(lcmd) # nonblocking

  def showSpecPlot (self):
    # start the spectrogram visualization process (separate window)
    outdir = os.path.join(get_output_dir(), 'data', self.baseparamwin.params['sim_prefix'])
    outparamf = os.path.join(outdir,
                             self.baseparamwin.params['sim_prefix'] +
                             '.param')
    lcmd = [getPyComm(), 'visspec.py',outparamf]
    Popen(lcmd) # nonblocking

  def showRasterPlot (self):
    # start the raster plot visualization process (separate window)
    global drawindivrast

    outdir = os.path.join(get_output_dir(), 'data', self.baseparamwin.params['sim_prefix'])
    spikefile = os.path.join(outdir,'spk.txt')
    if os.path.isfile(spikefile):
      outparamf = os.path.join(outdir,
                               self.baseparamwin.params['sim_prefix'] +
                               '.param')
      lcmd = [getPyComm(), 'visrast.py',outparamf,spikefile]
    else:
      QMessageBox.information(self, "HNN", "WARNING: no spiking data at %s" % spikefile)
      return

    if drawindivrast:
      lcmd.append('indiv')
    Popen(lcmd) # nonblocking

  def showDipolePlot (self):
    # start the dipole visualization process (separate window)

    outdir = os.path.join(get_output_dir(), 'data', self.baseparamwin.params['sim_prefix'])
    dipole_file = os.path.join(outdir,'dpl.txt')
    if os.path.isfile(dipole_file):
      outparamf = os.path.join(outdir,
                               self.baseparamwin.params['sim_prefix'] +
                               '.param')
      lcmd = [getPyComm(), 'visdipole.py',outparamf,dipole_file]
    else:
      QMessageBox.information(self, "HNN", "WARNING: no dipole data at %s" % dipole_file)
      return

    Popen(lcmd) # nonblocking    

  def showwaitsimwin (self):
    # show the wait sim window (has simulation log)
    bringwintotop(self.waitsimwin)

  def togAvgDpl (self):
    # toggle drawing of the average (across trials) dipole
    global drawavgdpl

    drawavgdpl = not drawavgdpl
    self.m.plot()
    self.m.draw()

  def hidesubwin (self):
    # hide GUI's sub windows
    self.baseparamwin.hide()
    self.schemwin.hide()
    self.baseparamwin.syngainparamwin.hide()
    for win in self.baseparamwin.lsubwin: win.hide()
    self.activateWindow()

  def distribsubwin (self):
    # distribute GUI's sub-windows on screen
    sw,sh = getscreengeom()
    lwin = [win for win in self.baseparamwin.lsubwin if win.isVisible()]
    if self.baseparamwin.isVisible(): lwin.insert(0,self.baseparamwin)
    if self.schemwin.isVisible(): lwin.insert(0,self.schemwin)
    if self.baseparamwin.syngainparamwin.isVisible(): lwin.append(self.baseparamwin.syngainparamwin)
    curx,cury,maxh=0,0,0
    for win in lwin: 
      win.move(curx, cury)
      curx += win.width()
      maxh = max(maxh,win.height())
      if curx >= sw: 
        curx = 0
        cury += maxh
        maxh = win.height()
      if cury >= sh: cury = cury = 0

  def updateDatCanv(self, params):
    # update the simulation data and canvas
    try:
      getinputfiles(self.baseparamwin.paramfn) # reset input data - if already exists
    except:
      pass

    # now update the GUI components to reflect the param file selected
    self.baseparamwin.updateDispParam(params)
    self.initSimCanvas() # recreate canvas
    self.setWindowTitle(self.baseparamwin.paramfn)

  def updateSelectedSim(self, sim_idx):
    """Update the sim shown in the ComboBox and update globals"""
    # update globals
    global lsimidx

    lsimidx = sim_idx
    paramfn = lsimdat[sim_idx]['paramfn']

    try:
      params = read_params(paramfn)
    except ValueError:
      QMessageBox.information(self, "HNN", "WARNING: could not"
                              "retrieve parameters from %s" %
                              paramfn)
      return

    self.baseparamwin.paramfn = paramfn

    # update GUI
    self.updateDatCanv(params)
    self.cbsim.setCurrentIndex(lsimidx)

  def removeSim(self):
    """Remove the currently selected simulation"""
    global lsimidx

    cidx = self.cbsim.currentIndex()
    self.cbsim.removeItem(cidx)
    del lsimdat[cidx]

    # go to last entry
    new_simidx = self.cbsim.count() - 1
    if new_simidx < 0:
      lsimidx = 0
      self.clearSimulations()
    else:
      self.updateSelectedSim(new_simidx)

  def prevSim(self):
    """Go to previous simulation"""
    global lsimidx

    new_simidx = self.cbsim.currentIndex() - 1
    if new_simidx < 0:
      print("There is no previous simulation")
      return
    else:
      self.updateSelectedSim(new_simidx)

  def nextSim (self):
    # go to next simulation

    if self.cbsim.currentIndex() + 2 > self.cbsim.count():
      print("There is no next simulation")
      return
    else:
      new_simidx = self.cbsim.currentIndex() + 1
      self.updateSelectedSim(new_simidx)

  def clearSimulationData (self):
    global lsimidx, ddat, lsimdat

    # clear the simulation data
    self.baseparamwin.params = None
    self.baseparamwin.paramfn = None
    ddat = {} # clear data in simdat.ddat
    lsimdat = []
    lsimidx = 0
    self.populateSimCB() # un-populate the combobox
    self.toggleEnableOptimization(False)


  def clearSimulations (self):
    # clear all simulation data and erase simulations from canvas (does not clear external data)
    self.clearSimulationData()
    self.initSimCanvas() # recreate canvas
    self.m.draw()
    self.setWindowTitle('')

  def clearCanvas (self):
    # clear all simulation & external data and erase everything from the canvas
    self.clearSimulationData()
    self.m.clearlextdatobj() # clear the external data
    self.dextdata = ddat['dextdata'] = {}
    self.initSimCanvas() # recreate canvas
    self.m.draw()
    self.setWindowTitle('')

  def initMenu (self):
    # initialize the GUI's menu
    exitAction = QAction(QIcon.fromTheme('exit'), 'Exit', self)        
    exitAction.setShortcut('Ctrl+Q')
    exitAction.setStatusTip('Exit HNN application')
    exitAction.triggered.connect(qApp.quit)

    selParamFile = QAction(QIcon.fromTheme('open'), 'Load parameter file', self)
    selParamFile.setShortcut('Ctrl+P')
    selParamFile.setStatusTip('Load simulation parameter (.param) file')
    selParamFile.triggered.connect(self.selParamFileDialog)

    clearCanv = QAction('Clear canvas', self)
    clearCanv.setShortcut('Ctrl+X')
    clearCanv.setStatusTip('Clear canvas (simulation+data)')
    clearCanv.triggered.connect(self.clearCanvas)

    clearSims = QAction('Clear simulation(s)', self)
    #clearSims.setShortcut('Ctrl+X')
    clearSims.setStatusTip('Clear simulation(s)')
    clearSims.triggered.connect(self.clearSimulations)

    loadDataFile = QAction(QIcon.fromTheme('open'), 'Load data file', self)
    loadDataFile.setShortcut('Ctrl+D')
    loadDataFile.setStatusTip('Load (dipole) data file')
    loadDataFile.triggered.connect(self.loadDataFileDialog)

    clearDataFileAct = QAction(QIcon.fromTheme('close'), 'Clear data file(s)', self)
    clearDataFileAct.setShortcut('Ctrl+C')
    clearDataFileAct.setStatusTip('Clear (dipole) data file(s)')
    clearDataFileAct.triggered.connect(self.clearDataFile)

    runSimAct = QAction('Run simulation', self)
    runSimAct.setShortcut('Ctrl+S')
    runSimAct.setStatusTip('Run simulation')
    runSimAct.triggered.connect(self.controlsim)

    self.menubar = self.menuBar()
    fileMenu = self.menubar.addMenu('&File')
    self.menubar.setNativeMenuBar(False)
    fileMenu.addAction(selParamFile)
    fileMenu.addSeparator()
    fileMenu.addAction(loadDataFile)
    fileMenu.addAction(clearDataFileAct)
    fileMenu.addSeparator()
    fileMenu.addAction(exitAction)

    # part of edit menu for changing drawing properties (line thickness, font size, toggle avg dipole drawing)
    editMenu = self.menubar.addMenu('&Edit')
    viewAvgDplAction = QAction('Toggle Average Dipole Drawing',self)
    viewAvgDplAction.setStatusTip('Toggle Average Dipole Drawing')
    viewAvgDplAction.triggered.connect(self.togAvgDpl)
    editMenu.addAction(viewAvgDplAction)
    changeFontSizeAction = QAction('Change Font Size',self)
    changeFontSizeAction.setStatusTip('Change Font Size.')
    changeFontSizeAction.triggered.connect(self.changeFontSize)
    editMenu.addAction(changeFontSizeAction)
    changeLineWidthAction = QAction('Change Line Width',self)
    changeLineWidthAction.setStatusTip('Change Line Width.')
    changeLineWidthAction.triggered.connect(self.changeLineWidth)
    editMenu.addAction(changeLineWidthAction)
    changeMarkerSizeAction = QAction('Change Marker Size',self)
    changeMarkerSizeAction.setStatusTip('Change Marker Size.')
    changeMarkerSizeAction.triggered.connect(self.changeMarkerSize)
    editMenu.addAction(changeMarkerSizeAction)    
    editMenu.addSeparator()
    editMenu.addAction(clearSims)
    clearDataFileAct2 = QAction(QIcon.fromTheme('close'), 'Clear data file(s)', self) # need new act to avoid DBus warning
    clearDataFileAct2.setStatusTip('Clear (dipole) data file(s)')
    clearDataFileAct2.triggered.connect(self.clearDataFile)
    editMenu.addAction(clearDataFileAct2)
    editMenu.addAction(clearCanv)
    
    # view menu - to view drawing/visualizations
    viewMenu = self.menubar.addMenu('&View')
    self.viewDipoleAction = QAction('View Simulation Dipoles',self)
    self.viewDipoleAction.setStatusTip('View Simulation Dipoles')
    self.viewDipoleAction.triggered.connect(self.showDipolePlot)
    viewMenu.addAction(self.viewDipoleAction)
    self.viewRasterAction = QAction('View Simulation Spiking Activity',self)
    self.viewRasterAction.setStatusTip('View Simulation Raster Plot')
    self.viewRasterAction.triggered.connect(self.showRasterPlot)
    viewMenu.addAction(self.viewRasterAction)
    self.viewPSDAction = QAction('View PSD',self)
    self.viewPSDAction.setStatusTip('View PSD')
    self.viewPSDAction.triggered.connect(self.showPSDPlot)
    viewMenu.addAction(self.viewPSDAction)

    self.viewSomaVAction = QAction('View Somatic Voltage',self)
    self.viewSomaVAction.setStatusTip('View Somatic Voltage')
    self.viewSomaVAction.triggered.connect(self.showSomaVPlot)
    viewMenu.addAction(self.viewSomaVAction)

    self.viewSpecAction = QAction('View Spectrograms',self)
    self.viewSpecAction.setStatusTip('View Spectrograms/Dipoles from Experimental Data')
    self.viewSpecAction.triggered.connect(self.showSpecPlot)
    viewMenu.addAction(self.viewSpecAction)

    viewMenu.addSeparator()
    viewSchemAction = QAction('View Model Schematics',self)
    viewSchemAction.setStatusTip('View Model Schematics')
    viewSchemAction.triggered.connect(self.showschematics)
    viewMenu.addAction(viewSchemAction)
    viewSimLogAction = QAction('View Simulation Log',self)
    viewSimLogAction.setStatusTip('View Detailed Simulation Log')
    viewSimLogAction.triggered.connect(self.showwaitsimwin)
    viewMenu.addAction(viewSimLogAction)
    viewMenu.addSeparator()    
    distributeWindowsAction = QAction('Distribute Windows',self)
    distributeWindowsAction.setStatusTip('Distribute Parameter Windows Across Screen.')
    distributeWindowsAction.triggered.connect(self.distribsubwin)
    viewMenu.addAction(distributeWindowsAction)
    hideWindowsAction = QAction('Hide Windows',self)
    hideWindowsAction.setStatusTip('Hide Parameter Windows.')
    hideWindowsAction.triggered.connect(self.hidesubwin)
    hideWindowsAction.setShortcut('Ctrl+H')
    viewMenu.addAction(hideWindowsAction)

    simMenu = self.menubar.addMenu('&Simulation')
    setParmAct = QAction('Set Parameters',self)
    setParmAct.setStatusTip('Set Simulation Parameters')
    setParmAct.triggered.connect(self.setparams)
    simMenu.addAction(setParmAct)
    simMenu.addAction(runSimAct)    
    setOptParamAct = QAction('Configure Optimization', self)
    setOptParamAct.setShortcut('Ctrl+O')
    setOptParamAct.setStatusTip('Set parameters for evoked input optimization')
    setOptParamAct.triggered.connect(self.showoptparamwin)
    simMenu.addAction(setOptParamAct)
    self.toggleEnableOptimization(False)
    prevSimAct = QAction('Go to Previous Simulation',self)
    prevSimAct.setShortcut('Ctrl+Z')
    prevSimAct.setStatusTip('Go Back to Previous Simulation')
    prevSimAct.triggered.connect(self.prevSim)
    simMenu.addAction(prevSimAct)
    nextSimAct = QAction('Go to Next Simulation',self)
    nextSimAct.setShortcut('Ctrl+Y')
    nextSimAct.setStatusTip('Go Forward to Next Simulation')
    nextSimAct.triggered.connect(self.nextSim)
    simMenu.addAction(nextSimAct)
    clearSims2 = QAction('Clear simulation(s)', self) # need another QAction to avoid DBus warning
    clearSims2.setStatusTip('Clear simulation(s)')
    clearSims2.triggered.connect(self.clearSimulations)
    simMenu.addAction(clearSims2)

    aboutMenu = self.menubar.addMenu('&About')
    aboutAction = QAction('About HNN',self)
    aboutAction.setStatusTip('About HNN')
    aboutAction.triggered.connect(self.showAboutDialog)
    aboutMenu.addAction(aboutAction)
    helpAction = QAction('Help',self)
    helpAction.setStatusTip('Help on how to use HNN (parameters).')
    helpAction.triggered.connect(self.showHelpDialog)
    #aboutMenu.addAction(helpAction)

  def toggleEnableOptimization (self, toEnable):
    for menu in self.menubar.findChildren(QMenu):
      if menu.title() == '&Simulation':
        for item in menu.actions():
          if item.text() == 'Configure Optimization':
            item.setEnabled(toEnable)
            break
        break

  def addButtons (self, gRow):
    self.pbtn = pbtn = QPushButton('Set Parameters', self)
    pbtn.setToolTip('Set Parameters')
    pbtn.resize(pbtn.sizeHint())
    pbtn.clicked.connect(self.setparams)
    self.grid.addWidget(self.pbtn, gRow, 0, 1, 3)

    self.pfbtn = pfbtn = QPushButton('Set Parameters From File', self)
    pfbtn.setToolTip('Set Parameters From File')
    pfbtn.resize(pfbtn.sizeHint())
    pfbtn.clicked.connect(self.selParamFileDialog)
    self.grid.addWidget(self.pfbtn, gRow, 3, 1, 3)

    self.btnsim = btn = QPushButton('Run Simulation', self)
    btn.setToolTip('Run Simulation')
    btn.resize(btn.sizeHint())
    btn.clicked.connect(self.controlsim)
    self.grid.addWidget(self.btnsim, gRow, 6, 1, 3)

    self.qbtn = qbtn = QPushButton('Quit', self)
    qbtn.clicked.connect(QApplication.exit)
    qbtn.resize(qbtn.sizeHint())
    self.grid.addWidget(self.qbtn, gRow, 9, 1, 3)

  def shownetparamwin (self): bringwintotop(self.baseparamwin.netparamwin)
  def showoptparamwin (self): bringwintotop(self.baseparamwin.optparamwin)
  def showdistparamwin (self): bringwintotop(self.erselectdistal)
  def showproxparamwin (self): bringwintotop(self.erselectprox)
  def showschematics (self): bringwintotop(self.schemwin)

  def addParamImageButtons (self,gRow):
    # add parameter image buttons to the GUI

    self.locbtn = QPushButton('Local Network'+os.linesep+'Connections',self)
    self.locbtn.setIcon(QIcon(lookupresource('connfig')))
    self.locbtn.clicked.connect(self.shownetparamwin)
    self.grid.addWidget(self.locbtn,gRow,0,1,4)

    self.proxbtn = QPushButton('Proximal Drive'+os.linesep+'Thalamus',self)
    self.proxbtn.setIcon(QIcon(lookupresource('proxfig')))
    self.proxbtn.clicked.connect(self.showproxparamwin)
    self.grid.addWidget(self.proxbtn,gRow,4,1,4)

    self.distbtn = QPushButton('Distal Drive Non3Lemniscal'+os.linesep+'Thal./Cortical Feedback',self)
    self.distbtn.setIcon(QIcon(lookupresource('distfig')))
    self.distbtn.clicked.connect(self.showdistparamwin)
    self.grid.addWidget(self.distbtn,gRow,8,1,4)

    gRow += 1

  def initUI (self):
    # initialize the user interface (UI)

    self.initMenu()
    self.statusBar()

    setscalegeomcenter(self, 1500, 1300) # start GUI in center of screenm, scale based on screen w x h 

    # move param windows to be offset from main GUI
    new_x = max(0, self.x() - 300)
    new_y = max(0, self.y() + 100)
    self.baseparamwin.move(new_x, new_y)
    self.baseparamwin.evparamwin.move(new_x+50, new_y+50)
    self.baseparamwin.optparamwin.move(new_x+100, new_y+100)
    self.setWindowTitle(self.baseparamwin.paramfn)
    QToolTip.setFont(QFont('SansSerif', 10))        

    self.grid = grid = QGridLayout()
    #grid.setSpacing(10)

    gRow = 0

    self.addButtons(gRow)

    gRow += 1

    self.initSimCanvas(gRow=gRow, reInit=False)
    gRow += 2

    # store any sim just loaded in simdat's list - is this the desired behavior? or should we start empty?
    if 'dpl' in ddat:
      # update lsimdat and its current sim index
      updatelsimdat(self.baseparamwin.paramfn,
                           self.baseparamwin.params,
                           ddat['dpl'])

    self.cbsim = QComboBox(self)
    self.populateSimCB() # populate the combobox
    self.cbsim.activated[str].connect(self.onActivateSimCB)
    self.grid.addWidget(self.cbsim, gRow, 0, 1, 8)#, 1, 3)
    self.btnrmsim = QPushButton('Remove Simulation',self)
    self.btnrmsim.resize(self.btnrmsim.sizeHint())
    self.btnrmsim.clicked.connect(self.removeSim)
    self.btnrmsim.setToolTip('Remove Currently Selected Simulation')
    self.grid.addWidget(self.btnrmsim, gRow, 8, 1, 4)

    gRow += 1
    self.addParamImageButtons(gRow)

    # need a separate widget to put grid on
    widget = QWidget(self)
    widget.setLayout(grid)
    self.setCentralWidget(widget)

    self.p = ParamSignal()
    self.p.psig.connect(self.baseparamwin.updateDispParam)

    self.d = DoneSignal()
    self.d.finishSim.connect(self.done)

    try: self.setWindowIcon(QIcon(os.path.join('res','icon.png')))
    except: pass

    self.schemwin.show() # so it's underneath main window

    self.show()

  def onActivateSimCB (self, paramfn):
    # load simulation when activating simulation combobox

    global lsimidx
    if self.cbsim.currentIndex() != lsimidx:
      try:
        params = read_params(paramfn)
      except ValueError:
        QMessageBox.information(self, "HNN", "WARNING: could not"
                                "retrieve parameters from %s" %
                                paramfn)
        return
      self.baseparamwin.paramfn = paramfn

      lsimidx = self.cbsim.currentIndex()
      self.updateDatCanv(params)

  def populateSimCB (self):
    # populate the simulation combobox
    self.cbsim.clear()
    for sim in lsimdat:
      sim_paramfn = sim['paramfn']
      self.cbsim.addItem(sim_paramfn)
    self.cbsim.setCurrentIndex(lsimidx)

  def initSimCanvas (self,recalcErr=True,optMode=False,gRow=1,reInit=True):
    # initialize the simulation canvas, loading any required data
    gCol = 0

    if reInit == True:
      self.grid.itemAtPosition(gRow, gCol).widget().deleteLater()
      self.grid.itemAtPosition(gRow + 1, gCol).widget().deleteLater()

    # if just initialized or after clearSimulationData
    if self.baseparamwin.paramfn and self.baseparamwin.params is None:
      try:
        self.baseparamwin.params = read_params(self.baseparamwin.paramfn)
      except ValueError:
        QMessageBox.information(self, "HNN", "WARNING: could not"
                                "retrieve parameters from %s" %
                                self.baseparamwin.paramfn)
        return

    self.m = SIMCanvas(self.baseparamwin.params, parent = self, width=10, height=1, dpi=getmplDPI(), optMode=optMode)
    # this is the Navigation widget
    # it takes the Canvas widget and a parent
    self.toolbar = NavigationToolbar2QT(self.m, self)
    gWidth = 12
    self.grid.addWidget(self.toolbar, gRow, gCol, 1, gWidth)
    self.grid.addWidget(self.m, gRow + 1, gCol, 1, gWidth)
    if len(self.dextdata.keys()) > 0:
      ddat['dextdata'] = self.dextdata
      self.m.plot(recalcErr)
      self.m.draw()

  def setcursors (self,cursor):
    # set cursors of self and children
    self.setCursor(cursor)
    self.update()
    kids = self.children()
    kids.append(self.m) # matplotlib simcanvas
    for k in kids:
      try:
        k.setCursor(cursor)
        k.update()
      except:
        pass

  def startoptmodel (self):
    # start model optimization
    if self.runningsim:
      self.stopsim() # stop sim works but leaves subproc as zombie until this main GUI thread exits
    else:
      self.optMode = True
      try:
        self.optmodel(self.baseparamwin.runparamwin.getntrial(),self.baseparamwin.runparamwin.getncore())
      except RuntimeError:
        print("ERR: Optimization aborted")

  def controlsim (self):
    # control the simulation
    if self.runningsim:
      self.stopsim() # stop sim works but leaves subproc as zombie until this main GUI thread exits
    else:
      self.optMode = False
      self.startsim(self.baseparamwin.runparamwin.getntrial(),self.baseparamwin.runparamwin.getncore())

  def stopsim (self):
    # stop the simulation
    if self.runningsim:
      self.waitsimwin.hide()
      print('Terminating simulation. . .')
      self.statusBar().showMessage('Terminating sim. . .')
      self.runningsim = False
      self.runthread.stop() # killed = True # terminate()
      self.btnsim.setText("Run Simulation")
      self.qbtn.setEnabled(True)
      self.statusBar().showMessage('')
      self.setcursors(Qt.ArrowCursor)

  def optmodel (self, ntrial, ncore):
    # make sure params saved and ok to run
    if not self.baseparamwin.saveparams():
      return

    self.baseparamwin.optparamwin.btnreset.setEnabled(False)
    self.baseparamwin.optparamwin.btnrunop.setText('Stop Optimization')
    self.baseparamwin.optparamwin.btnrunop.clicked.disconnect()
    self.baseparamwin.optparamwin.btnrunop.clicked.connect(self.stopsim)

    # optimize the model
    self.setcursors(Qt.WaitCursor)
    print('Starting model optimization. . .')

    self.runningsim = True

    self.statusBar().showMessage("Optimizing model. . .")

    self.runthread = RunSimThread(self.p, self.d, ntrial, ncore, self.waitsimwin, self.baseparamwin.params, opt=True, baseparamwin=self.baseparamwin, mainwin=self)

    # We have all the events we need connected we can start the thread
    self.runthread.start()
    # At this point we want to allow user to stop/terminate the thread
    # so we enable that button
    self.btnsim.setText("Stop Optimization") 
    self.qbtn.setEnabled(False)
    bringwintotop(self.waitsimwin)

  def startsim (self, ntrial, ncore):
    # start the simulation
    if not self.baseparamwin.saveparams(self.baseparamwin.paramfn):
      return # make sure params saved and ok to run

    # reread the params to get anything new
    try:
      params = read_params(self.baseparamwin.paramfn)
    except ValueError:
      QMessageBox.information(self, "HNN", "WARNING: could not"
                              "retrieve parameters from %s" %
                              self.baseparamwin.paramfn)
      return

    self.setcursors(Qt.WaitCursor)

    print('Starting simulation (%d cores). . .'%ncore)
    self.runningsim = True

    self.statusBar().showMessage("Running simulation. . .")

    self.runthread = RunSimThread(self.p, self.d, ntrial, ncore,
                                  self.waitsimwin, params, opt=False,
                                  baseparamwin=None, mainwin=None)

    # We have all the events we need connected we can start the thread
    self.runthread.start()
    # At this point we want to allow user to stop/terminate the thread
    # so we enable that button
    self.btnsim.setText("Stop Simulation") # setEnabled(False)
    # We don't want to enable user to start another thread while this one is
    # running so we disable the start button.
    # self.btn_start.setEnabled(False)
    self.qbtn.setEnabled(False)

    bringwintotop(self.waitsimwin)

  def done (self, optMode, except_msg):
    # called when the simulation completes running
    self.runningsim = False
    self.waitsimwin.hide()
    self.statusBar().showMessage("")
    self.btnsim.setText("Run Simulation")
    self.qbtn.setEnabled(True)
    self.initSimCanvas(optMode=optMode) # recreate canvas (plots too) to avoid incorrect axes
    # self.m.plot()
    self.setcursors(Qt.ArrowCursor)

    failed=False
    if len(except_msg) > 0:
      failed = True
      msg = "%s: Failed " % except_msg
    else:
      msg = "Finished "

    if optMode:
      msg += "running optimization "
      self.baseparamwin.optparamwin.btnrunop.setText('Prepare for Another Optimization')
      self.baseparamwin.optparamwin.btnrunop.clicked.disconnect()
      self.baseparamwin.optparamwin.btnrunop.clicked.connect(self.baseparamwin.optparamwin.prepareOptimization)
    else:
      msg += "running sim "

    if failed:
      QMessageBox.critical(self, "Failed!", msg + "using " + self.baseparamwin.paramfn + '. Check simulation log or console for error messages')
    else:
      data_dir = os.path.join(get_output_dir(), 'data')
      sim_dir = os.path.join(data_dir, self.baseparamwin.params['sim_prefix'])
      QMessageBox.information(self, "Done!", msg + "using " + self.baseparamwin.paramfn + '. Saved data/figures in: ' + sim_dir)
    self.setWindowTitle(self.baseparamwin.paramfn)
    self.populateSimCB() # populate the combobox

if __name__ == '__main__':    
  app = QApplication(sys.argv)
  ex = HNNGUI()
  sys.exit(app.exec_())  
