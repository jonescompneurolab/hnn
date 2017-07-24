How to Simulate:
================

Here we demonstrate how to use the HNN software to simulate
several patterns of interest: 

 1. Event Related Potentials (ERPs)
 2. Alpha/Beta Rhythms
 3. Gamma Rhythms

We take you step-by-step through the parameter settings required
to replicate the dynamics, and ahow you how to compare experimental
data to the model output. We also provide the parameter (.param) files
which contain parameter values to generate the dynamics. This way, you
can load the parameter files and run the model with *correct* parameter
values, without having to enter all the values manually.

Event Related Potentials (ERPs)
-------------------------------

We begin with running simulations of ERPs. ERPs are detectable
in EEG/MEG recordings from sensory brain areas in response to
sensory events. For example, when a tactile stimulus is applied
to the hand, after a delay, an ERP can be detected in somatosensory
cortex. ERPs have prototypical waveforms. However, the mechanisms
that lead to ERPs are not fully known. Previous modeling has demonstrated
that the timing and strength of inputs arriving into different cortical
layers is responsible for generating the events. 

.. figure:: images/MEG_pub_model_comp.png
	:scale: 20%	
	:align: center

	**Comparison of ERP in experiment and simulation.** Left: MEG experiment showing
	ERP in response to tactile stimulation.
	Red: suprathreshold/detected trials; Blue: Threshold detected trials.
	Right: Simulation showing proximal/distal inputs needed to replicate the
	ERP waveform from MEG experiment. 


We will use HNN to
generate ERP waveforms which have close similarity with ERPs from
primary somatosensory cortex (S1) *in vivo* MEG experiments. These
experiments were previously published (refs), and involve tactile
stimulation. The data is split into two conditions: yes (detected)
and no (non-detected) trials. As we will see, the ERP waveforms
differ noticeably.

To run the simulations yourself, first download the param file
here: - `ERPYes100Trials.param <param/ERPYes100Trials.param>`_
Then load the parameter file values by clicking ``Set Parameters From File``
and selecting the file you just downloaded.

To view the parameters, click on ``Set Paramters``, and then ``Evoked Inputs``.
You should see the values displayed in the dialogs below.

Alpha/Beta Rhythms
------------------

Gamma Rhythms
-------------

