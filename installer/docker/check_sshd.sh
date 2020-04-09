#!/bin/bash

if timeout 1 bash -c '</dev/tcp/127.0.0.1/22 &>/dev/null'
then
  echo "Port is open"
else
  echo "Port is closed"
  exit 1
fi
