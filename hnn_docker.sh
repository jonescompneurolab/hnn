#!/bin/bash

return=0

VERBOSE=0
UPGRADE=0
STOP=0
START=0
FAILED=0
UNINSTALL=0
OS=
VCXSRV_PID=
HNN_DOCKER_IMAGE=jonescompneurolab/hnn
DOCKER_STATUS=
ALREADY_RUNNING=0
NEW_CONTAINER=0
SSH_PORT=

while [ -n "$1" ]; do
    case "$1" in
    -v) VERBOSE=1 ;;
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
  FAILED=0
  [[ $1 ]] && FAILED=$1

  if [[ "$OS"  =~ "windows" ]] && [ ! -z "${VCXSRV_PID}" ]; then
    echo "Killing VcXsrv PID ${VCXSRV_PID}" >> hnn_docker.log
    kill ${VCXSRV_PID} &> /dev/null
  fi

  if [[ $FAILED -eq "0" ]]; then
    echo "Script hnn_docker.sh finished successfully" | tee -a hnn_docker.log
    exit 0
  elif [[ $FAILED -eq "1" ]]; then
    echo "Script cannot conntinue" | tee -a hnn_docker.log
  elif [[ $FAILED -eq "2" ]]; then
    echo "Please see hnn_docker.log for more details"
  fi
  exit $FAILED
}

function silent_run_command {
  echo -e "\nCommand: $COMMAND" >> hnn_docker.log
  $COMMAND >> hnn_docker.log 2>&1
}

function fail_on_bad_exit {
  local  __statusvar=$1

  if [[ $__statusvar -ne "0" ]]; then
    echo "failed" | tee -a hnn_docker.log
    cleanup 2
  else
    echo "done" | tee -a hnn_docker.log
  fi
}

function run_command {
  silent_run_command
  fail_on_bad_exit $?
}

function prompt_remove_container {
  while true; do
    echo
    read -p "Please confirm that you want to remove the old HNN container? (y/n)" yn
    case $yn in
      [Yy]* ) echo -n "Removing old container... " | tee -a hnn_docker.log
              COMMAND="docker rm -fv hnn_container"
              run_command
              break;;
      [Nn]* ) cleanup 1
              break;;
      * ) echo "Please answer yes or no.";;
    esac
  done
}

function stop_container {
  echo -n "Stopping HNN container... " | tee -a hnn_docker.log
  COMMAND="docker stop hnn_container"
  run_command
  ALREADY_RUNNING=0
}

function get_container_port {
  echo -n "Looking up port to connect to HNN container... " | tee -a hnn_docker.log
  SSH_PORT=$(docker port hnn_container 22 | cut -d':' -f 2)
  re='^[0-9]+$'
  if ! [[ $SSH_PORT =~ $re ]] ; then
    echo "failed" | tee -a hnn_docker.log
    cleanup 2
  fi
  echo "done" | tee -a hnn_docker.log
}

function ssh_start_hnn {
  echo -n "Starting HNN... " | tee -a hnn_docker.log
  COMMAND="ssh -o SendEnv=DISPLAY -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -t -i $SSH_PRIVKEY -R 6000:localhost:6000 hnn_user@$DOCKER_HOST_IP -p $SSH_PORT"
  echo -e "\nCommand: $COMMAND" >> hnn_docker.log
  DISPLAY=localhost:0 $COMMAND >> hnn_docker.log 2>&1
}

function prompt_restart_container {
  while true; do
    echo | tee -a hnn_docker.log
    if [[ "$UPGRADE" -eq "1" ]]; then
      str=" for upgrade"
    else
      str=
    fi

    read -p "Restart needed$str. Please confirm that you want to force stopping the HNN container? (y/n)" yn
    case $yn in
        [Yy]* ) stop_container
                break;;
        [Nn]* ) echo "Continuing without restarting container"
                break;;
        * ) echo "Please answer yes or no.";;
    esac
  done
}

function find_existing_container {
  echo -e "\nCommand: docker ps -a |grep hnn_container" >> hnn_docker.log
  docker ps -a |grep hnn_container >> hnn_docker.log 2>&1
}

