#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
export TRAVIS_TESTING=1
export PATH="$PATH:$HOME/.local/bin"
export OMPI_MCA_btl_vader_single_copy_mechanism=none

echo "Testing GUI on WSL..."
cd $DIR/../

export DISPLAY=:0
python3 hnn.py

echo "Testing MPI in WSL..."
mpiexec -np 2 nrniv -mpi -python run.py