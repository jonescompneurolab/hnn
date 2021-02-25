: $Id: kcpr.mod,v 1.1 2009/11/05 15:11:05 samn Exp $ 
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

ENDCOMMENT



NEURON {

	SUFFIX kcpr
	USEION k WRITE ik
	USEION ca READ cai
	RANGE gkc, ik
}
	
UNITS {    

    (mollar) = (1/liter)
	(mM)     = (millimollar)
	(mA) = (milliamp)
	(mV) = (millivolt)
	(mS) = (millisiemens)
}

PARAMETER {

    gkc = 15    (mS/cm2)
    ek = -75    (mV)
}
    
ASSIGNED { 

    ik   (mA/cm2)    
    v    (mV)
    cai  (mM)
    cinf (1)
    tauc (ms)
}

STATE { c }

INITIAL { 
    
    rates(v)
    c  = cinf
}

BREAKPOINT {

	SOLVE states METHOD cnexp
	
	ik = (1e-3) * gkc * min(cai/250(mM),1) * c * (v-ek)
}


DERIVATIVE states { 

    rates(v)
    c' = (cinf-c)/tauc
}


PROCEDURE rates(v(mV)) { LOCAL a, b

    if (v<=-10) {
    
        a = 2(/ms) / 37.95 * ( exp( ( v + 50 ) / 11(mV) - ( v + 53.5 ) / 27(mV) ) )
        b = 2(/ms) * exp( ( - v - 53.5 ) / 27(mV) ) - a
    
    }else{
    
        a =  2(/ms) * exp( ( - v - 53.5 ) / 27(mV) )
        b = 0(/ms)
    
    }
    
    cinf = a/(a+b)
    tauc = 1.0/(a+b)    
}

INCLUDE "aux_fun.inc"
