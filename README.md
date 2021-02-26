# About HNN

The **Human Neocortical Neurosolver (HNN)** is an open-source neural modeling tool designed to help
researchers/clinicians interpret human brain imaging data. HNN presents a convenient GUI to an
anatomically and biophysically detailed model of human thalamocortical brain circuits, which
makes it easier to generate and evaluate hypotheses on the mechanistic origin of signals measured
with MEG/EEG or intracranial ECoG. A unique feature of HNN's model is that it accounts for the
biophysics generating the primary electric currents underlying such data, so simulation results
are directly comparable to source localized data (nano-Ampere-meters); this enables precise
tuning of model parameters to match characteristics of recorded signals.
 
For more information visit [https://hnn.brown.edu](https://hnn.brown.edu) . There, we describe the use of HNN in studying the
circuit-level origin of some of the most commonly measured MEG/EEG and ECoG signal: event related
potentials (ERPs) and low frequency rhythms (alpha/beta/gamma).


hnn2
========

This is the proof-of-concept implementation of a NetPyNE-based HNN that enables it to work with any arbitrary model defined in NetPyNE (www.netpyne.org)  

Advantages of this NetPyNE-based HNN version include:

1. Disentangles HNN API from 2-layer neocortical model

2. Can be used with other existing and customizable models (e.g. A1, M1, etc)

3. Uses NetPyNE for model building/simulating (instead of NEURON directly) 
	a. Standardized clean model definition using a declarative language
	b. Easier to modify and extend (e.g. add a population, change connectivity, )
	c. Built-in visualization/analysis plots: connectivity, spike statistics, Granger causality, ...
	d. Record and plot LFP and CSD (raw signal, spectrogram, ...)
	e. Use NetPyNE GUI to modify/visualize model
	f. Automated parameter optimization/exploration (eg on HPCs via SLURM)
	g. Export to NeuroML and SONATA formats for sharing


The current proof-of-concept HNN API (hnn_api):

- uses similar function calls to HNN-Core  
- reproduces HNN-Core examples (e.g. /examples/plot_simulated_evoked.py)
- works with new models: 
	a. neocortex with divergence (/examples/plot_simulated_evoked_divergence.py) and 
	b. auditory thalamocortical network (/examples/plot_simulated_A1.py))  
- adds new features: plotting/analysis, parameter exploration, ...
- can reuse much of the existing HNN-Core code (e.g. dipole, backends, …) 



Dependencies
============

* numpy
* scipy
* matplotlib
* NetPyNE
* NEURON

Installation
============

We recommend the `Anaconda Python distribution <https://www.continuum.io/downloads>`_. To install ``hnn-core``, you first need to install its dependencies::

	$ conda install numpy matplotlib scipy

Additionally, you will need NEURON which is available here: `https://neuron.yale.edu/neuron/ <https://neuron.yale.edu/neuron/>`_. It can also be installed via pip now::

	$ pip install neuron

You will then need to install NetPyNE:

    $ pip install netpyne

To obtain the latest version of the hnn2 code you will need to clone the "hnn2" branch of this repo::

	$ git clone --single-branch --branch hnn2 https://github.com/jonescompneurolab/hnn.git hnn2

Compile the mod files of any model you are going to use, e.g.:

    $ cd hnn2/hnn_models/hnn_neocortex/mod

    $ nrnivmodl .

	$ cd ..; ln -s mod/x86_64 x86_64

Run any of the examples in the /examples folder:

	$ cd hnn2/examples

	$ python -i plot_simulate_examples.py

which should run the simulations and produce some plots.


Bug reports
===========

Use the `github issue tracker <https://github.com/jonescompneurolab/hnn/issues>`_ to report bugs.


