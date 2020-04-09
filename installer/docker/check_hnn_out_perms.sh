#!/bin/bash

[[ $SYSTEM_USER_DIR ]] || SYSTEM_USER_DIR=$HOME

echo -n "Checking permissions to access ${SYSTEM_USER_DIR}/hnn_out... "
test -x "${SYSTEM_USER_DIR}/hnn_out" && test -r "${SYSTEM_USER_DIR}/hnn_out" && test -w "${SYSTEM_USER_DIR}/hnn_out"
if [[ $? -ne 0 ]]; then
  echo "failed. Can't start HNN."
  exit 1
else
  echo "ok"
fi
