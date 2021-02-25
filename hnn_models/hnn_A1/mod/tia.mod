: $Id: tia.mod,v 1.9 2004/06/08 21:09:11 billl Exp $
TITLE rapidly inactivating potassium current
:
:   K+ current responsible for blocking rebound low threshold spikes (LTS)
:   LOCAL GABAERGIC INTERNEURONS IN THE THALAMUS
:   Differential equations 
:
:   Model of Huguenard & McCormick, J Neurophysiol 68: 1373-1383, 1992.
:   The kinetics is described by standard equations (NOT GHK)
:   using a m4h format, according to the voltage-clamp data
:   of Huguenard, Coulter & Prince, J Neurophysiol.
:   66: 1304-1315, 1991.
:
:    - Kinetics adapted to fit the A-channel of interneuron
:    - Q10 changed to 5 and 3
:    - Time constant tau_m and tau_h from experimental data (from TC)
:    - shift parameter for fitting interneuron data, according to the
:    - voltage-clamp data from premature rat by Pape et al. J.
:    - Physiol. 1994. 
:
:   ACTIVATION FUNCTIONS FROM EXPERIMENTS (NO CORRECTION)
:
:   Reversal potential taken from Nernst Equation
:
:   Written by Jun Zhu, University of Wisconsin, August 19, 1994, at MBL, Woods Hole, MA
:

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX ia
	USEION k  READ ek WRITE ik VALENCE 1
	RANGE gmax, i
	RANGE m_inf, tau_m, h_inf, tau_h, exptemp, q10
}

UNITS {
	(mV) =	(millivolt)
	(mA) =	(milliamp)
}

PARAMETER {
  ek
  v		(mV)
  : celsius	= 36	(degC)
  gmax	= 0.0	(mho/cm2)
  exptemp= 23.5
  q10 = 3
}

STATE {
  m h
}

ASSIGNED {
	ik	(mA/cm2)
	i	(mA/cm2)
	m_inf
	tau_m	(ms)
	h_inf
	tau_h	(ms)
        tadj
}

BREAKPOINT {
	SOLVE states METHOD cnexp
	i = gmax * (m*m*m*m*h * (v-ek))
        ik = i
}

DERIVATIVE states {
	evaluate_fct(v)

	m' = (m_inf - m) / tau_m
	h' = (h_inf - h) / tau_h 
}

UNITSOFF
INITIAL {
        tadj = pow(q10,((celsius-exptemp)/10))
	evaluate_fct(v)
	m = m_inf
	h = h_inf
:
:   Activation functions and kinetics were obtained from
:   Huguenard & McCormick, and were at 35.5 deg.

}

PROCEDURE evaluate_fct(v(mV)) { 
  :   Time constants were obtained from Huguenard & McCormick
  :   not sure about 7.4 and 5.0

  m_inf = 1.0 / ( 1 + exp(-(v+60)/8.5) )
  h_inf = 1.0 / ( 1 + exp((v+78)/6.0) )

  tau_m = (1.0/  (exp((v+35.82)/19.69)+exp(-(v+79.69)/12.7)) +0.37) / tadj
: tau_m = (0.27 /(exp((v+35.8 )/19.7 )+exp(-(v+79.7 )/12.7)) +0.1)
  if (v < -63) {
    tau_h =  1.0 /(exp((v+46.05)/5)+exp(-(v+238.4)/37.45)) / tadj
:   tau_h = (0.27/(exp((v+46)   /5)+exp(-(v+238)  /37.5)))
  } else {	
    tau_h = 19.0/tadj
   :tau_h = 5.1
  }
}
UNITSON




