#!/bin/bash

if [ ! -d /home/hnn_user/hnn ]; then
  echo "creating /home/hnn_user/hnn"
  mkdir /home/hnn_user/hnn
else
  echo "changing ownership permissions of /home/hnn_user/hnn"
  sudo chown -R hnn_user:hnn_group /home/hnn_user/hnn
fi

cd /home/hnn_user/hnn_repo
python3 hnn.py hnn.cfg

# fallback to sleep infinity so that container won't stop if hnn is closed
sleep infinity
