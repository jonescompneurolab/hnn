import os.path as op
import os
import sys
import shlex
from subprocess import Popen, PIPE

from numpy import loadtxt
from numpy.testing import assert_allclose


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

def test_view_rast():
    if 'SYSTEM_USER_DIR' in os.environ:
        basedir = os.environ['SYSTEM_USER_DIR']
    else:
        basedir = os.path.expanduser('~')

    spike_file = os.path.join(basedir, 'spk.txt')
    paramf = op.join('param', 'default.param')
    cmd = sys.executable + ' visrast.py ' + paramf + ' ' + spike_file

    view_window(cmd)

def test_view_dipole():
    if 'SYSTEM_USER_DIR' in os.environ:
        basedir = os.environ['SYSTEM_USER_DIR']
    else:
        basedir = os.path.expanduser('~')

    dipole_file = os.path.join(basedir, 'dpl.txt')
    paramf = op.join('param', 'default.param')
    cmd = sys.executable + ' visrast.py ' + paramf + ' ' + dipole_file

    view_window(cmd)

def test_view_psd():
    paramf = op.join('param', 'default.param')
    cmd = sys.executable + ' vispsd.py ' + paramf
    view_window(cmd)

def test_view_spec():
    paramf = op.join('param', 'default.param')
    cmd = sys.executable + ' visspec.py ' + paramf
    view_window(cmd)
