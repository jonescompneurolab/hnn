#!/bin/bash

return=0

VERBOSE=
[[ $1 ]] && VERBOSE=1

check_python_version () {
  # this works with system installed python 2.7 and Anaconda versions
  # mileage may vary with enthought or other distros

  PYTHON_VERSION=$1
  VERSION_STRING=
  if [ -n "$PYTHON_VERSION" ]; then  
    VERSION_STRING=$(echo "${PYTHON_VERSION}" | cut -d ' ' -f 2)
    SPLITVER=( ${VERSION_STRING//./ } )
    if [[ "${SPLITVER[0]}" -ge "3" ]] && [[ "${SPLITVER[1]}" -ge "5" ]]; then
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

echo -n "Checking if XQuartz is installed..."
XQUARTZ_VERSION=$(mdls -name kMDItemVersion /Applications/Utilities/XQuartz.app)
if [[ "$?" -eq "0" ]]; then
  echo "ok"
  echo "Xquartz version $(echo ${XQUARTZ_VERSION}|cut -d ' ' -f 3) is already installed"
  echo "You can skip the XQuartz installation step"
  echo
else
  echo "failed"
  return=2
fi

echo -n "Checking for existing python..."
PYTHON_VERSION=
FOUND=
for PYTHON in python python3; do
  which $PYTHON > /dev/null 2>&1
  if [[ "$?" -eq "0" ]]; then
    PYTHON_VERSION=$($PYTHON -V 2>&1)
    check_python_version "${PYTHON_VERSION}"
    if [[ "$?" -eq "0" ]]; then
      echo "warning"
      echo "Existing version ${PYTHON_VERSION} ($(which $PYTHON) is compatible with HNN."
      echo
      return=1
      FOUND=1
      break
    else
      FOUND=
      return=2
    fi
  fi
done

if [[ -z "$FOUND" ]]; then
  if [[ -z "$PYTHON_VERSION" ]]; then
    echo "failed"
    return=2
  else
    echo "You should install miniconda, and make sure that HNN is not trying to use the old python or any of its modules"
    echo
    return=2
  fi
fi


# Check for environment variables

echo -n "Checking PATH environment variable..."
which nrniv > /dev/null 2>&1
if [[ "$?" -eq "0" ]]; then
  echo "warning"
  echo "nrniv found in path ($(which nrniv))"
  echo "Make sure it is from the NEURON version used to compile HNN"
  return=1
  echo
elif [[ "PATH" =~ "NEURON" ]] || [[ "$PATH" =~ "NRN" ]]; then
  echo -e "\nNEURON found in path, but nrniv cannot be found. Does this need to be cleaned up?"
  echo "PATH=$PATH"
  echo
  return=2
else
  echo "ok"
fi

echo -n "Checking PYTHONPATH environment variable..."
if [ -n "$PYTHONPATH" ]; then
  if [[ "$PYTHONPATH" =~ "NEURON" ]] || [[ "$PYTHONPATH" =~ "NRN" ]]; then
    echo "warning"
    echo "NEURON libraries found in PYTHONPATH variable."
    echo "Make sure they match the version used to compile HNN"
    echo "PYTHONPATH=$PYTHONPATH"
    echo
    return=1
  else
    echo "ok"
  fi
else
  echo "ok"
fi

echo -n "Checking PYTHONHOME environment variable..."
if [ -n "$PYTHONHOME" ]; then
  echo -e "\nPYTHONHOME is set make sure that this is the correct environment to run HNN"
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

echo -n "Checking NRN_PYLIB environment variable..."
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
  echo "Optional: use this directory instead of step \"Clone and compile HNN source code\""
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