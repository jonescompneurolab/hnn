: $Id: Iahp.mod,v 1.8 2000/01/05 19:55:19 billl Exp $
TITLE Slow Ca-dependent potassium current
:
:   Ca++ dependent K+ current IC responsible for slow AHP
:   Differential equations
:
:   Model of Destexhe, 1992.  Based on a first order kinetic scheme
:      <closed> + n cai <-> <open>	(alpha,beta)
:   Following this model, the activation fct will be half-activated at 
:   a concentration of Cai = (beta/alpha)^(1/n) = cac (parameter)
:   The mod file is here written for the case n=2 (2 binding sites)
:   ---------------------------------------------
:
:   This current models the "slow" IK[Ca] (IAHP): 
:      - potassium current
:      - activated by intracellular calcium
:      - NOT voltage dependent
:
:   A minimal value for the time constant has been added
:
:   Written by Alain Destexhe, Salk Institute, Nov 3, 1992
:

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX iahp
	USEION k2 WRITE ik2 VALENCE 1
	USEION Ca READ Cai VALENCE 2
	USEION ca READ cai
        RANGE gkbar, i, g, ratc, ratC, minf, taum
	GLOBAL beta, cac, m_inf, tau_m, x
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
	erev = -95		(mV)
	Cai 	= 5e-5	(mM)		: initial [Ca]i = 50 nM
	cai 	= 5e-5	(mM)		: initial [Ca]i = 50 nM
	gkbar	= .001	(mho/cm2)
	beta	= 2.5	(1/ms)		: backward rate constant
	cac	= 1e-4	(mM)		: middle point of activation fct
	taumin	= 1	(ms)		: minimal value of the time cst
        ratc    = 0
        ratC    = 0
        x       = 2
}


STATE {
	m
}
ASSIGNED {
	ik2 	(mA/cm2)
	i	(mA/cm2)
	g       (mho/cm2)
	m_inf
	tau_m	(ms)
	minf
        taum
	tadj
}

BREAKPOINT { 
	SOLVE states METHOD cnexp
        minf=m_inf
        taum=tau_m
	g = gkbar * m*m
	i = g * (v - erev)
	ik2  = i
}

DERIVATIVE states { 
	evaluate_fct(v,Cai,cai)

	m' = (m_inf - m) / tau_m
}

UNITSOFF
INITIAL {
:
:  activation kinetics are assumed to be at 22 deg. C
:  Q10 is assumed to be 3
:
	VERBATIM
	cai = _ion_cai;
	Cai = _ion_Cai;
	ENDVERBATIM

	tadj = 3 ^ ((celsius-22.0)/10)

	evaluate_fct(v,Cai,cai)
	m = m_inf
        minf=m_inf
        taum=tau_m
}

PROCEDURE evaluate_fct(v(mV),Cai(mM), cai(mM)) {  LOCAL car, tcar

        tcar = ratC*Cai + ratc*cai
	car = (tcar/cac)^x

	m_inf = car / ( 1 + car )
	tau_m = 1 / beta / (1 + car) / tadj

        if(tau_m < taumin) { tau_m = taumin } 	: min value of time cst
}
UNITSON






