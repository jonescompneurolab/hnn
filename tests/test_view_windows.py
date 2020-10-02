import os.path as op
import os
import sys
import shlex
from subprocess import Popen, PIPE

from mne.utils import _fetch_file


def fetch_file(fname):
    data_dir = ('https://raw.githubusercontent.com/jonescompneurolab/'
                'hnn/test_data/')

    data_url = op.join(data_dir, fname)
    if not op.exists(fname):
        _fetch_file(data_url, fname)


def view_window(cmd):
    """Test to check that viewer displays without error"""

    # Split the command into shell arguments for passing to Popen
    cmdargs = shlex.split(cmd, posix="win" not in sys.platform)

    # Start the simulation
    proc = Popen(cmdargs, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                 cwd=os.getcwd(), universal_newlines=True)
    out, err = proc.communicate()

    # print all messages (including error messages)
    print('STDOUT', out)
    print('STDERR', err)

    if proc.returncode != 0:
        raise RuntimeError("Running command %s failed" % cmd)


def test_view_rast():
    if 'SYSTEM_USER_DIR' in os.environ:
        basedir = os.environ['SYSTEM_USER_DIR']
    else:
        basedir = os.path.expanduser('~')

    fetch_file('spk.txt')
    ntrials = 3
    for trial_idx in range(ntrials):
        fetch_file('spk_%d.txt' % trial_idx)

    spike_file = os.path.join(basedir, 'spk.txt')
    paramf = op.join('param', 'default.param')
    cmd = sys.executable + ' visrast.py ' + paramf + ' ' + spike_file

    view_window(cmd)


def test_view_dipole():
    if 'SYSTEM_USER_DIR' in os.environ:
        basedir = os.environ['SYSTEM_USER_DIR']
    else:
        basedir = os.path.expanduser('~')

    fetch_file('dpl.txt')
    ntrials = 3
    for trial_idx in range(ntrials):
        fetch_file('dpl_%d.txt' % trial_idx)

    dipole_file = os.path.join(basedir, 'dpl.txt')
    paramf = op.join('param', 'default.param')
    cmd = sys.executable + ' visdipole.py ' + paramf + ' ' + dipole_file

    view_window(cmd)


def test_view_psd():
    paramf = op.join('param', 'default.param')
    cmd = sys.executable + ' vispsd.py ' + paramf
    view_window(cmd)


def test_view_spec():
    paramf = op.join('param', 'default.param')
    cmd = sys.executable + ' visspec.py ' + paramf
    view_window(cmd)
