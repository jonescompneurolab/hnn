import os.path as op
import pytest

from numpy import loadtxt
from numpy.testing import assert_array_equal

from mne.utils import _fetch_file


def test_hnn():
    """Test to check that HNN produces consistent results"""
    # small snippet of data on data branch for now. To be deleted
    # later. Data branch should have only commit so it does not
    # pollute the history.
    data_url = ('https://raw.githubusercontent.com/jonescompneurolab/'
                'hnn-core/test_data/dpl.txt')
    if not op.exists('dpl.txt'):
        _fetch_file(data_url, 'dpl.txt')
    dpl_master = loadtxt('dpl.txt')

    from subprocess import Popen, PIPE
    import shlex
    import os
    from sys import platform

    cmd = 'nrniv -python -nobanner run.py'

    # Split the command into shell arguments for passing to Popen
    cmdargs = shlex.split(cmd, posix="win" not in platform)

    # Start the simulation
    proc = Popen(cmdargs, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                    cwd=os.getcwd(), universal_newlines=True)
    out, err = proc.communicate()

    # print all messages (including error messages)
    print('STDOUT', out)
    print('STDERR', err)

    fname = os.environ['HOME'] + '/hnn_out/data/default/dpl.txt'
    dpl_pr = loadtxt(fname)
    assert_array_equal(dpl_pr[:, 2], dpl_master[:, 2])  # L2
    assert_array_equal(dpl_pr[:, 3], dpl_master[:, 3])  # L5
