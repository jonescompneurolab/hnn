: $Id: ntIh.mod,v 1.6 1998/08/14 20:52:38 billl Exp $
TITLE anomalous rectifier channel
:
: Anomalous Rectifier Ih - cation (Na/K) channel for geniculate interneurons
: Differential equations
:
:
: Written by Jun Zhu, Univ. Wisconsin, Jan 1996
:

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX iar
	USEION other WRITE iother VALENCE 1
        RANGE ghbar, shift
	GLOBAL h_inf, tau_h, erev, stp
}

UNITS {
	(molar)	= (1/liter)
	(mM)	= (millimolar)
	(mA) 	= (milliamp)
	(mV) 	= (millivolt)
	(msM)	= (ms mM)
}


PARAMETER {
        v               (mV)
	erev	= -44	(mV)
	celsius = 36	(degC)
	ghbar	= .0008 (mho/cm2)
        shift   = -6    (mV)
        stp     = 7.4
}


STATE {
        h
}


ASSIGNED {
	i	(mA/cm2)
	iother 	(mA/cm2)
	h_inf
	tau_h	(ms)
	tadj
}


BREAKPOINT {
	SOLVE state METHOD cnexp
	iother = ghbar * h * (v - erev)
}

DERIVATIVE state  {
	evaluate_fct(v)

        h' = (h_inf - h) / tau_h
}

UNITSOFF
INITIAL {
        tadj = 3.0 ^ ((celsius-36)/10)
	evaluate_fct(v)

        h = h_inf

        :  Experiments of Coulter et al were at 36 deg.C
        :  Q10 is assumed equal to 3
:
}


PROCEDURE evaluate_fct(v (mV)) {
	h_inf = 1 / ( 1 + exp((v+shift+79)/stp) )	 
	tau_h = exp((v+shift+293.3)/29.67) / ( 1 + exp((v+shift+76.7)/7.82)) / tadj
}

UNITSON