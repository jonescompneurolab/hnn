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
layers is responsible for generating the events. We can use HNN to
generate ERP waveforms which have close similarity with ERPs from
*in vivo* EEG/MEG experiments.

To run the simulations yourself, first load the param file
ERPYes100Trials.param available here: 
This load the parameter values by clicking ``Set Parameters From File``
and selecting the file you just downloaded.

To view the parameters, click on ``Set Paramters``, and then ``Evoked Inputs``.
You should see the values displayed in the dialogs below.



Alpha/Beta Rhythms
------------------

Gamma Rhythms
-------------

