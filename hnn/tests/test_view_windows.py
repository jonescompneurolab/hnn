import os.path as op

from mne.utils import _fetch_file

from hnn import HNNGUI


def fetch_file(fname):
    data_dir = ('https://raw.githubusercontent.com/jonescompneurolab/'
                'hnn/test_data/')

    data_url = op.join(data_dir, fname)
    if not op.exists(fname):
        _fetch_file(data_url, fname)


def test_view_rast(qtbot):
    """Show the spiking activity window"""
    fname = 'spk.txt'
    fetch_file(fname)

    # start the GUI
    main = HNNGUI()
    qtbot.addWidget(main)

    main.viewRasterAction.trigger()


def test_view_dipole(qtbot):
    """Show the dipole window"""
    fname = 'dpl.txt'
    fetch_file(fname)

    # start the GUI
    main = HNNGUI()
    qtbot.addWidget(main)

    main.viewDipoleAction.trigger()


def test_view_psd(qtbot):
    """Show the PSD window"""
    fname = 'dpl.txt'
    fetch_file(fname)

    # start the GUI
    main = HNNGUI()
    qtbot.addWidget(main)

    main.viewPSDAction.trigger()


def test_view_spec(qtbot):
    """Show the pectrogram window"""
    fname = 'dpl.txt'
    fetch_file(fname)

    # start the GUI
    main = HNNGUI()
    qtbot.addWidget(main)

    main.viewSpecAction.trigger()


# def test_view_soma(qtbot):
#     fname = 'spike.txt'
#     fetch_file(fname)

#     # start the GUI
#     main = HNNGUI()
#     qtbot.addWidget(main)

#     main.viewSomaVAction.trigger()
