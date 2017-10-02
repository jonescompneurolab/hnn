
Background
===============================

Macroscale human brain imaging signals
--------------------------------------
Magneto-encephalography (MEG) and electro-encelphalography (EEG)
are the leading methods to non-invasively record human neural dynamics with millisecond
temporal resolution. However, it is extremely difficult to infer the underlying cellular and
circuit level origins of these "macro-scale" signals without simultaneous invasive recordings.
This limits the translation of MEG/EEG findings into novel principles of information
processing, or into new treatment modalities for neural pathologies. There is a pressing
need, and a unique opportunity, to relate the "macro-scale" signals to their underlying
circuit/cellular-level generators.

.. figure:: images/currentsource.png
	:scale: 20%	
	:align: center

	**Primary current sources (Jp) from intracellular currents in cortical pyramidal neuron dendrites contribute
	to the detected MEG/EEG signals** The intracellular longitudinal current flow in large populations of
	synchronously activated pyramidal neurons, aligned in parallel and tangential to MEG sensors outside of the
	head, create a net primary current dipole (*e.g.*, red arrows) large enough to be
	measured. Depending on the orientation and magnitude of the current sources, the signals will either be
	measurable only by MEG or also by EEG.


What is HNN?
^^^^^^^^^^^^

.. |megeegschemefig| image:: images/megeegscheme.png
        :scale: 45%
	:align: bottom

.. |modeqfig| image:: images/modeq.png
        :scale: 40%
	:align: bottom


.. |cortcolfig| image:: images/cortcol.png
        :scale: 40%
	:align: bottom


The Human Neocortical Neurosolver (HNN) is a user-friendly software tool that combines top-down
(sensors to electrical current sources) and bottom-up (circuits to electrical current sources)
models of signal interpretation, addressing one of the major challenges in Human Neuroscience:
connecting macroscale human imaging signals (MEG/EEG) to cellular and circuit level
electrophysiology, through linkage with biophysical modeling.

+-------------------+----------------+---------------+
| |megeegschemefig| | |modeqfig|     | |cortcolfig|  |
|                   |                |               |
| MEG/EEG signals   | Biophysical    | Cell,circuit  |
| provide           | models link    | generators of |
| multivariate      | data to cell,  | neocortical   |
| time-series.      | circuit level. | dynamics.     |
+-------------------+----------------+---------------+

Our goal was to design HNN to be useful to researchers with no formal computational neural
modeling or coding experience who want to develop and test hypotheses on the cellular and circuit
level generators of source localized human data. The software allows for interpretation,
visualization, and manipulation of cellular and circuit level dynamics. HNN presents a convenient
GUI to an anatomically and biophysically detailed model of human thalamocortical brain circuits,
which makes it easier to generate and evaluate hypotheses of the mechanistic origin of signals
measured with MEG/EEG or intracranial ECoG.

.. figure:: images/starthnndefaultrun.png
	:scale: 40%	
	:align: center

Above we show HNN's interface including model output. The output consists of several
panels -- top panel: modeled neuron synaptic input histograms; middle panel: model generated
dipole signal (units are in nAm, and directly comparable to data from MEG experiments); bottom panel:
wavelet-based spectrogram from the current dipole signal showing alpha/beta events. The very bottom of the
GUI shows several model schematics.


HNN's biophysical model
^^^^^^^^^^^^^^^^^^^^^^^

HNN's biophysical neural model is unique in that it goes beyond a mean field representation and
includes the morphology and physiology of neocortical neurons across the cortical layers, and
layer specific synaptic inputs, all of which contribute to the recorded signals. The model includes
biophysics generating the primary electric currents underlying such data, and therefore simulation results
are directly comparable to source localized data (in units of nano-Ampere-meters).

.. |modschemefig| image:: images/modscheme.png
        :scale: 20%
	:align: bottom


.. |modcolfig| image:: images/modcol.png
        :scale: 20%
	:align: bottom

+--------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------+
| |modschemefig|                                                                       | |modcolfig|                                                                                  |
|                                                                                      |                                                                                              |
|  Computational neural model written in `NEURON-Python <http://www.neuron.yale.edu>`_ | Model of cortical column includes 100s to                                                    |
|  simulates the direction and timecourse of the primary                               | 1000s (scalable) of multicompartment pyramidal                                               |
|  electrical currents (Jp) via intracellular electrical                               | neurons and single compartment interneurons                                                  |
|  currents in cortical pyramidal neuron dendrites                                     | `(model source code) <https://senselab.med.yale.edu/ModelDB/showmodel.cshtml?model=151685>`_ |
|  (units: nano-Ampere-meters).                                                        |                                                                                              |
|                                                                                      |                                                                                              |
+--------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------+



Integration with MNE-Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^

We are integrating HNN with the source localization software (`MNE
<http://martinos.org/mne/stable/index.html>`_; minimum-norm-estimate) so researchers can compute
the location, time course and circuit origin of their data all in one software package.

.. figure:: images/mnesource.png
	:scale: 40%	
	:align: center

	Source estimation using MNE-Python to model the location, direction, and time-course of the primary
	electric currents (Jp).

