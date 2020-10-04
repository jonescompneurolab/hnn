#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
export PATH="$PATH:$HOME/.local/bin"
export OMPI_MCA_btl_vader_single_copy_mechanism=none

echo "Testing GUI on WSL..."
cd $DIR/../

export DISPLAY=:0

echo "Running Python tests on WSL..."
py.test --cov=. hnn/tests/