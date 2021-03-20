import os.path as op
import sys
from numpy import loadtxt
from numpy.testing import assert_allclose

from mne.utils import _fetch_file
from PyQt5 import QtWidgets, QtCore
import pytest

from hnn import HNNGUI
from hnn.paramrw import get_output_dir, get_fname


def run_hnn(qtbot, monkeypatch):
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
    qtbot.waitUntil(lambda: main.runningsim, 10000)

    # wait up to 300 seconds for simulation to finish
    qtbot.waitUntil(lambda: not main.runningsim, 300000)
    qtbot.mouseClick(main.qbtn, QtCore.Qt.LeftButton)
    assert exit_calls == [1]


@pytest.mark.skipif(sys.platform == 'win32',
                    reason="does not run on windows")
def test_hnn(qtbot, monkeypatch):
    """Test HNN can run a simulation"""

    run_hnn(qtbot, monkeypatch)
    dirname = op.join(get_output_dir(), 'data', 'default')
    dipole_fn = get_fname(dirname, 'normdpl', 0)
    pr = loadtxt(op.join(dirname, dipole_fn))
    assert len(pr) > 0


@pytest.mark.skip(reason="Skipping until #232 verification is complete")
def test_compare_hnn(qtbot, monkeypatch):
    """Test simulation data are consistent with master"""

    # do we need to run a simulation?
    run_sim = False
    dirname = op.join(get_output_dir(), 'data', 'default')
    for data_type in ['normdpl', 'rawspk']:
        fname = get_fname(dirname, data_type, 0)
        if not op.exists(fname):
            run_sim = True
            break

    if run_sim:
        run_hnn(qtbot, monkeypatch)

    data_dir = ('https://raw.githubusercontent.com/jonescompneurolab/'
                'hnn/test_data/')
    for data_type in ['normdpl', 'rawspk']:
        fname = get_fname(dirname, data_type, 0)
        data_url = op.join(data_dir, fname)
        if not op.exists(fname):
            _fetch_file(data_url, fname)

        pr = loadtxt(op.join(dirname, fname))
        master = loadtxt(fname)

        assert_allclose(pr[:, 1], master[:, 1], rtol=1e-4, atol=0)
        assert_allclose(pr[:, 2], master[:, 2], rtol=1e-4, atol=0)
        assert_allclose(pr[:, 3], master[:, 3], rtol=1e-4, atol=0)
