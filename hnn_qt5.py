#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QToolTip, QPushButton, QFormLayout
from PyQt5.QtWidgets import QMenu, QSizePolicy, QMessageBox, QWidget, QFileDialog, QComboBox, QTabWidget
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QDialog, QGridLayout, QLineEdit, QLabel
from PyQt5.QtWidgets import QCheckBox, QTextEdit, QInputDialog, QSpacerItem, QFrame, QSplitter
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QPainter, QFont
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal, QObject, pyqtSlot, Qt, QSize
from PyQt5.QtCore import QMetaObject
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import multiprocessing
from subprocess import Popen, PIPE
import shlex, shutil
from collections import OrderedDict
from copy import deepcopy
from time import time, sleep
from conf import dconf
import conf
import numpy as np
from math import ceil, isclose
import spikefn
import params_default
from paramrw import quickreadprm, usingOngoingInputs, countEvokedInputs, usingEvokedInputs
from paramrw import chunk_evinputs, get_inputs, trans_input, find_param
from simdat import SIMCanvas, getinputfiles, readdpltrials
from gutils import setscalegeom, lowresdisplay, setscalegeomcenter, getmplDPI, getscreengeom
import nlopt
from psutil import cpu_count, wait_procs, process_iter, NoSuchProcess
from threading import Lock

prtime = False
decay_multiplier = 1.6

def isWindows ():
  # are we on windows? or linux/mac ?
  return sys.platform.startswith('win')

def getPyComm ():
  # get the python command - Windows only has python linux/mac have python3
  if sys.executable is not None: # check python command interpreter path - if available
    pyc = sys.executable
    if pyc.count('python') > 0 and len(pyc) > 0:
      return pyc # full path to python
  if isWindows():
    return 'python'
  return 'python3'

def parseargs ():
  for i in range(len(sys.argv)):
    if sys.argv[i] == '-dataf' and i + 1 < len(sys.argv):
      print('-dataf is ', sys.argv[i+1])
      conf.dconf['dataf'] = dconf['dataf'] = sys.argv[i+1]
      i += 1
    elif sys.argv[i] == '-paramf' and i + 1 < len(sys.argv):
      print('-paramf is ', sys.argv[i+1])
      conf.dconf['paramf'] = dconf['paramf'] = sys.argv[i+1]
      i += 1

parseargs()

simf = dconf['simf']
paramf = dconf['paramf']
debug = dconf['debug']
testLFP = dconf['testlfp'] or dconf['testlaminarlfp']
basedir = None

# get default number of cores
defncore = 0
try:
  defncore = len(os.sched_getaffinity(0))
except AttributeError:
  defncore = cpu_count(logical=False)

if defncore is None or defncore == 0:
  # in case psutil is not supported (e.g. BSD)
  defncore = multiprocessing.cpu_count()

if dconf['fontsize'] > 0: plt.rcParams['font.size'] = dconf['fontsize']
else: plt.rcParams['font.size'] = dconf['fontsize'] = 10

if debug: print('getPyComm:',getPyComm())

hnn_root_dir = os.path.dirname(os.path.realpath(__file__))

DEFAULT_CSS = """
QRangeSlider * {
    border: 0px;
    padding: 0px;
}
QRangeSlider #Head {
    background: #a7adba;
}
QRangeSlider #Span {
    background: #343d46;
}
QRangeSlider #Span:active {
    background: #343d46;
}
QRangeSlider #Tail {
    background: #a7adba;
}
QRangeSlider > QSplitter::handle {
    background: #4f5b66;
}
QRangeSlider > QSplitter::handle:vertical {
    height: 4px;
}
QRangeSlider > QSplitter::handle:pressed {
    background: #ca5;
}
"""

def scale(val, src, dst):
    try:
      return ((val - src[0]) / float(src[1]-src[0]) * (dst[1]-dst[0]) + dst[0])
    except ZeroDivisionError:
      return 0 

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("QRangeSlider")
        Form.resize(300, 30)
        Form.setStyleSheet(DEFAULT_CSS)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self._splitter = QSplitter(Form)
        self._splitter.setMinimumSize(QSize(0, 0))
        self._splitter.setMaximumSize(QSize(16777215, 16777215))
        self._splitter.setOrientation(Qt.Horizontal)
        self._splitter.setObjectName("splitter")
        self._head = QGroupBox(self._splitter)
        self._head.setTitle("")
        self._head.setObjectName("Head")
        self._handle = QGroupBox(self._splitter)
        self._handle.setTitle("")
        self._handle.setObjectName("Span")
        self._tail = QGroupBox(self._splitter)
        self._tail.setTitle("")
        self._tail.setObjectName("Tail")
        self.gridLayout.addWidget(self._splitter, 0, 0, 1, 1)
        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QCoreApplication.translate
        Form.setWindowTitle(_translate("QRangeSlider", "QRangeSlider"))


class Element(QGroupBox):
    def __init__(self, parent, main):
        super(Element, self).__init__(parent)
        self.main = main

    def setStyleSheet(self, style):
        self.parent().setStyleSheet(style)

    def textColor(self):
        return getattr(self, '__textColor', QColor(125, 125, 125))

    def setTextColor(self, color):
        if type(color) == tuple and len(color) == 3:
            color = QColor(color[0], color[1], color[2])
        elif type(color) == int:
            color = QColor(color, color, color)
        setattr(self, '__textColor', color)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.main.drawValues():
            self.drawText(event, qp)
        qp.end()


class Head(Element):
    def __init__(self, parent, main):
        super(Head, self).__init__(parent, main)

    def drawText(self, event, qp):
        qp.setPen(self.textColor())
        qp.setFont(QFont('Arial', 10))
        qp.drawText(event.rect(), Qt.AlignLeft, ("%.3f"%self.main.min()))


class Tail(Element):
    def __init__(self, parent, main):
        super(Tail, self).__init__(parent, main)

    def drawText(self, event, qp):
        qp.setPen(self.textColor())
        qp.setFont(QFont('Arial', 10))
        qp.drawText(event.rect(), Qt.AlignRight, ("%.3f"%self.main.max()))


class Handle(Element):
    def __init__(self, parent, main):
        super(Handle, self).__init__(parent, main)

    def drawText(self, event, qp):
        pass
        # qp.setPen(self.textColor())
        # qp.setFont(QFont('Arial', 10))
        # qp.drawText(event.rect(), Qt.AlignLeft, str(self.main.start()))
        # qp.drawText(event.rect(), Qt.AlignRight, str(self.main.end()))

    def mouseMoveEvent(self, event):
        event.accept()
        mx = event.globalX()
        _mx = getattr(self, '__mx', None)
        if not _mx:
            setattr(self, '__mx', mx)
            dx = 0
        else:
            dx = mx - _mx
        setattr(self, '__mx', mx)
        if dx == 0:
            event.ignore()
            return
        elif dx > 0:
            dx = 1
        elif dx < 0:
            dx = -1
        s = self.main.start() + dx
        e = self.main.end() + dx
        if s >= self.main.min() and e <= self.main.max():
            self.main.setRange(s, e)


class QRangeSlider(QWidget, Ui_Form):
    endValueChanged = pyqtSignal(int)
    maxValueChanged = pyqtSignal(int)
    minValueChanged = pyqtSignal(int)
    startValueChanged = pyqtSignal(int)
    rangeValuesChanged = pyqtSignal(str, float, float)

    _SPLIT_START = 1
    _SPLIT_END = 2

    def __init__(self, label, parent):
        super(QRangeSlider, self).__init__(parent)
        self.label = label
        self.rangeValuesChanged.connect(parent.updateRangeFromSlider)
        self.setupUi(self)
        self.setMouseTracking(False)
        self._splitter.splitterMoved.connect(self._handleMoveSplitter)
        self._head_layout = QHBoxLayout()
        self._head_layout.setSpacing(0)
        self._head_layout.setContentsMargins(0, 0, 0, 0)
        self._head.setLayout(self._head_layout)
        self.head = Head(self._head, main=self)
        self._head_layout.addWidget(self.head)
        self._handle_layout = QHBoxLayout()
        self._handle_layout.setSpacing(0)
        self._handle_layout.setContentsMargins(0, 0, 0, 0)
        self._handle.setLayout(self._handle_layout)
        self.handle = Handle(self._handle, main=self)
        self.handle.setTextColor((150, 255, 150))
        self._handle_layout.addWidget(self.handle)
        self._tail_layout = QHBoxLayout()
        self._tail_layout.setSpacing(0)
        self._tail_layout.setContentsMargins(0, 0, 0, 0)
        self._tail.setLayout(self._tail_layout)
        self.tail = Tail(self._tail, main=self)
        self._tail_layout.addWidget(self.tail)
        self.setMin(0)
        self.setMax(99)
        self.setStart(0)
        self.setEnd(99)
        self.setDrawValues(True)

    def min(self):
        return getattr(self, '__min', None)

    def max(self):
        return getattr(self, '__max', None)

    def setMin(self, value):
        setattr(self, '__min', value)
        self.minValueChanged.emit(value)

    def setMax(self, value):
        setattr(self, '__max', value)
        self.maxValueChanged.emit(value)

    def start(self):
        return getattr(self, '__start', None)

    def end(self):
        return getattr(self, '__end', None)

    def _setStart(self, value):
        setattr(self, '__start', value)
        self.startValueChanged.emit(value)

    def setStart(self, value):
        v = self._valueToPos(value)
        self._splitter.splitterMoved.disconnect()
        self._splitter.moveSplitter(v, self._SPLIT_START)
        self._splitter.splitterMoved.connect(self._handleMoveSplitter)
        self._setStart(value)

    def _setEnd(self, value):
        setattr(self, '__end', value)
        self.endValueChanged.emit(value)

    def setEnd(self, value):
        v = self._valueToPos(value)
        self._splitter.splitterMoved.disconnect()
        self._splitter.moveSplitter(v, self._SPLIT_END)
        self._splitter.splitterMoved.connect(self._handleMoveSplitter)
        self._setEnd(value)

    def drawValues(self):
        return getattr(self, '__drawValues', None)

    def setDrawValues(self, draw):
        setattr(self, '__drawValues', draw)

    def getRange(self):
        return (self.start(), self.end())

    def setRange(self, start, end):
        self.setStart(start)
        self.setEnd(end)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Left:
            s = self.start()-1
            e = self.end()-1
        elif key == Qt.Key_Right:
            s = self.start()+1
            e = self.end()+1
        else:
            event.ignore()
            return
        event.accept()
        if s >= self.min() and e <= self.max():
            self.setRange(s, e)

    def setBackgroundStyle(self, style):
        self._tail.setStyleSheet(style)
        self._head.setStyleSheet(style)

    def setSpanStyle(self, style):
        self._handle.setStyleSheet(style)

    def _valueToPos(self, value):
        return int(scale(value, (self.min(), self.max()), (0, self.width())))

    def _posToValue(self, xpos):
        return scale(xpos, (0, self.width()), (self.min(), self.max()))

    def _handleMoveSplitter(self, xpos, index):
        hw = self._splitter.handleWidth()
        def _lockWidth(widget):
            width = widget.size().width()
            widget.setMinimumWidth(width)
            widget.setMaximumWidth(width)
        def _unlockWidth(widget):
            widget.setMinimumWidth(0)
            widget.setMaximumWidth(16777215)
        if index == self._SPLIT_START:
            v = self._posToValue(xpos)
            _lockWidth(self._tail)
            if v >= self.end():
                return
            offset = -20
            w = xpos + offset
            self._setStart(v)
            self.rangeValuesChanged.emit(self.label, v, self.end())
        elif index == self._SPLIT_END:
            # account for width of head
            xpos += 4
            v = self._posToValue(xpos)
            _lockWidth(self._head)
            if v <= self.start():
                return
            offset = -40
            w = self.width() - xpos + offset
            self._setEnd(v)
            self.rangeValuesChanged.emit(self.label, self.start(), v)
        _unlockWidth(self._tail)
        _unlockWidth(self._head)
        _unlockWidth(self._handle)

# for signaling
class Communicate (QObject):
  commsig = pyqtSignal()

class DoneSignal (QObject):
  finishSim = pyqtSignal(bool, bool)

# for signaling - passing text
class TextSignal (QObject):
  tsig = pyqtSignal(str)

# for signaling - updating GUI & param file during optimization
class ParamSignal (QObject):
  psig = pyqtSignal(OrderedDict)

class CanvSignal (QObject):
  csig = pyqtSignal(bool, bool)

def bringwintobot (win):
  #win.show()
  #win.lower()
  win.hide()

def kill_list_of_procs(procs):
  # try terminate first
  for p in procs:
    try:
      p.terminate()
    except NoSuchProcess:
      pass
  gone, alive = wait_procs(procs, timeout=3)

  # now try kill
  for p in alive:
    p.kill()
  gone, alive = wait_procs(procs, timeout=3)

  return alive


def get_nrniv_procs_running():
  ls = []
  name = 'nrniv'
  for p in process_iter(attrs=["name", "exe", "cmdline"]):
      if name == p.info['name'] or \
              p.info['exe'] and os.path.basename(p.info['exe']) == name or \
              p.info['cmdline'] and p.info['cmdline'][0] == name:
          ls.append(p)
  return ls

def kill_and_check_nrniv_procs():
  procs = get_nrniv_procs_running()
  if len(procs) > 0:
    running = kill_list_of_procs(procs)
    if len(running) > 0:
      pids = [ proc.pid for proc in running ]
      print("ERROR: failed to kill nrniv process(es) %s" % ','.join(pids))

def bringwintotop (win):
  # bring a pyqt5 window to the top (parents still stay behind children)
  # based on examples from https://www.programcreek.com/python/example/101663/PyQt5.QtCore.Qt.WindowActive
  #win.show()
  #win.setWindowState(win.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
  #win.raise_()
  win.showNormal()
  win.activateWindow()
  #win.setWindowState((win.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
  #win.activateWindow()
  #win.raise_()
  #win.show() 

