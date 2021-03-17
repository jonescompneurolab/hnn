"""Classes for creating the main HNN GUI"""

# Authors: Sam Neymotin <samnemo@gmail.com>
#          Blake Caldwell <blake_caldwell@brown.edu>
#          Shane Lee

# Python builtins
import sys
import os
import multiprocessing
import numpy as np
import traceback
from subprocess import Popen
from collections import namedtuple
from copy import deepcopy
from psutil import cpu_count

# External libraries
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication
from PyQt5.QtWidgets import QFileDialog, QComboBox
from PyQt5.QtWidgets import QToolTip, QPushButton, QGridLayout, QInputDialog
from PyQt5.QtWidgets import QMenu, QMessageBox, QWidget, QLayout
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import pyqtSignal, QObject, Qt

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
import matplotlib.pyplot as plt

from hnn_core import read_params
from hnn_core.dipole import average_dipoles

# HNN modules
from .qt_dialog import (BaseParamDialog, EvokedOrRhythmicDialog,
                        WaitSimDialog, HelpDialog, SchematicDialog,
                        bringwintotop)
from .paramrw import (usingOngoingInputs, get_output_dir,
                      write_gids_param, get_fname)
from .simdata import SimData
from .qt_canvas import SIMCanvas
from .run import RunSimThread
from .qt_lib import getmplDPI, getscreengeom, lookupresource, setscalegeomcenter
from .specfn import spec_dpl_kernel, save_spec_data
from .DataViewGUI import DataViewGUI
from .visdipole import DipoleCanvas
from .visvolt import VoltViewGUI, VoltCanvas
from .visspec import SpecViewGUI, SpecCanvas
from .visrast import SpikeViewGUI, SpikeCanvas
from .vispsd import PSDViewGUI, PSDCanvas

# TODO: These globals should be made configurable via the GUI
drawavgdpl = 0
fontsize = plt.rcParams['font.size'] = 10


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

def bringwintobot(win):
    # win.show()
    # win.lower()
    win.hide()


