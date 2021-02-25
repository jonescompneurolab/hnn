: $Id: cp.mod,v 1.10 1998/08/16 20:43:43 billl Exp $
: EDITED BY ERICA Y GRIFFITH, JAN 2020 for use in THALAMIC INTERNEURON MODEL
TITLE decay of internal calcium concentration
:
: Internal calcium concentration due to calcium currents and pump.
: Differential equations.
:
: Simple model of ATPase pump with 3 kinetic constants (Destexhe 92)
:     Cai + P <-> CaP -> Cao + P  (k1,k2,k3)
: A Michaelis-Menten approximation is assumed, which reduces the complexity
: of the system to 2 parameters: 
:       kt = <tot enzyme concentration> * k3  -> TIME CONSTANT OF THE PUMP
:	kd = k2/k1 (dissociation constant)    -> EQUILIBRIUM CALCIUM VALUE
: The values of these parameters are chosen assuming a high affinity of 
: the pump to calcium and a low transport capacity (cfr. Blaustein, 
: TINS, 11: 438, 1988, and references therein).  
:
: Units checked using "modlunit" -> factor 10000 needed in ca entry
:
: VERSION OF PUMP + DECAY (decay can be viewed as simplified buffering)
:
: All variables are range variables
:
:
: This mechanism was published in:  Destexhe, A. Babloyantz, A. and 
: Sejnowski, TJ.  Ionic mechanisms for intrinsic slow oscillations in
: thalamic relay neurons. Biophys. J. 65: 1538-1552, 1993)
:
: Written by Alain Destexhe, Salk Institute, Nov 12, 1992
:

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX cad_int
	USEION ca READ ica, cai WRITE cai
	RANGE depth,kt,kt2,kd,cainf,taur,k,taur2,cainf2,cai0
        RANGE drive_channel,drive_pump,drive_pump2
}

UNITS {
	(molar) = (1/liter)			: moles do not appear in units
	(mM)	= (millimolar)
	(um)	= (micron)
	(mA)	= (milliamp)
	(msM)	= (ms mM)
}

CONSTANT {
	FARADAY = 96489		(coul)		: moles do not appear in units
:	FARADAY = 96.489	(k-coul)	: moles do not appear in units
}

PARAMETER {
	depth	= .1	(um)		: depth of shell
	taur	= 700	(ms)		: rate of calcium removal
	taur2	= 70	(ms)		: rate of calcium removal
	cainf	= 1e-8	(mM)
	cainf2	= 5e-5	(mM)
	cai0  = 5e-5	(mM)
	kt	= 1	(mM/ms)		: estimated from k3=.5, tot=.001
	kt2	= 1	(mM/ms)		: estimated from k3=.5, tot=.001
	kd	= 5e-4	(mM)		: estimated from k2=250, k1=5e5
	kd2	= 1e-7	(mM)		: estimated from k2=250, k1=5e5 : NOT RANGE VAR!!!
        k       = 1
}

ASSIGNED {
	ica		(mA/cm2)
	drive_channel	(mM/ms)
	drive_pump	(mM/ms)
	drive_pump2	(mM/ms)
}

STATE {
	cai		(mM) <1e-8> : to have tolerance of .01nM
}

INITIAL {
	cai = cai0
}

BREAKPOINT {
	SOLVE state METHOD cnexp
}

DERIVATIVE state { 

	drive_channel =  - (k*10000) * ica / (2 * FARADAY * depth)

	if (drive_channel<=0.) { drive_channel = 0. }: cannot pump inward

:	drive_pump = -tot * k3 * cai / (cai + ((k2+k3)/k1) )	: quasistat
	drive_pump = -kt * cai / (cai + kd )		: Michaelis-Menten
	drive_pump2 = -kt2 * cai / (cai + kd2 )		: Michaelis-Menten
	cai' = drive_channel+drive_pump+drive_pump2+(cainf-cai)/taur+(cainf2-cai)/taur2
}