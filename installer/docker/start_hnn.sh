#!/bin/bash

source /home/hnn_user/hnn_envs
cd /home/hnn_user/hnn_source_code

# make sure hnn_out directory is readable by the user
sudo chown -R hnn_user:hnn_group /home/hnn_user/hnn_out

echo "Starting HNN GUI..."

if [[ ! "$(ulimit -l)" =~ "unlimited" ]]; then
  ulimit -l unlimited > /dev/null 2>&1
fi

function retry_hnn {
  if [ -z "$2" ]; then
    export DISPLAY=:$1
  else
    export DISPLAY=$1:$2
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

export PYTHONPATH=/home/hnn_user/nrn/build/lib/python/
export CPU=$(uname -m)
export PATH=$PATH:/home/hnn_user/nrn/build/$CPU/bin

# get rid of warning about XDG_RUNTIME_DIR
export XDG_RUNTIME_DIR=/tmp/runtime-hnn_user
mkdir /tmp/runtime-hnn_user &> /dev/null
chmod 700 /tmp/runtime-hnn_user

# try once with current DISPLAY
python3 hnn.py
if [[ "$?" -eq "0" ]]; then
  # HNN quit gracefully
  echo "HNN GUI stopped by user."
  exit 0
fi

done=
XHOST=${DISPLAY%:0}
for PORT in 1 2; do
  retry_hnn $XHOST $PORT
done

echo "Failed to start HNN on any X port"
exit 1