# based on https://nikolak.com/pyqt-threading-tutorial/
class RunSimThread (QThread):
  def __init__ (self,c,d,ntrial,ncore,waitsimwin,opt=False,baseparamwin=None,mainwin=None,onNSG=False):
    QThread.__init__(self)
    self.c = c
    self.d = d
    self.killed = False
    self.proc = None
    self.ntrial = ntrial
    self.ncore = ncore
    self.waitsimwin = waitsimwin
    self.opt = opt
    self.baseparamwin = baseparamwin
    self.mainwin = mainwin
    self.onNSG = onNSG

    self.txtComm = TextSignal()
    self.txtComm.tsig.connect(self.waitsimwin.updatetxt)

    self.prmComm = ParamSignal()
    if self.baseparamwin is not None:
      self.prmComm.psig.connect(self.baseparamwin.updatesaveparams)

    self.canvComm = CanvSignal()
    if self.mainwin is not None:
      self.canvComm.csig.connect(self.mainwin.initSimCanvas)

    self.lock = Lock()

  def updatewaitsimwin (self, txt):
    # print('RunSimThread updatewaitsimwin, txt=',txt)
    self.txtComm.tsig.emit(txt)

  def updatebaseparamwin (self, d):
    self.prmComm.psig.emit(d)

  def updatedispparam (self):
    self.c.commsig.emit()

  def updatedrawerr (self):
    self.canvComm.csig.emit(False, self.opt) # False means do not recalculate error

  def stop (self):
    self.killproc()

  def __del__ (self):
    self.quit()
    self.wait()

  def run (self):
    failed=False

    if self.opt and self.baseparamwin is not None:
      try:
        self.optmodel() # run optimization
      except RuntimeError:
        failed = True
        self.baseparamwin.optparamwin.toggleEnableUserFields(self.cur_step, enable=True)
        self.baseparamwin.optparamwin.optimization_running = False
    else:
      try:
        self.runsim() # run simulation
        self.updatedispparam() # update params in all windows (optimization)
      except RuntimeError:
        failed = True

    self.d.finishSim.emit(self.opt, failed) # send the finish signal


  def killproc (self):
    if self.proc is None:
      # any nrniv processes found are not part of current sim
      return

    if debug: print('Thread killing sim. . .')

    # try the nice way to stop the mpiexec proc
    self.proc.terminate()

    retries = 0
    while self.proc.poll() is None and retries < 5:
      # mpiexec still running
      self.proc.kill()
      if self.proc.poll() is None:
        sleep(1)
      retries += 1

    # make absolute sure all nrniv procs have been killed
    kill_and_check_nrniv_procs()

    self.lock.acquire()
    self.killed = True
    self.lock.release()

  def spawn_sim (self, simlength, banner=False):
    import simdat

    mpicmd = 'mpiexec -np '

    if banner:
      nrniv_cmd = ' nrniv -python -mpi '
    else:
      nrniv_cmd = ' nrniv -python -mpi -nobanner '

    if self.onNSG:
      cmd = 'python nsgr.py ' + paramf + ' ' + str(self.ntrial) + ' 710.0'
    elif not simlength is None:
      cmd = mpicmd + str(self.ncore) + nrniv_cmd + simf + ' ' + paramf + ' ntrial ' + str(self.ntrial) + ' simlength ' + str(simlength)
    else:
      cmd = mpicmd + str(self.ncore) + nrniv_cmd + simf + ' ' + paramf + ' ntrial ' + str(self.ntrial)
    simdat.dfile = getinputfiles(paramf)
    cmdargs = shlex.split(cmd,posix="win" not in sys.platform) # https://github.com/maebert/jrnl/issues/348
    if debug: print("cmd:",cmd,"cmdargs:",cmdargs)
    if prtime:
      self.proc = Popen(cmdargs,cwd=os.getcwd())
    else: 
      self.proc = Popen(cmdargs,stdout=PIPE,stderr=PIPE,cwd=os.getcwd(),universal_newlines=True)

  def get_proc_stream (self, stream, print_to_console=False):
    try:
      for line in iter(stream.readline, ""):
        if print_to_console:
          print(line.strip())
        try: # see https://stackoverflow.com/questions/2104779/qobject-qplaintextedit-multithreading-issues
          self.updatewaitsimwin(line.strip()) # sends a pyqtsignal to waitsimwin, which updates its textedit
        except:
          if debug: print('RunSimThread updatewaitsimwin exception...')
          pass # catch exception in case anything else goes wrong
    except ValueError:
      # if process is killed and stream.readline() gives I/O error
      pass
    stream.close()

  # run sim command via mpi, then delete the temp file.
  def runsim (self, is_opt=False, banner=True, simlength=None):
    import simdat

    global defncore
    self.lock.acquire()
    self.killed = False
    self.lock.release()

    self.spawn_sim(simlength, banner=banner)
    retried = False

    #cstart = time()
    while True:
      status = self.proc.poll()
      if not status is None:
        if status == 0:
          # success, use same number of cores next time
          defncore = self.ncore
          break
        elif status == 1 and not retried:
          self.ncore = ceil(self.ncore/2)
          txt = "INFO: Failed starting mpiexec, retrying with %d cores" % self.ncore
          print(txt)
          self.updatewaitsimwin(txt)
          self.spawn_sim(simlength, banner=banner)
          retried = True
        else:
          txt = "Simulation exited with return code %d. Stderr from console:"%status
          print(txt)
          self.updatewaitsimwin(txt)
          self.get_proc_stream(self.proc.stderr, print_to_console=True)
          kill_and_check_nrniv_procs()
          raise RuntimeError

      self.get_proc_stream(self.proc.stdout, print_to_console=False)

      # check if proc was killed
      self.lock.acquire()
      if self.killed:
        self.lock.release()
        # exit using RuntimeError
        raise RuntimeError
      else:
        self.lock.release()

      sleep(1)

    #cend = time()
    #rtime = cend - cstart
    #if debug: print('sim finished in %.3f s'%rtime)

    try:
      # load data from sucessful sim
      simdat.ddat['dpl'] = np.loadtxt(simdat.dfile['dpl'])
      if debug: print('loaded new dpl file:', simdat.dfile['dpl'])#,'time=',time())
      if os.path.isfile(simdat.dfile['spec']):
        simdat.ddat['spec'] = np.load(simdat.dfile['spec'])
      else:
        simdat.ddat['spec'] = None
      simdat.ddat['spk'] = np.loadtxt(simdat.dfile['spk'])
      simdat.ddat['dpltrials'] = readdpltrials(os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0]),self.ntrial)
      if debug: print("Read simulation outputs:",simdat.dfile.values())

      if not is_opt:
        simdat.updatelsimdat(paramf,simdat.ddat['dpl']) # update lsimdat and its current sim index
    except OSError:
      print('WARN: could not read simulation outputs:',simdat.dfile.values())

  def optmodel (self):
    import simdat

    global basedir
    need_initial_ddat = False

    # initialize RNG with seed from config
    seed = int(find_param(paramf,'prng_seedcore_opt'))
    nlopt.srand(seed)

    # initial_ddat stores the initial fit (from "Run Simulation").
    # To be displayed in final dipole plot as black dashed line.
    if len(simdat.ddat) > 0:
      simdat.initial_ddat['dpl'] = deepcopy(simdat.ddat['dpl'])
      simdat.initial_ddat['errtot'] = deepcopy(simdat.ddat['errtot'])
    else:
      need_initial_ddat = True

    self.baseparamwin.optparamwin.populate_initial_opt_ranges()

    # save initial parameters file
    param_out = os.path.join(basedir,'before_opt.param')
    shutil.copyfile(paramf, param_out)

    self.updatewaitsimwin('Optimizing model. . .')

    self.last_step = False
    self.first_step = True
    num_steps = self.baseparamwin.optparamwin.get_num_chunks()
    for step in range(num_steps):
      self.cur_step = step
      if step == num_steps - 1:
        self.last_step = True

      # disable range sliders for each step once that step has begun
      self.baseparamwin.optparamwin.toggleEnableUserFields(step, enable=False)

      self.step_ranges = self.baseparamwin.optparamwin.get_chunk_ranges(step)
      self.step_sims = self.baseparamwin.optparamwin.get_sims_for_chunk(step)

      if self.step_sims == 0:
        txt = "Skipping optimization step %d (0 simulations)"%(step+1)
        self.updatewaitsimwin(txt)
        continue

      txt = "Starting optimization step %d/%d" % (step + 1, num_steps)
      self.updatewaitsimwin(txt)
      self.runOptStep(step)

      if self.best_ddat is not None:
        simdat.ddat = deepcopy(self.best_ddat)

      if need_initial_ddat:
        simdat.initial_ddat = deepcopy(simdat.ddat)

      simdat.updateoptdat(paramf,simdat.ddat['dpl']) # update optdat with best from this step

      # put best opt results into GUI and save to param file
      push_values = OrderedDict()
      for param_name in self.step_ranges.keys():
        push_values[param_name] = self.step_ranges[param_name]['final']
      self.updatebaseparamwin(push_values)

      sleep(1)

      self.first_step = False

    # one final sim with the best parameters to update display
    self.runsim(is_opt=True, banner=False)
    simdat.updatelsimdat(paramf,simdat.ddat['dpl']) # update lsimdat and its current sim index
    simdat.updateoptdat(paramf,simdat.ddat['dpl']) # update optdat with the final best

    # re-enable all the range sliders
    self.baseparamwin.optparamwin.toggleEnableUserFields(step, enable=True)

    self.baseparamwin.optparamwin.optimization_running = False


  def runOptStep (self, step):
    import simdat
    global basedir, paramf

    self.optsim = 0
    self.minopterr = 1e9
    self.stepminopterr = self.minopterr
    self.best_ddat = None
    self.opt_start = self.baseparamwin.optparamwin.get_chunk_start(step)
    self.opt_end = self.baseparamwin.optparamwin.get_chunk_end(step)
    self.opt_weights = self.baseparamwin.optparamwin.get_chunk_weights(step)
    def optrun (new_params, grad=0):
      txt = "Optimization step %d, simulation %d" % (step + 1,
                                                     self.optsim + 1)
      self.updatewaitsimwin(txt)
      print(txt)

      dtest = OrderedDict() # parameter values to test      
      for param_name, test_value in zip(self.step_ranges.keys(), new_params): # set parameters
        if test_value >= self.step_ranges[param_name]['minval'] and \
           test_value <= self.step_ranges[param_name]['maxval']:
          if debug:
            print('optrun prm:', self.step_ranges[param_name]['initial'],
                                 self.step_ranges[param_name]['minval'],
                                 self.step_ranges[param_name]['maxval'],
                                 test_value)
          dtest[param_name] = test_value
        else:
          # This test is not strictly necessary with COBYLA, but in case the algorithm
          # is changed at some point in the future
          print('INFO: optimization chose %.3f for %s outside of [%.3f-%.3f].'
                % (test_value, param_name,
                   self.step_ranges[param_name]['minval'],
                   self.step_ranges[param_name]['maxval']))
          return 1e9 # invalid param value -> large error

      # put new param values into GUI and save params to file
      self.updatebaseparamwin(dtest)
      sleep(1)

      # run the simulation, but stop early if possible
      self.runsim(is_opt=True, banner=False, simlength=self.opt_end)

      # calculate wRMSE for all steps
      simdat.weighted_rmse(simdat.ddat,
                           self.opt_end,
                           self.opt_weights,
                           tstart=self.opt_start)
      err = simdat.ddat['werrtot']

      if self.last_step:
        # weighted RMSE with weights of all 1's is the same as
        # regular RMSE
        simdat.ddat['errtot'] = simdat.ddat['werrtot']
        txt = "RMSE = %f"%err
      else:
        # calculate regular RMSE for displaying on plot
        simdat.calcerr(simdat.ddat,
                      self.opt_end,
                      tstart=self.opt_start)

        txt = "weighted RMSE = %f, RMSE = %f"% (err,simdat.ddat['errtot'])

      print(txt)
      self.updatewaitsimwin(os.linesep+'Simulation finished: ' + txt + os.linesep) # print error

      fnoptinf = os.path.join(basedir,'optinf.txt')
      with open(fnoptinf,'a') as fpopt:
        fpopt.write(str(simdat.ddat['errtot'])+os.linesep) # write error

      # save copy param file
      param_fname = os.path.basename(paramf)
      curr_paramf = os.path.join(basedir, param_fname)

      # save params numbered by optsim
      param_out = os.path.join(basedir,'step_%d_sim_%d.param'%(self.cur_step,self.optsim))
      shutil.copyfile(curr_paramf, param_out)

      if err < self.stepminopterr:
        self.updatewaitsimwin("new best with RMSE %f"%err)

        self.stepminopterr = err
        # save best param file
        shutil.copyfile(curr_paramf, os.path.join(basedir,'step_%d_best.param'%self.cur_step)) # convenience, save best here
        self.best_ddat = simdat.ddat.copy()

      if self.optsim == 0 and not self.first_step:
        # Update plots for the first simulation only of this step (best results from last round)
        # Skip the first step because there are no optimization results to show yet.
        self.updatedrawerr() # send event to draw updated error (asynchronously)

      self.optsim += 1

      return err # return error

    def optimize(params_input, evals, algorithm):
        opt_params = []
        lb = []
        ub = []

        for param_name in params_input.keys():
            upper = params_input[param_name]['maxval']
            lower = params_input[param_name]['minval']
            if upper == lower:
              continue

            ub.append(upper)
            lb.append(lower)
            opt_params.append(params_input[param_name]['initial'])

        if algorithm == nlopt.G_MLSL_LDS or algorithm == nlopt.G_MLSL:
            # In case these mixed mode (global + local) algorithms are used in the future
            local_opt = nlopt.opt(nlopt.LN_COBYLA, num_params)
            opt.set_local_optimizer(local_opt)

        opt.set_lower_bounds(lb)
        opt.set_upper_bounds(ub)
        opt.set_min_objective(optrun)
        opt.set_xtol_rel(1e-4)
        opt.set_maxeval(evals)
        opt_results = opt.optimize(opt_params)

        return opt_results

    txt = 'Optimizing from [%3.3f-%3.3f] ms' % (self.opt_start,
                                                self.opt_end)
    self.updatewaitsimwin(txt)

    num_params = len(self.step_ranges)
    algorithm = nlopt.LN_COBYLA
    opt = nlopt.opt(algorithm, num_params)
    opt_results = optimize(self.step_ranges, self.step_sims, algorithm)

    # update opt params for the next round
    for var_name, new_value in zip(self.step_ranges, opt_results):
        old_value = self.step_ranges[var_name]['initial']

        # only change the parameter value if it changed significantly
        if not isclose(old_value, new_value, abs_tol=1e-9):
          self.step_ranges[var_name]['final'] = new_value
        else:
          self.step_ranges[var_name]['final'] = \
            self.step_ranges[var_name]['initial']

