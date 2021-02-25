: $Id: nafolmkop.mod,v 1.1 2009/11/05 15:09:22 samn Exp $ 
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
	SUFFIX NafOlmKop
	USEION na WRITE ina
}
	
UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(mS) = (millisiemens)
}

PARAMETER {
    gna  = 30 (mS/cm2)
    ena  = 90 (mV)
}
    
ASSIGNED {
    v       (mV)
    ina     (mA/cm2)
    minf    (1)
    hinf    (1)
    taom    (ms)
    taoh    (ms)
}

STATE { m h }

INITIAL {
    rates(v)
    m    = minf
    h    = hinf
}

BREAKPOINT {

	SOLVE states METHOD cnexp
	
	ina = (1e-3) * gna * m^3 * h * (v-ena)
}

DERIVATIVE states { 
    rates(v)
    m' = (minf-m)/taom
    h' = (hinf-h)/taoh
}

PROCEDURE rates(v(mV)) { LOCAL am, bm, ah, bh
    
    am   = fun3(v,  -38, -0.1,    -10)
    bm   = fun1(v,  -65,  4,      -18)
    minf = am/(am+bm)
    taom = 1./(am+bm)
 
    ah   = fun1(v,  -63,    0.07,  -20)
    bh   = fun2(v,  -33,    1,     -10)
    hinf = ah/(ah+bh)
    taoh = 1./(ah+bh)
}

INCLUDE "aux_fun.inc"
