#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# we use start_download from utils.sh
source "$DIR/utils.sh"

URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
FILENAME="$HOME/miniconda.sh"
start_download "$FILENAME" "$URL"

echo "Installing miniconda..."
bash "$HOME/miniconda.sh" -b -p "${HOME}/Miniconda3"
source "$HOME/Miniconda3/etc/profile.d/conda.sh"

# create conda environment
conda env create -f environment.yml
conda install -y -n hnn openmpi mpi4py
# conda is faster to install nlopt
conda install -y -n hnn -c conda-forge nlopt