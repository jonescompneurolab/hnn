#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
export TRAVIS_TESTING=1

source "$DIR/../installer/docker/hnn_envs"

echo "Testing GUI on WSL..."
cd $DIR/../
export DISPLAY=:0
python3 hnn.py

echo "Building HNN in WSL..."
make clean
make -j2

echo "Running Python tests in WSL..."
py.test tests/

echo "Testing MPI in WSL..."
mpiexec -np 2 nrniv -mpi -python run.py