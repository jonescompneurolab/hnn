: $Id: nafpr.mod,v 1.1 2009/11/05 15:09:12 samn Exp $ 
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

	SUFFIX nafpr
	USEION na WRITE ina
	RANGE gna, ina
}
	
UNITS {

	(mA) = (milliamp)
	(mV) = (millivolt)
	(mS) = (millisiemens)
}

PARAMETER {

    gna  = 30 (mS/cm2)
    ena  = 55 (mV)
}
    
ASSIGNED {

    v    (mV)
    ina  (mA/cm2)
    minf (1)
    hinf (1)
    tauh (ms)
}

STATE { h }

INITIAL {
    
    rates(v)
    h  = hinf
}

BREAKPOINT {

	SOLVE states METHOD cnexp
	
	ina = (1e-3) * gna * minf^2 * h * (v-ena)
}


DERIVATIVE states { 

    rates(v)
    h' = (hinf-h)/tauh
}


:ina
PROCEDURE rates(v(mV)) { LOCAL a, b

    a    = fun3(v,  -46.9, -0.32,    -4) 
    b    = fun3(v,  -19.9,  0.28,     5) 
    minf = a/(a+b)
    
    a    = fun1(v,  -43,    0.128,  -18) 
    b    = fun2(v,  -20,    4,       -5)
    hinf = a/(a+b)
    tauh = 1.0/(a+b)
}

INCLUDE "aux_fun.inc"
