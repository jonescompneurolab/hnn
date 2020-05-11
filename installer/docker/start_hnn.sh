#!/bin/bash

[[ $TRAVIS_TESTING ]] || TRAVIS_TESTING=0
[[ $SYSTEM_USER_DIR ]] || SYSTEM_USER_DIR="$HOME"
[[ $DISPLAY ]] || DISPLAY=":0"

if [ -d "/usr/local/nrn/lib/python" ]; then
  # linux containers
  PYTHONPATH="/usr/local/nrn/lib/python"
elif [ -d "/c/nrn/lib/python" ]; then
  # windows containers
  PYTHONPATH="/c/nrn/lib/python"
fi

export SYSTEM_USER_DIR TRAVIS_TESTING DISPLAY PYTHONPATH

source "$HOME/hnn_envs"
cd "$HOME/hnn_source_code"

QT_CONF="$HOME/.config/QtProject.conf"
if [[ -f "$QT_CONF" ]]; then
  if [[ ! -w "$QT_CONF" ]]; then
    echo "Incorrect permissions to modifiy $QT_CONF"
  else
    echo -n "Updating Qt preferences... "
    grep -q "SYSTEM_USER_DIR" "$QT_CONF" > /dev/null 2>&1
    if [[ $? -eq 0 ]]; then
      sed "s@\$SYSTEM_USER_DIR@$SYSTEM_USER_DIR@; s@\$HOME@$HOME@" "$QT_CONF" > /tmp/qtconf
      cat /tmp/qtconf > "$QT_CONF"
      rm -f /tmp/qtconf
      if [[ $? -eq 0 ]]; then
        echo "changed"
      else
        echo "failed"
      fi
    else
      echo "already changed"
    fi
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
    python3 hnn.py
  else
    python hnn.py
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
export XDG_RUNTIME_DIR="/tmp/runtime-$USER"
if [[ -f "XDG_RUNTIME_DIR" ]]; then
  mkdir "$XDG_RUNTIME_DIR" && \
    chmod 700 "$XDG_RUNTIME_DIR"
fi

if [[ "$OS" == "Windows_NT" ]]; then
  source activate hnn
fi

# try once with current DISPLAY
start_hnn