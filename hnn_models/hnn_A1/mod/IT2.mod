: $Id: IT2.mod,v 1.9 2004/06/08 00:46:04 billl Exp $
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
:    - Time constant tau_h refitted from experimental data
:    - shift parameter for screening charge
:
:   Model described in detail in:   
:     Destexhe, A., Contreras, D., Steriade, M., Sejnowski, T.J. and
:     Huguenard, J.R.  In vivo, in vitro and computational analysis of
:     dendritic calcium currents in thalamic reticular neurons.
:     Journal of Neuroscience 16: 169-185, 1996.
:
:
:   Written by Alain Destexhe, Salk Institute, Sept 18, 1992
:

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX itre
	USEION ca READ cai, cao WRITE ica
	RANGE gmax, m_inf, tau_m, h_inf, tau_h, carev, shift, i
        GLOBAL exptemp, q10m, q10h
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
	gmax	= .003	(mho/cm2)
	shift	= 2 	(mV)
	q10m	= 2.5
	q10h	= 2.5
        exptemp = 24
        cao
        cai

}

STATE {
	m h
}

ASSIGNED {
	i	(mA/cm2)  
	ica	(mA/cm2)
	carev	(mV)
	m_inf
	tau_m	(ms)
	h_inf
	tau_h	(ms)
	phim
        phih
}

BREAKPOINT {
	SOLVE states METHOD cnexp
	carev = (1e3) * (R*(celsius+273.15))/(2*FARADAY) * log (cao/cai)
	i = gmax * m*m*h * (v-carev)
        ica=i
}

DERIVATIVE states {
	mh(v)

	m' = (m_inf - m) / tau_m
	h' = (h_inf - h) / tau_h
}

UNITSOFF
INITIAL {
:
:   Activation functions and kinetics were obtained from
:   Huguenard & Prince, and were at 23-25 deg.
:   Transformation to 36 deg using Q10
:
	phim = q10m ^ ((celsius-exptemp)/10)
	phih = q10h ^ ((celsius-exptemp)/10)

	mh(v)
	m = m_inf
	h = h_inf
}

PROCEDURE mh(v(mV)) { 
:
:   Time constants were obtained from J. Huguenard
:

	m_inf = 1.0 / ( 1 + exp(-(v+shift+50)/7.4) )
	h_inf = 1.0 / ( 1 + exp((v+shift+78)/5.0) )

	tau_m = ( 1 + 0.33 / ( exp((v+shift+25)/10) + exp(-(v+shift+100)/15) ) ) / phim
:	tau_h = ( 22.7 + 0.27 / ( exp((v+shift+46)/4) + exp(-(v+shift+405)/50) ) ) / phih
:	tau_h = ( 56.75 + 0.675 / ( exp((v+shift+46)/4) + exp(-(v+shift+405)/50) ) ) / phih
	tau_h = ( 85 + 1.0 / ( exp((v+shift+46)/4) + exp(-(v+shift+405)/50) ) ) / phih
}
UNITSON
