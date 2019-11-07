#!/bin/bash

return=0

VERBOSE=0
UPGRADE=0
RESTART_NEEDED=0
STOP=0
START=0
UNINSTALL=0
OS=
VCXSRV_PID=

while [ -n "$1" ]; do
    case "$1" in
    -v) VERBOSE=1 ;;
    -r) RESTART_NEEDED=1 ;;
    -u) UPGRADE=1; echo -e "Upgrade HNN image requested\n" ;;
    upgrade) UPGRADE=1; echo -e "Upgrade HNN image requested\n" ;;
    stop) STOP=1; echo -e "Stopping HNN container requested\n" ;;
    start) START=1; echo -e "Starting HNN container requested\n" ;;
    uninstall) UNINSTALL=1; echo -e "Uninstall of HNN requested\n" ;;
    *) echo -e "Option $1 not recognized\n" ;;
    esac
    shift
done

function cleanup {
  if [[ "$OS"  =~ "windows" ]] && [ ! -z "${VCXSRV_PID}" ]; then
    kill -9 ${VCXSRV_PID} &> /dev/null
  fi
}

function remove_container {
  while true; do
    echo
    read -p "Please confirm that you want to remove the old HNN container? (y/n)" yn
    case $yn in
      [Yy]* ) echo -n "Removing old container... " | tee -a hnn_docker.log
              docker rm -fv hnn_container &> /dev/null
              if [[ $? -eq "0" ]]; then
                echo "done" | tee -a hnn_docker.log
              else
                echo "failed" | tee -a hnn_docker.log
                cleanup
                exit 1
              fi
              break;;
      [Nn]* ) echo "Cannot continue" | tee -a hnn_docker.log
              cleanup
              exit 1
              break;;
      * ) echo "Please answer yes or no.";;
    esac
  done
}

if [[ $START -eq "0" ]] && [[ $STOP -eq "0" ]] && [[ $UNINSTALL -eq "0" ]] && [[ $UPGRADE -eq "0" ]]; then
  echo "No valid action provided. Available actions are start, stop, upgrade, and uninstall"
  exit 1
fi

echo "Performing pre-checks before starting HNN" | tee -a hnn_docker.log
echo "--------------------------------------" | tee -a hnn_docker.log

echo -n "Checking OS version... " | tee -a hnn_docker.log
OS_OUTPUT=$(uname -a)
if [[ $OS_OUTPUT =~ "MINGW" ]]; then
  OS="windows"
elif [[ $OS_OUTPUT =~ "Darwin" ]]; then
  OS="mac"
elif [[ $OS_OUTPUT =~ "Linux" ]]; then
  OS="linux"
fi
echo "$OS" | tee -a hnn_docker.log

echo -n "Checking if Docker is working... " | tee -a hnn_docker.log
DOCKER_OUTPUT=$(docker version 2> /dev/null)
DOCKER_STATUS=$?
DOCKER_VERSION=
DOCKER_TOOLBOX=0

while IFS= read -r line; do
  if [[ $line =~ " Version" ]]; then
    DOCKER_VERSION=$(echo $line | cut -d':' -f 2| sed 's/^[ \t]*//')
    break
  fi
done <<< "$DOCKER_OUTPUT"

if  [[ -n "${DOCKER_MACHINE_NAME}" ]]; then
  DOCKER_TOOLBOX=1
fi

if [[ "$DOCKER_STATUS" -eq "0" ]]; then
  if [[ "$DOCKER_TOOLBOX" -eq "1" ]]; then
    toolbox_str=" (Docker Toolbox)"
  fi
  echo "ok${toolbox_str}" | tee -a hnn_docker.log
else
  echo "failed" | tee -a hnn_docker.log
  if [ -z $DOCKER_VERSION ]; then
    echo "Docker could not be found. Please make sure it is installed correctly." | tee -a hnn_docker.log
  else
    echo "Docker version ${DOCKER_VERSION} is installed, but needs to be started." | tee -a hnn_docker.log
  fi
  exit 1
fi

