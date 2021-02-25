COMMENT
  ipulse3.mod
  Generates a train of current pulses of variable amplitude
  User specifies dur (pulse duration), per (period, i.e. interval 
  between pulse onsets), and num (number of pulses).
  Ensures that period is longer than pulse duration.
  2/6/2002 NTC
  Modif AD, 11-2006 -> variable amplitudes stored in a vector;
      added DC current
ENDCOMMENT

DEFINE MAXPULSES 1000		: maximum number of pulses

NEURON {
	POINT_PROCESS Ipulse3
	RANGE del, dur, per, num, amp, dc, i, pcount
	ELECTRODE_CURRENT i
}

UNITS {
	(nA) = (nanoamp)
}

PARAMETER {
	del (ms)
	dur (ms) <0, 1e9>	: duration of ON phase
	per (ms) <0, 1e9>	: period of stimuls, i.e. interval between pulse onsets
	num			: how many to deliver
	dc (nA)			: DC current
}

ASSIGNED {
	amp[MAXPULSES]		: vector for amplitudes
	ival (nA)
	i (nA)
	on
	tally			: how many more to deliver
	pcount			: pulse counter
}

INITIAL {
	pcount = 0
	if (dur >= per) {
		per = dur + 1 (ms)
		printf("per must be longer than dur\n")
UNITSOFF
		printf("per has been increased to %g ms\n", per)
UNITSON
	}
	i = 0
	ival = dc
	tally = num
	if (tally > 0) {
		net_send(del, 1)
		on = 0
		tally = tally - 1
	}
}

BREAKPOINT {
	i = ival
}

NET_RECEIVE (w) {
	: ignore any but self-events with flag == 1
	if (flag == 1) {
		if (on == 0) {
			: turn it on
			ival = amp[pcount]+dc
			pcount = pcount + 1
			on = 1
			: prepare to turn it off
			net_send(dur, 1)
		} else {
			: turn it off
			ival = dc
			on = 0
			if (tally > 0) {
				: prepare to turn it on again
				net_send(per - dur, 1)
				tally = tally - 1
			}
		}
	}
}
