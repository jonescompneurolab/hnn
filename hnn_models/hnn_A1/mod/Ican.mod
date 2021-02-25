: $Id: Ican.mod,v 1.8 2000/01/05 18:30:23 billl Exp $
TITLE Slow Ca-dependent cation current

: Stolen from Jun on 5/22/96
:


:
:   Ca++ dependent nonspecific cation current ICAN
:   Differential equations
:
:   Model of Destexhe, 1992.  Based on a first order kinetic scheme
:      <closed> + n cai <-> <open>	(alpha,beta)
:
:   Following this model, the activation fct will be half-activated at 
:   a concentration of Cai = (beta/alpha)^(1/n) = cac (parameter)
:   The mod file is here written for the case n=2 (2 binding sites)
:   ---------------------------------------------
:
:   Kinetics based on: Partridge & Swandulla, TINS 11: 69-72, 1988.
:
:   This current has the following properties:
:      - inward current (non specific for cations Na, K, Ca, ...)
:      - activated by intracellular calcium
:      - NOT voltage dependent
:
:   Written by Alain Destexhe, Salk Institute, Dec 7, 1992
:

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX icanINT
	USEION other2 WRITE iother2 VALENCE 1
	USEION Ca READ Cai VALENCE 2
	USEION ca READ cai
        RANGE gbar, i, g, ratc, ratC
	GLOBAL m_inf, tau_m, beta, cac, taumin, erev, x
}


UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(molar) = (1/liter)
	(mM) = (millimolar)
}


PARAMETER {
	v		(mV)
	celsius	= 36	(degC)
	erev = 10	(mV)
	cai 	= .00005	(mM)	: initial [Ca]i = 50 nM
	Cai 	= .00005	(mM)	: initial [Ca]i = 50 nM
	gbar	= 1e-5	(mho/cm2)
	beta	= 2.5	(1/ms)		: backward rate constant
	cac	= 1e-4	(mM)		: middle point of activation fct
	taumin	= 0.1	(ms)		: minimal value of time constant
        ratc    = 1
        ratC    = 1
        x       = 2
}


STATE {
	m
}

INITIAL {
:
:  activation kinetics are assumed to be at 22 deg. C
:  Q10 is assumed to be 3
:
	VERBATIM
	cai = _ion_cai;
	Cai = _ion_Cai;
	ENDVERBATIM

	tadj = 3.0 ^ ((celsius-22.0)/10)

	evaluate_fct(v,cai,Cai)
	m = m_inf
}

ASSIGNED {
	i	(mA/cm2)
	iother2	(mA/cm2)
	g       (mho/cm2)
	m_inf
	tau_m	(ms)
	tadj
}

BREAKPOINT { 
	SOLVE states METHOD cnexp
	g = gbar * m*m 
	i = g * (v - erev)
	iother2 = i
}

DERIVATIVE states { 
	evaluate_fct(v,cai,Cai)

	m' = (m_inf - m) / tau_m
}

UNITSOFF

PROCEDURE evaluate_fct(v(mV),cai(mM),Cai(mM)) {  LOCAL alpha2, tcar
  
        tcar = ratc*cai + ratC*Cai
	alpha2 = beta * (tcar/cac)^x
 
	tau_m = 1 / (alpha2 + beta) / tadj
	m_inf = alpha2 / (alpha2 + beta)

        if(tau_m < taumin) { tau_m = taumin } 	: min value of time cst
}
UNITSON






