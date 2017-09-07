Installing & Running HNN
=======================================

Installing HNN
--------------

We have provided installation scripts for Linux (CentOS, Ubuntu), and instructions for installing
HNN on Mac OSX below. Windows installation instructions are currently in development. 

Linux Installation Scripts
^^^^^^^^^^^^^^^^^^^^^^^^^^

 #. `CentOS install script <https://bitbucket.org/samnemo/hnn/src/70f8db5fc7310a811378920d61954d0277abe8c8/installer/centos/build.sh?at=master>`_ 
 #. `Ubuntu install script <https://bitbucket.org/samnemo/hnn/src/70f8db5fc7310a811378920d61954d0277abe8c8/installer/ubuntu/build.sh?at=master>`_

To install HNN on Linux using these scripts, download the installer appropriate for your
operating system. Then from a terminal, change into the directory with the ``build.sh`` script and run 
``sudo ./build.sh`` on CentOS or ``sudo source build.sh`` if you are using Ubuntu.
**Note: you will need to enter the sudo password.** The build.sh script will take
at least a few minutes to run, depending on your operating system and hardware.

Mac OSX Installation Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the instructions below, commands executed from the terminal are indicated in
different font background color (*e.g.* ``cd path``). Note that some commands
involve GUI interaction through a web browser or clicking on a window/button, etc.

1. ``echo 'export TMPDIR=/private/tmp' >> ~/.bash_profile``

2.  ``xcode-select --install``
  a. **click** install
  b. **click** agree

3. Use a web browser to go to xquartz.org, then download and install the latest XQuartz dmg

4. Restart the computer (yes, really)

5. Use a web browser to go to https://www.continuum.io/downloads and download and install the Python 3.x version (currently Python 3.6) (NOTE: you do NOT need to enter your email on the website)

6. Use a web browser to go to http://neuron.yale.edu/ftp/neuron/versions/alpha, download and install the most recent version of NEURON (currently nrn-7.5.master-1620.x86_64-osx.pkg) -- **NOTE:** be sure to say **YES** to both prompts about modifying paths

7. Use a web browser to go to https://www.open-mpi.org/software/ and download the current .tar.gz file (currently openmpi-2.1.1.tar.gz)
  a. With a terminal change to the directory you downloaded the tar.gz file to (e.g. ``cd ~/Downloads``)
  b. ``tar -zxvf openmpi*``
  c. ``cd openmpi*``
  d. ``./configure``
  e. ``make all -j4``
  f. ``sudo make install -j4``

9. ``git clone https://bitbucket.org/samnemo/hnn``
  **NOTE:** the git clone command above will prompt for your bitbucket username/password
  ``cd hnn``
  ``make``

Once these steps are complete, you can run hnn via ``./hnn.sh`` .

(The latest instructions for installing HNN on Mac OSX are also available here: `Mac OSX install script <https://bitbucket.org/samnemo/hnn/src/d721bbdcf1718b64af83d92fbbd5e0ee38ae7d2c/installer/mac/mac-install-instructions.txt?at=master>`_)

Starting HNN
------------

First start a terminal. Then change into the directory
where HNN is installed with ``cd path_to_hnn``. Next, from the
terminal, run the HNN startup script ``hnn.sh``. If everything
is installed correctly, you will see the HNN graphical user interface (GUI),
as shown below. Note that the empty white area in the GUI is 
where simulation data is displayed. Since no simulation was run, the
area is empty. 

.. image:: images/starthnnempty.png
	:width: 50%	
	:align: center

Test run
--------

To test the default simulation press the ``Run Simulation`` button.
You will be asked if you want to over-write the default.param file.
Press the OK button to confirm and the simulation will begin. 
Then, a simulation that displays ongoing alpha (~10 Hz) and beta (~20 Hz)
oscillations will begin. After 1-2 minutes (depending on your hardware), you will
get notified in a dialog window that the simulation has run to completion. Press OK
and you should see the output in the main GUI window, as displayed below. 

.. image:: images/starthnndefaultrun.png
	:width: 50%	
	:align: center

.. _simdefoutput:
The simulation output displayed  consists of several panels. The top panels
represent histograms of the inputs provided to the neurons. Note their rhythmicity, which
contributes to alpha/beta events. The middle panel shows the dipole signal generated
by the model. Note the units are in nAm, and directly comparable to data from MEG
experiments. The bottom portion show a wavelet-based spectrogram from the current
dipole signal. In the Tutorial, we will provide more information on what the output
represents. 

Troubleshooting
---------------

HNN Software Requirements (Advanced Users)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The packages below are automatically installed when running the installation scripts/instructions provided above. However,
if your operating system does not yet have an installer/instructions, you could install the required packages manually
and then install the HNN code itself using the source-code from the bitbucket repository: http://bitbucket.org/samnemo/hnn .
For more information and/or questions about this contact samuel_neymotin@brown.edu .

HNN requires Python 3.x (`<www.python.org>`_) and the NEURON simulation environment (`<www.neuron.yale.edu>`_)
compiled to use Python3 and MPI support. 

Required packages:
 #. MPI
 #. Matplotlib
 #. NEURON compiled with MPI, Python support - $PYTHONPATH must point to Python 3
 #. Numpy
 #. PyOpenGL
 #. Python3
 #. PyQt5
 #. pyqtgraph
 #. Scipy