function copy_security_files {
  if [[ "$NEW_CONTAINER" -eq "1" ]]; then
    echo -n "Copying authorized_keys file into container... " | tee -a hnn_docker.log
    docker cp $SSH_AUTHKEYS hnn_container:/home/hnn_user/.ssh/authorized_keys >> hnn_docker.log 2>&1
    fail_on_bad_exit $?

    echo -n "Copying known_hosts file into container... " | tee -a hnn_docker.log
    docker cp $SSH_PUBKEY hnn_container:/home/hnn_user/.ssh/known_hosts >> hnn_docker.log 2>&1
    fail_on_bad_exit $?

    echo -n "Changing container authorized_keys file permissions..." | tee -a hnn_docker.log
    docker exec hnn_container bash -c 'sudo chown hnn_user /home/hnn_user/.ssh/authorized_keys && \
                                      sudo chmod 600 /home/hnn_user/.ssh/authorized_keys' \
      >> hnn_docker.log 2>&1
    fail_on_bad_exit $?

    echo -n "Changing container known_hosts file permissions..." | tee -a hnn_docker.log
    docker exec hnn_container bash -c 'sudo chown hnn_user\:hnn_group /home/hnn_user/.ssh/known_hosts' \
      >> hnn_docker.log 2>&1
    fail_on_bad_exit $?
  fi
}

if [[ $START -eq "0" ]] && [[ $STOP -eq "0" ]] && [[ $UNINSTALL -eq "0" ]] && [[ $UPGRADE -eq "0" ]]; then
  echo "No valid action provided. Available actions are start, stop, upgrade, and uninstall"
  cleanup 1
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

echo -n "Checking if Docker is installed... " | tee -a hnn_docker.log
COMMAND="which docker"
silent_run_command
if [[ "$?" -eq "0" ]]; then
  echo "ok" | tee -a hnn_docker.log
else
  echo "failed" | tee -a hnn_docker.log
  echo "docker could not be found. Please check its installation." | tee -a hnn_docker.log
  cleanup 1
fi

echo -n "Checking if docker-compose is found... " | tee -a hnn_docker.log
COMMAND="which docker-compose"
silent_run_command
if [[ "$?" -eq "0" ]]; then
  echo "ok" | tee -a hnn_docker.log
else
  echo "failed" | tee -a hnn_docker.log
  echo "docker-compose could not be found. Please make sure it was installed with docker." | tee -a hnn_docker.log
  cleanup 1
fi

DOCKER_TOOLBOX=0
if  [[ -n "${DOCKER_MACHINE_NAME}" ]]; then
  DOCKER_TOOLBOX=1
  toolbox_str=" (Docker Toolbox)"
  eval $(docker-machine env -u 2> /dev/null)
  eval $(docker-machine env 2> /dev/null)
fi

echo -n "Checking if Docker is working... " | tee -a hnn_docker.log
DOCKER_OUTPUT=$(timeout 5 docker version)
DOCKER_STATUS=$?
if [[ $DOCKER_STATUS -ne "0" ]]; then
  echo "failed" | tee -a hnn_docker.log
  if [[ "$DOCKER_TOOLBOX" -eq "1" ]]; then
    echo -n "Trying to start docker machine... " | tee -a hnn_docker.log
    COMMAND="docker-machine start"
    run_command
    # rerun env commands in case IP address changed
    eval $(docker-machine env -u 2> /dev/null)
    eval $(docker-machine env 2> /dev/null)
    echo -n "Checking again if Docker is working... " | tee -a hnn_docker.log
    echo >> hnn_docker.log
    DOCKER_OUTPUT=$(timeout 5 docker version)
    DOCKER_STATUS=$?
    if [[ $DOCKER_STATUS -ne "0" ]]; then
      echo "failed" | tee -a hnn_docker.log
      cleanup 2
    else
      echo "ok${toolbox_str}" | tee -a hnn_docker.log
    fi
  else
    echo "failed" | tee -a hnn_docker.log
    cleanup 2
  fi
