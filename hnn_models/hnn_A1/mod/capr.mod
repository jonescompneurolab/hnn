: $Id: capr.mod,v 1.2 2010/12/13 21:31:31 samn Exp $ 
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



TITLE rcadecay

INDEPENDENT {t FROM 0 TO 1 WITH 10 (ms)}

NEURON {
	SUFFIX capr
	USEION ca READ ica WRITE cai
	RANGE  phi, beta
}

UNITS {

	(molar) = (1/liter)
	(mM)	= (millimolar)
	(um)	= (micron)
	(mA)	= (milliamp)
}

PARAMETER {

	phi             = 0.13e3 (milli-cm2/liter-milliamp-ms)
	beta            = 0.075 (/ms)
}
ASSIGNED {

  ica (milliamp/cm2)
}

STATE {	cai (milli/liter) }

INITIAL {
 
  cai= - phi * ica/ beta
  :cai = 0.2
}

BREAKPOINT {

  if       ( cai < 0 )      { cai = 0 
  } else                    { SOLVE state METHOD cnexp }

}

UNITSOFF

DERIVATIVE state { cai' = - phi * ica - beta * cai  }

UNITSON
