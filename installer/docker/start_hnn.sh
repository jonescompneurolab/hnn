#!/bin/bash

[[ $TRAVIS_TESTING ]] || TRAVIS_TESTING=0
[[ $SYSTEM_USER_DIR ]] || SYSTEM_USER_DIR=$HOME

source /home/hnn_user/hnn_envs
cd /home/hnn_user/hnn_source_code

if [[ "$(whoami 2> /dev/null)" == "hnn_user" ]]; then
  QT_CONF="/home/hnn_user/.config/QtProject.conf"
else
  # for all other users
  QT_CONF="/.config/QtProject.conf"
fi

grep -q "SYSTEM_USER_DIR" "$QT_CONF" > /dev/null 2>&1
if [[ $? -eq 0 ]]; then
  echo -n "Updating Qt preferences... "
  sed -i "s@\${SYSTEM_USER_DIR}@$SYSTEM_USER_DIR@" "$QT_CONF"
  if [[ $? -eq 0 ]]; then
    echo "changed"
  else
    echo "ok"
  fi
fi

which ulimit > /dev/null 2>&1
if [[ $? -eq 0 ]]; then
  echo -n "Checking locked memory limits..."
  if [[ ! "$(ulimit -l)" =~ "unlimited" ]]; then
    echo "failed."
    echo -n "Updating locked memory limits..."
    ulimit -l unlimited > /dev/null 2>&1
    if [[ $? -ne 0 ]]; then
      echo "failed."
    else
      echo "ok."
    fi
  else
    echo "ok."
  fi
fi

function retry_hnn {
  local __port
  local __ip

  if [[ -n "$1" ]]; then
    if [ -z "$2" ]; then
      export DISPLAY=:$1
    else
      export DISPLAY=$1:$2
    fi
  fi

  let __port=6000+${DISPLAY#*:}
  __ip=${DISPLAY%%:*}
  if [ ! -z $__ip ]; then
    if nc -zvw3 $__ip $__port > /dev/null 2>&1; then
      echo "Success connecting to X server at $__ip:$__port"
    else
      echo "Could not connect to X server at $__ip:$__port"
      false
      return
    fi
  fi

  TRAVIS_TESTING=$TRAVIS_TESTING python3 hnn.py
  if [[ "$?" -ne "0" ]]; then
    echo "***************************************************"
    echo "HNN failed to start GUI using DISPLAY=$DISPLAY"
    echo "***************************************************"
    echo
    return
  else
    echo "HNN GUI stopped by user."
    exit 0
  fi
}

# get rid of warning about XDG_RUNTIME_DIR
export XDG_RUNTIME_DIR=/tmp/runtime-hnn_user
mkdir /tmp/runtime-hnn_user &> /dev/null
chmod 700 /tmp/runtime-hnn_user

# try once with current DISPLAY
retry_hnn

# ports other than :0 are not supported currently
# done=
# XHOST=${DISPLAY%:0}
# for PORT in 1 2; do
#   retry_hnn $XHOST $PORT
# done

echo "Failed to start HNN on any X port"
exit 1
