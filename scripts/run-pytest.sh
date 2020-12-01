#!/bin/bash
set -e

if [[ "${WSL_INSTALL}" -eq 1 ]]; then
    export PATH="$PATH:$HOME/.local/bin"
    # unable to get vcxsrv to work (DLL loading problems)
    unset DISPLAY
fi

# first check code style with flake8 (ignored currently)
echo "Checking code style compliance with flake8..."
flake8 --quiet --count \
    --exclude hnn_qt5.py,qt_evoked.py,run.py,paramrw.py,visdipole.py,visrast.py,visvolt.py,visspec.py,vispsd.py,DataViewGUI.py \
    hnn

echo "Running unit tests with pytest..."
py.test --cov=. hnn/tests/
