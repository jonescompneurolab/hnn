#!/bin/bash

[[ $TRAVIS_TESTING ]] || TRAVIS_TESTING=0
[[ $SYSTEM_USER_DIR ]] || SYSTEM_USER_DIR="$HOME"

source "$HOME/hnn_envs"
cd "$HOME/hnn_source_code"

if [[ "$(whoami 2> /dev/null)" == "hnn_user" ]]; then
  QT_CONF="$HOME/.config/QtProject.conf"
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

function start_hnn {
  which nc > /dev/null 2>&1
  if [[ $? -eq 0 ]]; then
    local __port
    local __ip

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
  fi

  which python3 &> /dev/null
  if [[ $? -eq 0 ]]; then
    TRAVIS_TESTING=$TRAVIS_TESTING python3 hnn.py
  else
    TRAVIS_TESTING=$TRAVIS_TESTING python hnn.py
  fi
  if [[ "$?" -ne "0" ]]; then
    echo "HNN failed to start GUI using DISPLAY=$DISPLAY"
    false
    return
  else
    echo "HNN GUI stopped by user."
  fi
}

# get rid of warning about XDG_RUNTIME_DIR
export XDG_RUNTIME_DIR=/tmp/runtime-hnn_user
mkdir /tmp/runtime-hnn_user &> /dev/null
chmod 700 /tmp/runtime-hnn_user

if [[ "$OS" == "Windows_NT" ]]; then
  source activate hnn
fi

# try once with current DISPLAY
start_hnn