import os.path as op
import os
import sys
import shlex
from subprocess import Popen, PIPE

from numpy import loadtxt
from numpy.testing import assert_allclose


def test_view_dipole():
    """Test to check that Dipole viewer displays without error"""

    if 'SYSTEM_USER_DIR' in os.environ:
        basedir = os.environ['SYSTEM_USER_DIR']
    else:
        basedir = os.path.expanduser('~')

    dipole_file = os.path.join(basedir, 'dpl.txt')
    paramf = op.join('param', 'default.param')
    cmd = sys.executable + ' visdipole.py ' + paramf + ' ' + dipole_file

    # Split the command into shell arguments for passing to Popen
    cmdargs = shlex.split(cmd, posix="win" not in sys.platform)

    # Start the simulation
    proc = Popen(cmdargs, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                    cwd=os.getcwd(), universal_newlines=True)
    out, err = proc.communicate()

    # print all messages (including error messages)
    print('STDOUT', out)
    print('STDERR', err)
