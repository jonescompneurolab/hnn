import os.path as op

import pytest
from mne.utils import _fetch_file

from hnn import HNNGUI


def fetch_file(fname):
    data_dir = ('https://raw.githubusercontent.com/jonescompneurolab/'
                'hnn/test_data/')

    data_url = op.join(data_dir, fname)
    if not op.exists(fname):
        _fetch_file(data_url, fname)


@pytest.mark.skip(reason="Skipping until #232 improves launching view windows")
def test_view_rast(qtbot):
    """Show the spiking activity window"""
    fname = 'spk.txt'
    fetch_file(fname)

    # start the GUI
    main = HNNGUI()
    qtbot.addWidget(main)

    main.viewRasterAction.trigger()


@pytest.mark.skip(reason="Skipping until #232 improves launching view windows")
def test_view_dipole(qtbot):
    """Show the dipole window"""
    fname = 'dpl.txt'
    fetch_file(fname)

    # start the GUI
    main = HNNGUI()
    qtbot.addWidget(main)

    main.viewDipoleAction.trigger()


@pytest.mark.skip(reason="Skipping until #232 improves launching view windows")
def test_view_psd(qtbot):
    """Show the PSD window"""
    fname = 'dpl.txt'
    fetch_file(fname)

    # start the GUI
    main = HNNGUI()
    qtbot.addWidget(main)

    main.viewPSDAction.trigger()


@pytest.mark.skip(reason="Skipping until #232 improves launching view windows")
def test_view_spec(qtbot):
    """Show the pectrogram window"""
    fname = 'dpl.txt'
    fetch_file(fname)

    # start the GUI
    main = HNNGUI()
    qtbot.addWidget(main)

    main.viewSpecAction.trigger()


@pytest.mark.skip(reason="Skipping until #232 improves launching view windows")
def test_view_soma(qtbot):
    fname = 'spike.txt'
    fetch_file(fname)

    # start the GUI
    main = HNNGUI()
    qtbot.addWidget(main)

    main.viewSomaVAction.trigger()
