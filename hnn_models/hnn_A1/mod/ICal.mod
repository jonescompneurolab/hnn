TITLE high-threshold calcium (L-) current from hippocampal pyramidal cells

COMMENT Equations from
   McCormick DA, Huguenard JR (1992) A model of the electrophysiological
   properties of thalamocortical relay neurons. J Neurophys 68(4):
   1384-1400.
	See also
   Kay AR, Wong RK (1987) Calcium current activation kinetics in isolated    
   pyramidal neurones of the Ca1 region of the mature guinea-pig 
   hippocampus. J Physiol 392: 603-616.

>< Temperature adjusts time constants measured at 23.5 degC.
>< Written by Arthur Houweling for MyFirstNEURON.
ENDCOMMENT

NEURON {
	SUFFIX iL
	USEION ca READ cai,cao WRITE ica
        RANGE pca, minf, mtau, ica
}

UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(mM) = (milli/liter)
}

PARAMETER {
	v		(mV)
	celsius		(degC)
	cai		(mM)
	cao		(mM)
	pca= 2.76e-4	(cm/s)		
}

STATE { m }

ASSIGNED {
	ica	(mA/cm2)
	mtau	(ms)
	minf 
	tadj
}

BREAKPOINT { 
	SOLVE states METHOD cnexp
	ica= pca* m^2* nrn_ghk( v, cai, cao, 2)
}

DERIVATIVE states {
       rates()

       m'= (minf- m)/ mtau 
}
  
INITIAL {
	tadj= 3^ ((celsius- 23.5)/ 10)
	rates()
	m= minf
} 

PROCEDURE rates() { LOCAL a,b UNITSOFF
	a= 1.6/ (1+ exp(-0.072* (v- 5)))
	b= 0.02* vtrap(-(v- 1.31), 5.36)

	mtau= 1/ (a+ b)/ tadj
	minf= 1/ (1+ exp((v+ 10)/ -10))
}

FUNCTION vtrap( x, c) { 
	:check for zero in denominator of rate equations
        if (fabs(x/ c)< 1e-6) { vtrap= c+ x/ 2 }
        else { vtrap=  x/ (1- exp(-x/ c)) }
}
