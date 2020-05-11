#!/bin/bash

[[ $SYSTEM_USER_DIR ]] || SYSTEM_USER_DIR=$HOME

echo -n "Checking permissions within ${SYSTEM_USER_DIR}/hnn_out... "

for dir in "${SYSTEM_USER_DIR}/hnn_out" "${SYSTEM_USER_DIR}/hnn_out/data" "${SYSTEM_USER_DIR}/hnn_out/param"; do
  if [ -d "$dir" ]; then
    test -x "$dir" && \
    test -r "$dir" && \
    test -w "$dir"
  else
    mkdir "$dir"
  fi
  if [[ $? -ne 0 ]]; then
    echo "failed"
    echo "Error: $dir has incorrect permissions or could not create $dir. Can't start HNN."
    ls -ld "$dir"
    exit 1
  fi
done

echo "ok"
