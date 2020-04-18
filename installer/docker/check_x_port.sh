#!/bin/bash

[[ DISPLAY ]] || {
  echo "DISPLAY not set"
  exit 1
}

let PORT=6000+${DISPLAY#*:}
IP=${DISPLAY%%:*}
if [ ! -z $IP ]; then
  nc -nzvw3 $IP $PORT
  if [[ $? -ne 0 ]]; then
    exit 1
  fi
fi
