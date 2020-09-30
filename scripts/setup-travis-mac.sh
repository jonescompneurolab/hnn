#!/bin/bash
set -e

export TRAVIS_TESTING=1

source scripts/utils.sh

URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
FILENAME="$HOME/miniconda.sh"
start_download "$FILENAME" "$URL"

echo "Installing miniconda..."
chmod +x "$HOME/miniconda.sh"
"$HOME/miniconda.sh" -b -p "${HOME}/miniconda"
export PATH=${HOME}/miniconda/bin:$PATH

# create conda environment
conda create -n hnn --yes python=${PYTHON_VERSION} pip openmpi scipy numpy matplotlib pyqtgraph pyopengl psutil
source activate hnn && echo "activated conda HNN environment"
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/miniconda/envs/hnn/lib

# conda is faster to install nlopt
conda install -y -n hnn -c conda-forge nlopt

pip install NEURON flake8 pytest pytest-cov coverage coveralls mne

echo "Install finished"
