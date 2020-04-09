#!/bin/bash

[[ DISPLAY ]] || {
  echo "DISPLAY not set"
  exit 1
}

let PORT=6000+${DISPLAY#*:}
IP=${DISPLAY%%:*}
if [ ! -z $IP ]; then
  if nc -zvw3 $IP $PORT > /dev/null 2>&1; then
    echo "Success connecting to X server at $IP:$PORT"
  else
    echo "Could not connect to X server at $IP:$PORT"
    exit 1
  fi
fi
