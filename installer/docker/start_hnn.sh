#!/bin/bash

[[ $TRAVIS_TESTING ]] || TRAVIS_TESTING=0

source /home/hnn_user/hnn_envs
cd /home/hnn_user/hnn_source_code

echo -n "Checking permissions to access ${SYSTEM_USER_DIR}/hnn_out... "
test -x "${SYSTEM_USER_DIR}/hnn_out" && test -r "${SYSTEM_USER_DIR}/hnn_out" && test -w "${SYSTEM_USER_DIR}/hnn_out"
if [[ $? -ne 0 ]]; then
  echo "failed. Can't start HNN."
  exit 1
else
  echo "ok"
fi

which ulimit > /dev/null 2>&1
if [[ $? -eq 0 ]]; then
  echo -n "Checking locked memory limits..."
  if [[ ! "$(ulimit -l)" =~ "unlimited" ]]; then
    echo "failed."
    echo -n "Updating locked memory limits..."
    ulimit -l unlimited > /dev/null 2>&1
    if [[ $? -ne 0 ]]; then
      echo "failed."
    else
      echo "ok."
    fi
  else
    echo "ok."
  fi
fi

function retry_hnn {
  if [[ -n "$1" ]]; then
    if [ -z "$2" ]; then
      export DISPLAY=:$1
    else
      export DISPLAY=$1:$2
    fi
  fi

  TRAVIS_TESTING=$TRAVIS_TESTING python3 hnn.py
  if [[ "$?" -ne "0" ]]; then
    echo "***************************************************"
    echo "HNN failed to start GUI using DISPLAY=$DISPLAY"
    echo "***************************************************"
    echo
    return 1
  else
    echo "HNN GUI stopped by user."
    exit 0
  fi
}

# get rid of warning about XDG_RUNTIME_DIR
export XDG_RUNTIME_DIR=/tmp/runtime-hnn_user
mkdir /tmp/runtime-hnn_user &> /dev/null
chmod 700 /tmp/runtime-hnn_user

# try once with current DISPLAY
retry_hnn

done=
XHOST=${DISPLAY%:0}
for PORT in 1 2; do
  retry_hnn $XHOST $PORT
done

echo "Failed to start HNN on any X port"
exit 1