elif [[ $? -eq "124" ]]; then
  echo "ERROR: timed out connecting to Docker. Please check Docker install" | tee -a hnn_docker.log
  cleanup 2
else
  echo "ok${toolbox_str}" | tee -a hnn_docker.log
fi

DOCKER_VERSION=
while IFS= read -r line; do
  if [[ $line =~ " Version" ]]; then
    DOCKER_VERSION=$(echo $line | cut -d':' -f 2| sed 's/^[ \t]*//')
    break
  fi
done <<< "$DOCKER_OUTPUT"

if [ -z $DOCKER_VERSION ]; then
  echo "Docker version could not be determined. Please make sure it is installed correctly." | tee -a hnn_docker.log
  cleanup 1
fi

if [[ $UPGRADE -eq "1" ]]; then
  echo "Downloading new HNN image from Docker Hub (may require login)..." | tee -a hnn_docker.log
  COMMAND="docker pull ${HNN_DOCKER_IMAGE}"
  silent_run_command
  if [[ $? -eq "0" ]]; then
    DOCKER_CONTAINER=$(docker ps -a |grep hnn_container)
    DOCKER_STATUS=$?
    if [[ $DOCKER_STATUS -eq "0" ]]; then
      LAST_USED_IMAGE=$(echo ${DOCKER_CONTAINER}|cut -d' ' -f 2)
      if [[ "${LAST_USED_IMAGE}" =~ "${HNN_DOCKER_IMAGE}" ]]; then
        echo "HNN image already up to date." | tee -a hnn_docker.log
        UPGRADE=0
      else
        prompt_remove_container
      fi
    fi
    RETURN_STATUS=0
  else
    echo "Failed" | tee -a hnn_docker.log
    echo "WARNING: continuing with old image" | tee -a hnn_docker.log
    RETURN_STATUS=1
  fi
  if [[ $START -eq "0" ]]; then
    # just doing upgrade
    cleanup ${RETURN_STATUS}
  fi
fi

if [[ "$STOP" -eq "1" ]]; then
  stop_container
  cleanup 0
fi

if [[ "$UNINSTALL" -eq "1" ]]; then
  find_existing_container
  if [[ $? -eq "0" ]]; then
    prompt_remove_container
  fi
  while true; do
    echo
    read -p "Are you sure that you want to remove the HNN image? (y/n)" yn
    case $yn in
      [Yy]* ) echo -n "Removing HNN image... " | tee -a hnn_docker.log
              COMMAND="docker rmi -f ${HNN_DOCKER_IMAGE}"
              run_command
              break;;
      [Nn]* ) cleanup 1
              break;;
      * ) echo "Please answer yes or no.";;
    esac
  done

  cleanup 0
fi

XAUTH=~/.Xauthority
if [ -d "$XAUTH" ]; then
  echo -n "Removing misplaced directory $XAUTH... " | tee -a hnn_docker.log
  COMMAND="rmdir $XAUTH"
  silent_run_command
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

  echo -n "Checking if VcXsrv is running... " | tee -a hnn_docker.log
  VCXSRV_PID=$(tasklist | grep vcxsrv | awk '{print $2}')
  if [ -n "${VCXSRV_PID}" ]; then
    echo "yes" | tee -a hnn_docker.log
    echo -n "Stopping VcXsrv... " | tee -a hnn_docker.log
    COMMAND="cmd.exe //c taskkill //F //IM vcxsrv.exe >> hnn_docker.log 2>&1"
    run_command
  else
    echo "no" | tee -a hnn_docker.log
  fi

  if [ -n "${XAUTH_BIN}" ]; then
    echo -n "Starting VcXsrv... " | tee -a hnn_docker.log
    echo "Command: ${VCXSRV_DIR}/vcxsrv.exe -wgl -multiwindow > /dev/null 2>&1 &" >> hnn_docker.log
    "${VCXSRV_DIR}/vcxsrv.exe" -wgl -multiwindow > /dev/null 2>&1 &
    VCXSRV_PID=$!
    echo "done" | tee -a hnn_docker.log
    echo "Started VcXsrv with PID ${VCXSRV_PID}" >> hnn_docker.log

    echo -n "Checking VcXsrv authorization... " | tee -a hnn_docker.log
    echo >> hnn_docker.log
    echo "Command: "${XAUTH_BIN}" nlist :0" >> hnn_docker.log
    OUTPUT=$("${XAUTH_BIN}" nlist :0 2>> hnn_docker.log)
    if [[ -z $OUTPUT ]]; then
      echo "failed. Still an error with xauth" | tee -a hnn_docker.log
      cleanup 2
    fi
    echo "done" | tee -a hnn_docker.log
    echo "Output: $OUTPUT" >> hnn_docker.log
  fi
