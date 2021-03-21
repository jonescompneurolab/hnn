#!/bin/bash

return=0

VERBOSE=
[[ $1 ]] && VERBOSE=1

PYTHON_REQ_MAJ=3
PYTHON_REQ_MAJ=6

check_python_version () {
  # this works with system installed python 2.7 and Anaconda versions
  # mileage may vary with enthought or other distros

  PYTHON_VERSION=$1
  VERSION_STRING=
  if [ -n "$PYTHON_VERSION" ]; then  
    VERSION_STRING=$(echo "${PYTHON_VERSION}" | cut -d ' ' -f 2)
    SPLITVER=( ${VERSION_STRING//./ } )
    if [[ "${SPLITVER[0]}" -ge "3" ]] && [[ "${SPLITVER[1]}" -ge "6" ]]; then
      return 0
    else
      return 2
    fi
  else
    return 2
  fi
}

echo "Performing pre-install checks for HNN"
echo "--------------------------------------"

echo -n "Checking for existing python..."
PYTHON_VERSION=
FOUND=
for PYTHON in python python3; do
  which $PYTHON > /dev/null 2>&1
  if [[ "$?" -eq "0" ]]; then
    PYTHON_VERSION=$($PYTHON -V 2>&1)
    check_python_version "${PYTHON_VERSION}"
    if [[ "$?" -eq "0" ]]; then
      echo "ok"
      echo "Existing version ${PYTHON_VERSION} ($(which $PYTHON)) is compatible with HNN."
      echo "You can skip the miniconda install if you know what you are doing."
      echo
      FOUND=1
      break
    else
      FOUND=
      return=2
    fi
  fi
done

if [[ -z "$FOUND" ]]; then
  echo "failed"
  return=2
  if [[ -n "$PYTHON_VERSION" ]]; then
    echo "Existing version ${PYTHON_VERSION} ($(which $PYTHON)) is not compatible with HNN."
    echo "HNN requires at least Python ${PYTHON_REQ_MAJ}.${PYTHON_REQ_MIN}"
    echo
  else
    echo "ok"
    echo "No python version found. Make sure you install miniconda"
    echo
  fi
fi


# Check for environment variables

echo -n "Checking for existing NEURON installation..."
which nrniv > /dev/null 2>&1
if [[ "$?" -eq "0" ]]; then
  echo "ok"
  echo "nrniv found in path ($(which nrniv))"
  echo "Make sure it is from the NEURON version used to compile HNN"
  echo "You can skip the NEURON install step if you know what you are doing."
  echo
elif [[ "PATH" =~ "NEURON" ]] || [[ "$PATH" =~ "NRN" ]]; then
  echo -e "\nNEURON found in path, but nrniv cannot be found. Does this need to be cleaned up?"
  echo "PATH=$PATH"
  echo
  return=2
else
  echo "ok"
fi

echo -n "Checking PYTHONPATH environment variable is not set..."
if [ -n "$PYTHONPATH" ]; then
  if [[ "$PYTHONPATH" =~ "NEURON" ]] || [[ "$PYTHONPATH" =~ "NRN" ]]; then
    echo "warning"
    echo "NEURON libraries found in PYTHONPATH variable. This was used before "
    echo "the 'pip install' method."
    echo "PYTHONPATH=$PYTHONPATH"
    echo
    return=1
  else
    echo "ok"
  fi
else
  echo "ok"
fi

echo -n "Checking PYTHONHOME environment variable is not set..."
if [ -n "$PYTHONHOME" ]; then
  echo "warning"
  echo -e "\nPYTHONHOME is set. This is not the recommended way to set the python environment."
  echo "Make sure that this is the correct environment to run HNN."
  echo "PYTHONHOME=$PYTHONHOME"
  return=1
  if [[ -n "$PYTHON_VERSION" ]]; then
    echo "Python version: $(PYTHON)"
  else
    echo "Couldn't find a working python environment either"
    return=2
  fi
  echo
else
  echo "ok"
fi

echo -n "Checking NRN_PYLIB environment variable is not set..."
if [ -n "$NRN_PYLIB" ]; then
  echo -e "\nNRN_PYLIB is set. This is most likely not wanted and can prevent HNN from"
  echo "running if this file is missing or belongs to the wrong NEURON version."
  echo "NRN_PYLIB=$NRN_PYLIB"
  echo
  return=1
else
  echo "ok"
fi

echo -n "Checking for existing hnn directory..."

CUR_DIR=$(pwd)
HNN_DIR=
if [[ -f ${CUR_DIR}/hnn.py ]]; then
  HNN_DIR=${CUR_DIR}
elif [[ -f $HOME/hnn/hnn.py ]]; then
  HNN_DIR=${CUR_DIR}
fi

if [[ -n "$HNN_DIR" ]]; then
  echo "found"
  echo "Existing HNN source code directory found at $HNN_DIR"
  echo "Optional: use this directory instead of step \"Download HNN source code\""
  echo
else
  echo "ok"
fi

echo "--------------------------------------"
echo "Done with pre-install checks"
echo
if [[ "$return" -eq "0" ]]; then
  echo "SUCCESS: pre-install checks were successful!"
elif [[ "$return" -eq "1" ]]; then
  echo "WARNING: there were one or more checks that might be a problem"
else
  echo "FAILED: there were one or more failed checks"
fi

echo
exit $return