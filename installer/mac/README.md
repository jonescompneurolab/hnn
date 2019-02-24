# Installing HNN on Mac OS

This guide describes two methods for installing HNN and its prerequisites on Mac OS (tested on High Sierra):

Method 1: A Docker container running a Linux install of HNN (recommended)
   - The Docker installation fully isolates HNN's python environment and the NEURON installation from the rest of your system, reducing the possibility of version incompatibilities. Additionally, the same Docker container is used for all platforms (Windows/Linux/Mac) meaning it has likely been tested more recently.
   
Method 2: Installing HNN natively on Mac OS (advanced users)
   - This method will run HNN without using virtualization, meaning the GUI may feel more responsive and simulations may run slightly faster. However, the procedure is a set of steps that the user must follow, and there is a possibility that differences in the base environment may require additional troubleshooting. Thus, Method 2 is best suited for advanced users.

## Method 1: Docker install

[Docker Desktop](https://www.docker.com/products/docker-desktop) requires Mac OS Sierra 10.12 or above. For earlier versions of Mac OS, use the legacy version of [Docker Toolbox](https://docs.docker.com/toolbox/overview/).

The only other prerequisite besides docker is an X server. [XQuartz](https://www.xquartz.org/) is free and the recommended option for Mac OS.

### Prerequisite: install XQuartz
1. Download the installer image (version 2.7.11 tested): https://www.xquartz.org/
2. Run the XQuartz.pkg installer within the image, granting privileges when requested.
3. Start the XQuartz application. An "X" icon will appear in the taskbar along with a terminal, signaling that XQuartz is waiting for connections. You can minimize the terminal, but do not close it.
4. Open the XQuartz preferences and navigate to the "security" tab. Make sure "Authenticate connections" is unchecked and "Allow connections from network clients" is checked.

   <img src="install_pngs/xquartz_preferences.png" height="250" />

### Prerequisite (Mac OS Sierra 10.12 or above): install Docker Desktop
1. Download the installer image (requires a free Docker Hub account):
https://hub.docker.com/editions/community/docker-ce-desktop-mac
2. Run the Docker Desktop installer, moving docker to the applications folder.
3. Start the Docker application, acknowledging that it was downloaded from the Internet and you still want to open it.
4. The Docker Desktop icon will appear in the taskbar with the message "Docker Desktop is starting", Followed by "Docker Desktop is running".

### Prerequisite (Mac OS pre-10.12): install Docker Toolbox
1. Download the installer image:
https://docs.docker.com/toolbox/toolbox_install_mac/
2. Run the installer, selecting any directory for installation.
3. Choose "Docker Quickstart Terminal" tool
4. Verify that Docker has started by running the following in the provided terminal window. 
    ```
    docker info
    docker-compose --version
    ```
5. Run the following commands in the same terminal window or by relaunching "Docker Quickstart Terminal".
6. For Docker Toolbox only, we will need to set an IP address in the file docker-compose.yml before starting the HNN container.
    - Get the IP address of the local interface that Docker Toolbox created. It will be named similar to vboxnet1 with an IP address such as 192.168.99.1
      ```
      ifconfig vboxnet1
      ```
    - Edit the docker-compose.yml file in `hnn/installer/mac/`, replacing `host.docker.internal:0` with the IP address such as `192.168.99.1:0` (**The ":0" is required**). Save the file before running the commands below.


### Start HNN
1. Verify that XQuartz and Docker are running. These will not start automatically after a reboot. Check that Docker is running properly by typing the following in a new terminal window.
    ```
    docker info
    ```
2. Clone or download the [HNN repo](https://github.com/jonescompneurolab/hnn). If you already have a previous version of the repository, bring it up to date with the command `git pull origin master` instead of the `git clone` command below.
    ```
    git clone https://github.com/jonescompneurolab/hnn.git
    cd hnn/installer/mac
    ```
3. Start the Docker container. Note: the jonescompneurolab/hnn docker image will be downloaded from Docker Hub (about 1.5 GB). Docker-compose starts a docker container based on the specification file docker-compose.yml and "up" starts the containers in that file and "-d" starts the docker containers in the background.
    ```
    docker-compose up -d
    ```    
4. The HNN GUI should show up and you should now be able to run the tutorials at https://hnn.brown.edu/index.php/tutorials/
   * A directory called "hnn" exists both inside the container (at /home/hnn_user/hnn) and outside (in the directory where step 3 was run) that can be used to share files between the container and your host OS.
   * If you run into problems starting the Docker container or the GUI is not displaying, please see the [Docker troubleshooting section](../docker/README.md#Troubleshooting)
   * If you closed the HNN GUI, and would like to restart it, run the following:
      ```
      docker-compose restart
      ```
5. **NOTE:** You may want run commands or edit files within the container. To access a command prompt in the container, use [`docker exec`](https://docs.docker.com/engine/reference/commandline/exec/):
    ```
    C:\Users\myuser>docker exec -ti mac_hnn_1 bash
    hnn_user@054ba0c64625:/home/hnn_user$
    ```

    If you'd like to be able to copy files from the host OS without using the shared directory, you do so directly with [`docker cp`](https://docs.docker.com/engine/reference/commandline/cp/).

## Method 2: native install

### Prerequisite 1: Xcode Command Line Tools

The Xcode Command Line Tools package includes utilities for compiling code from the terminal window command line (gcc, make, git, etc.). This is needed for compiling mod files in NEURON. To install the package, type the following from a terminal window:
```
xcode-select --install
```


### Prerequisite 2: XQuartz
1. Download the installer image (version 2.7.11 tested): https://www.xquartz.org/
2. Run the XQuartz.pkg installer within the image, granting privileges when requested.
3. Start the XQuartz application. An "X" icon will appear in the taskbar along with a terminal, signaling that XQuartz is waiting for connections. You can minimize the terminal, but do not close it.

From the command line:
```
cd /tmp/
curl https://dl.bintray.com/xquartz/downloads/XQuartz-2.7.11.dmg -o XQuartz-2.7.11.dmg
hdiutil attach /tmp/XQuartz-2.7.11.dmg
sudo installer -verbose -pkg /Volumes/XQuartz-2.7.11/XQuartz.pkg -target /
hdiutil detach /Volumes/XQuartz-2.7.11
rm /tmp/XQuartz-2.7.11.dmg
open /Applications/Utilities/XQuartz.app
```

### Prerequisite 3: Miniconda (Python 3)

1. Run the commands below from a terminal window (as a regular user) or download and install miniconda from the link: https://conda.io/en/latest/miniconda.html. This will create a python environment isolated from other installations on the system (e.g. those installed using homebrew). You could use `brew install python3` if you wish (has been tested with HNN), but this guide will cover the miniconda version.
    ```
    cd /tmp/
    curl https://repo.anaconda.com/miniconda/ -o Miniconda3-latest-MacOSX-x86_64.sh
    sh ./Miniconda3-latest-MacOSX-x86_64.sh -b
    rm /tmp/Miniconda3-latest-MacOSX-x86_64.sh
    ```

### Prerequisite 4: NEURON

1. Install [NEURON](https://neuron.yale.edu/neuron/) from the terminal:
    ```
    cd /tmp/
    curl https://neuron.yale.edu/ftp/neuron/versions/v7.6/nrn-7.6.x86_64-osx.pkg -o nrn-7.6.x86_64-osx.pkg
    sudo installer -verbose -pkg /tmp/nrn-7.6.x86_64-osx.pkg -allowUntrusted -target /
    ```
2. You will be asked about setting PATH variable. Say 'No' to both prompts.

  <img src="install_pngs/neuron_path.png" height="250" />

3. Afterward, you will be presented with a confirmation message that NEURON has been installed. Click 'Continue'

  <img src="install_pngs/neuron_continue.png" height="250" />

### Prepare the Python environment

1. Create a conda environment with the Python prerequisites for HNN.

    ```
    conda create -n hnn mpi4py pyqtgraph pyopengl matplotlib scipy
    ```
2. Activate the HNN conda environment

    ```
    activate hnn
    ```

3. Set the bash (or other shell) environment variables. Note that depending on your shell (bash or c shell you will use the 4 export commands below or the 4 set commands below, respectively)

  * bash

    Add the following in your ~/.bash_profile (e.g. type "open ~/.bash_profile" in the terminal without the quotes to edit it):
    ```
    export PYTHONPATH=/Applications/NEURON-7.6/nrn/lib/python:$PYTHONPATH
    export PATH=/Applications/NEURON-7.6/nrn/x86_64/bin:$PATH
    export NRN_PYLIB="~/anaconda3/lib/libpython3.6m.dylib"
    ```
  * tcsh

    Add the following in your ~/.cshrc and/or ~/.tcshrc (e.g. type "open ~/.cshrc" or as appropriate in the terminal without the quotes to edit the file):
    ```
    set PYTHONPATH=(/Applications/NEURON-7.6/nrn/lib/python $PYTHONPATH)
    set path = ($path /Applications/NEURON-7.6/nrn/x86_64/bin)
    set NRN_PYLIB="~/anaconda3/lib/libpython3.6m.dylib" 
    ```

### Reboot your system
Please reboot your system before proceeding. A reboot is really needed after installing Xquartz. The environment variables set above will also be set for all terminal windows after the reboot.

### Compile HNN 
1. After rebooting, open a new terminal and clone the repository:
    ```
    git clone https://github.com/jonescompneurolab/hnn.git
    ```
2. Now enter the hnn directory and compile HNN's mod files for NEURON. This is where Xcode Command Line Tools are needed.
    ```
    cd hnn
    make
    ```

### Run the HNN model
1. Start the HNN GUI from a terminal window:
    ```
    conda activate hnn
    python hnn.py hnn.cfg
    ```
2. The HNN GUI should appear and you should now be able to run the tutorials at https://hnn.brown.edu/index.php/tutorials/
3. When you run simulations for the first time, the following dialog boxes may pop-up and ask you for permission to allow connections through the firewall. Saying 'Deny' is fine since simulations will just run locally on your Mac.

<img src="install_pngs/nrniv_firewall.png" height="250" />
<img src="install_pngs/orterun_firewall.png" height="250" />

# Troubleshooting

## Method 1 (docker install)
Please see the [Docker troubleshooting section](../docker/README.md#Troubleshooting)

## Method 2 (native install)

### Error message: `There are not enough slots available in the system`

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

This may happen when there is a discrepancy in how many cores HNN attempts to use (all available by default) and how many cores are available to MPI. This may be because of restrictions on user resource usage on batch/HPC cluster environments or particular versions of MPI (e.g. homebrew open-mpi) that don't count cores turned on by the processor's hyperthreading feature. Try reducing the number of cores in the HNN GUI under 'Set parameters' -> 'Run' by half.

### Error message: `ls: /usr/local/bin/../lib/libpython*.dylib: No such file or directory`

This error message may appear when running simulations and is more likely to appear if a different python is used than Anaconda or Miniconda. One such case is when python3 is installed using homebrew `brew install python3`. In this case, PYTHONHOME needs to be specified in addition to NRN_PYLIB. An example is below. Verify the paths that exist on your system and use them in place of the paths below.
  ```
  export NRN_PYLIB="/usr/local/Cellar/python3/3.7.2_2/Frameworks/Python.framework/Versions/3.7/lib/libpython3.7m.dylib"
  export PYTHONHOME="/usr/local/Cellar/python/3.7.2_2/Frameworks/Python.framework/Versions/3.7/"
  ```

### Error message: `Error: Cannot allocate memory. Check the CQE attribute`

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

### Simulation log says "X total processes failed to start"
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


### Stream of error messages from MPI

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

#### MPI debugging, step 1: is NEURON the problem (part 1)?

To remove NEURON from the list of possible problems, try running `nrniv -nopython` from the command line. You should get a `oc>` prompt when there are no problems.

#### MPI debugging, step 2: Is Python the problem?

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

#### MPI debugging, step 3: is NEURON the problem (part 2)?

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

#### MPI debugging, step 4: is MPI the problem?

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

