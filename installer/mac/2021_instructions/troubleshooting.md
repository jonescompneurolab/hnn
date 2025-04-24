# Troubleshooting on Mac OS

First, run the `post-install.sh` script. Save this output and please include it when creating a [GitHub issue](https://github.com/jonescompneurolab/hnn/issues)

```bash
installer/mac/check-post.sh
```

## Simulation log says "processes failed to start"

Check the simulation log (View menu) or the console output where "`python hnn.py`" was run. If you get a message like the following, then your PATH environment variable needs to be updated to include the NEURON binaries, like `nrniv`

```bash
Starting simulation. . .
--------------------------------------------------------------------------
mpiexec was unable to launch the specified application as it could not find an executable:

Executable: nrniv
Node: My-MacBook-Pro.local

while attempting to start process rank 0.
--------------------------------------------------------------------------
```

## Running simulations fail with "dyld: Library not loaded: /usr/X11/lib/libX11.6.dylib"

The full text of the error message in the terminal window will look something like:

```none
dyld: Library not loaded: /usr/X11/lib/libX11.6.dylib
  Referenced from: /Applications/NEURON-7.7/nrn/x86_64/bin/nrniv
  Reason: image not found

```

This error has been seen when upgrading macOS to Catalina 10.15. It occurs because files from XQuartz get removed during the upgrade. To fix this error, reinstall XQuartz following the instructions under "Prerequisite 1: XQuartz" on the [macOS native install page](native_install.md)

## Stream of error messages from MPI

When running an HNN simulation, you may get a message back immediately from HNN that all simulations have finished, but with a stream of error messages in the terminal window and no results in the GUI.

Some examples of the error messages:

```none
OPAL ERROR: Not initialized in file pmix3x_client.c at line 113
```

* Since OPAL is a part of MPI, we can reason that this is a problem when NEURON tries to call mpiexec.

```none
Local abort before MPI_INIT completed successfully

--------------------------------------------------------------------------
mpiexec noticed that the job aborted, but has no info as to the process
that caused that situation.
--------------------------------------------------------------------------
```

* These are standard error messages that openmpi produces when there's an error on one process. Since we are running an openmpi process for each core that HNN runs on, these messages will be repeated.

* Please open a [GitHub issue](https://github.com/jonescompneurolab/hnn/issues) (including the output from `check-post.sh`) if you notice a MPI error not documented here.

## NEURON/MPI debugging (deprecated)

The steps below have not been updated for new version of NEURON that get installed with `pip install`. They may be useful for advanced troubleshooting, however.

### MPI debugging, step 1:  NEURON (part 1)

To remove NEURON from the list of possible problems, try running `nrniv -nopython` from the command line. You should get a `oc>` prompt when there are no problems.

### MPI debugging, step 2: Python

As a simple debugging step, make sure that NEURON can load the necessary python libraries:

```bash
$ nrniv -python
NEURON -- VERSION 7.6.5 master (f3dad62b) 2019-01-11
Duke, Yale, and the BlueBrain Project -- Copyright 1984-2018
See http://neuron.yale.edu/neuron/credits

loading membrane mechanisms from x86_64/.libs/libnrnmech.so
Additional mechanisms from files
 mod/ar.mod mod/beforestep_py.mod mod/ca.mod mod/cad.mod mod/cat.mod mod/dipole.mod mod/dipole_pp.mod mod/hh2.mod mod/kca.mod mod/km.mod mod/lfp.mod mod/mea.mod mod/vecevent.mod
>>>
```

Exit the prompt by typing `quit()`.  If you didn't get any errors, then proceed to the next troubleshooting step. If you get the following error about "No module named 'encodings'", then the problem has to do with environment variables.

```bash
$ nrniv -python
NEURON -- VERSION 7.6.5 master (f3dad62b) 2019-01-11
Duke, Yale, and the BlueBrain Project -- Copyright 1984-2018
See http://neuron.yale.edu/neuron/credits

loading membrane mechanisms from x86_64/.libs/libnrnmech.so
Additional mechanisms from files
 mod/ar.mod mod/beforestep_py.mod mod/ca.mod mod/cad.mod mod/cat.mod mod/dipole.mod mod/dipole_pp.mod mod/hh2.mod mod/kca.mod mod/km.mod mod/lfp.mod mod/mea.mod mod/vecevent.mod
Fatal Python error: initfsencoding: unable to load the file system codec
ModuleNotFoundError: No module named 'encodings'

Current thread 0x000000010a2e45c0 (most recent call first):
Abort trap: 6
```

This message about 'encodings' means that NEURON is unable to load default python libraries, despite being able to start python. Note these are core libraries, not a package that needs to be installed. So we should be able to fix the problem with environment variables. Start by changing one at a time and re-running `nrniv -python`. If you get the '>>>' prompt, move on to the next step.

* PYTHONHOME: You shouldn't need to set this because it will often be determined by the location of the python binary used. However, if it is set to an invalid value, then `nrniv -python` will fail. Try unsetting it:

   ```bash
   unset PYTHONHOME
   ```

   If you are still having problems, set PYTHONHOME to the python installation directory that is the parent to all of the directories bin, lib, doc, and etc.

* NRN_PYLIB: this may not need to be set. Try unsetting it:

  ```bash
  unset NRN_PYLIB
  ```

  If it must be set, make sure that it points to a valid .dylib file that matches the python binary you are using (i.e. don't mix and match anaconda python with a homebrew dylib)

  * conda: `export NRN_PYLIB=~/miniconda3/envs/hnn/lib/libpython3.6m.dylib`
  * homebrew: `export NRN_PYLIB="/usr/local/Cellar/python3/3.7.2_2/Frameworks/Python.framework/Versions/3.7/lib/libpython3.7m.dylib"`

### MPI debugging, step 3: NEURON (part 2)

Based on the previous step, we know that `nrniv` can start python, but this step checks if python can load neuron libraries, By importing the neuron module into python, you should get something similar to the below:

```bash
$ python
Python 3.6.8 |Anaconda, Inc.| (default, Dec 29 2018, 19:04:46)
[GCC 4.2.1 Compatible Clang 4.0.1 (tags/RELEASE_401/final)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import neuron
>>>
```

Quit by typing `quit()`. If instead of the above, you get an error similar to below,

```bash
>>> import neuron
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'neuron'
>>> quit
```

Then the environment variable PYTHONPATH needs to be set

* PYTHONPATH: this should include the path to NEURON libraries. Make sure the path is valid (e.g. /Applications/NEURON-7.6/nrn/lib/python). The environment variable may include multiple entries (others that are related to NEURON).

### MPI debugging, step 4: MPI

If conda or pip was able to install mpi4py, then mpiexec (as part of openmpi) should be on your system. Make sure that it can be found from your PATH. To test running two MPI processes in parallel:

```bash
$ mpiexec -n 2 hostname
My-MacBook-Pro.local
My-MacBook-Pro.local
```

If there are no errors, then return to HNN and try to run a simulation.

If you receive the error

```bash
dyld: Library not loaded: @rpath/libmpi.1.dylib
```

You will need to specify the environment variable LD_LIBRARY_PATH similar to below, and add the command below to your `~/.bashrc` file (or tcsh equivalent) so that it gets set in every subsequent terminal session.

```bash
export LD_LIBRARY_PATH=~/miniconda3/envs/hnn/lib
```
