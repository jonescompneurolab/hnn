#!/bin/bash
set -e

if [[ "${WSL_INSTALL}" -eq 1 ]]; then
    export PATH="$PATH:$HOME/.local/bin"
fi

# first check code style with flake8 (ignored currently)
echo "Checking code style compliance with flake8..."
flake8 --exit-zero --quiet --count \
    --exclude visdipole.py,visrast.py,visvolt.py,visspec.py,vispsd.py,spikefn.py,specfn.py,DataViewGUI.py \
    hnn

echo "Running unit tests with pytest..."
py.test --cov=. hnn/tests/