class HNNGUI (QMainWindow):
    # main HNN GUI class
    def __init__ (self):
      # initialize the main HNN GUI

      super().__init__()
      sys.excepthook = self.excepthook

      global fontsize

      hnn_root_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))

      self.defncore = _get_defncore()
      self.runningsim = False
      self.runthread = None
      self.fontsize = fontsize
      self.linewidth = plt.rcParams['lines.linewidth'] = 1
      self.markersize = plt.rcParams['lines.markersize'] = 5
      self.schemwin = SchematicDialog(self)
      self.sim_canvas = self.toolbar = None
      paramfn = os.path.join(hnn_root_dir, 'param', 'default.param')
      self.baseparamwin = BaseParamDialog(self, paramfn, self.startoptmodel)
      self.is_optimization = False
      self.sim_data = SimData()
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


    def redraw(self):
      # redraw simulation & external data
      self.sim_canvas.plot()
      self.sim_canvas.draw()

    def changeFontSize(self):
      # bring up window to change font sizes
      global fontsize

      i, ok = QInputDialog.getInt(self, "Set Font Size","Font Size:", plt.rcParams['font.size'], 1, 100, 1)
      if ok:
        self.fontsize = plt.rcParams['font.size'] = fontsize = i
        self.redraw()

    def changeLineWidth(self):
      # bring up window to change line width(s)
      i, ok = QInputDialog.getInt(self, "Set Line Width","Line Width:", plt.rcParams['lines.linewidth'], 1, 20, 1)
      if ok:
        self.linewidth = plt.rcParams['lines.linewidth'] = i
        self.redraw()

    def changeMarkerSize(self):
      # bring up window to change marker size
      i, ok = QInputDialog.getInt(self, "Set Marker Size","Font Size:", self.markersize, 1, 100, 1)
      if ok:
        self.markersize = plt.rcParams['lines.markersize'] = i
        self.redraw()

    def selParamFileDialog(self):
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

      # check that valid number of trials was given
      if 'N_trials' not in params or params['N_trials'] == 0:
          print("Warning: invalid configured number of trials."
                " Setting 'N_trials' to 1.")
          params['N_trials'] = 1

      # Now update GUI components
      self.baseparamwin.paramfn = tmpfn

      # now update the GUI components to reflect the param file selected
      self.baseparamwin.updateDispParam(params)
      self.setWindowTitle(self.baseparamwin.paramfn)

      self.initSimCanvas()  # recreate canvas

      # check if param file exists in combo box already
      cb_index = self.cbsim.findText(self.baseparamwin.paramfn)
      self.populateSimCB(cb_index)  # populate the combobox

      if self.sim_data.get_exp_data_size() > 0:
        self.toggleEnableOptimization(True)

    def loadDataFile(self, fn):
      # load a dipole data file

      extdata = None
      try:
        extdata = np.loadtxt(fn)
      except ValueError:
        # possible that data file is comma delimted instead of whitespace delimted
        try:
          extdata = np.loadtxt(fn, delimiter=',')
        except ValueError:
          QMessageBox.information(self, "HNN", "WARNING: could not load data file %s" % fn)
          return False
      except IsADirectoryError:
        QMessageBox.information(self, "HNN", "WARNING: could not load data file %s" % fn)
        return False

      self.sim_data.update_exp_data(fn, extdata)
      print('Loaded data in ', fn)

      self.sim_canvas.plot()
      self.sim_canvas.draw() # make sure new lines show up in plot

      if self.baseparamwin.paramfn:
        self.toggleEnableOptimization(True)
      return True

    def loadDataFileDialog(self):
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

    def clearDataFile(self):
      # clear external dipole data
      self.sim_canvas.clearlextdatobj()
      self.sim_data.clear_exp_data()
      self.toggleEnableOptimization(False)
      self.sim_canvas.plot()  # recreate canvas
      self.sim_canvas.draw()

    def setparams(self):
      # show set parameters dialog window
      if self.baseparamwin:
        for win in self.baseparamwin.lsubwin: bringwintobot(win)
        bringwintotop(self.baseparamwin)

    def showAboutDialog(self):
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

    def showOptWarnDialog(self):
      # TODO : not implemented yet
      msgBox = QMessageBox(self)
      msgBox.setTextFormat(Qt.RichText)
      msgBox.setWindowTitle('Warning')
      msgBox.setText("")
      msgBox.setStandardButtons(QMessageBox.Ok)
      msgBox.exec_()

    def showHelpDialog(self):
      # show the help dialog box
      bringwintotop(self.helpwin)

    def show_plot(self, plot_type):
        paramfn = self.baseparamwin.paramfn
        if paramfn is None:
            return
        if paramfn in self.sim_data._sim_data:
            sim_data = self.sim_data._sim_data[paramfn]['data']
        else:
            sim_data = None

        if plot_type == 'dipole':
            DataViewGUI(DipoleCanvas, self.baseparamwin.params, sim_data,
                        'Dipole Viewer')
        elif plot_type == 'volt':
            VoltViewGUI(VoltCanvas, self.baseparamwin.params, sim_data,
                        'Dipole Viewer')
        elif plot_type == 'PSD':
            PSDViewGUI(PSDCanvas, self.baseparamwin.params, sim_data,
                      'PSD Viewer')
        elif plot_type == 'spec':
            SpecViewGUI(SpecCanvas, self.baseparamwin.params, sim_data,
                        'Spectrogram Viewer')
        elif plot_type == 'spike':
            SpikeViewGUI(SpikeCanvas, self.baseparamwin.params, sim_data,
                         'Spike Viewer')
        else:
          raise ValueError("Unknown plot type")

    def showSomaVPlot(self):
        # start the somatic voltage visualization process (separate window)
        if not float(self.baseparamwin.params['record_vsoma']):
            smsg='In order to view somatic voltages you must first rerun' + \
                 ' the simulation with saving somatic voltages. To do so' + \
                 ' from the main GUI, click on Set Parameters -> Run ->' + \
                 ' Analysis -> Save Somatic Voltages, enter a 1 and then' + \
                 ' rerun the simulation.'
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText(smsg)
            msg.setWindowTitle('Rerun simulation')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        else:
            self.show_plot('volt')

    def showPSDPlot(self):
        self.show_plot('PSD')

    def showSpecPlot(self):
        self.show_plot('spec')

    def showRasterPlot(self):
        self.show_plot('spike')

    def showDipolePlot(self):
        self.show_plot('dipole')

    def showwaitsimwin(self):
      # show the wait sim window (has simulation log)
      bringwintotop(self.waitsimwin)

    def togAvgDpl(self):
      # toggle drawing of the average (across trials) dipole
      global drawavgdpl

      drawavgdpl = not drawavgdpl
      self.sim_canvas.plot()
      self.sim_canvas.draw()

    def hidesubwin(self):
      # hide GUI's sub windows
      self.baseparamwin.hide()
      self.schemwin.hide()
      self.baseparamwin.syngainparamwin.hide()
      for win in self.baseparamwin.lsubwin: win.hide()
      self.activateWindow()

    def distribsubwin(self):
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
      # now update the GUI components to reflect the param file selected
      self.baseparamwin.updateDispParam(params)
      self.initSimCanvas() # recreate canvas
      self.setWindowTitle(self.baseparamwin.paramfn)

    def updateSelectedSim(self, sim_idx):
      """Update the sim shown in the ComboBox"""

      paramfn = self.cbsim.itemText(sim_idx)
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
      self.cbsim.setCurrentIndex(sim_idx)

    def removeSim(self):
      """Remove the currently selected simulation"""

      sim_idx = self.cbsim.currentIndex()
      paramfn = self.cbsim.itemText(sim_idx)
      if not paramfn == '':
        self.sim_data.remove_sim_by_fn(paramfn)

      self.cbsim.removeItem(sim_idx)

      # go to last entry
      new_simidx = self.cbsim.count() - 1
      if new_simidx < 0:
        self.clearSimulations()
      else:
        self.updateSelectedSim(new_simidx)

    def prevSim(self):
      """Go to previous simulation"""

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

      # clear the simulation data
      self.baseparamwin.params = None
      self.baseparamwin.paramfn = None

      self.sim_data.clear_sim_data()
      self.cbsim.clear() # un-populate the combobox
      self.toggleEnableOptimization(False)


    def clearSimulations (self):
      # clear all simulation data and erase simulations from canvas (does not clear external data)
      self.clearSimulationData()
      self.initSimCanvas() # recreate canvas
      self.sim_canvas.draw()
      self.setWindowTitle('')

    def clearCanvas (self):
      # clear all simulation & external data and erase everything from the canvas
      self.sim_canvas.clearlextdatobj() # clear the external data
      self.clearSimulationData()
      self.sim_data.clear_exp_data()
      self.initSimCanvas() # recreate canvas
      self.sim_canvas.draw()
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

      # start GUI in center of screenm, scale based on screen w x h 
      setscalegeomcenter(self, 1500, 1300)

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

      self.cbsim = QComboBox(self)
      try:
        self.populateSimCB()
      except ValueError:
        # If no simulations could be loaded into combobox
        # don't crash the initialization process
        print("Warning: no simulations to load")
        pass
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

      self.setWindowIcon(QIcon(os.path.join('res', 'icon.png')))

      self.schemwin.show() # so it's underneath main window

      self.show()

    def onActivateSimCB(self, paramfn):
      # load simulation when activating simulation combobox

      if paramfn != self.baseparamwin.paramfn:
        try:
          params = read_params(paramfn)
        except ValueError:
          QMessageBox.information(self, "HNN", "WARNING: could not"
                                  "retrieve parameters from %s" %
                                  paramfn)
          return
        self.baseparamwin.paramfn = paramfn

        self.updateDatCanv(params)

    def populateSimCB(self, index=None):
      # populate the simulation combobox

      self.cbsim.clear()
      for paramfn in self.sim_data._sim_data.keys():
        self.cbsim.addItem(paramfn)

      if self.cbsim.count() == 0:
        raise ValueError("No simulations to add to combo box")

      if index is None or index < 0:
        # set to last entry
        self.cbsim.setCurrentIndex(self.cbsim.count() - 1)
      else:
        self.cbsim.setCurrentIndex(index)

    def initSimCanvas(self, recalcErr=True, gRow=1, reInit=True):
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

      self.sim_canvas = SIMCanvas(self.baseparamwin.paramfn, self.baseparamwin.params,
                        parent=self, width=10, height=1, dpi=getmplDPI(),
                        is_optimization=self.is_optimization)

      # this is the Navigation widget
      # it takes the Canvas widget and a parent
      self.toolbar = NavigationToolbar2QT(self.sim_canvas, self)
      gWidth = 12
      self.grid.addWidget(self.toolbar, gRow, gCol, 1, gWidth)
      self.grid.addWidget(self.sim_canvas, gRow + 1, gCol, 1, gWidth)
      if self.sim_data.get_exp_data_size() > 0:
        self.sim_canvas.plot(recalcErr)
        self.sim_canvas.draw()

      if self.sim_canvas.saved_exception is not None:
        raise self.sim_canvas.saved_exception

    def setcursors(self, cursor):
      # set cursors of self and children
      self.setCursor(cursor)
      self.update()
      kids = self.children()
      kids.append(self.sim_canvas)  # matplotlib simcanvas
      for k in kids:
          if type(k) == QLayout or type(k) == QAction:
              # These types don't have setCursor()
              continue
          k.setCursor(cursor)
          k.update()

    def startoptmodel(self):
      # start model optimization
      if self.runningsim:
        self.stopsim() # stop sim works but leaves subproc as zombie until this main GUI thread exits
      else:
        self.is_optimization = True
        try:
          self.optmodel(self.baseparamwin.runparamwin.getncore())
        except RuntimeError:
          print("ERR: Optimization aborted")

    def controlsim(self):
        # control the simulation
        if self.runningsim:
            # stop sim works but leaves subproc as zombie until this main GUI
            # thread exits
            self.stopsim()
        else:
            self.is_optimization = False
            self.startsim(self.baseparamwin.runparamwin.getncore())

    def stopsim(self):
      # stop the simulation
        if self.runningsim:
            self.waitsimwin.hide()
            print('Terminating simulation. . .')
            self.statusBar().showMessage('Terminating sim. . .')
            self.runningsim = False
            self.runthread.stop()  # killed = True # terminate()
            self.btnsim.setText("Run Simulation")
            self.qbtn.setEnabled(True)
            self.statusBar().showMessage('')
            self.setcursors(Qt.ArrowCursor)

    def optmodel(self, ncore):
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

        self.runthread = RunSimThread(ncore, self.baseparamwin.params,
                                      self.result_callback,
                                      mainwin=self, is_optimization=True)

        # We have all the events we need connected we can start the thread
        self.runthread.start()
        # At this point we want to allow user to stop/terminate the thread
        # so we enable that button
        self.btnsim.setText("Stop Optimization")
        self.qbtn.setEnabled(False)
        bringwintotop(self.waitsimwin)

    def startsim(self, ncore):
        # start the simulation
        if not self.baseparamwin.saveparams(self.baseparamwin.paramfn):
            return # make sure params saved and ok to run

        # reread the params to get anything new
        try:
            params = read_params(self.baseparamwin.paramfn)
        except ValueError:
            txt = "WARNING: could not retrieve parameters from %s" % \
                  self.baseparamwin.paramfn
            QMessageBox.information(self, "HNN", txt)
            print(txt)
            return

        self.setcursors(Qt.WaitCursor)

        print('Starting simulation (%d cores). . .' % ncore)
        self.runningsim = True

        self.statusBar().showMessage("Running simulation. . .")

        # check that valid number of trials was given
        if 'N_trials' not in params or params['N_trials'] == 0:
            print("Warning: invalid configured number of trials. Setting to 1.")
            params['N_trials'] = 1

        self.runthread = RunSimThread(ncore, params,
                                      self.result_callback,
                                      mainwin=self, is_optimization=False)

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

    def result_callback(self, result):
        sim_data = result.data
        sim_data['spec'] = []
        params = result.params

        sim_data['dpls'] = deepcopy(sim_data['raw_dpls'])
        ntrial = len(sim_data['raw_dpls'])
        for trial_idx in range(ntrial):
            window_len = params['dipole_smooth_win']  # specified in ms
            fctr = params['dipole_scalefctr']
            if window_len > 0:  # param files set this to zero for no smoothing
                sim_data['dpls'][trial_idx].smooth(window_len=window_len)
            if fctr > 0:
                sim_data['dpls'][trial_idx].scale(fctr)

        # save average dipole from individual trials in a single file
        if ntrial > 1:
            sim_data['avg_dpl'] = average_dipoles(sim_data['dpls'])
        elif ntrial == 1:
            sim_data['avg_dpl'] = sim_data['dpls'][0]
        else:
            raise ValueError("No dipole(s) returned from simulation")

        # make sure the directory for saving data has been created
        data_dir = os.path.join(get_output_dir(), 'data')
        sim_dir = os.path.join(data_dir, params['sim_prefix'])
        try:
            os.mkdir(sim_dir)
        except FileExistsError:
            pass

        # TODO: Can below be removed if spk.txt is new hnn-core format with 3
        # columns (including spike type)?
        # Follow https://github.com/jonescompneurolab/hnn-core/issues/219
        write_gids_param(get_fname(sim_dir, 'param'), sim_data['gid_ranges'])

        # save spikes by trial
        glob = os.path.join(sim_dir, 'spk_%d.txt')
        sim_data['spikes'].write(glob)

        # save dipole for each trial and perform spectral analysis
        for trial_idx, dpl in enumerate(sim_data['dpls']):
            dipole_fn = get_fname(sim_dir, 'normdpl', trial_idx)
            dpl.write(dipole_fn)

            if params['save_dpl']:
                raw_dipole_fn = get_fname(sim_dir, 'rawdpl', trial_idx)
                sim_data['raw_dpls'][trial_idx].write(raw_dipole_fn)

            if params['save_spec_data'] or \
                    usingOngoingInputs(params):
                spec_results = spec_dpl_kernel(dpl, params['f_max_spec'],
                                               params['dt'], params['tstop'])
                sim_data['spec'].append(spec_results)

                if params['save_spec_data']:
                    spec_fn = get_fname(sim_dir, 'rawspec', trial_idx)
                    save_spec_data(spec_fn, spec_results)

        paramfn = os.path.join(get_output_dir(), 'param',
                                params['sim_prefix'] + '.param')

        self.sim_data.update_sim_data(paramfn, params, sim_data['dpls'],
                                      sim_data['avg_dpl'], sim_data['spikes'],
                                      sim_data['gid_ranges'],
                                      sim_data['spec'], sim_data['vsoma'])

    def done(self, except_msg):
        # called when the simulation completes running
        self.runningsim = False
        self.waitsimwin.hide()
        self.statusBar().showMessage("")
        self.btnsim.setText("Run Simulation")
        self.qbtn.setEnabled(True)
        # recreate canvas (plots too) to avoid incorrect axes
        self.initSimCanvas()
        # self.sim_canvas.plot()
        self.setcursors(Qt.ArrowCursor)

        failed=False
        if len(except_msg) > 0:
            failed = True
            msg = "%s: Failed " % except_msg
        else:
            msg = "Finished "

        if self.is_optimization:
            msg += "running optimization "
            self.baseparamwin.optparamwin.btnrunop.setText(
                'Prepare for Another Optimization')
            self.baseparamwin.optparamwin.btnrunop.clicked.disconnect()
            self.baseparamwin.optparamwin.btnrunop.clicked.connect(
                self.baseparamwin.optparamwin.prepareOptimization)
        else:
            msg += "running sim "

        if failed:
            QMessageBox.critical(self, "Failed!", msg + "using " +
                                self.baseparamwin.paramfn +
                                '. Check simulation log or console for error '
                                'messages')
        else:
            if self.baseparamwin.params['save_figs']:
                self.sim_data.save_dipole_with_hist(self.baseparamwin.paramfn,
                                                    self.baseparamwin.params)
                self.sim_data.save_spec_with_hist(self.baseparamwin.paramfn,
                                                  self.baseparamwin.params)

            if self.baseparamwin.params['record_vsoma']:
                self.sim_data.save_vsoma(self.baseparamwin.paramfn,
                                         self.baseparamwin.params)

            data_dir = os.path.join(get_output_dir(), 'data')
            sim_dir = os.path.join(data_dir,
                                  self.baseparamwin.params['sim_prefix'])
            QMessageBox.information(self, "Done!", msg + "using " +
                                    self.baseparamwin.paramfn +
                                    '. Saved data/figures in: ' + sim_dir)
        self.setWindowTitle(self.baseparamwin.paramfn)

        self.populateSimCB()  # populate the combobox
        cb_index = self.cbsim.findText(self.baseparamwin.paramfn)
        if cb_index < 0:
            raise ValueError("Couldn't find simulation in combobox: %s" %
                            self.baseparamwin.paramfn)
        self.cbsim.setCurrentIndex(cb_index)


if __name__ == '__main__':    
    app = QApplication(sys.argv)
    HNNGUI()
    sys.exit(app.exec_())