# look up resource adjusted for screen resolution
def lookupresource (fn):
  lowres = lowresdisplay() # low resolution display
  if lowres:
    return os.path.join('res',fn+'2.png')
  else:
    return os.path.join('res',fn+'.png')

def format_range_str(value):
  if value == 0:
    value_str = "0.000"
  elif value < 0.1 :
    value_str = ("%6f" % value)
  else:
    value_str = ("%.3f" % value)

  return value_str

# DictDialog - dictionary-based dialog with tabs - should make all dialogs
# specifiable via cfg file format - then can customize gui without changing py code
# and can reduce code explosion / overlap between dialogs 
class DictDialog (QDialog):

  def __init__ (self, parent, din):
    super(DictDialog, self).__init__(parent)
    self.ldict = [] # subclasses should override
    self.ltitle = []
    self.dtransvar = {} # for translating model variable name to more human-readable form
    self.stitle = ''
    self.initd()
    self.initUI()
    self.initExtra()
    self.setfromdin(din) # set values from input dictionary
    self.addtips()

  def addtips (self):
    for ktip in dconf.keys():
      if ktip in self.dqline:
        self.dqline[ktip].setToolTip(dconf[ktip])
      elif ktip in self.dqextra:
        self.dqextra[ktip].setToolTip(dconf[ktip])

  def __str__ (self):
    s = ''
    for k,v in self.dqline.items(): s += k + ': ' + v.text().strip() + os.linesep
    return s

  def saveparams (self): self.hide()

  def initd (self): pass # implemented in subclass

  def getval (self,k):
    if k in self.dqline.keys():
      return self.dqline[k].text().strip()

  def lines2val (self,ksearch,val):
    for k in self.dqline.keys():
      if k.count(ksearch) > 0:
        self.dqline[k].setText(str(val))

  def setfromdin (self,din):
    if not din: return
    for k,v in din.items():
      if k in self.dqline:
        self.dqline[k].setText(str(v).strip())

  def transvar (self,k):
    if k in self.dtransvar: return self.dtransvar[k]
    return k

  def addtransvar (self,k,strans):
    self.dtransvar[k] = strans
    self.dtransvar[strans] = k

  def initExtra (self): self.dqextra = OrderedDict() # extra items not written to param file

  def initUI (self):
    self.layout = QVBoxLayout(self)

    # Add stretch to separate the form layout from the button
    self.layout.addStretch(1)

    # Initialize tab screen
    self.ltabs = []
    self.tabs = QTabWidget(); self.layout.addWidget(self.tabs)

    for i in range(len(self.ldict)): self.ltabs.append(QWidget())

    self.tabs.resize(575,200) 

    # create tabs and their layouts
    for tab,s in zip(self.ltabs,self.ltitle):
      self.tabs.addTab(tab,s)
      tab.layout = QFormLayout()
      tab.setLayout(tab.layout)

    self.dqline = OrderedDict() # QLineEdits dict; key is model variable
    for d,tab in zip(self.ldict, self.ltabs):
      for k,v in d.items():
        self.dqline[k] = QLineEdit(self)
        self.dqline[k].setText(str(v))
        tab.layout.addRow(self.transvar(k),self.dqline[k]) # adds label,QLineEdit to the tab

    # Add tabs to widget        
    self.layout.addWidget(self.tabs)
    self.setLayout(self.layout)
    self.setWindowTitle(self.stitle)  
    #nw, nh = setscalegeom(self, 150, 150, 625, 300)
    #nx = parent.rect().x()+parent.rect().width()/2-nw/2
    #ny = parent.rect().y()+parent.rect().height()/2-nh/2
    #print(parent.rect(),nx,ny)
    #self.move(nx, ny)
    #self.move(self.parent.
    #self.move(self.parent.widget.rect().x+self.parent.widget.rect().width()/2-nw,
    #          self.parent.widget.rect().y+self.parent.widget.rect().height()/2-nh)

  def TurnOff (self): pass

  def addOffButton (self):
    # Create a horizontal box layout to hold the button
    self.button_box = QHBoxLayout() 
    self.btnoff = QPushButton('Turn Off Inputs',self)
    self.btnoff.resize(self.btnoff.sizeHint())
    self.btnoff.clicked.connect(self.TurnOff)
    self.btnoff.setToolTip('Turn Off Inputs')
    self.button_box.addWidget(self.btnoff)
    self.layout.addLayout(self.button_box)

  def addHideButton (self):
    self.bbhidebox = QHBoxLayout() 
    self.btnhide = QPushButton('Hide Window',self)
    self.btnhide.resize(self.btnhide.sizeHint())
    self.btnhide.clicked.connect(self.hide)
    self.btnhide.setToolTip('Hide Window')
    self.bbhidebox.addWidget(self.btnhide)
    self.layout.addLayout(self.bbhidebox)

# widget to specify ongoing input params (proximal, distal)
class OngoingInputParamDialog (DictDialog):
  def __init__ (self, parent, inty, din=None):
    self.inty = inty
    if self.inty.startswith('Proximal'):
      self.prefix = 'input_prox_A_'
      self.postfix = '_prox'
      self.isprox = True
    else:
      self.prefix = 'input_dist_A_'
      self.postfix = '_dist'
      self.isprox = False
    super(OngoingInputParamDialog, self).__init__(parent,din)
    self.addOffButton()
    self.addImages()
    self.addHideButton()

  # add png cartoons to tabs
  def addImages (self):
    if self.isprox: self.pix = QPixmap(lookupresource('proxfig'))
    else: self.pix = QPixmap(lookupresource('distfig'))
    for tab in self.ltabs:      
      pixlbl = ClickLabel(self)
      pixlbl.setPixmap(self.pix)
      tab.layout.addRow(pixlbl)


  # turn off by setting all weights to 0.0
  def TurnOff (self): self.lines2val('weight',0.0)

  def initd (self):
    self.dtiming = OrderedDict([#('distribution' + self.postfix, 'normal'),
                                ('t0_input' + self.postfix, 1000.),
                                ('t0_input_stdev' + self.postfix, 0.),
                                ('tstop_input' + self.postfix, 250.),
                                ('f_input' + self.postfix, 10.),
                                ('f_stdev' + self.postfix, 20.),
                                ('events_per_cycle' + self.postfix, 2),
                                ('repeats' + self.postfix, 10)])

    self.dL2 = OrderedDict([(self.prefix + 'weight_L2Pyr_ampa', 0.),
                            (self.prefix + 'weight_L2Pyr_nmda', 0.),
                            (self.prefix + 'weight_L2Basket_ampa', 0.),
                            (self.prefix + 'weight_L2Basket_nmda',0.),
                            (self.prefix + 'delay_L2', 0.1),])

    self.dL5 = OrderedDict([(self.prefix + 'weight_L5Pyr_ampa', 0.),
                            (self.prefix + 'weight_L5Pyr_nmda', 0.)])

    if self.isprox:
      self.dL5[self.prefix + 'weight_L5Basket_ampa'] = 0.0
      self.dL5[self.prefix + 'weight_L5Basket_nmda'] = 0.0
    self.dL5[self.prefix + 'delay_L5'] = 0.1

    self.ldict = [self.dtiming, self.dL2, self.dL5]
    self.ltitle = ['Timing', 'Layer 2/3', 'Layer 5']
    self.stitle = 'Set Rhythmic '+self.inty+' Inputs'

    dtmp = {'L2':'L2/3 ','L5':'L5 '}
    for d in [self.dL2, self.dL5]:
      for k in d.keys():
        lk = k.split('_')
        if k.count('weight') > 0:
          self.addtransvar(k, dtmp[lk[-2][0:2]] + lk[-2][2:]+' '+lk[-1].upper()+u' weight (µS)')
        else:
          self.addtransvar(k, 'Delay (ms)')

    #self.addtransvar('distribution'+self.postfix,'Distribution')
    self.addtransvar('t0_input'+self.postfix,'Start time mean (ms)')
    self.addtransvar('t0_input_stdev'+self.postfix,'Start time stdev (ms)')
    self.addtransvar('tstop_input'+self.postfix,'Stop time (ms)')
    self.addtransvar('f_input'+self.postfix,'Burst frequency (Hz)')
    self.addtransvar('f_stdev'+self.postfix,'Burst stdev (ms)')
    self.addtransvar('events_per_cycle'+self.postfix,'Spikes/burst')
    self.addtransvar('repeats'+self.postfix,'Number bursts')

class EvokedOrRhythmicDialog (QDialog):
  def __init__ (self, parent, distal, evwin, rhythwin):
    super(EvokedOrRhythmicDialog, self).__init__(parent)
    if distal: self.prefix = 'Distal'
    else: self.prefix = 'Proximal'
    self.evwin = evwin
    self.rhythwin = rhythwin
    self.initUI()

  def initUI (self):
    self.layout = QVBoxLayout(self)
    # Add stretch to separate the form layout from the button
    self.layout.addStretch(1)

    self.btnrhythmic = QPushButton('Rhythmic ' + self.prefix + ' Inputs',self)
    self.btnrhythmic.resize(self.btnrhythmic.sizeHint())
    self.btnrhythmic.clicked.connect(self.showrhythmicwin)
    self.layout.addWidget(self.btnrhythmic)

    self.btnevoked = QPushButton('Evoked Inputs',self)
    self.btnevoked.resize(self.btnevoked.sizeHint())
    self.btnevoked.clicked.connect(self.showevokedwin)
    self.layout.addWidget(self.btnevoked)

    self.addHideButton()

    setscalegeom(self, 150, 150, 270, 120)
    self.setWindowTitle("Pick Input Type")     

  def showevokedwin (self):
    bringwintotop(self.evwin)
    self.hide()

  def showrhythmicwin (self):
    bringwintotop(self.rhythwin)
    self.hide()

  def addHideButton (self):
    self.bbhidebox = QHBoxLayout() 
    self.btnhide = QPushButton('Hide Window',self)
    self.btnhide.resize(self.btnhide.sizeHint())
    self.btnhide.clicked.connect(self.hide)
    self.btnhide.setToolTip('Hide Window')
    self.bbhidebox.addWidget(self.btnhide)
    self.layout.addLayout(self.bbhidebox)


class SynGainParamDialog (QDialog):
  def __init__ (self, parent, netparamwin):
    super(SynGainParamDialog, self).__init__(parent)
    self.netparamwin = netparamwin
    self.initUI()

  def scalegain (self, k, fctr):
    oldval = float(self.netparamwin.dqline[k].text().strip())
    newval = oldval * fctr
    self.netparamwin.dqline[k].setText(str(newval))
    if debug: print('scaling ',k,' by', fctr, 'from ',oldval,'to ',newval,'=',oldval*fctr)
    return newval

  def isE (self,ty): return ty.count('Pyr') > 0
  def isI (self,ty): return ty.count('Basket') > 0

  def tounity (self):
    for k in self.dqle.keys(): self.dqle[k].setText('1.0')

  def scalegains (self):
    if debug: print('scaling synaptic gains')
    for i,k in enumerate(self.dqle.keys()):
      fctr = float(self.dqle[k].text().strip())
      if fctr < 0.:
        fctr = 0.
        self.dqle[k].setText(str(fctr))
      elif fctr == 1.0:
        continue
      if debug: print(k,fctr)
      for k2 in self.netparamwin.dqline.keys():
        l = k2.split('_')
        ty1,ty2 = l[1],l[2]
        if self.isE(ty1) and self.isE(ty2) and k == 'E -> E':
          self.scalegain(k2,fctr)
        elif self.isE(ty1) and self.isI(ty2) and k == 'E -> I':
          self.scalegain(k2,fctr)
        elif self.isI(ty1) and self.isE(ty2) and k == 'I -> E':
          self.scalegain(k2,fctr)
        elif self.isI(ty1) and self.isI(ty2) and k == 'I -> I':
          self.scalegain(k2,fctr)
    self.tounity() # go back to unity since pressed OK - next call to this dialog will reset new values
    self.hide()

  def initUI (self):
    grid = QGridLayout()
    grid.setSpacing(10)

    self.dqle = OrderedDict()
    for row,k in enumerate(['E -> E', 'E -> I', 'I -> E', 'I -> I']):
      lbl = QLabel(self)
      lbl.setText(k)
      lbl.adjustSize()
      grid.addWidget(lbl,row, 0)
      qle = QLineEdit(self)
      qle.setText('1.0')
      grid.addWidget(qle,row, 1)
      self.dqle[k] = qle

    row += 1
    self.btnok = QPushButton('OK',self)
    self.btnok.resize(self.btnok.sizeHint())
    self.btnok.clicked.connect(self.scalegains)
    grid.addWidget(self.btnok, row, 0, 1, 1)
    self.btncancel = QPushButton('Cancel',self)
    self.btncancel.resize(self.btncancel.sizeHint())
    self.btncancel.clicked.connect(self.hide)
    grid.addWidget(self.btncancel, row, 1, 1, 1)

    self.setLayout(grid)  
    setscalegeom(self, 150, 150, 270, 180)
    self.setWindowTitle("Synaptic Gains")  