if [[ $UPGRADE -eq "1" ]]; then
  echo -n "Downloading new HNN image from Docker Hub (may require login)... " | tee -a hnn_docker.log
  docker pull jonescompneurolab/hnn >> hnn_docker.log 2>&1
  if [[ $? -eq "0" ]]; then
    echo "ok" | tee -a hnn_docker.log
    docker ps -a |grep hnn_container >> hnn_docker.log 2>&1
    if [[ $? -eq "0" ]]; then
      remove_container
    fi
    RESTART_NEEDED=1
    RETURN_STATUS=0
  else
    echo "failed" | tee -a hnn_docker.log
    echo "WARNING: continuing with old image" | tee -a hnn_docker.log
    RETURN_STATUS=1
  fi
  if [[ $START -eq "0" ]]; then
    # just doing upgrade
    exit ${RETURN_STATUS}
  fi
fi

if [[ "$STOP" -eq "1" ]]; then
  docker stop hnn_container
  if [[ "$?" -ne "0" ]]; then
    echo "Failed to stop HNN container" | tee -a hnn_docker.log
  else
    echo "Successfully stopped HNN container" | tee -a hnn_docker.log
  fi
  exit 0
fi

if [[ "$UNINSTALL" -eq "1" ]]; then
  docker ps -a |grep hnn_container >> hnn_docker.log 2>&1
  if [[ $? -eq "0" ]]; then
    remove_container
  fi
  while true; do
    echo
    read -p "Are you sure that you want to remove the HNN image? (y/n)" yn
    case $yn in
      [Yy]* ) docker rmi -f jonescompneurolab/hnn
              if [[ "$?" -ne "0" ]]; then
                echo "Failed to remove HNN image" | tee -a hnn_docker.log
                exit 1
              else
                echo "Removed HNN image" | tee -a hnn_docker.log
              fi
              break;;
      [Nn]* ) break;;
      * ) echo "Please answer yes or no.";;
    esac
  done

  exit 0
fi

echo -n "Checking if docker-compose is found... " | tee -a hnn_docker.log
which docker-compose &> /dev/null
if [[ "$?" -eq "0" ]]; then
  echo "ok" | tee -a hnn_docker.log
else
  echo "failed" | tee -a hnn_docker.log
  echo "docker-compose could not be found. Please make sure it was installed with docker." | tee -a hnn_docker.log
  exit 1
fi

XAUTH=~/.Xauthority
if [ -d "$XAUTH" ]; then
  echo -n "Removing misplaced directory $XAUTH... " | tee -a hnn_docker.log
  rmdir $XAUTH
  echo "done" | tee -a hnn_docker.log
fi

if [[ "$OS" =~ "windows" ]]; then
  echo -n "Checking if VcXsrv is installed... " | tee -a hnn_docker.log
  VCXSRV_DIR="/c/Program Files/VcXsrv"
  if [ -f "${VCXSRV_DIR}/vcxsrv.exe" ]; then
    XAUTH_BIN="${VCXSRV_DIR}/xauth.exe"
    echo "done" | tee -a hnn_docker.log
  else
    unset XAUTH_BIN
    echo "failed. Could not find 'C:\Program Files\VcXsrv'. Please run XLaunch manually" | tee -a hnn_docker.log
  fi

  if [ -n "${XAUTH_BIN}" ]; then
    echo -n "Starting VcXsrv... " | tee -a hnn_docker.log
    "${VCXSRV_DIR}/vcxsrv.exe" -wgl -multiwindow >> hnn_docker.log 2>&1 &
    VCXSRV_PID=$!
    echo done | tee -a hnn_docker.log

    echo -n "Checking VcXsrv authorization... " | tee -a hnn_docker.log
    OUTPUT=$("${XAUTH_BIN}" nlist :0 2>> hnn_docker.log)
    if [[ -z $OUTPUT ]]; then
      echo "failed. Still an error with xauth" | tee -a hnn_docker.log
      cleanup
      exit 1
    fi
    echo "done" | tee -a hnn_docker.log
  fi
