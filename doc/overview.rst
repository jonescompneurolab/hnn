
Overview
===============================

What is HNN
----------------

The Human Neocortical Neurosolver (HNN) is an open-source
neural modeling tool designed to help researchers/clinicians interpret human brain imaging data. HNN
presents a convenient GUI to an anatomically and biophysically detailed model of human
thalamocortical brain circuits, which makes it easier to generate and evaluate hypotheses of the
mechanistic origin of signals measured with MEG/EEG or intracranial ECoG. A unique feature of
HNN’s model is that it accounts for the biophysics generating the primary electric currents
underlying such data, so simulation results are directly comparable to source localized data
(nano-Ampere-meters); this enables precise tuning of model parameters to match characteristics of
recorded signals.

We are integrating the circuit-level modeling with the minimum-norm-estimate (MNE) source
localization software, so researchers can compute MEG/EEG source estimates and test hypotheses on
the circuit origin of their data in one software package. Our goal is to design HNN to be useful
to researchers with no formal computational neural modeling or coding experience. Visualization
plugins, which provide 3D views of model cells and their connectivity, will aid intuition on how
circuit architecture can influence neocortical dynamics. We are also building resources for
freely using and expanding the software through the Neuroscience Gateway Portal, and online
documentation and a user forum for interaction between users and developers. We will present the
initial construction of our tool and describe its use in studying the circuit-level origin of
some of the most commonly measured MEG/EEG and ECoG signal: event related potentials (ERPs) and
low frequency rhythms (alpha/beta/gamma).

Features
--------------

Further information
----------------

- `Overview (slides) from Cutting EEG 2017 Workshop <https://www.dropbox.com/preview/HNN/CuttingEEG-Workshop/CuttingEEG-workshop-6-19-17.pdf?role=work>`_

- `Tutorial (slides) from Cutting EEG 2017 Workshop <https://www.dropbox.com/home/HNN/CuttingEEG-Workshop?preview=slides_workshop_coding.pdf>`_

- `Poster from Cutting EEG 2017 conference <https://www.dropbox.com/home/HNN/CuttingEEG-Poster?preview=CuttingEEG-poster.pdf>`_ 

Contact
-----------------------------------------

HNN is under active development by the Jones lab (https://www.brown.edu/research/labs/jones/) 
and supported by a NIH BRAIN grant. 

HNN is open source and available at https://bitbucket.com/samnemo/hnn .

For questions/suggestions or further information contact samuel_neymotin@brown.edu or stephanie_jones@brown.edu .