elif [[ "$OS" =~ "mac" ]]; then
  echo -n "Checking if XQuartz is installed... " | tee -a hnn_docker.log
  XQUARTZ_OUTPUT=$(defaults read org.macosforge.xquartz.X11.plist)
  XQUARTZ_STATUS=$?
  fail_on_bad_exit $XQUARTZ_STATUS

  echo -n "Checking for xauth... " | tee -a hnn_docker.log
  XAUTH_BIN=$(which xauth)
  COMMAND_STATUS=$?
  fail_on_bad_exit $COMMAND_STATUS

  while IFS= read -r line; do
    if [[ $line =~ "no_auth" ]]; then
      XQUARTZ_NOAUTH=$(echo $line | cut -d'=' -f 2| sed 's/^[ \t]*\(.*\);/i\1/')
    elif [[ $line =~ "nolisten_tcp" ]]; then
      XQUARTZ_NOLISTEN=$(echo $line | cut -d'=' -f 2| sed 's/^[ \t]*\(.*\);/i\1/')
    fi
  done <<< "$XQUARTZ_OUTPUT"

  STATUS=0
  if [[ "$XQUARTZ_NOLISTEN" =~ "0" ]]; then
    echo -n "Setting XQuartz preferences to listen for network connections... " | tee -a hnn_docker.log
    COMMAND="defaults write org.macosforge.xquartz.X11.plist nolisten_tcp 0"
    run_command
  fi

  if [[ "$XQUARTZ_NOAUTH" =~ "1" ]]; then
    echo -n "Setting XQuartz preferences to use authentication... " | tee -a hnn_docker.log
    COMMAND="defaults write org.macosforge.xquartz.X11.plist no_auth 0"
    run_command
  fi

  echo -n "Retrieving current XQuartz authentication keys... " | tee -a hnn_docker.log
  OUTPUT=$(${XAUTH_BIN} nlist :0 2>> hnn_docker.log)
  if [[ -z $OUTPUT ]]; then
    echo "XQuartz authentication keys need to be updated" | tee -a hnn_docker.log
    echo -n "Restarting XQuartz... " | tee -a hnn_docker.log
    COMMAND="killall Xquartz && sleep 1 && open -a XQuartz && sleep 3"
    run_command

    # run xauth again
    OUTPUT=$(${XAUTH_BIN} nlist :0 2>> hnn_docker.log)
    if [[ -z $OUTPUT ]]; then
      echo "Error: still no keys valid keys" | tee -a hnn_docker.log
      cleanup 2
    fi
    COMMAND="killall Xquartz && sleep 1"
    silent_run_command
  fi
  echo "done" | tee -a hnn_docker.log

  echo -n "Starting XQuartz... " | tee -a hnn_docker.log
  COMMAND="open -a XQuartz"
  run_command
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
  cleanup 1
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
        cleanup 2
      fi
      echo "done" | tee -a hnn_docker.log
    fi
  fi

  echo -n "Setting up SSH authentication files... " | tee -a hnn_docker.log
  # set up ssh keys
  SSH_PRIVKEY="$CWD/installer/docker/id_rsa_hnn"
  SSH_PUBKEY="./installer/docker/id_rsa_hnn.pub"
  SSH_AUTHKEYS="./installer/docker/authorized_keys"
  if [[ ! -f "$SSH_PRIVKEY" ]] || [[ ! -f "$SSH_PUBKEY" ]] || [[ ! -f "$SSH_AUTHKEYS" ]]; then
    rm -f "$SSH_PRIVKEY"
    command="ssh-keygen -f $SSH_PRIVKEY -t rsa -N ''"
    silent_run_command
    if [[ $? -ne "0" ]]; then
      echo "Error: failed running ssh-keygen." | tee -a hnn_docker.log
      cleanup 2
    fi

    echo -n "command=\"/home/hnn_user/start_hnn.sh\" " > "$SSH_AUTHKEYS"
    cat "$SSH_PUBKEY" >> "$SSH_AUTHKEYS"
  fi
  echo "done" | tee -a hnn_docker.log
