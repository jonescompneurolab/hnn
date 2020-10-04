#!/bin/bash
set -e

echo "Installing Microsoft MPI"
powershell -command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/microsoft/Microsoft-MPI/releases/download/v10.1.1/msmpisetup.exe', 'msmpisetup.exe')" && \
    ./msmpisetup.exe -unattend && \
    rm -f msmpisetup.exe

echo "Running HNN Windows install script..."
powershell.exe -ExecutionPolicy Bypass -File ./installer/windows/hnn-windows.ps1

source "$HOME/Miniconda3/etc/profile.d/conda.sh"
conda activate hnn

# # add miniconda python to the path
# export PATH=$PATH:$HOME/Miniconda3/Scripts
# export PATH=$HOME/Miniconda3/envs/hnn/:$PATH
# export PATH=$HOME/Miniconda3/envs/hnn/Scripts:$PATH
# export PATH=$HOME/Miniconda3/envs/hnn/Library/bin:$PATH

# set other variables for neuron and HNN
export PATH=$PATH:/c/nrn/bin
export NEURONHOME=/c/nrn
