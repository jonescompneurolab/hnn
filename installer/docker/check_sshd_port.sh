#!/bin/bash

pgrep sshd &> /dev/null
if [[ $? -ne 0 ]]; then
  echo "sshd is not running"
  exit 1
fi

if nc -zvw3 127.0.0.1 22 > /dev/null 2>&1; then
  echo "sshd has opened port 22"
else
  echo "sshd had not opened port 22"
  exit 1
fi
