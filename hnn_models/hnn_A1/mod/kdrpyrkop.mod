: $Id: kdrpyrkop.mod,v 1.1 2009/11/05 15:10:24 samn Exp $ 
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
	SUFFIX KdrPyrKop
	USEION k WRITE ik
	RANGE gmax
}
	
UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(mS) = (millisiemens)
}

PARAMETER {
    gmax =  10.0 (mS/cm2)
    ek   = -90.0 (mV)
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
	
	ik = (1e-3) * gmax * n * (v-ek)
}


DERIVATIVE states { 

    rates(v)
    n' = (ninf-n)/taon
}

PROCEDURE rates(v(mV)) { LOCAL an, bn

    an = exp(-0.11(/mV)*(v-13.0))
    bn = exp(-0.08(/mV)*(v-13.0))
    
    ninf = 1.0/(1.0+an)
    taon = max(2.0,50.0*bn/(1.0+an))*1.0(ms)
}

INCLUDE "aux_fun.inc"