fi

echo -n "Checking for running HNN container... " | tee -a hnn_docker.log
COMMAND="docker ps|grep hnn_container"
silent_run_command
if [[ $? -eq "0" ]]; then
  ALREADY_RUNNING=1
  echo "found" | tee -a hnn_docker.log
else
  ALREADY_RUNNING=0
  echo "not found" | tee -a hnn_docker.log
fi

if [[ "$RESTART_NEEDED" -eq "1" ]] && [[ "$ALREADY_RUNNING" -eq "1" ]]; then
  prompt_restart_container
fi

if [[ "$OS" =~ "linux" ]]; then
  echo -n "Starting HNN container... " | tee -a hnn_docker.log
  COMMAND="docker-compose -f $COMPOSE_FILE up --no-recreate"
  silent_run_command
  if [[ $? -ne "0" ]]; then
    # try removing container
    echo "failed" | tee -a hnn_docker.log
    echo -n "Looking for old containers..." | tee -a hnn_docker.log
    echo >> hnn_docker.log
    find_existing_container
    if [[ $? -eq "0" ]]; then
      echo "found" | tee -a hnn_docker.log
      prompt_remove_container
    else
      echo "not found" | tee -a hnn_docker.log
    fi

    echo -n "Starting HNN container again... " | tee -a hnn_docker.log
    COMMAND="docker-compose -f $COMPOSE_FILE up --no-recreate"
    run_command
    cleanup 0
  else
    echo "done" | tee -a hnn_docker.log
    cleanup 0
  fi
elif [[ "$ALREADY_RUNNING" -eq "0" ]]; then
  find_existing_container
  if [[ $? -ne "0" ]]; then
    NEW_CONTAINER=1
  fi

  echo -n "Starting HNN container in background... " | tee -a hnn_docker.log
  COMMAND="docker-compose -f $COMPOSE_FILE up -d --no-recreate"
  silent_run_command
  if [[ $? -ne "0" ]]; then
    # try removing container
    echo "failed" | tee -a hnn_docker.log
    echo -n "Looking for old containers..." | tee -a hnn_docker.log
    echo >> hnn_docker.log
    find_existing_container
    if [[ $? -eq "0" ]]; then
      echo "found" | tee -a hnn_docker.log
      prompt_remove_container
    else
      echo "not found" | tee -a hnn_docker.log
    fi

    echo -n "Starting HNN container again in background... " | tee -a hnn_docker.log
    COMMAND="docker-compose -f $COMPOSE_FILE up -d --no-recreate"
    run_command
  else
    echo "done" | tee -a hnn_docker.log
  fi
fi

if [[ ! "$OS" =~ "linux" ]]; then
  copy_security_files
  get_container_port

  if [[ "${DOCKER_TOOLBOX}" -eq "1" ]]; then
    DOCKER_HOST_IP=192.168.99.100
  else
    DOCKER_HOST_IP=localhost
  fi

  ssh_start_hnn
  if [[ $? -ne "0" ]]; then
    echo "failed" | tee -a hnn_docker.log
    echo "Will try to restart HNN container..." | tee -a hnn_docker.log
    prompt_restart_container
    echo -n "Starting HNN container in background... " | tee -a hnn_docker.log
    COMMAND="docker-compose -f $COMPOSE_FILE start"
    run_command
    NEW_CONTAINER=1  # make sure auth files are copied in
    copy_security_files
    get_container_port
    ssh_start_hnn
    fail_on_bad_exit $?
  else
    echo "done" | tee -a hnn_docker.log
    cleanup 0
  fi
fi
