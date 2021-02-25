: $Id: wrap.mod,v 1.1 2010/12/21 19:56:41 samn Exp $ 

NEURON {
THREADSAFE
 SUFFIX wrap
 GLOBAL INSTALLED
 GLOBAL verbose
}

PARAMETER {
  INSTALLED=0
  verbose=0
}

VERBATIM

#include <math.h>
#include <stdlib.h>

double* Wrap(double* x,int n,int flen){
  double* y = (double*) calloc(n,sizeof(double));
  int i,j=0;
  for(i=flen/2+1;i<flen;i++)    y[j++]=x[i];
  j=n-flen/2-1;
  for(i=0;i<=flen/2;i++)   y[j++]=x[i];
  return y;
}

void WrapAround(void* vv) {
  double* x,*y;
  int vsz,fsz,i;
  vsz = vector_instance_px(vv,&x);
  fsz = (int) *getarg(1);
  if(fsz > vsz) {
    printf("WrapAround ERRA: invalid filter len %d > vector len %d!\n",fsz,vsz);
    return;
  }
  y = Wrap(x,vsz,fsz);
  for(i=0;i<vsz;i++) x[i]=y[i];
  free(y);
}

ENDVERBATIM

PROCEDURE install () {
  if (INSTALLED==1) {
    printf("already installed wrap.mod")
  } else {
    INSTALLED=1
    VERBATIM
    install_vector_method("WrapAround",WrapAround);
    ENDVERBATIM
  }
}
