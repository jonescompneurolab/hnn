TITLE High threshold calcium current

COMMENT
-----------------------------------------------------------------------------
	High threshold calcium current
	------------------------------

   - Ca++ current, L type channels
   - Differential equations

   - Model from:

   Reuveni I; Friedman A; Amitai Y; Gutnick MJ.
     Stepwise repolarization from Ca2+ plateaus in neocortical pyramidal cells:
     evidence for nonhomogeneous distribution of HVA Ca2+ channels in
     dendrites.
   Journal of Neuroscience, 1993 Nov, 13(11):4609-21.

   - Experimental data for voltage-dependent activation:

   Sayer RJ; Schwindt PC; Crill WE.
     High- and low-threshold calcium currents in neurons acutely isolated from
     rat sensorimotor cortex.
   Neuroscience Letters, 1990 Dec 11, 120(2):175-8.
 
   - Experimental data for voltage-dependent inactivation:

   Dichter MA; Zona C.
     Calcium currents in cultured rat cortical neurons.
   Brain Research, 1989 Jul 17, 492(1-2):219-29.

   - Calcium-dependent inactivation was not modeled; if interested, see:

   Kay AR.
     Inactivation kinetics of calcium current of acutely dissociated CA1
     pyramidal cells of the mature guinea-pig hippocampus.
   Journal of Physiology, 1991 Jun, 437:27-48.

   - m2h kinetics from:

   Kay AR; Wong RK.
     Calcium current activation kinetics in isolated pyramidal neurones of the
     Ca1 region of the mature guinea-pig hippocampus.
   Journal of Physiology, 1987 Nov, 392:603-16.

   - Reversal potential described by Nernst equation
   - no temperature dependence included (rates correspond to 36 degC)


   Alain Destexhe, Laval University, 1996

-----------------------------------------------------------------------------
ENDCOMMENT

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX ical
	USEION ca READ eca WRITE ica
        RANGE gcabar, alpha_m, beta_m, alpha_h, beta_h, m, h, carev
}


UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(molar) = (1/liter)
	(mM) = (millimolar)
	FARADAY = (faraday) (coulomb)
	R = (k-mole) (joule/degC)
}


PARAMETER {
	v		(mV)
	celsius	= 36	(degC)
	eca		(mV)
	cai 	= .00024 (mM)		: initial [Ca]i = 200 nM
	cao 	= 2	(mM)		: [Ca]o = 2 mM
	gcabar	= 1e-4	(mho/cm2)	: Max conductance
}


STATE {
	m
	h
}

ASSIGNED {
	ica	(mA/cm2)		: current
	carev	(mV)			: rev potential
	alpha_m	(/ms)			: rate cst
	beta_m	(/ms)
	alpha_h	(/ms)
	beta_h	(/ms)
	tadj
}


BREAKPOINT { 
	SOLVE states METHOD cnexp : see http://www.neuron.yale.edu/phpBB/viewtopic.php?f=28&t=592
	carev = (1e3) * (R*(celsius+273.15))/(2*FARADAY) * log (cao/cai)
	ica = gcabar * m * m * h * (v-carev)
}

DERIVATIVE states { 
	evaluate_fct(v)

	m' = alpha_m * (1-m) - beta_m * m
	h' = alpha_h * (1-h) - beta_h * h
}


UNITSOFF

INITIAL {
	evaluate_fct(v)
:	m = alpha_m / (alpha_m + beta_m)
:	h = alpha_h / (alpha_h + beta_h)
:	tadj = 3 ^ ((celsius-36)/10)
}

PROCEDURE evaluate_fct(v(mV)) {

	: rates at 36 degC

	alpha_m = 0.055 * (-27-v) / (exp((-27-v)/3.8) - 1)
	beta_m = 0.94 * exp((-75-v)/17)

	alpha_h = 0.000457 * exp((-13-v)/50)
	beta_h = 0.0065 / (exp((-15-v)/28) + 1)
}

UNITSON
