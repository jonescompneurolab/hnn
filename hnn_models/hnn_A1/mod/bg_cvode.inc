: $Id: bg_cvode.inc,v 1.19 2009/01/13 13:59:48 billl Exp $
TITLE Kevin's Cvode modification to Borg Graham Channel Model
: EDITED BY ERICA Y GRIFFITH FEB 2020 FOR USE IN THALAMIC INTERNEURON MODEL 
COMMENT

Modeling the somatic electrical response of hippocampal pyramidal neurons, 
MS thesis, MIT, May 1987.

Each channel has activation and inactivation particles as in the original
Hodgkin Huxley formulation.  The activation particle mm and inactivation
particle hh go from on to off states according to kinetic variables alpha
and beta which are voltage dependent.  The form of the alpha and beta
functions were dissimilar in the HH study.  The BG formulae are:
	alpha = base_rate * Exp[(v - v_half)*valence*gamma*F/RT]
	beta = base_rate * Exp[(-v + v_half)*valence*(1-gamma)*F/RT]
where,
	baserate : no affect on Inf.  Lowering this increases the maximum
		    value of Tau
	basetau : (in msec) minimum Tau value.
	chanexp : number for exponentiating the state variable; e.g.
		  original HH Na channel use m^3, note that chanexp = 0
		  will turn off this state variable
	erev : reversal potential for the channel
	gamma : (between 0 and 1) does not affect the Inf but makes the
		Tau more asymetric with increasing deviation from 0.5
	celsius : temperature at which experiment was done (Tau will
		      will be adjusted using a q10 of 3.0)
	valence : determines the steepness of the Inf sigmoid.  Higher
		  valence gives steeper sigmoid.
	vhalf : (a voltage) determines the voltage at which the value
		 of the sigmoid function for Inf is 1/2
        vrest : (a voltage) voltage shift for vhalf

ENDCOMMENT

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
  RANGE gmax, mvhalf, mvalence, hvhalf, hvalence, g, i
  GLOBAL erev, Inf, Tau, vrest, ki, mininf
} : end NEURON

CONSTANT {
  FARADAY = 96489.0	: Faraday's constant
  R= 8.31441		: Gas constant
} : end CONSTANT

UNITS {
  (mA) = (milliamp)
  (mV) = (millivolt)
  (umho) = (micromho)
} : end UNITS


COMMENT
** Parameter values should come from files specific to particular channels
PARAMETER {
	erev 		= 0    (mV)
	gmax 		= 0    (mho/cm^2)
        vrest           = 0    (mV)

	mvalence 	= 0
	mgamma 		= 0
	mbaserate 	= 0
	mvhalf 		= 0
	mbasetau 	= 0
	mtemp 		= 0
	mq10		= 3
	mexp 		= 0

	hvalence 	= 0
	hgamma		= 0
	hbaserate 	= 0
	hvhalf 		= 0
	hbasetau 	= 0
	htemp 		= 0
	hq10		= 3
	hexp 		= 0

} : end PARAMETER
ENDCOMMENT

PARAMETER {
  ki = 1e-3  (mM)
  mininf = 1e-4
  cao                (mM)
  cai                (mM)
}

ASSIGNED {
  i (mA/cm^2)		
  g (mho/cm^2)
  Inf[2]		: 0 = m and 1 = h
  Tau[2]		: 0 = m and 1 = h
  mexp_val
  hexp_val
} : end ASSIGNED 

STATE { m h }

INITIAL { 
  mh(v)
  m = Inf[0] h = Inf[1]
}

BREAKPOINT {
  if (gmax==0.0) { g=0. } else {

  SOLVE states METHOD cnexp

  hexp_val = 1
  mexp_val = 1

  : Determining h's exponent value
  if (hexp > 0) {
    FROM index=1 TO hexp {
      hexp_val = h * hexp_val
    }
  }

  : Determining m's exponent value
  if (mexp > 0) {
    FROM index = 1 TO mexp {
      mexp_val = m * mexp_val
    }
  }

  :		       	         mexp			      hexp
  : Note that mexp_val is now = m      and hexp_val is now = h 
  g = gmax * mexp_val * hexp_val
  }
  iassign()
} : end BREAKPOINT