elif [[ "$OS" =~ "mac" ]]; then
  echo -n "Checking if XQuartz is installed... " | tee -a hnn_docker.log
  XQUARTZ_OUTPUT=$(defaults read org.macosforge.xquartz.X11.plist 2> /dev/null)
  XQUARTZ_STATUS=$?
  XQUARTZ_VERSION=

  if [[ "$XQUARTZ_STATUS" -eq "0" ]]; then
    echo "ok" | tee -a hnn_docker.log
  else
    echo "failed. Please install XQuartz" | tee -a hnn_docker.log
    exit 1
  fi

  XAUTH_BIN="$(which xauth)"

  while IFS= read -r line; do
    if [[ $line =~ "no_auth" ]]; then
      XQUARTZ_NOAUTH=$(echo $line | cut -d'=' -f 2| sed 's/^[ \t]*\(.*\);/i\1/')
    elif [[ $line =~ "nolisten_tcp" ]]; then
      XQUARTZ_NOLISTEN=$(echo $line | cut -d'=' -f 2| sed 's/^[ \t]*\(.*\);/i\1/')
    fi
  done <<< "$XQUARTZ_OUTPUT"

  STATUS=0
  echo -n "Setting XQuartz security preferences... " | tee -a hnn_docker.log
  if [[ "$XQUARTZ_NOLISTEN" =~ "0" ]]; then
    defaults write org.macosforge.xquartz.X11.plist nolisten_tcp 0 >> hnn_docker.log 2>&1
    if [[ $? -ne "0" ]]; then
      STATUS=1
    fi
  fi
  if [[ "$XQUARTZ_NOAUTH" =~ "1" ]]; then

    defaults write org.macosforge.xquartz.X11.plist no_auth 0 >> hnn_docker.log 2>&1
    if [[ $? -ne "0" ]]; then
      STATUS=1
    fi
  fi
  if [[ "$STATUS" -eq "0" ]]; then
    echo "ok" | tee -a hnn_docker.log
  else
    echo "failed" | tee -a hnn_docker.log
    exit 1
  fi

  echo -n "Checking XQuartz authorization... " | tee -a hnn_docker.log
  OUTPUT=$(${XAUTH_BIN} nlist :0 2>> hnn_docker.log)
  if [[ -z $OUTPUT ]]; then
    echo "needs updating" | tee -a hnn_docker.log
    echo -n "Restarting XQuartz... " | tee -a hnn_docker.log
    killall Xquartz >> hnn_docker.log 2>&1
    sleep 1
    open -a XQuartz | tee -a hnn_docker.log 2>&1
    sleep 5
    OUTPUT=$(${XAUTH_BIN} nlist :0 2>> hnn_docker.log)
    if [[ -z $OUTPUT ]]; then
      echo "failed. Still an error with xauth" | tee -a hnn_docker.log
      exit 1
    fi
    killall Xquartz >> hnn_docker.log 2>&1
    sleep 1
  fi
  echo "done" | tee -a hnn_docker.log

  echo -n "Starting XQuartz... " | tee -a hnn_docker.log
  open -a XQuartz
  if [[ $? -eq "0" ]]; then
    echo "ok" | tee -a hnn_docker.log
  else
    echo "failed" | tee -a hnn_docker.log
    exit 1
  fi
fi

echo -n "Locating HNN source code... " | tee -a hnn_docker.log
# find the source code directory
CWD=$(pwd)

if [[ "$OS" =~ "linux" ]]; then
  COMPOSE_FILE="$CWD/installer/docker/docker-compose.yml"
else
  COMPOSE_FILE="$CWD/installer/$OS/docker-compose.yml"
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "failed"
  echo "Could not find source code files for starting docker container."
  echo "Please run this script from the source code directory. e.g.:"
  echo "./hnn_docker.sh"
  cleanup
  exit 1
fi
echo $CWD | tee -a hnn_docker.log

echo | tee -a hnn_docker.log
echo "Starting HNN" | tee -a hnn_docker.log
echo "--------------------------------------" | tee -a hnn_docker.log

