NEURON { SUFFIX kdr2orig }
  
NEURON { USEION k WRITE ik }         

ASSIGNED { ik }

PARAMETER {
	erev 		= -95        (mV)
	gmax 		= 0.005     (umho)

        vrest           = 0.0
	mvalence 	= 2.8
	mgamma 		= 0.5			: 0.7
	mbaserate 	= .13 
	mvhalf 		=  -18
	mbasetau 	= 0.3
	mtemp 		=  36
	mq10		=  3.0
	mexp 		= 3

	hvalence 	= -6
	hgamma		=  0.3
	hbaserate 	=  0.095
	hvhalf 		=  -39
	hbasetau 	=  0.25
	htemp 		=  36
	hq10        =  3.
	hexp 		=  0




	celsius			     (degC)
	dt 				     (ms)
	v 			         (mV)

	vmax 		= 100     (mV)
	vmin 		= -100   (mV)

} : end PARAMETER

INCLUDE "bg_cvode.inc"

PROCEDURE iassign () { i = g*(v-erev) ik=i }
:** kmbg 






