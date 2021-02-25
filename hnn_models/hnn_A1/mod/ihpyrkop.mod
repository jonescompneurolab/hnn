: $Id: ihpyrkop.mod,v 1.1 2009/11/05 15:11:39 samn Exp $ 
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
	SUFFIX IhPyrKop
    NONSPECIFIC_CURRENT i
	RANGE v50, gmax
}
	
UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(mS) = (millisiemens)
}

PARAMETER {
    gmax =   0.0  (mS/cm2)
    eh   = -30.0  (mV)
    v50  =   0.0 (mV)
}
    
ASSIGNED { 

    v (mV)
    i (mA/cm2)
}

STATE { q }

INITIAL { q  = qinf(v) }

BREAKPOINT {

	SOLVE states METHOD cnexp
	
    i = (1e-3) * gmax * q * (v-eh)
}

DERIVATIVE states { q' = (qinf(v)-q)/qtau(v) }

FUNCTION qinf(v(mV))     { qinf = fun2(v, v50, 1.0, 10.5)*1.0(ms) }
FUNCTION qtau(v(mV))(ms) { qtau = 1.0(ms)/(exp((-14.59(mV)-0.086*v)/1.0(mV)) + exp((-1.87(mV)+0.0701*v)/1.0(mV))) }

:HCN1
:FUNCTION qinf(v(mV))     { qinf = fun2(v, v50, 1, 1.0/0.151)*1(ms) }
:FUNCTION qtau(v(mV))(ms) { qtau = exp(0.033(/mV)*(v+75))/(0.011*(1+exp(0.083(/mV)*(v+75))))*1(ms)}

INCLUDE "aux_fun.inc"