if [[ ! "$OS" =~ "linux" ]]; then
  # ignore hostname in Xauthority by setting FamilyWild mask
  # https://stackoverflow.com/questions/16296753/can-you-run-gui-applications-in-a-docker-container/25280523#25280523

  # we can assume ~/.Xauthority exists because xauth nlist was successful

  if [ -n "${XAUTH_BIN}" ]; then
    AUTH_KEYS=$("${XAUTH_BIN}" nlist :0 |grep -v '^ffff')
    if [[ -n $AUTH_KEYS ]]; then
      echo -n "Updating Xauthority file... " | tee -a hnn_docker.log
      "${XAUTH_BIN}" nlist :0 | sed -e 's/^..../ffff/' | "${XAUTH_BIN}" -f "$XAUTH" -b -i nmerge - >> hnn_docker.log 2>&1
      if [[ "$?" -ne "0" ]] || [[ -f "${XAUTH}-n" ]]; then
        echo "failed"
        rm -f "${XAUTH}-n"
        cleanup
        exit 1
      fi
      echo "done" | tee -a hnn_docker.log
      RESTART_NEEDED=1
    fi
  fi

  echo -n "Setting up SSH authentication files... " | tee -a hnn_docker.log
  # set up ssh keys
  SSH_PRIVKEY="$CWD/installer/docker/id_rsa_hnn"
  SSH_PUBKEY="$CWD/installer/docker/id_rsa_hnn.pub"
  SSH_AUTHKEYS="$CWD/installer/docker/authorized_keys"
  if [[ ! -f "$SSH_PRIVKEY" ]] || [[ ! -f "$SSH_PUBKEY" ]] || [[ ! -f "$SSH_AUTHKEYS" ]]; then
    rm -f "$SSH_PRIVKEY"
    if [[ "$OS" =~ "windows" ]]; then
      ssh-keygen -f $SSH_PRIVKEY -t rsa -N '' >> hnn_docker.log 2>&1
    else
      ssh-keygen -f $SSH_PRIVKEY -t rsa -N '' >> hnn_docker.log 2>&1
    fi

    if [[ $? -ne "0" ]]; then
      echo "failed running ssh-keygen. Please see hnn_docker.log for more details" | tee -a hnn_docker.log
      cleanup
      exit 1
    fi

    echo -n "command=\"/home/hnn_user/start_hnn.sh\" " > "$SSH_AUTHKEYS"
    cat "$SSH_PUBKEY" >> "$SSH_AUTHKEYS"
  fi
  echo "done" | tee -a hnn_docker.log
fi

echo -n "Checking for running HNN container... " | tee -a hnn_docker.log
docker ps |grep hnn_container >> hnn_docker.log 2>&1
if [[ $? -eq "0" ]]; then
  ALREADY_RUNNING=1
  echo "found" | tee -a hnn_docker.log
else
  ALREADY_RUNNING=0
  echo "not found" | tee -a hnn_docker.log
fi

if [[ "$RESTART_NEEDED" -eq "1" ]]; then
  if [[ "$ALREADY_RUNNING" -eq "1" ]]; then
    while true; do
      echo | tee -a hnn_docker.log
      if [[ "$UPGRADE" -eq "1" ]]; then
        str=" for upgrade"
      else
        str=
      fi

      read -p "Restart needed$str. Please confirm that you want to force stopping the HNN container? (y/n)" yn
      case $yn in
          [Yy]* ) echo -n "Stopping HNN container... " | tee -a hnn_docker.log
                  docker stop hnn_container &> /dev/null
                  if [[ $? -ne "0" ]]; then
                    echo "Failed to stop container" | tee -a hnn_docker.log
                    cleanup
                    exit 1
                  else
                    ALREADY_RUNNING=0
                    echo "done" | tee -a hnn_docker.log
                  fi
                  break;;
          [Nn]* ) break;;
          * ) echo "Please answer yes or no.";;
      esac
    done
  fi
fi