: ASSIGNMENT PROCEDURES
: Must be overwritten by user routines in parameters.multi
: PROCEDURE iassign () { i = g*(v-erev) ina=i }
: PROCEDURE iassign () { i = g*ghkca(v) ica=i }

:-------------------------------------------------------------------

DERIVATIVE states {
  mh(v)
  m' = (-m + Inf[0]) / Tau[0] 
  h' = (-h + Inf[1]) / Tau[1]
}
:-------------------------------------------------------------------
: NOTE : 0 = m and 1 = h
PROCEDURE mh (v) {
  LOCAL a, b, j, mqq10, hqq10

  mqq10 = mq10^((celsius-mtemp)/10.)	
  hqq10 = hq10^((celsius-htemp)/10.)	

  : Calculater Inf and Tau values for h and m
  FROM j = 0 TO 1 {
    a = alpha (v, j)
    b = beta (v, j)

    Inf[j] = a / (a + b)
    if (Inf[j]<mininf) { Inf[j]=0 }

    VERBATIM
    switch (_lj) {
      case 0:
      /* Make sure Tau is not less than the base Tau */
if ((Tau[_lj] = 1 / (_la + _lb)) < mbasetau) {
  Tau[_lj] = mbasetau;
}
Tau[_lj] = Tau[_lj] / _lmqq10;
break;
case 1:
if ((Tau[_lj] = 1 / (_la + _lb)) < hbasetau) {
  Tau[_lj] = hbasetau;
}
Tau[_lj] = Tau[_lj] / _lhqq10;
if (hexp==0) {
  Tau[_lj] = 1.; }
  break;
    }

    ENDVERBATIM
  }
} : end PROCEDURE mh (v)
:-------------------------------------------------------------------
FUNCTION alpha(v,j) {
  if (j == 1) {
    if (hexp==0) {
      alpha = 1
    } else {
      alpha = hbaserate * exp((v - (hvhalf+vrest)) * hvalence * hgamma * FRT(htemp)) }
  } else {
    alpha = mbaserate * exp((v - (mvhalf+vrest)) * mvalence * mgamma * FRT(mtemp))
  }
} : end FUNCTION alpha (v,j)

:-------------------------------------------------------------------
FUNCTION beta (v,j) {
  if (j == 1) {
    if (hexp==0) {
      beta = 1
    } else {
      beta = hbaserate * exp((-v + (hvhalf+vrest)) * hvalence * (1 - hgamma) * FRT(htemp)) }
  } else {
    beta = mbaserate * exp((-v + (mvhalf+vrest)) * mvalence * (1 - mgamma) * FRT(mtemp))
  }
} : end FUNCTION beta (v,j)

:-------------------------------------------------------------------
FUNCTION FRT(temperature) {
	FRT = FARADAY * 0.001 / R / (temperature + 273.15)
} : end FUNCTION FRT (temperature)

:-------------------------------------------------------------------
FUNCTION ghkca (v) { : Goldman-Hodgkin-Katz eqn
  LOCAL nu, efun

  nu = v*2*FRT(celsius)
  if(fabs(nu) < 1.e-6) {
    efun = 1.- nu/2.
  } else {
    efun = nu/(exp(nu)-1.) }

    ghkca = -FARADAY*2.e-3*efun*(cao - cai*exp(nu))
} : end FUNCTION ghkca()

: Ca-mediated inactivation of Ca channels, see Hille, Ed2 p179-180
: use eg iassign () { i = g*faco()*ghkca(v) ica=i }
FUNCTION faco() {
  faco = ki/(ki+cai)
}






