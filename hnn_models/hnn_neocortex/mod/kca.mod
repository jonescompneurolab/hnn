COMMENT
    26 Ago 2002 Modification of original channel to allow variable time step
            and to correct an initialization error.

    Done by Michael Hines (michael.hines@yale.edu) and Ruggero Scorcioni (rscorcio@gmu.edu)
            at EU Advance Course in Computational Neuroscience. Obidos, Portugal

    kca.mod

    Calcium-dependent potassium channel
    Based on Pennefather (1990) -- sympathetic ganglion cells
            taken from Reuveni et al (1993) -- neocortical cells

    Author: Zach Mainen, Salk Institute, 1995, zach@salk.edu

ENDCOMMENT

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
    SUFFIX kca
    USEION k READ ek WRITE ik
    USEION ca READ cai
    RANGE n, gk, gbar
    RANGE ninf, ntau
    GLOBAL Ra, Rb, caix
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
    cai         (mM)
    caix = 1

    : max act rate
    Ra   = 0.01 (/ms)

    : max deact rate
    Rb   = 0.02 (/ms)

    dt          (ms)
    celsius     (degC)

    : original temp
    temp = 23   (degC)
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
    rates(cai)
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
    rates(cai)
    n' =  (ninf - n) / ntau
}

PROCEDURE rates(cai(mM)) {
    a = Ra * cai^caix
    b = Rb

    tadj = q10^((celsius - temp - tshift) / 10)

    ntau = 1 / tadj / (a + b)
    ninf = a / (a + b)

    : tinc = -dt * tadj
    : nexp = 1 - exp(tinc/ntau)
}
