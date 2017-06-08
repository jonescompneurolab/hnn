import sys, os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QToolTip, QPushButton, QFormLayout
from PyQt5.QtWidgets import QMenu, QSizePolicy, QMessageBox, QWidget, QFileDialog, QComboBox, QTabWidget
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QDialog, QGridLayout, QLineEdit, QLabel
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal, QObject, pyqtSlot
from PyQt5 import QtCore
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

# GUI for viewing data from individual/all trials
class DataViewGUI (QMainWindow):
  def __init__ (self, CanvasType, paramf, ntrial):
    super().__init__()        
    self.CanvasType = CanvasType
    self.paramf = paramf
    self.ntrial = ntrial
    self.initUI()

  def initMenu (self):
    exitAction = QAction(QIcon.fromTheme('exit'), 'Exit', self)        
    exitAction.setShortcut('Ctrl+Q')
    exitAction.setStatusTip('Exit HNN PSD Viewer.')
    exitAction.triggered.connect(qApp.quit)

    menubar = self.menuBar()
    self.fileMenu = menubar.addMenu('&File')
    menubar.setNativeMenuBar(False)
    self.fileMenu.addAction(exitAction)

  def printStat (self,s):
    print(s)
    self.statusBar().showMessage(s)

  def initCanvas (self):
    try: # to avoid memory leaks remove any pre-existing widgets before adding new ones
      self.grid.removeWidget(self.m)
      self.grid.removeWidget(self.toolbar)
      self.m.setParent(None)
      self.toolbar.setParent(None)
      self.m = self.toolbar = None
    except:
      pass
    self.m = self.CanvasType(self.paramf, self.index, parent = self, width=12, height=10)
    # this is the Navigation widget
    # it takes the Canvas widget and a parent
    self.toolbar = NavigationToolbar(self.m, self)
    self.grid.addWidget(self.toolbar, 0, 0, 1, 4); 
    self.grid.addWidget(self.m, 1, 0, 1, 4);     

  def initUI (self):
    self.initMenu()
    self.statusBar()
    self.setGeometry(300, 300, 1300, 1100)
    self.setWindowTitle('HNN PSD Viewer - ' + self.paramf)
    self.grid = grid = QGridLayout()
    self.index = 0
    self.initCanvas()
    self.cb = QComboBox(self)
    self.grid.addWidget(self.cb,2,0,1,4)

    if self.ntrial > 0:
      self.cb.addItem('Show All Trials')
      for i in range(self.ntrial):
        self.cb.addItem('Show Trial ' + str(i+1))
    else:
      self.cb.addItem('All Trials')
    self.cb.activated[int].connect(self.onActivated) 

    # need a separate widget to put grid on
    widget = QWidget(self)
    widget.setLayout(grid)
    self.setCentralWidget(widget);

    self.show()

  def onActivated(self, idx):
    if idx != self.index:
      self.index = idx
      if self.index == 0:
        self.statusBar().showMessage('Loading data from all trials.')
      else:
        self.statusBar().showMessage('Loading data from trial ' + str(self.index) + '.')
      self.m.index = self.index
      self.initCanvas()
      self.m.plot()
      self.statusBar().showMessage('')
