: $Id: kl.mod,v 1.3 2004/06/07 21:15:08 billl Exp $
COMMENT
-----------------------------------------------------------------------------

  Leak potassium current -- converted to a SUFFIX from kleak.mod

  This mechanism was written to be used as a potassium channel that is
  open or closed by neuromodulators.  

  A. Destexhe , The Salk Institute, Feb 1994.

-----------------------------------------------------------------------------
ENDCOMMENT

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX kl
        USEION k READ ek WRITE ik VALENCE 1
	RANGE gmax, i
        GLOBAL erev
}

UNITS {
	(nA) = (nanoamp)
	(mV) = (millivolt)
	(umho) = (micromho)
}

PARAMETER {
  ek  (mV)
  gmax	= 4e-4	(S/cm2)		: maximum conductance
  erev	= -100	(mV)		: reversal potential (potassium)
}

ASSIGNED {
	v		(mV)		: postsynaptic voltage
	i 		(mA/cm^2)
	ik 		(mA/cm^2)
}

INITIAL {
}

BREAKPOINT {
	i = gmax * (v - erev)
        ik=i
}
