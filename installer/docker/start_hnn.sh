#!/bin/bash

cd /home/hnn_user/hnn_source_code

if [[ ! "$(ulimit -l)" =~ "unlimited" ]]; then
  ulimit -l unlimited > /dev/null 2>&1
fi

function retry_hnn {
  export DISPLAY=$1:$2
  echo "Trying to start HNN with DISPLAY=$DISPLAY"
  python3 hnn.py
  if [[ "$?" -ne "0" ]]; then
    echo "HNN failed to start GUI using DISPLAY=$DISPLAY"
    return 1
  else
    echo "HNN GUI stopped by user. Restart container to open again"
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
  echo "HNN GUI stopped by user. Restart container to open again"
  exit 0
fi

done=
XHOST=${DISPLAY%:0}
# try some common hosts
for PORT in 0 1 2 3 4; do
  for XHOST in $XHOST 192.168.99.1 192.168.65.2 ""; do
    retry_hnn $XHOST $PORT
  done
done

echo "Failed to start HNN on any X port at host"

# fallback to sleep infinity so that container won't stop if hnn is closed
sleep infinity
