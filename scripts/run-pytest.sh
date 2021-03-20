#!/bin/bash
set -e

if [[ "${WSL_INSTALL}" -eq 1 ]]; then
    export PATH="$PATH:$HOME/.local/bin"
    # unable to get vcxsrv to work (DLL loading problems)
    unset DISPLAY
fi

# first check code style with flake8
echo "Checking code style compliance with flake8..."
flake8 --count --exclude  __init__.py,qt_evoked.py
echo "Running unit tests with pytest..."
py.test --cov=. hnn/tests/
