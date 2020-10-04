import os.path as op
import os
import sys

from numpy import loadtxt
from numpy.testing import assert_allclose

from mne.utils import _fetch_file
from PyQt5 import QtWidgets, QtCore

from hnn import HNNGUI


def test_hnn(qtbot, monkeypatch):
    """Test to check that HNN produces consistent results"""

    # for pressing exit button
    exit_calls = []
    monkeypatch.setattr(QtWidgets.QApplication, "exit",
                        lambda: exit_calls.append(1))

    # skip in warning messages
    monkeypatch.setattr(QtWidgets.QMessageBox, "warning",
                        lambda *args: QtWidgets.QMessageBox.Ok)
    monkeypatch.setattr(QtWidgets.QMessageBox, "information",
                        lambda *args: QtWidgets.QMessageBox.Ok)

    main = HNNGUI()
    qtbot.addWidget(main)

    # start the simulation by pressing the button
    qtbot.mouseClick(main.btnsim, QtCore.Qt.LeftButton)
    qtbot.waitUntil(lambda: main.runningsim)

    # wait up to 100 seconds for simulation to finish
    qtbot.waitUntil(lambda: not main.runningsim, 100000)
    qtbot.mouseClick(main.qbtn, QtCore.Qt.LeftButton)
    assert exit_calls == [1]

    # only testing default configuration with 1 trial
    ntrials = 1

    for trial in range(ntrials):
        print("Checking data for trial %d" % trial)
        if 'SYSTEM_USER_DIR' in os.environ:
            basedir = os.environ['SYSTEM_USER_DIR']
        else:
            basedir = os.path.expanduser('~')
        dirname = op.join(basedir, 'hnn_out', 'data', 'default')

        data_dir = ('https://raw.githubusercontent.com/jonescompneurolab/'
                    'hnn/test_data/')
        for data_type in ['dpl', 'rawdpl', 'i']:
            sys.stdout.write("%s..." % data_type)

            fname = "%s_%d.txt" % (data_type, trial)
            data_url = op.join(data_dir, fname)
            if not op.exists(fname):
                _fetch_file(data_url, fname)

            print("comparing %s" % fname)
            pr = loadtxt(op.join(dirname, fname))
            master = loadtxt(fname)

            assert_allclose(pr[:, 1], master[:, 1], rtol=1e-8, atol=0)
            if data_type in ['dpl', 'rawdpl', 'i']:
                assert_allclose(pr[:, 2], master[:, 2], rtol=1e-8, atol=0)
            if data_type in ['dpl', 'rawdpl']:
                assert_allclose(pr[:, 3], master[:, 3], rtol=1e-8, atol=0)
            print("done")