# widget to specify tonic inputs
class TonicInputParamDialog (DictDialog):
  def __init__ (self, parent, din):
    super(TonicInputParamDialog, self).__init__(parent,din)
    self.addOffButton()
    self.addHideButton()

  # turn off by setting all weights to 0.0
  def TurnOff (self): self.lines2val('A',0.0)

  def initd (self):

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

    dtmp = {'L2':'L2/3 ','L5':'L5 '} # temporary dictionary for string translation
    for d in [self.dL2, self.dL5]:
      for k in d.keys():
        cty = k.split('_')[2] # cell type
        tcty = dtmp[cty[0:2]] + cty[2:] # translated cell type
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
class PoissonInputParamDialog (DictDialog):
  def __init__ (self, parent, din):
    super(PoissonInputParamDialog, self).__init__(parent,din)
    self.addOffButton()
    self.addHideButton()

  # turn off by setting all weights to 0.0
  def TurnOff (self): self.lines2val('weight',0.0)

  def initd (self):

    self.dL2,self.dL5 = OrderedDict(),OrderedDict()
    ld = [self.dL2,self.dL5]

    for i,lyr in enumerate(['L2','L5']):
      d = ld[i]
      for ty in ['Pyr', 'Basket']:
        for sy in ['ampa','nmda']: d[lyr+ty+'_Pois_A_weight'+'_'+sy]=0.
        d[lyr+ty+'_Pois_lamtha']=0.

    self.dtiming = OrderedDict([('t0_pois', 0.),
                                ('T_pois', -1)])

    self.addtransvar('t0_pois','Start time (ms)')
    self.addtransvar('T_pois','Stop time (ms)')

    dtmp = {'L2':'L2/3 ','L5':'L5 '} # temporary dictionary for string translation
    for d in [self.dL2, self.dL5]:
      for k in d.keys():
        ks = k.split('_')
        cty = ks[0] # cell type
        tcty = dtmp[cty[0:2]] + cty[2:] # translated cell type
        if k.count('weight'):
          self.addtransvar(k, tcty+ ' ' + ks[-1].upper() + u' weight (µS)')
        elif k.endswith('lamtha'):
          self.addtransvar(k, tcty+ ' freq (Hz)')

    self.ldict = [self.dL2, self.dL5, self.dtiming]
    self.ltitle = ['Layer 2/3', 'Layer 5', 'Timing']
    self.stitle = 'Set Poisson Inputs'

