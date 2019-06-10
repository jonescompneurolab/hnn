#!/bin/bash

if [ ! -d /home/hnn_user/hnn ]; then
  echo "creating /home/hnn_user/hnn"
  mkdir /home/hnn_user/hnn
else
  echo "changing ownership permissions of /home/hnn_user/hnn"
  sudo chown -R hnn_user:hnn_group /home/hnn_user/hnn
fi

cd /home/hnn_user/hnn_repo

done=
XHOST=${DISPLAY%:0}
# try some common hosts
for XHOST in $XHOST 192.168.99.1 192.168.65.2 ""; do
  for PORT in 0 1 2 3 4; do
    export DISPLAY=$XHOST:$PORT
    echo "Trying to start HNN with DISPLAY=$DISPLAY"
    python3 hnn.py hnn.cfg
    if [[ "$?" -ne "0" ]]; then
      echo "HNN failed to start GUI using DISPLAY=$DISPLAY"
    else
      done=1
      break
    fi
  done
  if [[ "$done" -eq "1" ]]; then
    break
  fi
done

if [[ "$done" -eq "1" ]]; then
  echo "HNN GUI stopped by user. Restart container to open again"
else
  echo "Failed to start HNN on any X port at host"
fi

# fallback to sleep infinity so that container won't stop if hnn is closed
sleep infinity
