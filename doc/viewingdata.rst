Viewing Data 
===============================

Loading experimental data
-------------------------

Data format
^^^^^^^^^^^

HNN currently supports loading dipole data stored in plain text files. 
The first column of a txt file is the time, and the second column is
the dipole time-series. HNN assumes data is sampled at 600 Hz, the
standard for many MEG systems. We have provided a few examples of MEG ERP
data to get you started. This data is located in the data subfolder under
the hnn root folder.

How to Load Data
^^^^^^^^^^^^^^^^

From the main HNN window, go to ``File menu`` -> ``Load data file``
and select the file. HNN will then load the data and display the waveform
in the dipole panel of the output canvas as shown below.

.. figure:: images/ERPYes2Compare.png
	:scale: 40%	
	:align: center

In this example, the dotted yellow line is the experimental data and the solid
lines are from the simulation (gray lines are individual trials, black line
is average across trials).

Root-mean-square error (RMSE) comparison of model and experimental data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When HNN loads dipole data, it performs a root-mean-square error
comparison against all simulation dipole traces. 
Root mean squared error is defined as :math:`\sqrt \frac{\sum (S_i - E_i)^2}{n}`.
The summation is across all corresponding samples of the simulated (:math:`S`)
and experimental (:math:`E`) dipole signals, where there are :math:`n` samples.
Since the simulation typically uses a higher sampling rate than MEG data,
HNN downsamples the simulation data before performing the RMSE calculation.

Viewing experimental spectrograms
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Viewing experimental power spectral density
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
