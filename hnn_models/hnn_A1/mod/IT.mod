:$Id: IT.mod,v 1.12 2004/06/08 19:32:19 billl Exp $
TITLE Low threshold calcium current
:
:   Ca++ current responsible for low threshold spikes (LTS)
:   THALAMOCORTICAL CELLS
:   Differential equations
:
:   Model based on the data of Huguenard & McCormick, J Neurophysiol
:   68: 1373-1383, 1992 and Huguenard & Prince, J Neurosci.
:   12: 3804-3817, 1992.
:
:   Features:
:
:	- kinetics described by Nernst equations using a m2h format
:	- activation considered at steady-state
:	- inactivation fit to Huguenard's data using a bi-exp function
:	- shift for screening charge, q10 of inactivation of 3
:
:   Described in:
:    Destexhe, A., Bal, T., McCormick, D.A. and Sejnowski, T.J.  Ionic 
:    mechanisms underlying synchronized oscillations and propagating waves
:    in a model of ferret thalamic slices. Journal of Neurophysiology 76:
:    2049-2070, 1996.  (see http://www.cnl.salk.edu/~alain)
:
:
:   Alain Destexhe, Salk Institute and Laval University, 1995
:

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX ittc
	USEION ca READ cai,cao WRITE ica
	GLOBAL q10m,q10h
	RANGE g, gmax, m_inf, tau_m, h_inf, tau_h, shift, i
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
	gmax	= 0.0022 (mho/cm2)
	q10m	= 3			: Q10 of activation
	q10h	= 3			: Q10 of inactivation
        exptemp = 24    (degC)
	shift	= 2 	(mV)		: corresponds to 2mM ext Ca++
	cai	= 2.4e-4 (mM)		: adjusted for eca=120 mV
	cao	= 2	(mM)
}

STATE {
  m h
}

ASSIGNED {
	g	(mho/cm2)
	i	(mA/cm2)
	ica	(mA/cm2)
	carev	(mV)
	m_inf
	tau_m	(ms)			: dummy variable for compatibility
	h_inf
	tau_h	(ms)
	phi_m
	phi_h
        celsius
}

BREAKPOINT {
	SOLVE states METHOD cnexp
	carev = (1e3) * (R*(celsius+273.15))/(2*FARADAY) * log (cao/cai)
	g = gmax * m * m * h
	i = g * (v-carev)
        ica = i
}

DERIVATIVE states {
	mh(v)

	m' = (m_inf - m) / tau_m
	h' = (h_inf - h) / tau_h
}


UNITSOFF
INITIAL {
:
:   Transformation to 36 deg assuming Q10 of 3 for h
:   (as in Coulter et al., J Physiol 414: 587, 1989)

	phi_m = q10m ^ ((celsius-exptemp)/10)
	phi_h = q10h ^ ((celsius-exptemp)/10)

	mh(v)
	h = h_inf
	m = m_inf
}

PROCEDURE mh (v(mV)) { LOCAL Vm

	Vm = v + shift

	m_inf = 1.0 / ( 1 + exp(-(Vm+57)/6.2) )
	h_inf = 1.0 / ( 1 + exp((Vm+81)/4.0) )

:       tau_m = (0.822/(exp(-(Vm+130  )/16.7) + exp((Vm+14.8)/18.2) ) + 0.480)/phi_m
        tau_m = (1  /  (exp(-(Vm+129.6)/16.7) + exp((Vm+14.8)/18.2) ) + 0.612)/phi_m
:	tau_h = ( 8.2+(56.6+0.27*exp((Vm+113.2)/5))/(1+exp((Vm+84)/3.2)))/phi_h
        tau_h = (30.8+(211.4  +  exp((Vm+113.2)/5))/(1+exp((Vm+84)/3.2)))/phi_h
}

UNITSON
