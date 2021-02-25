: $Id: nafpyrkop.mod,v 1.1 2009/11/05 15:09:03 samn Exp $ 
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
	SUFFIX NafPyrKop
	USEION na WRITE ina
	RANGE  bk, gmax, taom, taoh, taoi, minf, hinf, iinf
}
	
UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(mS) = (millisiemens)
}

PARAMETER {
    gmax = 32.0 (mS/cm2)
    ena  = 55.0 (mV)
    bk   =  0.0  (1)
}
    
ASSIGNED {
    v       (mV)
    ina     (mA/cm2)
    minf    (1)
    hinf    (1)
    iinf    (1)
    taom    (ms)
    taoh    (ms)
    taoi    (ms)
}

STATE { m h ii }

INITIAL {
    rates(v)
    m    = minf
    h    = hinf
    ii   = iinf
}

BREAKPOINT {

	SOLVE states METHOD cnexp
	
	ina = (1e-3) * gmax * m^3 * h * ii * (v-ena)
}

DERIVATIVE states { 
    rates(v)
    m'  = (minf-m)/taom
    h'  = (hinf-h)/taoh
    ii' = (iinf-ii)/taoi
}

PROCEDURE rates(v(mV)) { LOCAL am, bm, ah, bh, ai, bi
    
    am   = fun3(v,  -30.0, -0.4,   -7.2)
    bm   = fun3(v,  -30.0,  0.124,  7.2)
    minf = am/(am+bm)
    taom = max( 0.02, 0.5(/ms)/(am+bm) )*1.0(ms)
 
    ah   = fun3(v,  -45.0,   -0.03, -1.5)
    bh   = fun3(v,  -45.0,    0.01,  1.5)
    taoh = max( 0.5, 0.5(/ms)/(ah+bh) )*1.0(ms)        
    hinf = fun2(v, -50.0, 1.0, 4.0)*1.0(ms)
    
    ai   = exp(0.45(/mV)*(v+66.0))
    bi   = exp(0.09(/mV)*(v+66.0))
    taoi = max( 10.0, 3000.0*bi/(1.0+ai) )*1.0(ms)
    iinf = (1.0+bk*exp((v+60.0)/2.0(mV))) / (1.0+exp((v+60.0)/2.0(mV)))
}

INCLUDE "aux_fun.inc"
