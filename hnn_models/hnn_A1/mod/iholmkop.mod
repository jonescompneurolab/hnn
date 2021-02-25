: $Id: iholmkop.mod,v 1.1 2009/11/05 15:11:54 samn Exp $ 
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
	SUFFIX IhOlmKop
    NONSPECIFIC_CURRENT i
    RANGE gmax
}
	
UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(mS) = (millisiemens)
}

PARAMETER {
    gmax =  12    (mS/cm2)
    eh   = -32.9  (mV)
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

FUNCTION qinf(v(mV))     { qinf = fun2(v, -84, 1, 10.2)*1(ms) }
FUNCTION qtau(v(mV))(ms) { qtau = 1(ms)/(exp((-14.59(mV)-0.086*v)/1(mV)) + exp((-1.87(mV)+0.0701*v)/1(mV))) }

INCLUDE "aux_fun.inc"