# evoked input param dialog (allows adding/removing arbitrary number of evoked inputs)
class EvokedInputParamDialog (QDialog):
  def __init__ (self, parent, din):
    super(EvokedInputParamDialog, self).__init__(parent)
    self.nprox = self.ndist = 0 # number of proximal,distal inputs
    self.ld = [] # list of dictionaries for proximal/distal inputs
    self.dqline = OrderedDict()
    self.dtransvar = {} # for translating model variable name to more human-readable form
    self.initUI()
    self.setfromdin(din)

  def addtips (self):
    for ktip in dconf.keys():
      if ktip in self.dqline:
        self.dqline[ktip].setToolTip(dconf[ktip])

  def transvar (self,k):
    if k in self.dtransvar: return self.dtransvar[k]
    return k

  def addtransvar (self,k,strans):
    self.dtransvar[k] = strans
    self.dtransvar[strans] = k

  def set_qline_float (self, key_str, value):
    try:
      new_value = float(value)
    except ValueError:
      print("WARN: bad value for param %s: %s. Unable to convert"
            " to a floating point number" % (key_str, value))
      return

    # Enforce no sci. not. + limit field len + remove trailing 0's
    self.dqline[key_str].setText(("%7f" % new_value).rstrip('0').rstrip('.'))

  def setfromdin (self,din):
    if not din: return

    if 'dt' in din:

      # Optimization feature introduces the case where din just contains optimization
      # relevant parameters. In that case, we don't want to remove all inputs, just
      # modify existing inputs.
      self.removeAllInputs() # turn off any previously set inputs

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

    for k,v in din.items():
      if k == 'sync_evinput':
        try:
          new_value = bool(int(v))
        except ValueError:
          print("WARN: bad value for param %s: %s. Unable to convert"
                " to a boolean value" % (k,v))
          continue
        if new_value:
          self.chksync.setChecked(True)
        else:
          self.chksync.setChecked(False)
      elif k == 'inc_evinput':
        try:
          new_value = float(v)
        except ValueError:
          print("WARN: bad value for param %s: %s. Unable to convert"
                " to a floating point number" % (k,v))
          continue
        self.incedit.setText(str(new_value).strip())
      elif k in self.dqline:
        if k.startswith('numspikes'):
          try:
            new_value = int(v)
          except ValueError:
            print("WARN: bad value for param %s: %s. Unable to convert"
                  " to a integer" % (k, v))
            continue
          self.dqline[k].setText(str(new_value))
        else:
          self.set_qline_float(k, v)
      elif k.count('gbar') > 0 and \
           (k.count('evprox') > 0 or \
            k.count('evdist') > 0):
        # NOTE: will be deprecated in future release
        # for back-compat with old-style specification which didn't have ampa,nmda in evoked gbar
        lks = k.split('_')
        eloc = lks[1]
        enum = lks[2]
        base_key_str = 'gbar_' + eloc + '_' + enum + '_'
        if eloc == 'evprox':
          for ct in ['L2Pyr', 'L2Basket', 'L5Pyr', 'L5Basket']:
            # ORIGINAL MODEL/PARAM: only ampa for prox evoked inputs
            key_str = base_key_str + ct + '_ampa'
            self.set_qline_float(key_str, v)
        elif eloc == 'evdist':
          for ct in ['L2Pyr', 'L2Basket', 'L5Pyr']:
            # ORIGINAL MODEL/PARAM: both ampa and nmda for distal evoked inputs
            key_str = base_key_str + ct + '_ampa'
            self.set_qline_float(key_str, v)
            key_str = base_key_str + ct + '_nmda'
            self.set_qline_float(key_str, v)

  def initUI (self):
    self.layout = QVBoxLayout(self)

    # Add stretch to separate the form layout from the button
    self.layout.addStretch(1)

    self.ltabs = []
    self.tabs = QTabWidget()
    self.layout.addWidget(self.tabs)
    
    self.button_box = QVBoxLayout() 
    self.btnprox = QPushButton('Add Proximal Input',self)
    self.btnprox.resize(self.btnprox.sizeHint())
    self.btnprox.clicked.connect(self.addProx)
    self.btnprox.setToolTip('Add Proximal Input')
    self.button_box.addWidget(self.btnprox)

    self.btndist = QPushButton('Add Distal Input',self)
    self.btndist.resize(self.btndist.sizeHint())
    self.btndist.clicked.connect(self.addDist)
    self.btndist.setToolTip('Add Distal Input')
    self.button_box.addWidget(self.btndist)

    self.chksync = QCheckBox('Synchronous Inputs',self)
    self.chksync.resize(self.chksync.sizeHint())
    self.chksync.setChecked(True)
    self.button_box.addWidget(self.chksync)

    self.incbox = QHBoxLayout()
    self.inclabel = QLabel(self)
    self.inclabel.setText('Increment start time (ms)')
    self.inclabel.adjustSize()
    self.inclabel.setToolTip('Increment mean evoked input start time(s) by this amount on each trial.')
    self.incedit = QLineEdit(self)
    self.incedit.setText('0.0')
    self.incbox.addWidget(self.inclabel)
    self.incbox.addWidget(self.incedit)

    self.layout.addLayout(self.button_box)
    self.layout.addLayout(self.incbox)

    self.tabs.resize(425,200) 

    # Add tabs to widget        
    self.layout.addWidget(self.tabs)
    self.setLayout(self.layout)

    setscalegeom(self, 150, 150, 475, 300)
    self.setWindowTitle('Evoked Inputs')

    self.addRemoveInputButton()
    self.addHideButton()
    self.addtips()

  def lines2val (self,ksearch,val):
    for k in self.dqline.keys():
      if k.count(ksearch) > 0:
        self.dqline[k].setText(str(val))

  def allOff (self): self.lines2val('gbar',0.0)

  def removeAllInputs (self):
    for i in range(len(self.ltabs)): self.removeCurrentInput()
    self.nprox = self.ndist = 0

  def IsProx (self,idx):
    # is this evoked input proximal (True) or distal (False) ?
    try:
      d = self.ld[idx]
      for k in d.keys():
        if k.count('evprox'):
          return True
    except:
      pass
    return False

  def getInputID (self,idx):
    # get evoked input number of the evoked input associated with idx
    try:
      d = self.ld[idx]
      for k in d.keys():
        lk = k.split('_')
        if len(lk) >= 3:
          return int(lk[2])
    except:
      pass
    return -1

  def downShift (self,idx):
    # downshift the evoked input ID, keys, values
    d = self.ld[idx]
    dnew = {} # new dictionary
    newidx = 0 # new evoked input ID
    for k,v in d.items():
      lk = k.split('_')
      if len(lk) >= 3:
        if lk[0]=='sigma':
          newidx = int(lk[3])-1
          lk[3] = str(newidx)
        else:
          newidx = int(lk[2])-1
          lk[2] = str(newidx)
      newkey = '_'.join(lk)
      dnew[newkey] = v
      if k in self.dqline:
        self.dqline[newkey] = self.dqline[k]
        del self.dqline[k]
    self.ld[idx] = dnew
    currtxt = self.tabs.tabText(idx)
    newtxt = currtxt.split(' ')[0] + ' ' + str(newidx)
    self.tabs.setTabText(idx,newtxt)
    # print('d original:',d, 'd new:',dnew)

  def removeInput (self,idx):
    # remove the evoked input specified by idx
    if idx < 0 or idx > len(self.ltabs): return
    # print('removing input at index', idx)
    self.tabs.removeTab(idx)
    tab = self.ltabs[idx]
    self.ltabs.remove(tab)
    d = self.ld[idx]

    isprox = self.IsProx(idx) # is it a proximal input?
    isdist = not isprox # is it a distal input?
    inputID = self.getInputID(idx) # wht's the proximal/distal input number?

    # print('isprox,isdist,inputid',isprox,isdist,inputID)

    for k in d.keys(): 
      if k in self.dqline:
        del self.dqline[k]
    self.ld.remove(d)
    tab.setParent(None)

    # now downshift the evoked inputs (only proximal or only distal) that came after this one
    #  first get the IDs of the evoked inputs to downshift
    lds = [] # list of inputs to downshift
    for jdx in range(len(self.ltabs)):
      if isprox and self.IsProx(jdx) and self.getInputID(jdx) > inputID:
        #print('downshift prox',self.getInputID(jdx))
        lds.append(jdx)
      elif isdist and not self.IsProx(jdx) and self.getInputID(jdx) > inputID:
        #print('downshift dist',self.getInputID(jdx))
        lds.append(jdx)
    for jdx in lds: self.downShift(jdx) # then do the downshifting

    # print(self) # for testing

  def removeCurrentInput (self): # removes currently selected input
    idx = self.tabs.currentIndex()
    if idx < 0: return
    self.removeInput(idx)

  def __str__ (self):
    s = ''
    for k,v in self.dqline.items(): s += k + ': ' + v.text().strip() + os.linesep
    if self.chksync.isChecked(): s += 'sync_evinput: 1'+os.linesep
    else: s += 'sync_evinput: 0'+os.linesep
    s += 'inc_evinput: ' + self.incedit.text().strip() + os.linesep
    return s

  def addRemoveInputButton (self):
    self.bbremovebox = QHBoxLayout() 
    self.btnremove = QPushButton('Remove Input',self)
    self.btnremove.resize(self.btnremove.sizeHint())
    self.btnremove.clicked.connect(self.removeCurrentInput)
    self.btnremove.setToolTip('Remove This Input')
    self.bbremovebox.addWidget(self.btnremove)
    self.layout.addLayout(self.bbremovebox)

  def addHideButton (self):
    self.bbhidebox = QHBoxLayout() 
    self.btnhide = QPushButton('Hide Window',self)
    self.btnhide.resize(self.btnhide.sizeHint())
    self.btnhide.clicked.connect(self.hide)
    self.btnhide.setToolTip('Hide Window')
    self.bbhidebox.addWidget(self.btnhide)
    self.layout.addLayout(self.bbhidebox)

  def addTab (self,s):
    tab = QWidget()
    self.ltabs.append(tab)
    self.tabs.addTab(tab,s)
    tab.layout = QFormLayout()
    tab.setLayout(tab.layout)
    return tab

  def addFormToTab (self,d,tab):
    for k,v in d.items():
      self.dqline[k] = QLineEdit(self)
      self.dqline[k].setText(str(v))
      tab.layout.addRow(self.transvar(k),self.dqline[k]) # adds label,QLineEdit to the tab

  def makePixLabel (self,fn):
    pix = QPixmap(fn)
    pixlbl = ClickLabel(self)
    pixlbl.setPixmap(pix)
    return pixlbl

  def addtransvarfromdict (self,d):
    dtmp = {'L2':'L2/3 ','L5':'L5 '}
    for k in d.keys():
      if k.startswith('gbar'):
        ks = k.split('_')
        stmp = ks[-2]
        self.addtransvar(k,dtmp[stmp[0:2]] + stmp[2:] + ' ' + ks[-1].upper() + u' weight (µS)')
      elif k.startswith('t'):
        self.addtransvar(k,'Start time mean (ms)')
      elif k.startswith('sigma'):
        self.addtransvar(k,'Start time stdev (ms)')
      elif k.startswith('numspikes'):
        self.addtransvar(k,'Number spikes')

  def addProx (self):
    self.nprox += 1 # starts at 1
    # evprox feed strength
    dprox = OrderedDict([('t_evprox_' + str(self.nprox), 0.), # times and stdevs for evoked responses
                         ('sigma_t_evprox_' + str(self.nprox), 2.5),
                         ('numspikes_evprox_' + str(self.nprox), 1),
                         ('gbar_evprox_' + str(self.nprox) + '_L2Pyr_ampa', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L2Pyr_nmda', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L2Basket_ampa', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L2Basket_nmda', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L5Pyr_ampa', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L5Pyr_nmda', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L5Basket_ampa', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L5Basket_nmda', 0.)])
    self.ld.append(dprox)
    self.addtransvarfromdict(dprox)
    self.addFormToTab(dprox, self.addTab('Proximal ' + str(self.nprox)))
    self.ltabs[-1].layout.addRow(self.makePixLabel(lookupresource('proxfig')))
    #print('index to', len(self.ltabs)-1)
    self.tabs.setCurrentIndex(len(self.ltabs)-1)
    #print('index now', self.tabs.currentIndex(), ' of ', self.tabs.count())
    self.addtips()

  def addDist (self):
    self.ndist += 1
    # evdist feed strengths
    ddist = OrderedDict([('t_evdist_' + str(self.ndist), 0.),
                         ('sigma_t_evdist_' + str(self.ndist), 6.),
                         ('numspikes_evdist_' + str(self.ndist), 1),
                         ('gbar_evdist_' + str(self.ndist) + '_L2Pyr_ampa', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L2Pyr_nmda', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L2Basket_ampa', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L2Basket_nmda', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L5Pyr_ampa', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L5Pyr_nmda', 0.)])
    self.ld.append(ddist)
    self.addtransvarfromdict(ddist)
    self.addFormToTab(ddist,self.addTab('Distal ' + str(self.ndist)))
    self.ltabs[-1].layout.addRow(self.makePixLabel(lookupresource('distfig')))
    #print('index to', len(self.ltabs)-1)
    self.tabs.setCurrentIndex(len(self.ltabs)-1)
    #print('index now', self.tabs.currentIndex(), ' of ', self.tabs.count())
    self.addtips()

class OptEvokedInputParamDialog (EvokedInputParamDialog):

  def __init__ (self, optrun_func):
    # self.dqchkbox = OrderedDict()
    super(EvokedInputParamDialog, self).__init__(None)
    self.nprox = self.ndist = 0 # number of proximal,distal inputs
    self.ld = [] # list of dictionaries for proximal/distal inputs
    self.dtab_idx = {} # for translating input names to tab indices
    self.dtab_names = {} # for translating tab indices to input names
    self.dparams = OrderedDict()  # actual values
    self.dqline = OrderedDict() # not used, prevents failure in removeInput

    # these store values used in grid
    self.dqchkbox = OrderedDict()  # optimize
    self.dqparam_name = OrderedDict()  # parameter name
    self.dqinitial_label = OrderedDict()  # initial
    self.dqopt_label = OrderedDict()  # optimtized
    self.dqdiff_label = OrderedDict() # delta
    self.dqrange_multiplier = OrderedDict() # user-defined multiplier
    self.dqrange_mode = OrderedDict() # range mode (stdev, %, absolute)
    self.dqrange_slider = OrderedDict() # slider
    self.dqrange_label = OrderedDict() # defined range

    self.chunk_list = []
    self.lqnumsim = []
    self.lqnumparams = []
    self.opt_params = {}
    self.initial_opt_ranges = []
    self.dtabdata = []
    self.dtransvar = {} # for translating model variable name to more human-readable form
    self.simlength = 0.0
    self.sim_dt = 0.0
    self.default_num_step_sims = 30
    self.default_num_total_sims = 50
    self.optrun_func = optrun_func
    self.optimization_running = False
    self.initUI()

  def initUI (self):
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
    self.btnrecalc = QPushButton('Recalculate Ranges',self)
    self.btnrecalc.resize(self.btnrecalc.sizeHint())
    self.btnrecalc.clicked.connect(self.updateOptDialog)
    self.btnrecalc.setToolTip('Recalculate Ranges')
    self.grid.addWidget(self.btnrecalc, row, 0)

    row += 1
    self.btnrunop = QPushButton('Run Optimization', self)
    self.btnrunop.resize(self.btnrunop.sizeHint())
    self.btnrunop.setToolTip('Run Optimization')
    self.btnrunop.clicked.connect(self.runOptimization)
    self.grid.addWidget(self.btnrunop, row, 0)

    row += 1
    btnhide = QPushButton('Hide Window',self)
    btnhide.resize(btnhide.sizeHint())
    btnhide.clicked.connect(self.hide)
    btnhide.setToolTip('Hide Window')
    self.grid.addWidget(btnhide, row, 0)

    self.setLayout(self.grid)

    self.setWindowTitle("Configure Optimization")

    # the largest horizontal component will be column 0 (headings)
    self.resize(self.minimumSizeHint())

  def toggle_field(self, label):
    widget_dict_list = [self.dqinitial_label, self.dqopt_label,
                          self.dqdiff_label, self.dqparam_name,
                          self.dqrange_mode, self.dqrange_multiplier,
                          self.dqrange_label, self.dqrange_slider]

    if self.dqchkbox[label].isChecked():
      # set all other fields in the row to enabled
      for widget_dict in widget_dict_list:
        widget_dict[label].setEnabled(True)
    else:
      # disable all other fields in the row
      for widget_dict in widget_dict_list:
        widget_dict[label].setEnabled(False)

  def addTab (self,id_str):
    tab = QWidget()
    self.ltabs.append(tab)

    name_str = trans_input(id_str)
    self.tabs.addTab(tab, name_str)
 
    tab_index = len(self.ltabs)-1
    self.tabs.setCurrentIndex(tab_index)
    self.dtab_idx[id_str] = tab_index
    self.dtab_names[tab_index] = id_str

    return tab

  def cleanLabels(self):
    """
    To avoid memory leaks we need to delete all widgets when we recreate grid.
    Go through all tabs and check for each var name (k)
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

  def addGridToTab (self, d, tab):
    from functools import partial
    import re

    current_tab = self.tabs.currentIndex()
    tab.layout = QGridLayout()
    #tab.layout.setSpacing(10)

    self.ltabkeys.append([])

    # The first row has column headings
    row = 0
    self.ltabkeys[current_tab].append("")
    for column_index, column_name in enumerate(["Optimize", "Parameter name",
      "Initial", "Optimized", "Delta"]):
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
    for k,v in d.items():
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
      # use partial instead of lamda (so args won't be evaluated ahead of time?)
      self.dqchkbox[k].clicked.connect(partial(self.toggle_field, k))
      self.dqparam_name[k] = QLabel(self)
      self.dqparam_name[k].setText(self.transvar(k))
      self.dqinitial_label[k] = QLabel()
      self.dqopt_label[k] = QLabel()
      self.dqdiff_label[k] = QLabel()

      # add widgets to grid
      tab.layout.addWidget(self.dqchkbox[k], row, 0, alignment = Qt.AlignBaseline | Qt.AlignCenter)
      tab.layout.addWidget(self.dqparam_name[k], row, 1)
      tab.layout.addWidget(self.dqinitial_label[k], row, 2)  # initial value
      tab.layout.addWidget(self.dqopt_label[k], row, 3)  # optimized value
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
        self.dqrange_slider[k] = QRangeSlider(k,self)
        self.dqrange_slider[k].setMinimumWidth(140)
        self.dqrange_label[k] = QLabel()
        self.dqrange_multiplier[k] = QLineEdit(range_multiplier)
        self.dqrange_multiplier[k].setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.dqrange_multiplier[k].setMinimumWidth(50)
        self.dqrange_multiplier[k].setMaximumWidth(50)
        self.dqrange_mode[k] = QLabel(range_mode)
        tab.layout.addWidget(self.dqrange_multiplier[k], row, 5)  # range specifier
        tab.layout.addWidget(self.dqrange_mode[k], row, 6)  # range mode
        tab.layout.addWidget(self.dqrange_slider[k], row, 7)  # range slider
        tab.layout.addWidget(self.dqrange_label[k], row, 8)  # calculated range

      row += 1

    # A spacer in the last row stretches to fill remaining space.
    # For inputs with fewer parameters than the rest, this pushes parameters
    # to the top with the same spacing as the other inputs.
    tab.layout.addItem(QSpacerItem(0, 0), row, 0, 1, 9)
    tab.layout.setRowStretch(row,1)
    tab.setLayout(tab.layout)

  def addProx (self):
    self.nprox += 1 # starts at 1
    # evprox feed strength
    dprox = OrderedDict([('t_evprox_' + str(self.nprox), 0.), # times and stdevs for evoked responses
                         ('sigma_t_evprox_' + str(self.nprox), 2.5),
                         #('numspikes_evprox_' + str(self.nprox), 1),
                         ('gbar_evprox_' + str(self.nprox) + '_L2Pyr_ampa', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L2Pyr_nmda', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L2Basket_ampa', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L2Basket_nmda', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L5Pyr_ampa', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L5Pyr_nmda', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L5Basket_ampa', 0.),
                         ('gbar_evprox_' + str(self.nprox) + '_L5Basket_nmda', 0.)])
    self.ld.append(dprox)
    self.addtransvarfromdict(dprox)
    tab = self.addTab('evprox_' + str(self.nprox))
    self.addGridToTab(dprox, tab)

  def addDist (self):
    self.ndist += 1
    # evdist feed strengths
    ddist = OrderedDict([('t_evdist_' + str(self.ndist), 0.),
                         ('sigma_t_evdist_' + str(self.ndist), 6.),
                         #('numspikes_evdist_' + str(self.ndist), 1),
                         ('gbar_evdist_' + str(self.ndist) + '_L2Pyr_ampa', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L2Pyr_nmda', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L2Basket_ampa', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L2Basket_nmda', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L5Pyr_ampa', 0.),
                         ('gbar_evdist_' + str(self.ndist) + '_L5Pyr_nmda', 0.)])
    self.ld.append(ddist)
    self.addtransvarfromdict(ddist)
    tab = self.addTab('evdist_' + str(self.ndist))
    self.addGridToTab(ddist, tab)

  def runOptimization(self):
    self.optimization_running = True
    self.current_opt_step = 0

    # update the opt info dict to capture num_sims from GUI
    self.updateOptDialog()

    # run the actual optimization. optrun_func comes from HNNGUI.startoptmodel():
    # passed to BaseParamDialog then finally OptEvokedInputParamDialog
    self.optrun_func()


  def get_chunk_start(self, step):
    return self.chunk_list[step]['opt_start']

  def get_chunk_end(self, step):
    return self.chunk_list[step]['opt_end']

  def get_chunk_weights(self, step):
    return self.chunk_list[step]['weights']

  def get_num_chunks(self):
    return len(self.chunk_list)

  def get_sims_for_chunk(self, step):
    return self.chunk_list[step]['num_sims']

  def get_chunk_ranges(self, step):
    ranges = {}
    for input_name in self.chunk_list[step]['inputs']:
      ranges.update(self.opt_params[input_name]['ranges'])

    return ranges

  def save_opt_grid(self):
    self.old_numsims = []

    for chunk_index in range(len(self.chunk_list)):
      try:
        num_sims = int(self.lqnumsim[chunk_index].text())
      except ValueError:
        # couldn't get value for some reason (invalid), so set to the default
        if chunk_index == len(self.chunk_list) - 1:
          num_sims = self.default_num_total_sims
        else:
          num_sims = self.default_num_step_sims

      self.old_numsims.append(num_sims)

  def clean_opt_grid(self):
    # This is the top part of the Configure Optimization dialog.

    column_count = self.sublayout.columnCount()
    row = 0
    while True:
      try:
        self.sublayout.itemAtPosition(row,0).widget()
      except AttributeError:
        # no more rows
        break

      for column in range(column_count):
        try:
          # Use deleteLater() to avoid memory leaks.
          self.sublayout.itemAtPosition(row, column).widget().deleteLater()
        except AttributeError:
          # if item wasn't found
          pass
      row += 1

  def rebuildOptStepInfo(self):
    # get number of sims from GUI
    self.save_opt_grid()

    if not self.optimization_running:
      # reset data for number of sims per chunk (step)
      self.lqnumsim = []
      self.lqnumparams = []

      # clean up the old grid sublayout
      self.clean_opt_grid()

      # split chunks from paramter file
      self.chunk_list = chunk_evinputs(self.opt_params, self.simlength, self.sim_dt)

      if len(self.chunk_list) == 0:
        qlabel = QLabel("No valid evoked inputs to optimize!")
        qlabel.setAlignment(Qt.AlignBaseline | Qt.AlignLeft)
        qlabel.resize(qlabel.minimumSizeHint())
        self.sublayout.addWidget(qlabel, 0, 0)
        self.btnrunop.setEnabled(False)
        self.btnrecalc.setEnabled(False)
      else:
        self.btnrunop.setEnabled(True)
        self.btnrecalc.setEnabled(True)

    # create a new grid sublayout with a row for each optimization step
    for chunk_index, chunk in enumerate(self.chunk_list):
      if len(self.chunk_list) == len(self.old_numsims):
        # can we reuse the previous number of sims for each step?
        chunk['num_sims'] = self.old_numsims[chunk_index]
      else:
        if chunk_index == len(self.chunk_list) - 1:
          chunk['num_sims'] = self.default_num_total_sims
        else:
          chunk['num_sims'] = self.default_num_step_sims

      chunk['num_params'] = 0

      for input_name in chunk['inputs']:
        num_params = len(self.opt_params[input_name]['ranges'])
        if num_params > 0:
          chunk['num_params'] += num_params

      if self.optimization_running:
        num_params = chunk['num_params']
        self.lqnumparams[chunk_index].setText("Num params: %d" % num_params)
        # don't make changes to the rest of the grid
        continue

      qlabel = QLabel("Optimization step %d:"%(chunk_index+1))
      qlabel.setAlignment(Qt.AlignBaseline | Qt.AlignLeft)
      qlabel.resize(qlabel.minimumSizeHint())
      self.sublayout.addWidget(qlabel,chunk_index, 0)

      inputs = []
      for input_name in chunk['inputs']:
        inputs.append(trans_input(input_name))
      qlabel = QLabel("Inputs: %s"%', '.join(inputs))
      qlabel.setAlignment(Qt.AlignBaseline | Qt.AlignLeft)
      qlabel.resize(qlabel.minimumSizeHint())
      self.sublayout.addWidget(qlabel,chunk_index, 1)

      # spacer here for readability of input names and reduce size
      # of "Num simulations:"
      self.sublayout.addItem(QSpacerItem(0, 0, hPolicy = QSizePolicy.MinimumExpanding), chunk_index, 2)

      self.lqnumparams.append(QLabel("Num params: %d"%chunk['num_params']))
      self.lqnumparams[chunk_index].setAlignment(Qt.AlignBaseline | Qt.AlignLeft)
      self.lqnumparams[chunk_index].resize(self.lqnumparams[chunk_index].minimumSizeHint())
      self.sublayout.addWidget(self.lqnumparams[chunk_index],chunk_index, 3)

      qlabel = QLabel("Num simulations:")
      qlabel.setAlignment(Qt.AlignBaseline | Qt.AlignLeft)
      qlabel.resize(qlabel.minimumSizeHint())
      self.sublayout.addWidget(qlabel,chunk_index, 4)

      self.lqnumsim.append(QLineEdit(str(chunk['num_sims'])))
      self.lqnumsim[chunk_index].resize(
        self.lqnumsim[chunk_index].minimumSizeHint())
      self.sublayout.addWidget(self.lqnumsim[chunk_index],
                               chunk_index, 5)

  def toggleEnableUserFields(self, step, enable=True):
    if not enable:
      # the optimization called this to disable parameters on
      # for the step passed in to this function
      self.current_opt_step = step

    for input_name in self.chunk_list[step]['inputs']:
      tab_index = self.dtab_idx[input_name]
      tab = self.ltabs[tab_index]

      for row_index in range(2, tab.layout.rowCount()-1):  # last row is a spacer
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
            (label,timing_sigma))

    if timing_sigma == 0.0:
      # sigma of 0 will not produce a CDF
      timing_sigma = 0.01

    return timing_sigma

  def createOptParams(self):
    global decay_multiplier

    if not self.optimization_running:
      # do not preserve opt_params if not optimizing
      self.opt_params = {}
    else:
      return

    # iterate through tabs. data is contained in grid layout
    for tab_index in range(len(self.ltabs)):
      tab_name = self.dtab_names[tab_index]

      timing_sigma = self.get_input_timing_sigma(tab_name)
      self.opt_params[tab_name] = {'ranges': {},
                                  'sigma': timing_sigma,
                                  'decay_multiplier': decay_multiplier}

  def populate_initial_opt_ranges(self):
    self.initial_opt_ranges = {}

    for input_name in self.opt_params.keys():
      self.initial_opt_ranges[input_name] = self.opt_params[input_name]['ranges'].copy()

  def updateOptDeltas(self):
    # iterate through tabs. data is contained in grid layout
    for tab_index, tab in enumerate(self.ltabs):
      tab_name = self.dtab_names[tab_index]

      # update the initial value
      for row_index in range(2, tab.layout.rowCount()-1):  # last row is a spacer
        label = self.ltabkeys[tab_index][row_index]
        value = self.dparams[label]

        # Calculate value to put in "Delta" column. When possible, use
        # percentages, but when initial value is 0, use absolute changes
        if tab_name not in self.initial_opt_ranges or \
           not self.dqchkbox[label].isChecked():
          self.dqdiff_label[label].setEnabled(False)
          self.dqinitial_label[label].setText(("%6f"%self.dparams[label]).rstrip('0').rstrip('.'))
          text = '--'
          color_fmt = "QLabel { color : black; }"
          self.dqopt_label[label].setText(text)
          self.dqopt_label[label].setStyleSheet(color_fmt)
          self.dqopt_label[label].setAlignment(Qt.AlignHCenter)
          self.dqdiff_label[label].setAlignment(Qt.AlignHCenter)
        else:
          initial_value = float(self.initial_opt_ranges[tab_name][label]['initial'])
          self.dqinitial_label[label].setText(("%6f"%initial_value).rstrip('0').rstrip('.'))

          self.dqopt_label[label].setText(("%6f"%self.dparams[label]).rstrip('0').rstrip('.'))
          self.dqopt_label[label].setAlignment(Qt.AlignVCenter|Qt.AlignLeft)
          self.dqdiff_label[label].setAlignment(Qt.AlignVCenter|Qt.AlignLeft)

          if isclose(value, initial_value, abs_tol=1e-7):
            diff = 0
            text = "0.0"
            color_fmt = "QLabel { color : black; }"
          else:
            diff = value - initial_value

          if initial_value == 0:
            # can't calculate %
            if diff < 0:
              text = ("%6f"%diff).rstrip('0').rstrip('.')
              color_fmt = "QLabel { color : red; }"
            elif diff > 0:
              text = ("+%6f"%diff).rstrip('0').rstrip('.')
              color_fmt = "QLabel { color : green; }"
          else:
            # calculate percent difference
            percent_diff = 100 * diff/initial_value
            if percent_diff < 0:
              text = ("%2.2f %%"%percent_diff)
              color_fmt = "QLabel { color : red; }"
            elif percent_diff > 0:
              text = ("+%2.2f %%"%percent_diff)
              color_fmt = "QLabel { color : green; }"

        self.dqdiff_label[label].setStyleSheet(color_fmt)
        self.dqdiff_label[label].setText(text)

  def updateRangeFromSlider(self, label, range_min, range_max):
    import re

    label_match = re.search('(evprox|evdist)_([0-9]+)', label)
    if label_match:
      tab_name = label_match.group(1) + '_' + label_match.group(2)
    else:
      print("ERR: can't determine input name from parameter: %s" % label)
      return

    if range_min > self.opt_params[tab_name]['ranges'][label]['initial']:
      self.opt_params[tab_name]['ranges'][label]['initial'] = range_min
    if range_max < self.opt_params[tab_name]['ranges'][label]['initial']:
      self.opt_params[tab_name]['ranges'][label]['initial'] = range_max

    self.dqrange_label[label].setText(format_range_str(range_min) + " - " +
                                      format_range_str(range_max))
    self.opt_params[tab_name]['ranges'][label]['minval'] = range_min
    self.opt_params[tab_name]['ranges'][label]['maxval'] = range_max

  def updateOptRanges(self):
    max_width = 0

    # iterate through tabs. data is contained in grid layout
    for tab_index, tab in enumerate(self.ltabs):
      tab_name = self.dtab_names[tab_index]

      if not self.optimization_running:
        # before optimization has started update 'mean', 'sigma',
        # 'start', and 'user_end'
        start_time_label = 't_' + tab_name
        try:
          try:
            range_multiplier = float(self.dqrange_multiplier[start_time_label].text())
          except ValueError:
            range_multiplier = 0.0
          value = self.dparams[start_time_label]
          timing_sigma = self.get_input_timing_sigma(tab_name)
          timing_bound = timing_sigma * range_multiplier
          range_min = max(0, value - timing_bound)
          range_max = min(self.simlength, value + timing_bound)
          self.opt_params[tab_name]['mean'] = value
          self.opt_params[tab_name]['sigma'] = value
          self.opt_params[tab_name]['user_start'] = range_min
          self.opt_params[tab_name]['user_end'] = range_max
        except KeyError:
          print("ERR: could not find start time parameter: %s" % start_time_label)
          continue

      # now update the ranges
      for row_index in range(2, tab.layout.rowCount()-1):  # last row is a spacer
        label = self.ltabkeys[tab_index][row_index]

        if not self.dqchkbox[label].isChecked():
          # remove this param from the dictionary used during opt.
          if label in self.opt_params[tab_name]['ranges']:
            del self.opt_params[tab_name]['ranges'][label]
          continue
        elif self.optimization_running:
          if tab_name in self.chunk_list[self.current_opt_step]['inputs']:
            # we are currently optimizating the input on this tab. make no
            # changes
            continue

        if tab_name not in self.initial_opt_ranges:
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

        if self.optimization_running:
          continue

        if range_type == "(max)":
          range_min = 0
          try:
            range_max = float(self.dqrange_mode[label].text())
          except ValueError:
            range_max = 1.0
        elif range_type == "(stdev)":  # timing
          range_min = self.opt_params[tab_name]['user_start']
          range_max = self.opt_params[tab_name]['user_end']
        else:  # range_type == "(%)"
          range_min = max(0, value - (value * range_multiplier / 100.0))
          range_max = value + (value * range_multiplier / 100.0)

        # add param to list for optimization
        self.opt_params[tab_name]['ranges'][label] = {'initial': value, 'minval': range_min, 'maxval': range_max }

        # set up the slider
        self.dqrange_slider[label].setMin(range_min)
        self.dqrange_slider[label].setMax(range_max)

        self.dqrange_slider[label].setRange(range_min, range_max)
        if range_min == range_max:
          self.dqrange_label[label].setText(format_range_str(range_min))  # use the exact value
          self.dqrange_label[label].setEnabled(False)
          # uncheck because invalid range
          self.dqchkbox[label].setChecked(False)
          # disable slider
          self.dqrange_slider[label].setEnabled(False)
        else:
          self.dqrange_label[label].setText(format_range_str(range_min) +
                                            " - " +
                                            format_range_str(range_max))

        if self.dqrange_label[label].sizeHint().width() > max_width:
          max_width = self.dqrange_label[label].sizeHint().width() + 15
        # fix the size for the defined range so that changing the slider doesn't change
        # the dialog's width
        self.dqrange_label[label].setMinimumWidth(max_width)
        self.dqrange_label[label].setMaximumWidth(max_width)

  def updateOptDialog(self):
    self.updateOptRanges()
    self.rebuildOptStepInfo()
    self.updateOptDeltas()

  def setfromdin (self,din):
    if not din:
      return

    if 'dt' in din:
      # din proivdes a complete parameter set
      self.din = din
      self.simlength = float(din['tstop'])
      self.sim_dt = float(din['dt'])

      self.cleanLabels()
      self.removeAllInputs() # turn off any previously set inputs
      self.ltabkeys = []
      self.dtab_idx = {}
      self.dtab_names = {}

      for evinput in get_inputs(din):
        if 'evprox_' in evinput:
          self.addProx()
        elif 'evdist_' in evinput:
          self.addDist()

    for k,v in din.items():
      if k in self.dparams:
        try:
          new_value = float(v)
        except ValueError:
          print("WARN: bad value for param %s: %s. Unable to convert"
                " to a floating point number" % (k,v))
          continue
        self.dparams[k] = new_value
      elif k.count('gbar') > 0 and \
           (k.count('evprox') > 0 or \
            k.count('evdist') > 0):
        # NOTE: will be deprecated in future release
        # for back-compat with old-style specification which didn't have ampa,nmda in evoked gbar
        try:
          new_value = float(v)
        except ValueError:
          print("WARN: bad value for param %s: %s. Unable to convert"
                " to a floating point number" % (k,v))
          continue
        lks = k.split('_')
        eloc = lks[1]
        enum = lks[2]
        base_key_str = 'gbar_' + eloc + '_' + enum + '_'
        if eloc == 'evprox':
          for ct in ['L2Pyr','L2Basket','L5Pyr','L5Basket']:
            # ORIGINAL MODEL/PARAM: only ampa for prox evoked inputs
            key_str = base_key_str + ct + '_ampa'
            self.dparams[key_str] = new_value
        elif eloc == 'evdist':
          for ct in ['L2Pyr','L2Basket','L5Pyr']:
            # ORIGINAL MODEL/PARAM: both ampa and nmda for distal evoked inputs
            key_str = base_key_str + ct + '_ampa'
            self.dparams[key_str] = new_value
            key_str = base_key_str + ct + '_nmda'
            self.dparams[key_str] = new_value

    self.createOptParams()
    self.updateOptDialog()

  def __str__ (self):
    # don't write any values to param file
    return ''

# widget to specify run params (tstop, dt, etc.) -- not many params here
class RunParamDialog (DictDialog):
  def __init__ (self, parent, din = None):
    super(RunParamDialog, self).__init__(parent,din)
    self.addHideButton()

  def initd (self):

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
    self.addtransvar('dt','Integration timestep (ms)')
    self.addtransvar('celsius','Temperature (C)')
    self.addtransvar('threshold','Firing threshold (mV)')
    self.addtransvar('N_trials','Trials')
    self.addtransvar('save_spec_data','Save spectral data')
    self.addtransvar('save_figs','Save figures')
    self.addtransvar('f_max_spec', 'Max spectral frequency (Hz)')
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

  def initExtra (self):
    DictDialog.initExtra(self)
    self.dqextra['NumCores'] = QLineEdit(self)
    self.dqextra['NumCores'].setText(str(defncore))
    self.addtransvar('NumCores','Number Cores')
    self.ltabs[0].layout.addRow('NumCores',self.dqextra['NumCores'])

  def getntrial (self): return int(self.dqline['N_trials'].text().strip())

  def getncore (self): return int(self.dqextra['NumCores'].text().strip())

  def setfromdin (self,din):
    if not din: return

    # number of cores may have changed if the configured number failed
    self.dqextra['NumCores'].setText(str(defncore))
    for k,v in din.items():
      if k in self.dqline:
        self.dqline[k].setText(str(v).strip())

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

# dialog for visualizing model
class VisnetDialog (QDialog):
  def __init__ (self, parent):
    super(VisnetDialog, self).__init__(parent)
    self.initUI()

  def showcells3D (self): Popen([getPyComm(), 'visnet.py', 'cells', paramf]) # nonblocking
  def showEconn (self): Popen([getPyComm(), 'visnet.py', 'Econn', paramf]) # nonblocking
  def showIconn (self): Popen([getPyComm(), 'visnet.py', 'Iconn', paramf]) # nonblocking

  def runvisnet (self):
    lcmd = [getPyComm(), 'visnet.py', 'cells']
    #if self.chkcells.isChecked(): lcmd.append('cells')
    #if self.chkE.isChecked(): lcmd.append('Econn')
    #if self.chkI.isChecked(): lcmd.append('Iconn')
    lcmd.append(paramf)
    Popen(lcmd) # nonblocking

  def initUI (self):

    self.layout = QVBoxLayout(self)

    # Add stretch to separate the form layout from the button
    # self.layout.addStretch(1)

    """
    self.chkcells = QCheckBox('Cells in 3D',self)
    self.chkcells.resize(self.chkcells.sizeHint())
    self.chkcells.setChecked(True)
    self.layout.addWidget(self.chkcells)
    self.chkE = QCheckBox('Excitatory Connections',self)
    self.chkE.resize(self.chkE.sizeHint())
    self.layout.addWidget(self.chkE)

    self.chkI = QCheckBox('Inhibitory Connections',self)
    self.chkI.resize(self.chkI.sizeHint())
    self.layout.addWidget(self.chkI)
    """

    # Create a horizontal box layout to hold the buttons
    self.button_box = QHBoxLayout()
 
    self.btnok = QPushButton('Visualize',self)
    self.btnok.resize(self.btnok.sizeHint())
    self.btnok.clicked.connect(self.runvisnet)
    self.button_box.addWidget(self.btnok)

    self.btncancel = QPushButton('Cancel',self)
    self.btncancel.resize(self.btncancel.sizeHint())
    self.btncancel.clicked.connect(self.hide)
    self.button_box.addWidget(self.btncancel)

    self.layout.addLayout(self.button_box)
        
    setscalegeom(self, 100, 100, 300, 100)

    self.setWindowTitle('Visualize Model')

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

    self.netbtn = QPushButton('Model'+os.linesep+'Visualization',self)
    self.netbtn.setIcon(QIcon(lookupresource('netfig')))
    self.netbtn.clicked.connect(self.parent().showvisnet)
    self.grid.addWidget(self.netbtn,gRow,3,1,1)

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

    self.pixNet = QPixmap(lookupresource('netfig'))
    self.pixNetlbl = ClickLabel(self)
    self.pixNetlbl.setScaledContents(True)
    self.pixNetlbl.setPixmap(self.pixNet)
    # self.pixNetlbl.clicked.connect(self.showvisnet)
    self.grid.addWidget(self.pixNetlbl,gRow,3,1,1)

    self.setLayout(grid)

class BaseParamDialog (QDialog):
  # base widget for specifying params (contains buttons to create other widgets
  def __init__ (self, parent, optrun_func):
    super(BaseParamDialog, self).__init__(parent)
    self.proxparamwin = self.distparamwin = self.netparamwin = self.syngainparamwin = None
    self.initUI()
    self.runparamwin = RunParamDialog(self)
    self.cellparamwin = CellParamDialog(self)
    self.netparamwin = NetworkParamDialog(self)    
    self.syngainparamwin = SynGainParamDialog(self,self.netparamwin)
    self.proxparamwin = OngoingInputParamDialog(self,'Proximal')
    self.distparamwin = OngoingInputParamDialog(self,'Distal')
    self.evparamwin = EvokedInputParamDialog(self,None)
    self.optparamwin = OptEvokedInputParamDialog(optrun_func)
    self.poisparamwin = PoissonInputParamDialog(self,None)
    self.tonicparamwin = TonicInputParamDialog(self,None)
    self.lsubwin = [self.runparamwin, self.cellparamwin, self.netparamwin,
                    self.proxparamwin, self.distparamwin, self.evparamwin,
                    self.poisparamwin, self.tonicparamwin, self.optparamwin]
    self.updateDispParam()

  def updateDispParam (self):
    # now update the GUI components to reflect the param file selected
    din = quickreadprm(paramf)
    if not 'tstop' in din:
      print("WARNING: could not find a complete parameter file")
      return

    if usingEvokedInputs(din): # default for evoked is to show average dipole
      conf.dconf['drawavgdpl'] = True
    elif usingOngoingInputs(din): # default for ongoing is NOT to show average dipole
      conf.dconf['drawavgdpl'] = False

    for dlg in self.lsubwin: dlg.setfromdin(din) # update to values from file
    self.qle.setText(paramf.split(os.path.sep)[-1].split('.param')[0]) # update simulation name

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
    self.qle.setText(paramf.split(os.path.sep)[-1].split('.param')[0])
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
        
    setscalegeom(self, 100, 100, 400, 100)

    self.setWindowTitle('Set Parameters')    

  def saveparams (self, checkok = True):
    global paramf,basedir
    tmpf = os.path.join(dconf['paramoutdir'],self.qle.text() + '.param')
    oktosave = True
    if os.path.isfile(tmpf) and checkok:
      self.show()
      oktosave = False
      msg = QMessageBox()
      msg.setIcon(QMessageBox.Warning)
      msg.setText(tmpf + ' already exists. Over-write?')
      msg.setWindowTitle('Over-write file(s)?')
      msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)      
      if msg.exec_() == QMessageBox.Ok:
          oktosave = True

    if oktosave:
      with open(tmpf,'w') as fp:
        fp.write(str(self))

      paramf = dconf['paramf'] = tmpf # update paramf
      basedir = os.path.join(dconf['datdir'], self.qle.text())
      os.makedirs(basedir, exist_ok=True)

    return oktosave

  def updatesaveparams (self, dtest):
    if debug: print('BaseParamDialog updatesaveparams: dtest=',dtest)
    # update parameter values in GUI (so user can see and so GUI will save these param values)
    for win in self.lsubwin: win.setfromdin(dtest)
    # save parameters - do not ask if can over-write the param file
    self.saveparams(checkok = False)

  def __str__ (self):
    s = 'sim_prefix: ' + self.qle.text() + os.linesep
    s += 'expmt_groups: {' + self.qle.text() + '}' + os.linesep
    for win in self.lsubwin: s += str(win)
    return s

# clickable label
class ClickLabel (QLabel):
  """
  def __init__(self, *args, **kwargs):
    QLabel.__init__(self)
    # self._pixmap = QPixmap(self.pixmap())
    # spolicy = QSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding)
    spolicy = QSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
    # spolicy = QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred)
    # spolicy.setHorizontalStretch(0)
    # spolicy.setVerticalStretch(0)
    self.setSizePolicy(spolicy)
    self.setMinimumWidth(150)
    self.setMinimumHeight(150)
  def setPixmap (self, pm):
    QLabel.setPixmap(self,pm)
    self._pixmap = pm
  """
  clicked = pyqtSignal()
  def mousePressEvent(self, event):
    self.clicked.emit()
  """
  def resizeEvent(self, event):
    self.setPixmap(self._pixmap.scaled(
      self.width(), self.height(),
      QtCore.Qt.KeepAspectRatio))
  """

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
    global dfile, paramf
    super().__init__()   
    self.runningsim = False
    self.runthread = None
    self.fontsize = dconf['fontsize']
    self.linewidth = plt.rcParams['lines.linewidth'] = 1
    self.markersize = plt.rcParams['lines.markersize'] = 5
    self.dextdata = OrderedDict() # external data
    self.schemwin = SchematicDialog(self)
    self.m = self.toolbar = None
    self.baseparamwin = BaseParamDialog(self, self.startoptmodel)
    self.optMode = False
    self.initUI()
    self.visnetwin = VisnetDialog(self)
    self.helpwin = HelpDialog(self)
    self.erselectdistal = EvokedOrRhythmicDialog(self, True, self.baseparamwin.evparamwin, self.baseparamwin.distparamwin)
    self.erselectprox = EvokedOrRhythmicDialog(self, False, self.baseparamwin.evparamwin, self.baseparamwin.proxparamwin)
    self.waitsimwin = WaitSimDialog(self)
    default_param = os.path.join(dconf['dbase'],'data','default')
    first_load = not (os.path.exists(default_param))
    if first_load:
      QMessageBox.information(self, "HNN", "Welcome to HNN! Default parameter file loaded. Press 'Run Simulation' to display simulation output")
    else:
      self.statusBar().showMessage("Loaded %s"%default_param)

  def redraw (self):
    # redraw simulation & external data
    self.m.plot()
    self.m.draw()

  def changeFontSize (self):
    # bring up window to change font sizes
    i, ok = QInputDialog.getInt(self, "Set Font Size","Font Size:", plt.rcParams['font.size'], 1, 100, 1)
    if ok:
      self.fontsize = plt.rcParams['font.size'] = dconf['fontsize'] = i
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
    global paramf,basedir,dfile
    qfd = QFileDialog()
    qfd.setHistory([os.path.join(dconf['dbase'],'data')])
    fn = qfd.getOpenFileName(self, 'Open param file',
                                     os.path.join(hnn_root_dir,'param')) # uses forward slash, even on Windows OS
    if fn[0]:
      paramf = os.path.abspath(fn[0]) # to make sure have right path separators on Windows OS
      param_fname = os.path.splitext(os.path.basename(paramf))
      basedir = os.path.join(dconf['datdir'], param_fname[0])
      try:
        dfile = getinputfiles(paramf) # reset input data - if already exists
      except:
        pass
      # now update the GUI components to reflect the param file selected
      self.baseparamwin.updateDispParam()
      self.initSimCanvas() # recreate canvas
      # self.m.plot() # replot data
      self.setWindowTitle(paramf)
      # store the sim just loaded in simdat's list - is this the desired behavior? or should we first erase prev sims?
      import simdat
      if 'dpl' in simdat.ddat:
        simdat.updatelsimdat(paramf,simdat.ddat['dpl']) # update lsimdat and its current sim index
      self.populateSimCB() # populate the combobox

      if len(self.dextdata) > 0:
        self.toggleEnableOptimization(True)

  def loadDataFile (self, fn):
    # load a dipole data file
    global paramf

    import simdat
    try:
      self.dextdata[fn] = np.loadtxt(fn)
      simdat.ddat['dextdata'] = self.dextdata
      print('Loaded data in ', fn)
    except:
      raise
      print('WARNING: could not load data in ', fn)
      return False
    try:
      self.m.plot()
      self.m.draw() # make sure new lines show up in plot

      if paramf:
        self.toggleEnableOptimization(True)
      return True
    except:
      print('WARNING: could not plot data from ', fn)
      raise
      return False

  def loadDataFileDialog (self):
    # bring up window to select/load external dipole data file
    qfd = QFileDialog()
    qfd.setHistory([os.path.join(dconf['dbase'],'data')])
    fn = qfd.getOpenFileName(self, 'Open data file',
                                     os.path.join(hnn_root_dir,'data'))
    if fn[0]: self.loadDataFile(os.path.abspath(fn[0])) # use abspath to make sure have right path separators

  def clearDataFile (self):
    # clear external dipole data
    import simdat
    self.m.clearlextdatobj()
    self.dextdata = simdat.ddat['dextdata'] = OrderedDict()
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
    from __init__ import __version__
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
    global basedir, dfile
    if not float(self.baseparamwin.runparamwin.getval('save_vsoma')):
      smsg='In order to view somatic voltages you must first rerun the simulation with saving somatic voltages. To do so from the main GUI, click on Set Parameters -> Run -> Analysis -> Save Somatic Voltages, enter a 1 and then rerun the simulation.'
      msg = QMessageBox()
      msg.setIcon(QMessageBox.Information)
      msg.setText(smsg)
      msg.setWindowTitle('Rerun simulation')
      msg.setStandardButtons(QMessageBox.Ok)      
      msg.exec_()
    else:
      basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
      lcmd = [getPyComm(), 'visvolt.py',paramf]
      if debug: print('visvolt cmd:',lcmd)
      Popen(lcmd) # nonblocking

  def showPSDPlot (self):
    # start the PSD visualization process (separate window)
    global basedir
    basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
    lcmd = [getPyComm(), 'vispsd.py',paramf]
    if debug: print('vispsd cmd:',lcmd)
    Popen(lcmd) # nonblocking

  def showLFPPlot (self):
    # start the LFP visualization process (separate window)
    global basedir
    basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
    lcmd = [getPyComm(), 'vislfp.py',paramf]
    if debug: print('vislfp cmd:',lcmd)
    Popen(lcmd) # nonblocking

  def showSpecPlot (self):
    # start the spectrogram visualization process (separate window)
    global basedir
    basedir = os.path.join(dconf['datdir'],paramf.split(os.path.sep)[-1].split('.param')[0])
    lcmd = [getPyComm(), 'visspec.py',paramf]
    if debug: print('visspec cmd:',lcmd)
    Popen(lcmd) # nonblocking

  def showRasterPlot (self):
    # start the raster plot visualization process (separate window)
    global basedir
    lcmd = [getPyComm(), 'visrast.py',paramf,os.path.join(basedir,'spk.txt')]
    if dconf['drawindivrast']: lcmd.append('indiv')
    if debug: print('visrast cmd:',lcmd)
    Popen(lcmd) # nonblocking

  def showDipolePlot (self):
    # start the dipole visualization process (separate window)
    global basedir
    lcmd = [getPyComm(), 'visdipole.py',paramf,os.path.join(basedir,'dpl.txt')]
    if debug: print('visdipole cmd:',lcmd)
    Popen(lcmd) # nonblocking    

  def showwaitsimwin (self):
    # show the wait sim window (has simulation log)
    bringwintotop(self.waitsimwin)

  def togAvgDpl (self):
    # toggle drawing of the average (across trials) dipole
    conf.dconf['drawavgdpl'] = not conf.dconf['drawavgdpl']
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

  def updateDatCanv (self,fn):
    # update the simulation data and canvas
    try:
      getinputfiles(fn) # reset input data - if already exists
    except:
      pass
    # now update the GUI components to reflect the param file selected
    self.baseparamwin.updateDispParam()
    self.initSimCanvas() # recreate canvas
    self.setWindowTitle(fn)

  def removeSim (self):
    # remove the currently selected simulation
    global paramf,basedir,dfile
    import simdat
    if debug: print('removeSim',paramf,simdat.lsimidx)
    if len(simdat.lsimdat) > 0 and simdat.lsimidx >= 0:
      cidx = self.cbsim.currentIndex() # 
      a = simdat.lsimdat[:cidx]
      b = simdat.lsimdat[cidx+1:]
      c = [x for x in a]
      for x in b: c.append(x)
      simdat.lsimdat = c
      self.cbsim.removeItem(cidx)
      simdat.lsimidx = max(0,len(simdat.lsimdat) - 1)
      if len(simdat.lsimdat) > 0:
        paramf = simdat.lsimdat[simdat.lsimidx][0]
        param_fname = os.path.splitext(os.path.basename(paramf))
        basedir = os.path.join(dconf['datdir'], param_fname[0])
        if debug: print('new paramf:',paramf,simdat.lsimidx)
        self.updateDatCanv(paramf)
        self.cbsim.setCurrentIndex(simdat.lsimidx)
      else:
        self.clearSimulations()

  def prevSim (self):
    # go to previous simulation 
    global paramf,dfile
    import simdat
    if debug: print('prevSim',paramf,simdat.lsimidx)
    if len(simdat.lsimdat) > 0 and simdat.lsimidx > 0:
      simdat.lsimidx -= 1
      paramf = simdat.lsimdat[simdat.lsimidx][0]
      param_fname = os.path.splitext(os.path.basename(paramf))
      basedir = os.path.join(dconf['datdir'], param_fname[0])
      if debug: print('new paramf:',paramf,simdat.lsimidx)
      self.updateDatCanv(paramf)
      self.cbsim.setCurrentIndex(simdat.lsimidx)

  def nextSim (self):
    # go to next simulation
    global paramf,basedir,dfile
    import simdat
    if debug: print('nextSim',paramf,simdat.lsimidx)
    if len(simdat.lsimdat) > 0 and simdat.lsimidx + 1 < len(simdat.lsimdat):
      simdat.lsimidx += 1
      paramf = simdat.lsimdat[simdat.lsimidx][0]
      param_fname = os.path.splitext(os.path.basename(paramf))
      basedir = os.path.join(dconf['datdir'], param_fname[0])
      if debug: print('new paramf:',paramf,simdat.lsimidx)
      self.updateDatCanv(paramf)
      self.cbsim.setCurrentIndex(simdat.lsimidx)

  def clearSimulationData (self):
    # clear the simulation data
    global paramf
    import simdat
    paramf = '' # set paramf to empty so no data gets loaded
    basedir = None
    simdat.ddat = {} # clear data in simdat.ddat
    simdat.lsimdat = []
    simdat.lsimidx = 0
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
    import simdat
    self.clearSimulationData()
    self.m.clearlextdatobj() # clear the external data
    self.dextdata = simdat.ddat['dextdata'] = OrderedDict()
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

    runSimNSGAct = QAction('Run simulation on NSG', self)
    runSimNSGAct.setShortcut('Ctrl+N')
    runSimNSGAct.setStatusTip('Run simulation on Neuroscience Gateway Portal (requires NSG account and internet connection).')
    runSimNSGAct.triggered.connect(self.controlNSGsim)

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
    viewDipoleAction = QAction('View Simulation Dipoles',self)
    viewDipoleAction.setStatusTip('View Simulation Dipoles')
    viewDipoleAction.triggered.connect(self.showDipolePlot)
    viewMenu.addAction(viewDipoleAction)
    viewRasterAction = QAction('View Simulation Spiking Activity',self)
    viewRasterAction.setStatusTip('View Simulation Raster Plot')
    viewRasterAction.triggered.connect(self.showRasterPlot)
    viewMenu.addAction(viewRasterAction)
    viewPSDAction = QAction('View PSD',self)
    viewPSDAction.setStatusTip('View PSD')
    viewPSDAction.triggered.connect(self.showPSDPlot)
    viewMenu.addAction(viewPSDAction)

    viewSomaVAction = QAction('View Somatic Voltage',self)
    viewSomaVAction.setStatusTip('View Somatic Voltage')
    viewSomaVAction.triggered.connect(self.showSomaVPlot)
    viewMenu.addAction(viewSomaVAction)

    if testLFP:
      viewLFPAction = QAction('View Simulation LFPs',self)
      viewLFPAction.setStatusTip('View LFP')
      viewLFPAction.triggered.connect(self.showLFPPlot)
      viewMenu.addAction(viewLFPAction)

    viewSpecAction = QAction('View Spectrograms',self)
    viewSpecAction.setStatusTip('View Spectrograms/Dipoles from Experimental Data')
    viewSpecAction.triggered.connect(self.showSpecPlot)
    viewMenu.addAction(viewSpecAction)

    viewMenu.addSeparator()
    viewSchemAction = QAction('View Model Schematics',self)
    viewSchemAction.setStatusTip('View Model Schematics')
    viewSchemAction.triggered.connect(self.showschematics)
    viewMenu.addAction(viewSchemAction)
    viewNetAction = QAction('View Local Network (3D)',self)
    viewNetAction.setStatusTip('View Local Network Model (3D)')
    viewNetAction.triggered.connect(self.showvisnet)
    viewMenu.addAction(viewNetAction)
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
    if dconf['nsgrun']: simMenu.addAction(runSimNSGAct)
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
    self.grid.addWidget(self.pbtn, gRow, 0, 1, 1)

    self.pfbtn = pfbtn = QPushButton('Set Parameters From File', self)
    pfbtn.setToolTip('Set Parameters From File')
    pfbtn.resize(pfbtn.sizeHint())
    pfbtn.clicked.connect(self.selParamFileDialog)
    self.grid.addWidget(self.pfbtn, gRow, 1, 1, 1)

    self.btnsim = btn = QPushButton('Run Simulation', self)
    btn.setToolTip('Run Simulation')
    btn.resize(btn.sizeHint())
    btn.clicked.connect(self.controlsim)
    self.grid.addWidget(self.btnsim, gRow, 2, 1, 1)

    self.qbtn = qbtn = QPushButton('Quit', self)
    qbtn.clicked.connect(QCoreApplication.instance().quit)
    qbtn.resize(qbtn.sizeHint())
    self.grid.addWidget(self.qbtn, gRow, 3, 1, 1)
    
  def shownetparamwin (self): bringwintotop(self.baseparamwin.netparamwin)
  def showoptparamwin (self): bringwintotop(self.baseparamwin.optparamwin)
  def showdistparamwin (self): bringwintotop(self.erselectdistal)
  def showproxparamwin (self): bringwintotop(self.erselectprox)
  def showvisnet (self): Popen([getPyComm(), 'visnet.py', 'cells', paramf]) # nonblocking
  def showschematics (self): bringwintotop(self.schemwin)

  def addParamImageButtons (self,gRow):
    # add parameter image buttons to the GUI

    self.locbtn = QPushButton('Local Network'+os.linesep+'Connections',self)
    self.locbtn.setIcon(QIcon(lookupresource('connfig')))
    self.locbtn.clicked.connect(self.shownetparamwin)
    self.grid.addWidget(self.locbtn,gRow,0,1,1)

    self.proxbtn = QPushButton('Proximal Drive'+os.linesep+'Thalamus',self)
    self.proxbtn.setIcon(QIcon(lookupresource('proxfig')))
    self.proxbtn.clicked.connect(self.showproxparamwin)
    self.grid.addWidget(self.proxbtn,gRow,1,1,1)

    self.distbtn = QPushButton('Distal Drive NonLemniscal'+os.linesep+'Thal./Cortical Feedback',self)
    self.distbtn.setIcon(QIcon(lookupresource('distfig')))
    self.distbtn.clicked.connect(self.showdistparamwin)
    self.grid.addWidget(self.distbtn,gRow,2,1,1)

    self.netbtn = QPushButton('Model'+os.linesep+'Visualization',self)
    self.netbtn.setIcon(QIcon(lookupresource('netfig')))
    self.netbtn.clicked.connect(self.showvisnet)
    self.grid.addWidget(self.netbtn,gRow,3,1,1)

    gRow += 1

    return

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

    self.pixNet = QPixmap(lookupresource('netfig'))
    self.pixNetlbl = ClickLabel(self)
    self.pixNetlbl.setScaledContents(True)
    self.pixNetlbl.setPixmap(self.pixNet)
    # self.pixNetlbl.clicked.connect(self.showvisnet)
    self.grid.addWidget(self.pixNetlbl,gRow,3,1,1)


  def initUI (self):
    # initialize the user interface (UI)

    self.initMenu()
    self.statusBar()

    setscalegeomcenter(self, 1500, 1300) # start GUI in center of screenm, scale based on screen w x h 

    self.setWindowTitle(paramf)
    QToolTip.setFont(QFont('SansSerif', 10))        

    self.grid = grid = QGridLayout()
    #grid.setSpacing(10)

    gRow = 0

    self.addButtons(gRow)

    gRow += 1

    self.initSimCanvas(gRow=gRow, reInit=False)
    gRow += 2

    # store any sim just loaded in simdat's list - is this the desired behavior? or should we start empty?
    import simdat
    if 'dpl' in simdat.ddat:
      simdat.updatelsimdat(paramf,simdat.ddat['dpl']) # update lsimdat and its current sim index

    self.cbsim = QComboBox(self)
    self.populateSimCB() # populate the combobox
    self.cbsim.activated[str].connect(self.onActivateSimCB)
    self.grid.addWidget(self.cbsim, gRow, 0, 1, 3)#, 1, 3)
    self.btnrmsim = QPushButton('Remove Simulation',self)
    self.btnrmsim.resize(self.btnrmsim.sizeHint())
    self.btnrmsim.clicked.connect(self.removeSim)
    self.btnrmsim.setToolTip('Remove Currently Selected Simulation')
    self.grid.addWidget(self.btnrmsim, gRow, 3)#, 4, 1)

    gRow += 1
    self.addParamImageButtons(gRow)

    # need a separate widget to put grid on
    widget = QWidget(self)
    widget.setLayout(grid)
    self.setCentralWidget(widget)

    self.c = Communicate()
    self.c.commsig.connect(self.baseparamwin.updateDispParam)

    self.d = DoneSignal()
    self.d.finishSim.connect(self.done)

    try: self.setWindowIcon(QIcon(os.path.join('res','icon.png')))
    except: pass

    self.schemwin.show() # so it's underneath main window

    if 'dataf' in dconf:
      if os.path.isfile(dconf['dataf']):
        self.loadDataFile(dconf['dataf'])

    self.show()

  def onActivateSimCB (self, s):
    # load simulation when activating simulation combobox
    global paramf,basedir,dfile
    import simdat
    if debug: print('onActivateSimCB',s,paramf,self.cbsim.currentIndex(),simdat.lsimidx)
    if self.cbsim.currentIndex() != simdat.lsimidx:
      if debug: print('Loading',s)
      paramf = s
      param_fname = os.path.splitext(os.path.basename(paramf))
      basedir = os.path.join(dconf['datdir'], param_fname[0])
      simdat.lsimidx = self.cbsim.currentIndex()
      self.updateDatCanv(paramf)

  def populateSimCB (self):
    # populate the simulation combobox
    if debug: print('populateSimCB')
    global paramf
    self.cbsim.clear()
    import simdat
    for l in simdat.lsimdat:
      self.cbsim.addItem(l[0])
    self.cbsim.setCurrentIndex(simdat.lsimidx)

  def initSimCanvas (self,recalcErr=True,optMode=False,gRow=1,reInit=True):
    # initialize the simulation canvas, loading any required data

    gCol = 0

    if reInit == True:
      self.grid.itemAtPosition(gRow, gCol).widget().deleteLater()
      self.grid.itemAtPosition(gRow + 1, gCol).widget().deleteLater()

    if debug: print('paramf in initSimCanvas:',paramf)
    self.m = SIMCanvas(paramf, parent = self, width=10, height=1, dpi=getmplDPI(), optMode=optMode) # also loads data
    # this is the Navigation widget
    # it takes the Canvas widget and a parent
    self.toolbar = NavigationToolbar(self.m, self)
    gWidth = 4
    self.grid.addWidget(self.toolbar, gRow, gCol, 1, gWidth)
    self.grid.addWidget(self.m, gRow + 1, gCol, 1, gWidth)
    if len(self.dextdata.keys()) > 0:
      import simdat
      simdat.ddat['dextdata'] = self.dextdata
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

  def controlNSGsim (self):
    # control simulation on NSG
    if self.runningsim:
      self.stopsim() # stop sim works but leaves subproc as zombie until this main GUI thread exits
    else:
      self.startsim(self.baseparamwin.runparamwin.getntrial(),self.baseparamwin.runparamwin.getncore(),True)

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

    # optimize the model
    self.setcursors(Qt.WaitCursor)
    print('Starting model optimization. . .')

    if debug: print('in optmodel')
    self.runningsim = True

    self.statusBar().showMessage("Optimizing model. . .")
    self.btnsim.setText("Stop Optimization") 
    self.qbtn.setEnabled(False)

    self.runthread = RunSimThread(self.c, self.d, ntrial, ncore, self.waitsimwin, opt=True, baseparamwin=self.baseparamwin, mainwin=self, onNSG=False)

    # We have all the events we need connected we can start the thread
    self.runthread.start()
    # At this point we want to allow user to stop/terminate the thread
    # so we enable that button
    self.btnsim.setText("Stop Optimization") 
    self.qbtn.setEnabled(False)
    bringwintotop(self.waitsimwin)

  def startsim (self, ntrial, ncore, onNSG=False):
    # start the simulation
    if not self.baseparamwin.saveparams(): return # make sure params saved and ok to run

    self.setcursors(Qt.WaitCursor)

    print('Starting simulation (%d cores). . .'%ncore)
    self.runningsim = True

    if onNSG:
      self.statusBar().showMessage("Running simulation on Neuroscience Gateway Portal. . .")
    else:
      self.statusBar().showMessage("Running simulation. . .")

    self.runthread=RunSimThread(self.c,self.d,ntrial,ncore,self.waitsimwin,opt=False,baseparamwin=None,mainwin=None,onNSG=onNSG)

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

  def done (self, optMode, failed):
    # called when the simulation completes running
    if debug: print('done')
    self.runningsim = False
    self.waitsimwin.hide()
    self.statusBar().showMessage("")
    self.btnsim.setText("Run Simulation")
    self.qbtn.setEnabled(True)
    self.initSimCanvas(optMode=optMode) # recreate canvas (plots too) to avoid incorrect axes
    # self.m.plot()
    global basedir
    self.setcursors(Qt.ArrowCursor)
    if failed:
      msg = "Failed "
    else:
      msg = "Finished "

    if optMode:
      msg += "running optimization "
    else:
      msg += "running sim "

    QMessageBox.information(self, "Done!", msg + "using " + paramf + '. Saved data/figures in: ' + basedir)
    self.setWindowTitle(paramf)
    self.populateSimCB() # populate the combobox

if __name__ == '__main__':    
  app = QApplication(sys.argv)
  ex = HNNGUI()
  sys.exit(app.exec_())  
