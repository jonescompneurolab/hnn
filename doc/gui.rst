Tour of the Graphical User Interface (GUI)
==========================================

Here we provide an overview of the major GUI
components, and provide a description of all
the parameters that the GUI provides.

This is a display of the GUI after running
a simulation that produces ongoing alpha/beta rhythms.

.. image:: images/starthnndefaultrun.png
	:width: 50%	
	:align: center

Parameter Files
---------------

In order to facilitate modeling, we have provided text-based parameter files for replicating event related
potentials (ERPs), and alpha/beta/gamma rhythms. HNN can load the parameter files, allowing 
you to replicate the dynamics, see the critical parameter values that are responsible for
the observed dynamics, and then modify the parameter files/values to observe the effect on 
dynamics. Parameter files are stored in the param subdirectory and can be viewed in any
text editor. To load these parameter files into HNN, press the ``Set Parameters from File`` button,
select the parameter file, and press enter. HNN will parse the file and display the values
in the GUI. Then, running the simulation will use these parameter values. 

Setting Parameters 
----------------------

To view and set the parameters that control the simulation, press the ``Set Parameters`` button from the
main GUI window. This will bring up the following dialog:

.. image:: images/setparamsdlg.png
        :width: 25%
	:align: center	

Pressing each button on this dialog brings up a new dialog box with more adjustable
parameters. We will go through each below.

The next thing to note is the ``Simulation Name``. This should be a unique identifier
for any particular simulation you run. HNN also uses this variable to determine where
to save the output files. In the dialog displayed, note that the value is set to ``default``.
This is because the ``default.param`` file was loaded. We suggest you change this name
when you make changes to the parameters and before you run a new simulation.

Here is an example of the data directory and files saved after running the simulation
specified in ``default.param``.

.. image:: images/dataoutputwin.png
        :width: 35%
	:align: center	

Note that the directory path is ``/home/hnn/data/default``, corresponding to the ``default``
``Simulation Name`` parameter specified in the GUI. Also note the individual files present
in the window: 
 #. default.param - a backup copy of the param file used to run the simulation
 #. dpl.txt - normalized dipole in units of nAm; 1st column is time; 2nd column is layer 2 dipole; 3rd column is layer 5 dipole; 45h column is aggregate dipole from layers 2 and 5
 #. i.txt - currents from the cells
 #. param.txt - a machine-readable representation of all parameters used to run the simulation
 #. rawdpl.txt - un-normalized dipole; same columnar layout as dpl.txt
 #. rawspec.npz - spectrogram from the dipole saved in numpy format; you can use numpy to load this file
 #. spk.txt - a list of cell identifiers and spike times

We provide these files for advanced users who want to load them into their own analysis
software, and also to allow HNN to load data after a simulation was run. For example, if you
close HNN and then restart it, load a param file from a simulation that was already run, 
HNN will load and display the data. 

Run Parameters
^^^^^^^^^^^^^^

Pressing the ``Run`` button on the ``Set Parameters`` dialog box brings up the
following dialog, enabling you to view/change the following displayed parameters.

.. image:: images/runparamdlg.png
        :width: 35%
	:align: center	

* Duration (ms) - this sets the simulation duration in milliseconds.
* Integration timestep (ms) - this sets the fixed timestep that the NEURON simulator uses to perform integration; smaller values take longer to run but potentially offer more accurate simulations; we recommend using the default value of 0.025 ms.
* Trials - specifies the number of trials to run; note that the simulation parameters across trials are identical except for inputs which are randomized across trials. 
* NumCores - this specifies the number of cores that NEURON will use to run a simulation in parallel; we suggest using the default, which HNN automatically determines based on your computer hardware. 

Clicking on the ``Analysis`` tab brings up the following parameters.

.. image:: images/run_analysisparamdlg.png
        :width: 35%
	:align: center	

* Save figures - whether to save figures of model activity when the simulation is run; if set to 1, figures are saved in simulation output directory.
* Save spectral data - Whether to save spectral simulation spectral data - time/frequency/power; if set to 1, saved to simulation output directory. **Note: when using rhythmic inputs, spectrograms will be saved whether or not this is set to 1.**
* Max spectral frequency (Hz) - Maximum frequency used in dipole spectral analysis.
* Dipole scaling - Scaling used to match simulation dipole signal to data; implicitly estimates number of cells contributing to dipole signal.
* Dipole Smooth Window (ms) - Window size (ms) used for Hamming filtering of dipole signal (0 means no smoothing); for analysis of ongoing rhythms (alpha/beta/gamma), best to avoid smoothing, while for evoked responses, best to smooth with 15-30 ms window.

Clicking on the Randomization Seeds tab brings up the following parameters.

.. image:: images/run_randparamdlg.png
        :width: 35%
	:align: center	

All these paramters are random number generator seeds for the different types of *inputs* provided
to the model. Varying a seed will still maintain statistically identical inputs but allow for controlled variability.

* Random number generator seed used for rhythmic proximal inputs.
* Random number generator seed used for rhythmic distal inputs.
* Random number generator seed used for Poisson inputs.
* Random number generator seed used for Gaussian inputs.
* Random number generator seed used for evoked proximal input 1.
* Random number generator seed used for evoked distal input 1. 
* Random number generator seed used for evoked proximal input 2.
* Random number generator seed used for evoked distal input 2.

Cell Parameters
^^^^^^^^^^^^^^^

Pressing the ``Cell`` button on the ``Set Parameters`` dialog box brings up the
following dialog, enabling you to view/change the cell parameters
associated with geometry, synapses, and biophysics for layer 2 and layer 5
pyramidal neurons.

These parameters control the cell's geometry:

.. image:: images/cell_geomparamdlg.png
        :width: 35%
	:align: center	

and include lengths/diameters of individual compartments. Although not
strictly related, we have also included axial resistivity and capacitive
in this panel. 

Clicking on the Synapses tab allows you to modify the postsynaptic
properties of layer 2 pyramidal neurons:

.. image:: images/cell_synparamdlg.png
        :width: 35%
	:align: center	

These include the excitatory (AMPA/NMDA) and inhibitory (GABAA/GABAB)
reversal potentials and rise/decay exponential time-constants.

Clicking on the L2Pyr Biophysics tab allows you to modify the biophysical
properties of layer 2 pyramidal neurons, including ion channel densities
and reversal potentials:

.. image:: images/cell_biophysparamdlg.png
        :width: 35%
	:align: center	

To modify properties of the layer 5 pyramidal neurons, click on the right
arrow to access the relevant tabs (beginning with L5Pyr).

