: $Id: kapyrkop.mod,v 1.1 2009/11/05 15:11:20 samn Exp $ 
COMMENT

//%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
//
// NOTICE OF COPYRIGHT AND OWNERSHIP OF SOFTWARE
//
// Copyright 2007, The University Of Pennsylvania
// 	School of Engineering & Applied Science.
//   All rights reserved.
//   For research use only; commercial use prohibited.
//   Distribution without permission of Maciej T. Lazarewicz not permitted.
//   mlazarew@seas.upenn.edu
//
//%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

This mode file is based on the paper:

Tort, A. B., Rotstein, H. G., Dugladze, T., et al. (2007). On the formation of gamma-coherent cell
assemblies by oriens lacunosum-moleculare interneurons in the hippocampus. Proc Natl Acad Sci U S A.

ENDCOMMENT

NEURON {
	SUFFIX KaPyrKop
	USEION k WRITE ik
	RANGE  ck, dk, ek, fk, gmax, ik, atau, btau, ainf, binf
}
	
UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(mS) = (millisiemens)
}

PARAMETER {
    gmax =    0.0 (mS/cm2)
    erev =  -90.0 (mV)
    ck   =    0.0 (1)
    dk   =    0.0 (1)
    ek   =    0.0 (mV)
    fk   =    0.0 (1)
}
    
ASSIGNED {
    v       (mV)
    ik      (mA/cm2)
    ainf	(1)
    binf	(1)
    atau	(ms)
    btau	(ms) 
}

STATE { a b }

INITIAL { 
    rates(v)
    a  = ainf
    b  = binf
}

BREAKPOINT {
	SOLVE states METHOD cnexp
	ik = (1e-3) * gmax * a * b * (v-erev)
}


DERIVATIVE states { 
	rates(v)
	a' = (ainf-a)/atau 
	b' = (binf-b)/btau 
}


PROCEDURE rates(v (mV)) { LOCAL aa, ba

	aa = exp(-0.038(/mV)*(dk+fun2(v, -40.0, 1.0, 5.0)*1.0(ms))*(v-ek))
	
	: originally there was a bug (following code)
	:aa = exp(-0.038*(dk+1/(1+exp(v+40)/5))*(v-ek))
	
	ba = exp(-0.038(/mV)*(fk+fun2(v, -40.0, 1.0, 5.0)*1.0(ms))*(v-ek))
	
	:ba = exp(-0.038*(fk+1/(1+exp(v+40)/5))*(v-ek))
	
	ainf = 1.0/(1.0+aa)
	atau = max(0.1,ck*ba/(1.0+aa))*1.0(ms)
	
	binf = fun2(v, -56.0, 1.0, 1.0/0.11)*1.0(ms)
	btau = max(2.0, 0.26(/mV)*(v+50.0))*1.0(ms) 
}


INCLUDE "aux_fun.inc"
