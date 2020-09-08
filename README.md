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


hnn-netpyne
========

This is the NetPyNE (www.netpyne.org) version of the HNN thalamocortical network model in the master branch of the HNN repository (https://github.com/jonescompneurolab/hnn).

Advantages of the NetPyNE version include:

1. Standardized clean model definition using a declarative language

2. Easier to modify and extend (e.g. add a population, change connectivity, )

3. Built-in visualization/analysis plots: connectivity, spike statistics, Granger causality, ...

4. Record and plot LFP and CSD (raw signal, spectrogram, ...)

5. Use NetPyNE GUI to modify/visualize model

6. Automated parameter optimization/exploration (eg on HPCs via SLURM)

7. Export to NeuroML and SONATA formats for sharing


Dependencies
============

* numpy
* scipy
* matplotlib
* NetPyNE: installation instructions here: https://http://www.netpyne.org/install.html
* NEURON: installation instructions here: https://neuron.yale.edu/neuron/


Installation
============

We recommend the `Anaconda Python distribution <https://www.continuum.io/downloads>`_. To install ``hnn-core``, you first need to install its dependencies::

	$ conda install numpy matplotlib scipy

Additionally, you would need NEURON which is available here: `https://neuron.yale.edu/neuron/ <https://neuron.yale.edu/neuron/>`_. It can also be installed via pip now::

	$ pip install neuron

To obtain the latest version of the hnn-netpyne code you will need to clone the "netpyne" branch of this repo::

	$ git clone --single-branch -branch netpyne https://github.com/jonescompneurolab/hnn.git 

To check if everything worked fine, you can do::

    $ cd hnn/hnn-netpyne
    $ nrnivmodl ../mod
	$ python -i init.py

which should run the simulation and produce some plots.

Usage
============

The NetPyNE model is inside the */hnn-netpyne* folder, containing just 6 files:

- *init.py*: file to run a single simulation  
- *batch.py*: code to run multiple simulations for parameter exploration/optimization
- *cellParams.py*: cell parameters 
- *netParams.py*: network parameters
- *cfg.py*: simulation configuration options

You can select what set of parameters (.param file) to run by modifying init.py, e.g. replace *cfgFile='../param/ERPYes100Trials.param'* with *cfgFile='../param/AlphaAndBeta.param'* . This will allow you to replicate the different HNN tutorials. 


Bug reports
===========

Use the `github issue tracker <https://github.com/jonescompneurolab/hnn/issues>`_ to report bugs.


