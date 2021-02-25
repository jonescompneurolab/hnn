: $Id: ntleak.mod,v 1.3 1998/08/14 19:47:45 billl Exp $
TITLE passive membrane channel

UNITS {
	(mV) = (millivolt)
	(mA) = (milliamp)
}

INDEPENDENT { v FROM -100 TO 50 WITH 50	(mV) }

NEURON {
	SUFFIX Pass
	NONSPECIFIC_CURRENT i
	RANGE g, erev
}

PARAMETER {
	g = .0005	(mho/cm2)
	erev = -82	(mV)
}

ASSIGNED { i	(mA/cm2)}

BREAKPOINT {
	i = g*(v - erev)
}