if [[ "$ALREADY_RUNNING" -eq "0" ]]; then
  echo "Starting HNN container..." | tee -a hnn_docker.log
  docker-compose -f "$COMPOSE_FILE" up -d >> hnn_docker.log 2>&1
  if [[ $? -ne "0" ]]; then
    # try removing container
    echo "failed starting with docker-compose." | tee -a hnn_docker.log
    docker ps -a |grep hnn_container >> hnn_docker.log 2>&1
    if [[ $? -eq "0" ]]; then
      echo "Found an old container that could have cause this failure" | tee -a hnn_docker.log
      remove_container
    else
      echo "Please see hnn_docker.log for more details" | tee -a hnn_docker.log
      cleanup
      exit 1
    fi

    echo -n "Starting HNN container again... " | tee -a hnn_docker.log
    docker-compose -f "$COMPOSE_FILE" up -d >> hnn_docker.log 2>&1
    if [[ $? -ne "0" ]]; then
      echo "failed starting with docker-compose." | tee -a hnn_docker.log
      cleanup
      exit 1
    elif [[ $? -eq "0" ]] && [[ "$OS" =~ "linux" ]]; then
      echo "User exited HNN" | tee -a hnn_docker.log
    fi
  fi
fi

if [[ ! "$OS" =~ "linux" ]]; then
  echo -n "Copying authentication files into container... " | tee -a hnn_docker.log
  chmod 600 "$SSH_AUTHKEYS"
  echo -n "Copying authorized_keys..." >> hnn_docker.log
  docker cp "$SSH_AUTHKEYS" hnn_container:/home/hnn_user/.ssh/authorized_keys >> hnn_docker.log 2>&1
  if [[ $? -ne "0" ]]; then
    echo "failed running docker cp. Please see hnn_docker.log for more details" | tee -a hnn_docker.log
    cleanup
    exit 1
  fi
  echo "done" >> hnn_docker.log

  echo -n "Copying known_hosts..." >> hnn_docker.log
  docker cp "$SSH_PUBKEY" hnn_container:/home/hnn_user/.ssh/known_hosts >> hnn_docker.log 2>&1
  if [[ $? -ne "0" ]]; then
    echo "failed running docker cp. Please see hnn_docker.log for more details" | tee -a hnn_docker.log
    cleanup
    exit 1
  fi
  echo "done" >> hnn_docker.log

  echo -n "Changing ssh file permissions..." >> hnn_docker.log
  docker exec hnn_container bash -c 'sudo chown hnn_user:hnn_group /home/hnn_user/.ssh/authorized_keys' >> hnn_docker.log 2>&1
  docker exec hnn_container bash -c 'sudo chown hnn_user:hnn_group /home/hnn_user/.ssh/known_hosts' >> hnn_docker.log 2>&1

  echo "done" | tee -a hnn_docker.log

  echo -n "Looking up port to connect to HNN container... " | tee -a hnn_docker.log
  SSH_PORT=$(docker port hnn_container 22 | cut -d':' -f 2 2> /dev/null)
  re='^[0-9]+$'
  if ! [[ $SSH_PORT =~ $re ]] ; then
    echo "failed" | tee -a hnn_docker.log
    cleanup
    exit 1
  fi
  echo "done" | tee -a hnn_docker.log

  echo -n "Starting HNN... " | tee -a hnn_docker.log
  if [[ "${DOCKER_TOOLBOX}" -eq "1" ]]; then
    DOCKER_HOST=192.168.99.100
  else
    DOCKER_HOST=localhost
  fi
  DISPLAY=localhost:0 ssh -o "SendEnv DISPLAY" -o "UserKnownHostsFile=/dev/null" -o "StrictHostKeyChecking=no" -t -i "$SSH_PRIVKEY" -R 6000:localhost:6000 hnn_user@$DOCKER_HOST -p $SSH_PORT >> hnn_docker.log 2>&1
  if [[ $? -ne "0" ]]; then
    echo "failed to start HNN. Please see hnn_docker.log for more details" | tee -a hnn_docker.log
    cleanup
    exit 1
  else
    echo "User exited HNN" | tee -a hnn_docker.log
  fi
fi
cleanup
