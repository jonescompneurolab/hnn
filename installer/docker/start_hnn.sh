#!/bin/bash

source /home/hnn_user/hnn_envs
cd /home/hnn_user/hnn_source_code

# make sure hnn_out directory is usable by hnn_user (world writable)
if [[ ${SYSTEM_USER_DIR} ]] && [ -d ${SYSTEM_USER_DIR} ]; then
  sudo chmod a+rwx ${SYSTEM_USER_DIR}/hnn_out
fi

echo "Starting HNN GUI..."

if [[ ! "$(ulimit -l)" =~ "unlimited" ]]; then
  ulimit -l unlimited > /dev/null 2>&1
fi

function retry_hnn {
  if [[ -n "$1" ]]; then
    if [ -z "$2" ]; then
      export DISPLAY=:$1
    else
      export DISPLAY=$1:$2
    fi
  fi

  echo "Trying to start HNN with DISPLAY=$DISPLAY"
  python3 hnn.py
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
