: $Id: ntt.mod,v 1.7 2003/12/11 00:37:51 billl Exp $
: EDITED BY ERICA GRIFFITH FEB 2020 FOR USE IN THALAMIC INTERNEURON MODEL 
TITLE Low threshold calcium current
:
:   Ca++ current responsible for low threshold spikes (LTS)
:   RETICULAR THALAMUS
:   Differential equations 
:
:   Model of Huguenard & McCormick, J Neurophysiol 68: 1373-1383, 1992.
:   The kinetics is described by standard equations (NOT GHK)
:   using a m2h format, according to the voltage-clamp data
:   (whole cell patch clamp) of Huguenard & Prince, J Neurosci.
:   12: 3804-3817, 1992.
:
:    - Kinetics adapted to fit the T-channel of reticular neuron
:    - Q10 changed to 5 and 3
:    - Time constant tau_h fitted from experimental data
:    - shift parameter for screening charge
:
:   ACTIVATION FUNCTIONS FROM EXPERIMENTS (NO CORRECTION)
:
:   Reversal potential taken from Nernst Equation
:
:   Written by Alain Destexhe, Salk Institute, Sept 18, 1992
:

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX it2INT
	USEION ca READ cai, cao WRITE ica VALENCE 2
	RANGE gcabar, g, shift1
	GLOBAL m_inf, tau_m, h_inf, tau_h, shift2, sm, sh, phi_m, phi_h, hx, mx,rat
}

UNITS {
	(molar) = (1/liter)
	(mV) =	(millivolt)
	(mA) =	(milliamp)
	(mM) =	(millimolar)

	FARADAY = (faraday) (coulomb)
	R = (k-mole) (joule/degC)
}

PARAMETER {
	v		(mV)
	celsius	= 36	(degC)
:	eCa	= 120	(mV)
	gcabar	= .024	(mho/cm2)
	shift1	= -1 	(mV)
        shift2  = -6    (mV) 
        sm      = 7.4
        sh      = 5.0
        hx      = 1.5
        mx      = 3.0
	cai	= 5e-5 (mM)		: adjusted for eca=120 mV
	cao	= 2	(mM)
	rat	= 1
}

STATE {
	m h
}

ASSIGNED {
	ica	(mA/cm2)
	g       (mho/cm2)
	carev	(mV)
	m_inf
	tau_m	(ms)
	h_inf
	tau_h	(ms)
	phi_m
	phi_h
}

BREAKPOINT {
	SOLVE castate METHOD cnexp
	g = gcabar * m*m*h
	ica = g * ghk(v, cai, cao)
}

DERIVATIVE castate {
	evaluate_fct(v)

	m' = (m_inf - m) / tau_m
	h' = (h_inf - h) / tau_h
}

UNITSOFF
INITIAL {
	VERBATIM
	cai = _ion_cai;
	cao = _ion_cao;
	ENDVERBATIM

:   Activation functions and kinetics were obtained from
:   Huguenard & Prince, and were at 23-25 deg.
:   Transformation to 36 deg assuming Q10 of 5 and 3 for m and h
:   (as in Coulter et al., J Physiol 414: 587, 1989)
:
	phi_m = mx ^ ((celsius-24)/10)
	phi_h = hx ^ ((celsius-24)/10)

	evaluate_fct(v)
	m = m_inf
	h = h_inf
}

PROCEDURE evaluate_fct(v(mV)) { 
:
:   Time constants were obtained from J. Huguenard
:

	m_inf = 1.0 / ( 1 + exp(-(v+shift1+50)/sm) )
	h_inf = 1.0 / ( 1 + exp((v+shift2+78)/sh) )

	tau_m = (2+1.0/(exp((v+shift1+35)/10)+exp(-(v+shift1+100)/15)))/ phi_m
	tau_h = (24.22+1.0/(exp((v+55.56)/3.24)+exp(-(v+383.56)/51.26)))/phi_h
}

FUNCTION ghk(v(mV), Ci(mM), Co(mM)) (.001 coul/cm3) {
	LOCAL z, eci, eco
	z = (1e-3)*2*FARADAY*v/(R*(celsius+273.15))
	eco = Co*efun(z)*rat
	eci = Ci*efun(-z)
	:high Cao charge moves inward
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






