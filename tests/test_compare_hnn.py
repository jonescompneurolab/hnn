import os.path as op

from numpy import loadtxt
from numpy.testing import assert_allclose

from mne.utils import _fetch_file


def test_hnn():
    """Test to check that HNN produces consistent results"""
    # small snippet of data on data branch for now. To be deleted
    # later. Data branch should have only commit so it does not
    # pollute the history.
    from subprocess import Popen, PIPE
    import shlex
    import os
    import sys

    ntrials = 3
    paramf = op.join('param', 'default.param')

    nrniv_str = 'nrniv -python -nobanner'
    cmd = nrniv_str + ' ' + sys.executable + ' run.py ' + paramf \
        + ' ntrial ' + str(ntrials)

    # Split the command into shell arguments for passing to Popen
    cmdargs = shlex.split(cmd, posix="win" not in sys.platform)

    # Start the simulation
    proc = Popen(cmdargs, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                 cwd=os.getcwd(), universal_newlines=True)
    out, err = proc.communicate()

    # print all messages (including error messages)
    print('STDOUT', out)
    print('STDERR', err)

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
