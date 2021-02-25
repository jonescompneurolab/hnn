TITLE passive membrane channel (equivalent to NEURON 'pas' mechanism)

UNITS {
	(mV) = (millivolt)
	(mA) = (milliamp)
	(S) = (siemens)
}

NEURON {
	SUFFIX ppasi
	NONSPECIFIC_CURRENT i
	RANGE g, e
}

PARAMETER {
	g = .001	(S/cm2)	<0,1e9>
	e = -70	(mV)
}

ASSIGNED {v (mV)  i (mA/cm2)}

BREAKPOINT {
	i = g*(v - e)
}
