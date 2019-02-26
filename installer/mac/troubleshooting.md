# Troubleshooting on Mac OS

## Docker
For errors related to installing docker, please see the [Docker troubleshooting section](../docker/README.md#Troubleshooting)

## Error message: `There are not enough slots available in the system`

The message on the console from mpiexec looks something like:
```
Starting simulation. . .
--------------------------------------------------------------------------
There are not enough slots available in the system to satisfy the 8 slots
that were requested by the application:
  nrniv

Either request fewer slots for your application or make more slots available
for use.
--------------------------------------------------------------------------
```

This may happen when there is a discrepancy in how many cores HNN attempts to use (all available by default) and how many cores are available to MPI. This may be because of restrictions on user resource usage on batch/HPC cluster environments or particular versions of MPI (e.g. homebrew open-mpi) that don't count cores turned on by the processor's hyperthreading feature. Try reducing the number of cores in the HNN GUI under 'Set Parameters' -> 'Run' by half.

## Error message: `ls: /usr/local/bin/../lib/libpython*.dylib: No such file or directory`

This error message may appear when running simulations and is more likely to appear if a different python is used than Anaconda or Miniconda. One such case is when python3 is installed using homebrew `brew install python3`. In this case, PYTHONHOME needs to be specified in addition to NRN_PYLIB. An example is below. Verify the paths that exist on your system and use them in place of the paths below.
  ```
  export NRN_PYLIB="/usr/local/Cellar/python3/3.7.2_2/Frameworks/Python.framework/Versions/3.7/lib/libpython3.7m.dylib"
  export PYTHONHOME="/usr/local/Cellar/python/3.7.2_2/Frameworks/Python.framework/Versions/3.7/"
  ```

## Error message: `Error: Cannot allocate memory. Check the CQE attribute`

This message gets printed to the command line from mpiexec:
```
Starting simulation. . .
--------------------------------------------------------------------------
Failed to create a completion queue (CQ):

Hostname: node423
Requested CQE: 16384
Error:    Cannot allocate memory

Check the CQE attribute
--------------------------------------------------------------------------
```

One possible fix to this may be increasing the maximum locked memory a user is able to allocate using
```
ulimit -l unlimited
```
This may not be allowed for a non-privileged user, such as on a batch or HPC environment. Check with the system administrator if you get an error message running this command.

## Simulation log says "X total processes failed to start"
Check the command line output where "`python hnn.py hnn.cfg`" was run. If you get a message like the following, then your PATH environment variable needs to be updated to include the NEURON binaries, like `nrniv`
```
Starting simulation. . .
--------------------------------------------------------------------------
mpiexec was unable to launch the specified application as it could not find an executable:

Executable: nrniv
Node: My-MacBook-Pro.local

while attempting to start process rank 0.
--------------------------------------------------------------------------
```
Try running `nrniv` from the command line. If you get a message like `-bash: nrniv: command not found`, add the directory containing `nrniv` to the PATH environment variable. If this fixed the problem, you will need to add the export or set (for tcsh) command to your .bashrc or .csh/.tcsh file so that it works for every terminal window.
```
$ export PATH=/Applications/NEURON-7.6/nrn/x86_64/bin:$PATH
$ nrniv
NEURON -- VERSION 7.6.5 master (f3dad62b) 2019-01-11
Duke, Yale, and the BlueBrain Project -- Copyright 1984-2018
See http://neuron.yale.edu/neuron/credits

loading membrane mechanisms from x86_64/.libs/libnrnmech.so
Additional mechanisms from files
 mod/ar.mod mod/beforestep_py.mod mod/ca.mod mod/cad.mod mod/cat.mod mod/dipole.mod mod/dipole_pp.mod mod/hh2.mod mod/kca.mod mod/km.mod mod/lfp.mod mod/mea.mod mod/vecevent.mod
oc>
```


## Stream of error messages from MPI

When running an HNN simulation, you may get a message back immediately from HNN that all simulations have finished, but with a stream of error messages in the terminal window and no results in the GUI.

Some examples of the error messages:

```
OPAL ERROR: Not initialized in file pmix3x_client.c at line 113
```
  * Since OPAL is a part of MPI, you can reason that this is a problem when NEURON tries to call mpiexec.
```
Local abort before MPI_INIT completed successfully
```
```
--------------------------------------------------------------------------
mpiexec noticed that the job aborted, but has no info as to the process
that caused that situation.
--------------------------------------------------------------------------
```
  * These are standard error messages that openmpi produces when there's an error on one process. Since we are running an openmpi process for each core that HNN runs on, these messages will be repeated.

### MPI debugging, step 1: is NEURON the problem (part 1)?

To remove NEURON from the list of possible problems, try running `nrniv -nopython` from the command line. You should get a `oc>` prompt when there are no problems.

### MPI debugging, step 2: Is Python the problem?

As a simple debugging step, make sure that NEURON can load the necessary python libraries:
```
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
```
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
   ```
   unset PYTHONHOME
   ```
   If you are still having problems, set PYTHONHOME to the python installation directory that is the parent to all of the directories bin, lib, doc, and etc.

 * NRN_PYLIB: this may not need to be set. Try unsetting it:
   ```
   unset NRN_PYLIB
   ```
   If it must be set, make sure that it points to a valid .dylib file that matches the python binary you are using (i.e. don't mix and match anaconda python with a homebrew dylib)
   - conda: `export NRN_PYLIB=~/miniconda3/envs/hnn/lib/libpython3.6m.dylib`
   - homebrew: `export NRN_PYLIB="/usr/local/Cellar/python3/3.7.2_2/Frameworks/Python.framework/Versions/3.7/lib/libpython3.7m.dylib"`

### MPI debugging, step 3: is NEURON the problem (part 2)?

Based on the previous step, we know that `nrniv` can start python, but this step checks if python can load neuron libraries, By importing the neuron module into python, you should get something similar to the below:
```
$ python 
Python 3.6.8 |Anaconda, Inc.| (default, Dec 29 2018, 19:04:46) 
[GCC 4.2.1 Compatible Clang 4.0.1 (tags/RELEASE_401/final)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import neuron
>>>
```
Quit by typing `quit()`. If instead of the above, you get an error similar to below,
```
>>> import neuron
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'neuron'
>>> quit
```
Then the environment variable PYTHONPATH needs to be set
 * PYTHONPATH: this should include the path to NEURON libraries. Make sure the path is valid (e.g. /Applications/NEURON-7.6/nrn/lib/python). The environment variable may include multiple entries (others that are related to NEURON).

### MPI debugging, step 4: is MPI the problem?

If conda or pip was able to install mpi4py, then mpiexec (as part of openmpi) should be on your system. Make sure that it can be found from your PATH. To test running two MPI processes in parallel:
```
$ mpiexec -n 2 hostname
My-MacBook-Pro.local
My-MacBook-Pro.local
```
If there are no errors, then return to HNN and try to run a simulation.

If you receive the error
```
dyld: Library not loaded: @rpath/libmpi.1.dylib
```
You will need to specify the environment variable LD_LIBRARY_PATH similar to below, and add the command below to your `~/.bashrc` file (or tcsh equivalent) so that it gets set in every subsequent terminal session.
```
export LD_LIBRARY_PATH=~/miniconda3/envs/hnn/lib
```

