COMMENT
    26 Ago 2002 Modification of original channel to allow variable time step
            and to correct an initialization error.

    Done by Michael Hines (michael.hines@yale.edu) and Ruggero Scorcioni (rscorcio@gmu.edu)
            at EU Advance Course in Computational Neuroscience. Obidos, Portugal

    km.mod

    Potassium channel, Hodgkin-Huxley style kinetics
    Based on I-M (muscarinic K channel)
    Slow, noninactivating

    Original Author: Zach Mainen, Salk Institute, 1995, zach@salk.edu
ENDCOMMENT

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
    SUFFIX km
    USEION k READ ek WRITE ik
    RANGE n, gk, gbar
    RANGE ninf, ntau
    GLOBAL Ra, Rb
    GLOBAL q10, temp, tadj, vmin, vmax, tshift
}

UNITS {
    (mA) = (milliamp)
    (mV) = (millivolt)
    (pS) = (picosiemens)
    (um) = (micron)
}

PARAMETER {
    : 0.03 mho/cm2
    gbar = 10   (pS/um2)
    v           (mV)

    : v 1/2 for inf
    tha = -30   (mV)

    : inf slope
    qa = 9      (mV)

    : max act rate  (slow)
    Ra = 0.001  (/ms)

    : max deact rate  (slow)
    Rb = 0.001  (/ms)

    dt          (ms)
    celsius     (degC)

    : original temp
    temp = 23   (degC)

    : temp sensitivity
    q10  = 2.3

    tshift = 30.7

    vmin = -120 (mV)
    vmax = 100  (mV)
}


ASSIGNED {
    a       (/ms)
    b       (/ms)
    ik      (mA/cm2)
    gk      (pS/um2)
    ek      (mV)
    ninf
    ntau    (ms)
    tadj
}


STATE {
    n
}

INITIAL {
    trates(v)
    n = ninf
}

BREAKPOINT {
    SOLVE states METHOD cnexp
    gk = tadj * gbar * n
    ik = (1e-4) * gk * (v - ek)
}

LOCAL nexp

: Computes state variable n at the current v and dt.
DERIVATIVE states {
    trates(v)
    n' = (ninf - n) / ntau
}

: Computes rate and other constants at current v.
: Call once from HOC to initialize inf at resting v.
PROCEDURE trates(v) {
    TABLE ninf, ntau
    DEPEND  celsius, temp, Ra, Rb, tha, qa

    FROM vmin TO vmax WITH 199

    : not consistently executed from here if usetable_hh == 1
    rates(v)
    : tinc = -dt * tadj
    : nexp = 1 - exp(tinc/ntau)
}

: Computes rate and other constants at current v.
: Call once from HOC to initialize inf at resting v.
PROCEDURE rates(v) {
    a = Ra * (v - tha) / (1 - exp(-(v - tha) / qa))
    b = -Rb * (v - tha) / (1 - exp((v - tha) / qa))

    tadj = q10^((celsius - temp - tshift) / 10)
    ntau = 1/tadj/(a+b)
    ninf = a/(a+b)
}
