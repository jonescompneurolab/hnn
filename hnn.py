"""Main file to launch HNN GUI"""

# Authors: Sam Neymotin <samnemo@gmail.com>
#          Blake Caldwell <blake_caldwell@brown.edu>

import sys
from PyQt5 import QtWidgets

from hnn import HNNGUI


def runqt5():
    app = QtWidgets.QApplication(sys.argv)
    HNNGUI()
    sys.exit(app.exec_())


if __name__ == '__main__':
    runqt5()
