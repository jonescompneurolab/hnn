: $Id: IL.mod,v 1.5 2009/01/13 14:32:37 billl Exp $
TITLE High threshold calcium current
:
:   Ca++ current, L type channels, responsible for calcium spikes
:   Differential equations
:
:   Model of Huguenard & McCormick, J Neurophysiol, 1992
:   Formalism of Goldman-Hodgkin-Katz
:
:   Kinetic functions were fitted from data of hippocampal pyr cells
:   (Kay & Wong, J. Physiol. 392: 603, 1987)
:
:   Written by Alain Destexhe, Salk Institute, Sept 18, 1992
:

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX icalINT
	USEION Ca READ Cai, Cao WRITE iCa VALENCE 2
        RANGE pcabar, g
	GLOBAL 	m_inf, tau_m, sh1, sh2, rat
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
	eCa     = 120	(mV)
	Cai 	= .00005	(mM)	: initial [Ca]i = 50 nM
	Cao 	= 2	(mM)	: [Ca]o = 2 mM
	pcabar	= .003	(mho/cm2)	: gL is about 2x that of IT (McCormick)
	sh1 	= 0		 
	sh2	= 0
	rat	= 1
}


STATE {
	m
}


ASSIGNED {
	iCa	(mA/cm2)
	g       (mho/cm2)
	m_inf
	tau_m	(ms)
        tadj
}

BREAKPOINT { 
	SOLVE states METHOD cnexp
	g = pcabar * m * m
	iCa = g * ghk(v, Cai, Cao)
}

DERIVATIVE states { 
	evaluate_fct(v)

	m' = (m_inf - m) / tau_m
}

UNITSOFF
INITIAL {
	tadj = 3 ^ ((celsius-21.0)/10)
	evaluate_fct(v)
	m = m_inf
}

PROCEDURE evaluate_fct(v(mV)) {  LOCAL a,b
:
:  activation kinetics of Kay-Wong were at 20-22 deg. C
:  transformation to 36 deg assuming Q10=3
:
	a = 1.6 / (1 + exp(-0.072*(v+sh1+5)) )
	b = 0.02 * (v+sh2-1.31) / ( exp((v+sh2-1.31)/5.36) - 1)

	tau_m = 1.0 / (a + b) / tadj
	m_inf = a / (a + b)
}

FUNCTION ghk(v(mV), ci(mM), co(mM)) (.001 coul/cm3) {
	LOCAL z, eci, eco
	z = (1e-3)*2*FARADAY*v/(R*(celsius+273.15))
	eco = co*efun(z)*rat
	eci = ci*efun(-z)
	:high co charge moves inward
	:negative potential charge moves inward
	ghk = (.001)*2*FARADAY*(eci - eco)
}

FUNCTION efun(z) {
	if (fabs(z) < 1e-4) {
		efun = 1 - z/2
	}else{
		efun = z/(exp(z) - 1)
	}
}
UNITSON






