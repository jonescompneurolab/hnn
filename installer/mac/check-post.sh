#!/bin/bash

return=0

VERBOSE=
[[ $1 ]] && VERBOSE=1

check_python_version () {
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


echo "Performing post-install checks for HNN"
echo "--------------------------------------"


echo -n "Checking for XQuartz..."
XQUARTZ_VERSION=$(mdls -name kMDItemVersion /Applications/Utilities/XQuartz.app)
if [[ "$?" -eq "0" ]]; then
  echo "ok"
else
  echo "failed"
fi

CUR_DIR=$(pwd)

echo -n "Checking if HNN is compiled..."
if [[ -f ${CUR_DIR}/hnn.py ]]; then
  if [[ -f "${CUR_DIR}/x86_64/hh2.mod" ]]; then
    echo "ok"
    if [[ "$VERBOSE" -eq "1" ]]; then
      echo "HNN source code compiled and ready to use at ${CUR_DIR}"
      echo
    fi
  else
    echo "failed"
    echo "Found a source code directory at ${CUR_DIR}, but it needs to be compiled (run make)."
    echo
    return=2
  fi
else
  if [[ -f "$HOME/hnn/x86_64/hh2.mod" ]]; then
    echo "warning"
    echo "Did you mean to run this from $HOME/hnn instead?"
    echo
    return=1
  else
    echo "failed"
    echo "Didn't find HNN source code in this directory"
    echo
    return=2
  fi
fi

echo -n "Checking for miniconda..."
MINICONDA_FOUND=
which conda > /dev/null 2>&1
if [[ "$?" -eq "0" ]]; then
  echo "ok"
  MINICONDA_FOUND=1
else
  echo "not found"
  return=1
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
      echo "ok"
      if [[ "$VERBOSE" -eq "1" ]]; then
        echo "Existing version ${PYTHON_VERSION} ($(which $PYTHON) is compatible with HNN."
        echo
      fi
      FOUND=1
      break
    else
      FOUND=
    fi
  fi
done

if [[ -z "$FOUND" ]]; then
  if [[ -z "$PYTHON_VERSION" ]]; then
    echo "Python not found"
    return=2
  else
    echo "${PYTHON_VERSION}"
    echo "${PYTHON_VERSION} not compatible with HNN"
    echo
    return=2
  fi
fi

# Check for environment variables

echo -n "Checking PATH environment variable for nrniv..."
NRN_FOUND=
which nrniv > /dev/null 2>&1
if [[ "$?" -eq "0" ]]; then
  echo "ok"
  if [[ "$VERBOSE" -eq "1" ]]; then
    echo "nvniv found at $(which nrniv)"
    echo "Make sure it is part of the NEURON version used to compile HNN"
    echo
  fi
  NRN_FOUND=1
elif [[ "PATH" =~ "NEURON" ]] || [[ "$PATH" =~ "NRN" ]]; then
  echo -e "\nNEURON found in path, but nrniv cannot be found. Does this need to be cleaned up?"
  echo "PATH=$PATH"
  echo
  return=2
else
  echo "failed"
  return=2
fi

echo -n "Checking PATH environment variable for mpiexec..."
MPI_FOUND=
which mpiexec > /dev/null 2>&1
if [[ "$?" -ne "0" ]]; then
  echo "failed"
  echo "mpiexec binary not found. Was this command run in the conda environment?"
  echo
  return=2
else
  echo "ok"
  MPI_FOUND=1
fi

# should be empty
echo -n "Checking PYTHONHOME environment variable is not set..."
if [ -n "$PYTHONHOME" ]; then
  echo -e "\nPYTHONHOME is set. This is not recommended."
  echo "Make sure that this is the correct environment to run HNN"
  echo "PYTHONHOME=$PYTHONHOME"
  echo
  return=1
else
  echo "ok"
fi

# should be empty
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

MPI_WORKS=
if [[ "$MPI_FOUND" -eq "1" ]]; then
  echo -n "Checking MPI functionality..."
  COMMAND="mpiexec -n 1 echo \"hello\" 2>&1"
  OUTPUT=$(mpiexec -n 1 echo "hello" 2>&1)
  if [[ "$?" -eq "0" ]] && [[ "$OUTPUT" =~ "hello" ]]; then
    echo "ok"
    MPI_WORKS=1
  else
    echo "failed"
    echo "the command that failed was:"
    echo "$COMMAND"
    echo $OUTPUT
    echo
    return=2
  fi
fi

# NEURON functionality checks from https://github.com/jonescompneurolab/hnn/issues/11
NRNIV_WORKS=
if [[ "$NRN_FOUND" -eq "1" ]]; then
  echo -n "Checking NEURON nrniv funtionality..."
  COMMAND="nrniv -nobanner -nopython -c '{print \"hello\" quit()}' 2>&1"
  OUTPUT=$(nrniv -nobanner -nopython -c '{print "hello" quit()}' 2>&1)
  if [[ "$?" -eq "0" ]]; then
    echo "ok"
    NRNIV_WORKS=1
  else
    echo "failed"
    echo "Could not run nrniv even without Python or MPI"
    echo "the command that failed was:"
    echo "$COMMAND"
    echo $OUTPUT
    echo
    return=2
  fi
else
  echo "Skipping NEURON funtionality tests."
fi

PREREQS_INSTALLED=1
for prereq in "pyqtgraph" "matplotlib" "scipy" "psutil" "numpy" "nlopt" "neuron"; do
  echo -n "Checking Python can import $prereq module..."
  $PYTHON -c "import $prereq" > /dev/null 2>&1
  if [[ "$?" -eq "0" ]]; then
    echo "ok"
  else
    echo "failed"
    $PYTHON -c "import $prereq"
    echo
    PREREQS_INSTALLED=0
    return=2
  fi
done

NRNIV_AND_PYTHON_WORKS=
if [[ "$NRN_FOUND" -eq "1" ]] && [[ "$NRNIV_WORKS" -eq "1" ]] && [[ "$PREREQS_INSTALLED" -eq "1" ]]; then
  echo -n "Checking NEURON nrniv funtionality with Python..."
  COMMAND="nrniv -nobanner -python -c 'from neuron import h; print(\"Hello\"); h.quit()' 2>&1"
  OUTPUT=$(nrniv -nobanner -python -c 'from neuron import h; print("Hello"); h.quit()' 2>&1)
  if [[ "$?" -eq "0" ]]; then
    echo "ok"
    NRNIV_AND_PYTHON_WORKS=1
  else
    echo "failed"
    echo "Could not run nrniv with Python"
    echo "the command that failed was:"
    echo "$COMMAND"
    echo $OUTPUT
    echo
    return=2
    fi
else
  echo "Skipping NEURON funtionality tests with Python."
fi

echo -n "Checking for setting LD_LIBRARY_PATH..."
source ${CONDA_PREFIX}/etc/conda/activate.d/env_vars.sh > /dev/null 2>&1
if [[ "$?" -eq "0" ]] && [[ -n "${LD_LIBRARY_PATH}" ]]; then
  echo "ok"
else
  echo "warning"
  echo "The LD_LIBRARY_PATH variable is not set correctly. Make sure you follow the installation"
  echo "instructions to add the correct lines to ${CONDA_PREFIX}/etc/conda/activate.d/env_vars.sh"
  return=1
fi


MPI_AND_NRNIV_WORKS=
if [[ "$NRN_FOUND" -eq "1" ]] && [[ "$NRNIV_WORKS" -eq "1" ]] && [[ "$MPI_WORKS" -eq "1" ]]; then
  echo -n "Checking NEURON nrniv funtionality with MPI..."
  mpiexec -n 2 nrniv -nobanner -nopython -mpi -c 'quit()' > /dev/null 2>&1
  if [[ "$?" -eq "0" ]]; then
    echo "ok"
    MPI_AND_NRNIV_WORKS=1
  else
    # try with LD_LIBRARY_PATH
    COMMAND="mpiexec -n 2 nrniv -nobanner -nopython -mpi -c 'quit()'"
    OUTPUT=$(export LD_LIBRARY_PATH=${CONDA_PREFIX}/lib; mpiexec -n 2 nrniv -nobanner -nopython -mpi -c 'quit()')
    if [[ "$?" -eq "0" ]]; then
      echo "warning"
      echo "The LD_LIBRARY_PATH variable is not set correctly. Make sure you follow the installation"
      echo "instructions to add the correct lines to ${CONDA_PREFIX}/etc/conda/activate.d/env_vars.sh"
      echo
      return=1
      MPI_AND_NRNIV_WORKS=1
    else
      echo "failed"
      echo "Could not run nrniv with MPI"
      echo "The command that failed was:"
      echo "$COMMAND"
      echo "Tried environment variable LD_LIBRARY_PATH=${CONDA_PREFIX}/lib"
      echo "Command output (on a single line):"
      echo $OUTPUT
      echo
      return=2
    fi
  fi
else
  echo "Skipping NEURON funtionality tests with MPI."
fi

NRNIV_AND_PYTHON_AND_MPI_WORKS=
if [[ "$NRN_FOUND" -eq "1" ]] && [[ "$NRNIV_WORKS" -eq "1" ]] &&
  [[ "$PREREQS_INSTALLED" -eq "1" ]] && [[ "$MPI_WORKS" -eq "1" ]] &&
  [[ "$MPI_AND_NRNIV_WORKS" -eq "1" ]]; then
 echo -n "Checking NEURON nrniv funtionality with Python and MPI..."
 COMMAND="mpiexec -n 2 nrniv -nobanner -mpi -python -c 'from neuron import h; pc = h.ParallelContext(); h.quit()'  2>&1"
 OUTPUT=$(mpiexec -n 2 nrniv -nobanner -mpi -python -c 'from neuron import h; pc = h.ParallelContext(); h.quit()'  2>&1)
 if [[ "$?" -eq "0" ]]; then
   echo "ok"
   NRNIV_AND_PYTHON_AND_MPI_WORKS=1
 else
   echo "failed"
   echo "Could not run nrniv with Python and MPI"
   echo "the command that failed was:"
   echo "$COMMAND"
   echo $OUTPUT
   return=2
   fi
else
 echo "Skipping NEURON funtionality tests with Python and MPI."
fi


echo "--------------------------------------"
echo "Done with post-install checks"
echo
if [[ "$return" -eq "0" ]]; then
  echo "SUCCESS: post-install checks were successful!"
elif [[ "$return" -eq "1" ]]; then
  echo "WARNING: there were one or more checks that might be a problem"
else
  echo "FAILED: there were one or more failed checks"
fi

echo
exit $return