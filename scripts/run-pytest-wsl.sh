#!/bin/bash
set -e

export PATH="$PATH:$HOME/.local/bin"
export OMPI_MCA_btl_vader_single_copy_mechanism=none
export DISPLAY=:0

echo "Running Python tests on WSL..."
py.test --cov=. hnn/tests/