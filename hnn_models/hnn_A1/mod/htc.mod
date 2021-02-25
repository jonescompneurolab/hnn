: $Id: Ih.mod,v 1.9 2004/06/08 20:09:04 billl Exp $
: from https://senselab.med.yale.edu/ModelDB/showmodel.cshtml?model=37819
: based on: Bazhenov M, Timofeev I, Steriade M, Sejnowski TJ (1998)
:           Computational models of thalamocortical augmenting responses. J Neurosci 18:6444-65
TITLE anomalous rectifier channel
COMMENT
:
: Anomalous Rectifier Ih - cation (Na/K) channel in thalamocortical neurons
:
: Kinetic model of calcium-induced shift in the activation of Ih channels.
: Model of Destexhe et al., Biophys J. 65: 1538-1552, 1993, based on the
: voltage-clamp data on the calcium dependence of If in heart cells
: (Harigawa & Irisawa, J. Physiol. 409: 121, 1989)
:
: The voltage-dependence is derived from Huguenard & McCormick, 
: J Neurophysiol. 68: 1373-1383, 1992, based on voltage-clamp data of 
: McCormick & Pape, J. Physiol. 431: 291, 1990. 
:
: Modified model of the binding of calcium through a calcium-binding (CB)
: protein, which in turn acts on Ih channels.  This model was described in
: detail in the following reference:
:    Destexhe, A., Bal, T., McCormick, D.A. and Sejnowski, T.J.  Ionic 
:    mechanisms underlying synchronized oscillations and propagating waves
:    in a model of ferret thalamic slices. Journal of Neurophysiology 76:
:    2049-2070, 1996.  (see http://www.cnl.salk.edu/~alain)
:
:   KINETIC MODEL:
:
:	  Normal voltage-dependent opening of Ih channels:
:
:		c1 (closed) <-> o1 (open)	; rate cst alpha(V),beta(V)
:
:	  Ca++ binding on CB protein
:
:		p0 (inactive) + nca Ca <-> p1 (active)	; rate cst k1,k2
:
:	  Binding of active CB protein on the open form (nexp binding sites) :
:
:		o1 (open) + nexp p1 <-> o2 (open)	; rate cst k3,k4
:
:
:   PARAMETERS:
:	It is more useful to reformulate the parameters k1,k2 into
:	k2 and cac = (k2/k1)^(1/nca) = half activation calcium dependence, 
:	and idem for k3,k4 into k4 and Pc = (k4/k3)^(1/nexp) = half activation
:	of Ih binding (this is like dealing with tau_m and m_inf instead of
:	alpha and beta in Hodgkin-Huxley equations)
:	- k2:	this rate constant is the inverse of the real time constant of 
:             	the binding of Ca to the CB protein
:	- cac:	the half activation (affinity) of the CB protein;
:		around 1 to 10 microM.  
:	- k4:	this rate constant is the inverse of the real time constant of 
:             	the binding of the CB protein to Ih channels
:		very low: it basically governs the interspindle period
:	- Pc:	the half activation (affinity) of the Ih channels for the
:		CB protein;
:	- nca:	number of binding sites of calcium on CB protein; usually 4
:	- nexp:	number of binding sites on Ih channels
:       - ginc: augmentation of conductance associated with the Ca bound state
:	  (about 2-3; see Harigawa & Hirisawa, 1989)
:
:
:   IMPORTANT REMARKS:
:       - This simple model for the binding of Ca++ on the open channel 
:	  suffies to account for the shift in the voltage-dependence of Ih
:	  activation with calcium (see details in Destexhe et al, 1993).
:	- It may be that calcium just binds to the Ih channel, preventing the 
:	  conformational change between open and closed; in this case one
:	  should take into account binding on the closed state, which is 
:	  neglected here.
:
:   MODIFICATIONS
:	- this file also contains a procedure ("activation") to estimate
:	  the steady-state activation of the current; callable from outside
:	- the time constant now contains a changeable minimal value (taum)
:	- shift: new local variable to displace the voltage-dependence
:	  (shift>0 -> depolarizing shift)
:
:
: Alain Destexhe, Salk Institute and Laval University, 1995
:
ENDCOMMENT

NEURON {
  THREADSAFE
	SUFFIX htc
    NONSPECIFIC_CURRENT ih
	USEION ca READ cai
        RANGE gmax, h_inf, tau_s, m, shift, i
        RANGE alpha,beta,k1ca,k3p
	:GLOBAL k2, cac, k4, Pc, nca, nexp, ginc, taum
        RANGE k2, cac, k4, Pc, nca, nexp, ginc, taum, exptemp
}

UNITS {
	(molar)	= (1/liter)
	(mM)	= (millimolar)
	(mA) 	= (milliamp)
	(mV) 	= (millivolt)
	(msM)	= (ms mM)
}


PARAMETER {
  eh        (mV)
  : celsius = 36	(degC)
  gmax	= 2e-5 (mho/cm2)
  cac	= 0.002 (mM)		: half-activation of calcium dependence
  k2	= 0.0004 (1/ms)		: inverse of time constant
  Pc	= 0.01			: half-activation of CB protein dependence
  k4	= 0.001	(1/ms)		: backward binding on Ih
  nca	= 4			: number of binding sites of ca++
  nexp	= 1			: number of binding sites on Ih channels
  ginc	= 2			: augmentation of conductance with Ca++
  taum	= 20.0	(ms)		: min value of tau
  shift	= 0	(mV)		: shift of Ih voltage-dependence
  q10     = 3
  exptemp = 36
}


STATE {
	c1	: closed state of channel
	o1	: open state
	o2	: CB-bound open state
	p0	: resting CB
	p1	: Ca++-bound CB
}


ASSIGNED {
	v	(mV)
	cai	(mM)
	i	(mA/cm2)
	ih	(mA/cm2)
        gh	(mho/cm2)
	h_inf
	tau_s	(ms)
	alpha	(1/ms)
	beta	(1/ms)
	k1ca	(1/ms)
	k3p	(1/ms)
	m
	tadj
}


BREAKPOINT {
	SOLVE ihkin METHOD sparse

	m = o1 + ginc * o2

	i = gmax * m * (v - eh)
        ih=i
}

KINETIC ihkin {
:
:  Here k1ca and k3p are recalculated at each call to evaluate_fct
:  because Ca or p1 have to be taken at some power and this does
:  not work with the KINETIC block.
:  So the kinetics is actually equivalent to
:	c1 <-> o1
:	p0 + nca Cai <-> p1
:	o1 + nexp p1 <-> o2

	evaluate_fct(v,cai)

	~ c1 <-> o1		(alpha,beta)

	~ p0 <-> p1		(k1ca,k2)

	~ o1 <-> o2		(k3p,k4)

	CONSERVE p0 + p1 = 1
	CONSERVE c1 + o1 + o2 = 1
}

INITIAL {
:
:  Experiments of McCormick & Pape were at 36 deg.C
:  Q10 is assumed equal to 3
:
        tadj = q10 ^ ((celsius-exptemp)/10)

	evaluate_fct(v,cai)

	c1 = 1
	o1 = 0
	o2 = 0
	p0 = 1
	p1 = 0
}


UNITSOFF
PROCEDURE evaluate_fct(v (mV), cai (mM)) {

VERBATIM
cai = _ion_cai;
ENDVERBATIM

	h_inf = 1 / ( 1 + exp((v+75-shift)/5.5) )

:	tau_s = (taum + 267/(exp((v+71.5-shift)/14.2)+exp(-(v+89-shift)/11.6))) / tadj
        tau_s = (taum +1000/(exp((v+71.5-shift)/14.2)+exp(-(v+89-shift)/11.6))) / tadj

	alpha = h_inf / tau_s
	beta  = (1-h_inf)/tau_s

	k1ca = k2 * (cai/cac)*(cai/cac)*(cai/cac)*(cai/cac) : ^nca = 4
	k3p = k4 * (p1/Pc) : ^nexp = 1
}

:
:  procedure for evaluating the activation curve of Ih
:
PROCEDURE activation(v (mV), cai (mM)) { LOCAL cc

VERBATIM
cai = _ion_cai;
ENDVERBATIM
	evaluate_fct(v,cai)
	cc = 1 / (1 + (cac/cai)^nca ) 		: equil conc of CB-protein
	m = 1 / ( 1 + beta/alpha + (cc/Pc)^nexp )
	m = ( 1 + ginc * (cc/Pc)^nexp ) * m
}

UNITSON

