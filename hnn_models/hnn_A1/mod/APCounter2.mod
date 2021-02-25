COMMENT
Hines' counter for action potentials
after a run, n indicates the number of action potentials that crossed
some threshold value (thresh)
AD: store the action potential times in vector "times"; 
calculate ISI and instantaneous rate
ENDCOMMENT

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

DEFINE MAXAP 20000

NEURON {
	POINT_PROCESS APCounter2
	RANGE n, thresh, times, isi, rate
}

UNITS {
	(mV) = (millivolt)
}

PARAMETER {
	n
	thresh = 0 (mV)
}

ASSIGNED {
	firing
	times[MAXAP]	(ms)
	isi		(ms)
	rate		(1/s)
}

INITIAL {
	n = 0
	firing = 0
	isi = 0
	rate = 0
	check()
}

BREAKPOINT {
	SOLVE check
}

PROCEDURE check() {
	if (v >= thresh && !firing) {
		firing = 1
		times[n] = t
		n = n + 1
		if(n>1) {
			isi = t-times[n-2]
			rate = 1000/isi
		}
	}
	if (firing && v < thresh) {
		firing = 0
	}
}
