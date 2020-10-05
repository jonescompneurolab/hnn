#!/bin/bash
set -e

echo "Installing Microsoft MPI"
powershell -command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/microsoft/Microsoft-MPI/releases/download/v10.1.1/msmpisetup.exe', 'msmpisetup.exe')" && \
    ./msmpisetup.exe -unattend && \
    rm -f msmpisetup.exe

echo "Running HNN Windows install script..."
powershell.exe -ExecutionPolicy Bypass -File ./installer/windows/hnn-windows.ps1

source "$HOME/Miniconda3/etc/profile.d/conda.sh"
