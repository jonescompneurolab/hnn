import sys
from PyQt5.QtWidgets import QApplication

from hnn import HNNGUI

def runqt5 ():
    app = QApplication(sys.argv)
    ex = HNNGUI()
    sys.exit(app.exec_())

if __name__ == '__main__':
    runqt5()
