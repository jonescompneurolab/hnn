""" GUI for viewing data from individual/all trials"""

# Authors: Sam Neymotin <samnemo@gmail.com>
#          Blake Caldwell <blake_caldwell@brown.edu>

import os

from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QWidget, QComboBox
from PyQt5.QtWidgets import QGridLayout, QInputDialog
from PyQt5.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
import matplotlib.pyplot as plt

from .qt_lib import getmplDPI
from .paramrw import get_output_dir

fontsize = plt.rcParams['font.size'] = 10


class DataViewGUI(QMainWindow):
    def __init__(self, CanvasType, params, title):
        super().__init__()

        global fontsize

        self.fontsize = fontsize
        self.linewidth = plt.rcParams['lines.linewidth'] = 1
        self.markersize = plt.rcParams['lines.markersize'] = 5
        self.CanvasType = CanvasType
        self.ntrial = params['N_trials']
        self.params = params
        self.title = title
        self.initUI()

    def initMenu(self):
        exitAction = QAction(QIcon.fromTheme('exit'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit ' + self.title + '.')
        exitAction.triggered.connect(qApp.quit)

        menubar = self.menuBar()
        self.fileMenu = menubar.addMenu('&File')
        menubar.setNativeMenuBar(False)
        self.fileMenu.addAction(exitAction)

        viewMenu = menubar.addMenu('&View')
        changeFontSizeAction = QAction('Change Font Size', self)
        changeFontSizeAction.setStatusTip('Change Font Size.')
        changeFontSizeAction.triggered.connect(self.changeFontSize)
        viewMenu.addAction(changeFontSizeAction)
        changeLineWidthAction = QAction('Change Line Width', self)
        changeLineWidthAction.setStatusTip('Change Line Width.')
        changeLineWidthAction.triggered.connect(self.changeLineWidth)
        viewMenu.addAction(changeLineWidthAction)
        changeMarkerSizeAction = QAction('Change Marker Size', self)
        changeMarkerSizeAction.setStatusTip('Change Marker Size.')
        changeMarkerSizeAction.triggered.connect(self.changeMarkerSize)
        viewMenu.addAction(changeMarkerSizeAction)

    def changeFontSize(self):
        global fontsize

        i, okPressed = QInputDialog.getInt(self, "Set Font Size",
                                           "Font Size:",
                                           plt.rcParams['font.size'], 1, 100,
                                           1)
        if okPressed:
            self.fontsize = plt.rcParams['font.size'] = fontsize = i
            self.initCanvas()
            self.m.plot()

    def changeLineWidth(self):
        i, okPressed = QInputDialog.getInt(self, "Set Line Width",
                                           "Line Width:",
                                           plt.rcParams['lines.linewidth'], 1,
                                           20, 1)
        if okPressed:
            self.linewidth = plt.rcParams['lines.linewidth'] = i
            self.initCanvas()
            self.m.plot()

    def changeMarkerSize(self):
        i, okPressed = QInputDialog.getInt(self, "Set Marker Size",
                                           "Font Size:", self.markersize, 1,
                                           100, 1)
        if okPressed:
            self.markersize = plt.rcParams['lines.markersize'] = i
            self.initCanvas()
            self.m.plot()

    def printStat(self, s):
        print(s)
        self.statusBar().showMessage(s)

    def initCanvas(self):
        """Initialize canvas

        This function will add widgets, which may create a memory leak if it
        is called repeatedly (according to a comment in the previous code).
        The previous code addressed it with the following:

        self.grid.removeWidget(self.m)
        self.grid.removeWidget(self.toolbar)
        self.m.setParent(None)
        self.toolbar.setParent(None)
        self.m = self.toolbar = None
        """

        self.m = self.CanvasType(self.params, self.index, parent=self,
                                 width=12, height=10, dpi=getmplDPI())
        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar2QT(self.m, self)
        self.grid.addWidget(self.toolbar, 0, 0, 1, 4)
        self.grid.addWidget(self.m, 1, 0, 1, 4)

    def updateCB(self):
        self.cb.clear()
        if self.ntrial > 1:
            self.cb.addItem('Show All Trials')
            for i in range(self.ntrial):
                self.cb.addItem('Show Trial ' + str(i + 1))
        else:
            self.cb.addItem('All Trials')
        self.cb.activated[int].connect(self.onActivated)

    def initUI(self):
        self.initMenu()
        self.statusBar()
        self.setGeometry(300, 300, 1300, 1100)
        self.setWindowTitle(self.title + ' - ' +
                            os.path.join(get_output_dir(), 'data',
                                         self.params['sim_prefix'] +
                                         '.param'))
        self.grid = grid = QGridLayout()
        self.index = 0
        self.initCanvas()
        self.cb = QComboBox(self)
        self.grid.addWidget(self.cb, 2, 0, 1, 4)

        self.updateCB()

        # need a separate widget to put grid on
        widget = QWidget(self)
        widget.setLayout(grid)
        self.setCentralWidget(widget)

        self.setWindowIcon(QIcon(os.path.join('res', 'icon.png')))

        self.show()

    def onActivated(self, idx):
        if idx != self.index:
            self.index = idx
            if self.index == 0:
                self.statusBar().showMessage('Loading data from all trials.')
            else:
                self.statusBar().showMessage('Loading data from trial ' +
                                             str(self.index) + '.')
            self.m.index = self.index
            self.initCanvas()
            self.m.plot()
            self.statusBar().showMessage('')
