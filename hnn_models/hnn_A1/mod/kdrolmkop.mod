: $Id: kdrolmkop.mod,v 1.1 2009/11/05 15:10:43 samn Exp $ 
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
	SUFFIX KdrOlmKop
	USEION k WRITE ik
}
	
UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(mS) = (millisiemens)
}

PARAMETER {
    gkdr =   23 (mS/cm2)
    ek   = -100 (mV)
}
    
ASSIGNED {
    v       (mV)
    ik      (mA/cm2)
	ninf    (1)
	taon    (ms)
}

STATE { n }

INITIAL { 
    rates(v)
    n  = ninf
}

BREAKPOINT {

	SOLVE states METHOD cnexp
	
	ik = (1e-3) * gkdr * n^4 * (v-ek)
}


DERIVATIVE states { 

    rates(v)
    n' = (ninf-n)/taon
}

PROCEDURE rates(v(mV)) { LOCAL an, bn

    an = fun3(v,   25,  -0.018,  -25)
    bn = fun3(v,   35,   0.0036,  12)
    
    ninf = an/(an+bn)
    taon = 1./(an+bn)
}

INCLUDE "aux_fun.inc"
