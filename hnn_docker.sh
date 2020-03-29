#!/bin/bash

[[ $TRAVIS_TESTING ]] || TRAVIS_TESTING=0

return=0

VERBOSE=0
UPGRADE=0
STOP=0
START=0
RETRY=0
UNINSTALL=0
OS=
VCXSRV_PID=
HNN_DOCKER_IMAGE=jonescompneurolab/hnn
DOCKER_STATUS=
ALREADY_RUNNING=0
COPY_SSH_FILES=0
SSH_PORT=
XAUTH_BIN=
TEST_PID=
DOCKER=
DOCKER_MACHINE=
DOCKER_COMPOSE=

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
  local __failed=0
  [[ $1 ]] && __failed=$1

  if [[ "$OS"  =~ "windows" ]] && [ ! -z "${VCXSRV_PID}" ]; then
    echo "Killing VcXsrv PID ${VCXSRV_PID}" >> hnn_docker.log
    kill ${VCXSRV_PID} &> /dev/null
  fi

  if [[ $__failed -eq "0" ]]; then
    echo "Script hnn_docker.sh finished successfully" | tee -a hnn_docker.log
    exit 0
  elif [[ $__failed -eq "1" ]]; then
    echo "Script cannot conntinue" | tee -a hnn_docker.log
  elif [[ $__failed -eq "2" ]]; then
    echo "Please see hnn_docker.log for more details"
  fi
  exit $__failed
}

function cleanup_except_travis {
  if [[ $TRAVIS_TESTING -ne 1 ]]; then
    cleanup $1
  fi
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

function fail_on_bad_exit_except_travis {
  local  __statusvar=$1

  if [[ $__statusvar -ne "0" ]]; then
    echo "failed" | tee -a hnn_docker.log
    cleanup_except_travis 2
  else
    echo "done" | tee -a hnn_docker.log
  fi
}

function run_command {
  silent_run_command
  fail_on_bad_exit $?
}

function remove_container {
  COMMAND="$DOCKER rm -fv hnn_container"
  run_command
}

function prompt_remove_container {
  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    echo -n "Removing old container... " | tee -a hnn_docker.log
    remove_container
  else
    while true; do
      echo
      read -p "Please confirm that you want to remove the old HNN container? (y/n)" yn
      case $yn in
        [Yy]* ) echo -n "Removing old container... " | tee -a hnn_docker.log
                remove_container
                break;;
        [Nn]* ) cleanup 1
                break;;
        * ) echo "Please answer yes or no.";;
      esac
    done
  fi
}

function stop_container {
  echo -n "Stopping HNN container... " | tee -a hnn_docker.log
  COMMAND="$DOCKER stop hnn_container"
  run_command
  ALREADY_RUNNING=0
}

function get_container_port {
  echo -n "Looking up port to connect to HNN container... " | tee -a hnn_docker.log
  PORT_STRING=$($DOCKER port hnn_container 22)
  if [[ $? -ne "0" ]]; then
    COMMAND="$DOCKER restart hnn_container"
    silent_run_command
  fi
  PORT_STRING=$($DOCKER port hnn_container 22)
  if [[ $? -ne "0" ]]; then
    echo "failed" | tee -a hnn_docker.log
    cleanup 2
  fi

  SSH_PORT=$(echo $PORT_STRING| cut -d':' -f 2)
  re='^[0-9]+$'
  if ! [[ $SSH_PORT =~ $re ]] ; then
    echo "failed" | tee -a hnn_docker.log
    cleanup 2
  fi
  echo "done" | tee -a hnn_docker.log
}

function ssh_start_hnn {
  get_container_port
  if [[ "${DOCKER_TOOLBOX}" -eq "1" ]]; then
    DOCKER_HOST_IP=192.168.99.100
  else
    DOCKER_HOST_IP=localhost
  fi

  echo -n "Starting HNN GUI... " | tee -a hnn_docker.log
  COMMAND="ssh -o SendEnv=DISPLAY -o SendEnv=SYSTEM_USER_DIR -o SendEnv=TRAVIS_TESTING \
               -o PasswordAuthentication=no -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no \
               -t -i $SSH_PRIVKEY -R 6000:localhost:6000 hnn_user@$DOCKER_HOST_IP -p $SSH_PORT"
  if [[ $VERBOSE -eq 1 ]]; then
    COMMAND="$COMMAND -v"
  fi
  echo -e "\nCommand: $COMMAND" >> hnn_docker.log
  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    DISPLAY=localhost:0 SYSTEM_USER_DIR=$HOME TRAVIS_TESTING=${TRAVIS_TESTING} $COMMAND \
      >> hnn_docker.log 2>&1 &
    TEST_PID=$!
  else
    DISPLAY=localhost:0 SYSTEM_USER_DIR=$HOME $COMMAND >> hnn_docker.log 2>&1
  fi
}

function prompt_stop_container {
  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    stop_container
    return
  fi

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
  echo -n "Looking for existing containers..." | tee -a hnn_docker.log
  echo -e "\nCommand: $DOCKER ps -a |grep hnn_container" >> hnn_docker.log
  $DOCKER ps -a |grep hnn_container >> hnn_docker.log 2>&1
}

function copy_ssh_files {
  echo -n "Copying authorized_keys file into container... " | tee -a hnn_docker.log
  $DOCKER cp $SSH_AUTHKEYS hnn_container:/home/hnn_user/.ssh/authorized_keys >> hnn_docker.log 2>&1
  fail_on_bad_exit_except_travis $?

  echo -n "Copying known_hosts file into container... " | tee -a hnn_docker.log
  $DOCKER cp $SSH_PUBKEY hnn_container:/home/hnn_user/.ssh/known_hosts >> hnn_docker.log 2>&1
  fail_on_bad_exit_except_travis $?
}

function restart_xquartz {
  local __timeout=0
  local __retries=0

  if [[  $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a hnn_docker.log
  fi
  echo -n "Restarting XQuartz... " | tee -a hnn_docker.log
  echo >> hnn_docker.log

  let __retries=5
  while [[ $__retries -gt 0 ]]; do
    pgrep X11.bin > /dev/null 2>&1 || pgrep Xquartz > /dev/null 2>&1 || \
      pgrep quartz-wm > /dev/null 2>&1 || pgrep xinit > /dev/null 2>&1
    if [[ $? -eq 0 ]]; then
      procs="X11.bin Xquartz quartz-wm xinit"
      PIDS=$(pgrep -d ' ' $procs 2>&1)
      if [[ $? -eq 0 ]]; then
        pkill $procs >> hnn_docker.log 2>&1
        if [[ $? -eq 0 ]]; then
          echo "killed $procs ($CLEANED)" >> hnn_docker.log
        else
          echo "failed to kill $procs ($CLEANED)" >> hnn_docker.log
        fi
      fi
    else
      break
    fi
    sleep 1
    (( __retries-- ))
  done

  if [[ $__retries -eq 0 ]]; then
    echo "couldn't stop all Xquartz procs" >> hnn_docker.log
    cleanup 2
  fi

  if [[ -e /tmp/.X*-lock ]]; then
    echo "Removing locks: $(ls /tmp/.X*-lock)" >> hnn_docker.log
    rm -f /tmp/.X*-lock
  fi

  COMMAND="open -a XQuartz"
  run_command

  echo -n "Waiting for XQuartz to start... " | tee -a hnn_docker.log
  let __timeout=30
  DISPLAY_INT=
  while [[ $__timeout -gt 0 ]]; do
    PID=$(pgrep Xquartz 2> /dev/null)
    if [[ $? -eq 0 ]]; then
      DISPLAY=$(ps $PID|grep -v PID|sed 's/.*\(\:[0-9]\{1,\}\).*/\1/')
      DISPLAY_INT=$(echo $DISPLAY|sed 's/\:\([0-9]\{1,\}\)/\1/')
      if [[ -e "/tmp/.X11-unix/X${DISPLAY_INT}" ]]; then
        echo -e "\nStarted XQuartz on DISPLAY $DISPLAY" >> hnn_docker.log
        break
      fi
    fi
    sleep 1
    (( __timeout-- ))
  done

  if [[ $__timeout -eq 0 ]]; then
    echo "failed" | tee -a hnn_docker.log
    if [[ -n $DISPLAY_INT ]]; then
      echo "/tmp/.X11-unix/X${DISPLAY_INT} not found" >> hnn_docker.log
    fi
    cleanup 2
  else
    echo "done" | tee -a hnn_docker.log
  fi
}

function wait_for_container_to_start {
  local __timeout=0
  local __started=0

  let __timeout=$1
  while true; do
    $DOCKER ps |grep hnn_container | grep Up > /dev/null 2>&1
    if [[ $? -eq 0 ]]; then
      __started="1"
      # make sure GUI (Linux) starts
      sleep 5
      break
    elif [[ $__timeout -eq 0 ]]; then
      break
    fi
    sleep 1
    (( __timeout-- ))
  done

  echo $__started
}

function docker_compose_up {
  if [[  $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a hnn_docker.log
  fi
  echo -n "Starting HNN container... " | tee -a hnn_docker.log
  COMMAND="${DOCKER_COMPOSE} -f $COMPOSE_FILE up -d --no-recreate hnn"
  silent_run_command
  if [[ $? -ne 0 ]]; then
    echo "failed" | tee -a hnn_docker.log
    cleanup_except_travis 2
  else
    TIMEOUT=20
    STARTED=$(wait_for_container_to_start $TIMEOUT)
    if [[ ! "$STARTED" =~ "1" ]]; then
      echo "failed" | tee -a hnn_docker.log
      echo "Waited for $TIMEOUT seconds for container to start" >> hnn_docker.log
      false
    else
      echo "done" | tee -a hnn_docker.log
    fi
  fi
}

function print_docker_logs {
  find_existing_container
  if [[ $? -eq "0" ]]; then
    echo "found" | tee -a hnn_docker.log
    echo -e "\n Docker logs (100 lines):" >> hnn_docker.log
    $DOCKER logs --tail 100  hnn_container >> hnn_docker.log 2>&1
    echo >> hnn_docker.log
  else
    echo "not found" | tee -a hnn_docker.log
  fi
}

function create_container {
  echo -n "Creating HNN container... " | tee -a hnn_docker.log
  if [[ "$OS" =~ "mac" ]]; then
    COMMAND="${DOCKER_COMPOSE} -f $COMPOSE_FILE up --no-start hnn"
  else
    COMMAND="timeout 60 ${DOCKER_COMPOSE} -f $COMPOSE_FILE up --no-start hnn"
  fi
  silent_run_command
  fail_on_bad_exit_except_travis $?

  if [[ $USE_SSH -eq 1 ]]; then
    copy_ssh_files
  fi
}

function check_docker_machine {
  if [[ "$OS" =~ "windows" ]]; then
    COMMAND="which docker-machine.exe"
    silent_run_command
    COMMAND_STATUS=$?
    DOCKER_MACHINE="docker-machine.exe"
  else
    COMMAND="which docker-machine"
    silent_run_command
    COMMAND_STATUS=$?
    DOCKER_MACHINE="docker-machine"
  fi
  if [[ "${COMMAND_STATUS}" -ne "0" ]]; then
    echo "failed" | tee -a hnn_docker.log
    cleanup 2
  fi
}

function get_xauth_keys {
  echo -n "Retrieving current X11 authentication keys... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  echo "Command: ${XAUTH_BIN} -f $XAUTHORITY nlist $DISPLAY" >> hnn_docker.log
  OUTPUT=$("${XAUTH_BIN}" -f "$XAUTHORITY" nlist $DISPLAY 2>> hnn_docker.log)
  echo "Output: $OUTPUT" >> hnn_docker.log
}

if [[ $START -eq "0" ]] && [[ $STOP -eq "0" ]] && [[ $UNINSTALL -eq "0" ]] && [[ $UPGRADE -eq "0" ]]; then
  echo "No valid action provided. Available actions are start, stop, upgrade, and uninstall"
  cleanup 1
fi

echo "Performing pre-checks before starting HNN" | tee -a hnn_docker.log
echo "--------------------------------------" | tee -a hnn_docker.log

echo -n "Checking OS version... " | tee -a hnn_docker.log
OS_OUTPUT=$(uname -a)
if [[ $OS_OUTPUT =~ "MINGW" ]] || [[ $OS_OUTPUT =~ "MSYS" ]]; then
  OS="windows"
elif [[ $OS_OUTPUT =~ "Darwin" ]]; then
  OS="mac"
elif [[ $OS_OUTPUT =~ "Linux" ]]; then
  OS="linux"
fi
echo "$OS" | tee -a hnn_docker.log

# defaults
if [[ "$OS" =~ "linux" ]]; then
  [[ $USE_SSH ]] || USE_SSH=0
else
  [[ $USE_SSH ]] || USE_SSH=1
fi

echo -n "Checking if Docker is installed... " | tee -a hnn_docker.log
if [[ "$OS" =~ "windows" ]]; then
  COMMAND="which docker.exe"
  silent_run_command
  COMMAND_STATUS=$?
  DOCKER="docker.exe"
else
  COMMAND="which docker"
  silent_run_command
  COMMAND_STATUS=$?
  DOCKER="docker"
fi

if [[ "${COMMAND_STATUS}" -eq "0" ]]; then
  echo "ok" | tee -a hnn_docker.log
else
  echo "failed" | tee -a hnn_docker.log
  echo "docker could not be found. Please check its installation." | tee -a hnn_docker.log
  cleanup 1
fi

echo -n "Checking if docker-compose is found... " | tee -a hnn_docker.log
if [[ "$OS" =~ "windows" ]]; then
  COMMAND="which docker-compose.exe"
  silent_run_command
  COMMAND_STATUS=$?
  DOCKER_COMPOSE="docker-compose.exe"
else
  COMMAND="which docker-compose"
  silent_run_command
  COMMAND_STATUS=$?
  DOCKER_COMPOSE="docker-compose"
fi

if [[ "${COMMAND_STATUS}" -eq "0" ]]; then
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
  check_docker_machine
  eval $(${DOCKER_MACHINE} env -u 2> /dev/null)
  eval $(${DOCKER_MACHINE} env 2> /dev/null)
fi

echo -n "Checking if Docker is working... " | tee -a hnn_docker.log
if [[ "$OS" =~ "mac" ]]; then
  DOCKER_OUTPUT=$($DOCKER version 2>> hnn_docker.log)
else
  DOCKER_OUTPUT=$(timeout 5 $DOCKER version 2>> hnn_docker.log)
fi
DOCKER_STATUS=$?
if [[ $DOCKER_STATUS -ne "0" ]] && [[ $TRAVIS_TESTING -eq 1 ]]; then
    echo "failed" | tee -a hnn_docker.log
elif [[ $DOCKER_STATUS -ne "0" ]]; then
  check_docker_machine
  eval $(${DOCKER_MACHINE} env -u 2> /dev/null)
  eval $(${DOCKER_MACHINE} env 2> /dev/null)
  if [[ "$OS" =~ "mac" ]]; then
    DOCKER_OUTPUT=$($DOCKER version 2>> hnn_docker.log)
  else
    DOCKER_OUTPUT=$(timeout 5 $DOCKER version 2>> hnn_docker.log)
  fi

  if [[ "$?" -eq "0" ]]; then
    echo "ok (Docker Toolbox)" | tee -a hnn_docker.log
  else
    echo "failed" | tee -a hnn_docker.log
    echo -n "Starting docker machine... " | tee -a hnn_docker.log
    COMMAND="${DOCKER_MACHINE} start"
    run_command
    # rerun env commands in case IP address changed
    eval $(${DOCKER_MACHINE} env -u 2> /dev/null)
    eval $(${DOCKER_MACHINE} env 2> /dev/null)
    echo -n "Checking again if Docker is working... " | tee -a hnn_docker.log
    echo >> hnn_docker.log
    if [[ "$OS" =~ "mac" ]]; then
      DOCKER_OUTPUT=$($DOCKER version 2>> hnn_docker.log)
    else
      DOCKER_OUTPUT=$(timeout 5 $$DOCKER version 2>> hnn_docker.log)
    fi
    DOCKER_STATUS=$?
    if [[ $DOCKER_STATUS -ne "0" ]]; then
      echo "failed" | tee -a hnn_docker.log
      cleanup 2
    fi
    echo "ok (Docker Toolbox)" | tee -a hnn_docker.log
  fi
elif [[ $? -eq "124" ]]; then
  echo "Error: timed out connecting to Docker. Please check Docker install" | tee -a hnn_docker.log
  cleanup 2
else
  echo "ok${toolbox_str}" | tee -a hnn_docker.log
fi

if  [[ -n "${DOCKER_MACHINE_NAME}" ]]; then
  DOCKER_TOOLBOX=1
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
  cleanup_except_travis 1
fi

if [[ $UPGRADE -eq "1" ]]; then
  echo "Downloading new HNN image from Docker Hub..." | tee -a hnn_docker.log
  $DOCKER pull ${HNN_DOCKER_IMAGE} 2>&1 | tee -a hnn_docker.log
  if [[ $? -eq "0" ]]; then
    DOCKER_CONTAINER=$($DOCKER ps -a |grep hnn_container)
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
  else
    echo "Failed" | tee -a hnn_docker.log
    cleanup_except_travis 2
  fi
  if [[ $START -eq "0" ]]; then
    # just doing upgrade
    cleanup 0
  fi
fi

if [[ "$STOP" -eq "1" ]]; then
  stop_container
  if [[ "${DOCKER_TOOLBOX}" -eq "1" ]]; then
    echo -n "Stopping docker machine... " | tee -a hnn_docker.log
    COMMAND="${DOCKER_MACHINE} stop"
    run_command
  fi
  cleanup 0
fi

if [[ "$UNINSTALL" -eq "1" ]]; then
  find_existing_container
  if [[ $? -eq "0" ]]; then
    echo "found" | tee -a hnn_docker.log
    prompt_remove_container
  else
    echo "not found" | tee -a hnn_docker.log
  fi

  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    echo -n "Removing HNN image... " | tee -a hnn_docker.log
    COMMAND="$DOCKER rmi -f ${HNN_DOCKER_IMAGE}"
    run_command
    cleanup 0
  fi

  while true; do
    echo
    read -p "Are you sure that you want to remove the HNN image? (y/n)" yn
    case $yn in
      [Yy]* ) echo -n "Removing HNN image... " | tee -a hnn_docker.log
              COMMAND="$DOCKER rmi -f ${HNN_DOCKER_IMAGE}"
              run_command
              break;;
      [Nn]* ) cleanup 1
              break;;
      * ) echo "Please answer yes or no.";;
    esac
  done

  cleanup 0
fi

if [[ "$OS" =~ "windows" ]]; then
  echo -n "Checking if VcXsrv is running... " | tee -a hnn_docker.log
  VCXSRV_PID=$(tasklist | grep vcxsrv | awk '{print $2}')
  if [ -n "${VCXSRV_PID}" ]; then
    echo "yes" | tee -a hnn_docker.log
    echo -n "Stopping VcXsrv... " | tee -a hnn_docker.log
    COMMAND="cmd.exe //c taskkill //F //IM vcxsrv.exe >> hnn_docker.log 2>&1"
    silent_run_command
    if [[ $? -ne "0" ]]; then
      echo "failed" | tee -a hnn_docker.log
      echo "WARNING: continuing with existing VcXsrv process. You many need to quit manually for GUI to display"
    else
      echo "done" | tee -a hnn_docker.log
      VCXSRV_PID=
    fi
  else
    echo "no" | tee -a hnn_docker.log
    VCXSRV_PID=
  fi

  VCXSRV_DIR="/c/Program Files/VcXsrv"
  if [ -z "${VCXSRV_PID}" ]; then
    echo -n "Checking if VcXsrv is installed... " | tee -a hnn_docker.log
    if [ -f "${VCXSRV_DIR}/vcxsrv.exe" ]; then
      echo "done" | tee -a hnn_docker.log
    else
      echo "failed. Could not find 'C:\Program Files\VcXsrv'. Please run XLaunch manually" | tee -a hnn_docker.log
      cleanup 1
    fi

    echo -n "Starting VcXsrv... " | tee -a hnn_docker.log
    echo >> hnn_docker.log
    echo "Command: ${VCXSRV_DIR}/vcxsrv.exe -wgl -multiwindow 2>&1 &" >> hnn_docker.log
    "${VCXSRV_DIR}/vcxsrv.exe" -wgl -multiwindow >> hnn_docker.log 2>&1 &
    VCXSRV_PID=$!
    echo "done" | tee -a hnn_docker.log
    echo "Started VcXsrv with PID ${VCXSRV_PID}" >> hnn_docker.log
  fi

  echo -n "Checking for xauth.exe... " | tee -a hnn_docker.log
  [[ ${XAUTH_BIN} ]] || XAUTH_BIN="${VCXSRV_DIR}/xauth.exe"
  if [[ ! -f "${XAUTH_BIN}" ]]; then
    echo "failed." | tee -a hnn_docker.log
    echo "Could not find xauth.exe at ${XAUTH_BIN}. Please set XAUTH_BIN variable at the beginning of this file." | tee -a hnn_docker.log
    cleanup 1
  else
    echo "done" | tee -a hnn_docker.log
  fi
elif [[ "$OS" =~ "mac" ]]; then
  echo -n "Checking if XQuartz is installed... " | tee -a hnn_docker.log
  XQUARTZ_OUTPUT=$(defaults read org.macosforge.xquartz.X11.plist 2>> hnn_docker.log)
  XQUARTZ_STATUS=$?
  if [[ $XQUARTZ_STATUS -ne 0 ]]; then
    echo "failed" | tee -a hnn_docker.log
    restart_xquartz
    echo -n "Checking again if XQuartz is installed... " | tee -a hnn_docker.log
    XQUARTZ_OUTPUT=$(defaults read org.macosforge.xquartz.X11.plist 2>> hnn_docker.log)
    XQUARTZ_STATUS=$?
    fail_on_bad_exit $XQUARTZ_STATUS
  else
    echo "done" | tee -a hnn_docker.log
  fi

  while IFS= read -r line; do
    if [[ $line =~ "no_auth" ]]; then
      XQUARTZ_NOAUTH=$(echo $line | cut -d'=' -f 2| sed 's/^[ \t]*\(.*\);/i\1/')
    elif [[ $line =~ "nolisten_tcp" ]]; then
      XQUARTZ_NOLISTEN=$(echo $line | cut -d'=' -f 2| sed 's/^[ \t]*\(.*\);/i\1/')
    fi
  done <<< "$XQUARTZ_OUTPUT"

  NEED_RESTART_XQUARTZ=0
  if [[ "$XQUARTZ_NOLISTEN" =~ "1" ]]; then
    NEED_RESTART_XQUARTZ=1
    echo -n "Setting XQuartz preferences to listen for network connections... " | tee -a hnn_docker.log
    COMMAND="defaults write org.macosforge.xquartz.X11.plist nolisten_tcp 0"
    run_command
  fi

  if [[ "$XQUARTZ_NOAUTH" =~ "1" ]]; then
    NEED_RESTART_XQUARTZ=1
    echo -n "Setting XQuartz preferences to use authentication... " | tee -a hnn_docker.log
    COMMAND="defaults write org.macosforge.xquartz.X11.plist no_auth 0"
    run_command
  fi

  if [[ "$NEED_RESTART_XQUARTZ" =~ "1" ]]; then
    restart_xquartz
  fi
fi

if [[ "$OS" =~ "mac" ]]; then
  echo -n "Checking for xauth... " | tee -a hnn_docker.log
  echo "Command: which xauth" >> hnn_docker.log
  XAUTH_BIN=$(which xauth 2>> hnn_docker.log)
  COMMAND_STATUS=$?
  echo "Output: $XAUTH_BIN" >> hnn_docker.log
  fail_on_bad_exit $COMMAND_STATUS

  # test xauth
  echo -n "Checking that xauth works... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  echo "Command: ${XAUTH_BIN} info" >> hnn_docker.log
  OUTPUT=$("${XAUTH_BIN}" info 2>> hnn_docker.log)
  COMMAND_STATUS=$?
  echo "Output: $OUTPUT" >> hnn_docker.log

  if [[ $COMMAND_STATUS -ne "0" ]]; then
    echo "failed." | tee -a hnn_docker.log
    if [[ ! "${XAUTH_BIN}" =~ "/opt/X11/bin/xauth" ]] &&
       [[ -f "/opt/X11/bin/xauth" ]]; then
      XAUTH_BIN=/opt/X11/bin/xauth

      echo -n "Instead trying $XAUTH_BIN... " | tee -a hnn_docker.log
      echo >> hnn_docker.log
      echo "Command: ${XAUTH_BIN} info" >> hnn_docker.log
      OUTPUT=$("${XAUTH_BIN}" info 2>> hnn_docker.log)
      COMMAND_STATUS=$?
      echo "Output: $OUTPUT" >> hnn_docker.log
      fail_on_bad_exit $COMMAND_STATUS
    fi
  else
    echo "done." | tee -a hnn_docker.log
  fi
elif [[ "$OS" =~ "linux" ]]; then
  echo -n "Checking for xauth... " | tee -a hnn_docker.log
  echo "Command: which xauth" >> hnn_docker.log
  XAUTH_BIN=$(which xauth 2>> hnn_docker.log)
  COMMAND_STATUS=$?
  echo "Output: $XAUTH_BIN" >> hnn_docker.log
  fail_on_bad_exit $COMMAND_STATUS
fi

# XAUTH_BIN should be set
if [[ ! -n "${XAUTH_BIN}" ]]; then
  echo "xauth binary could not be located." | tee -a hnn_docker.log
  cleanup 1
fi

# check if XAUTHORITY can be used (Linux)
if [[ "$OS" =~ "linux" ]] && [[ -f "$XAUTHORITY" ]]; then
  true
else
  export XAUTHORITY=~/.Xauthority
  if [ -d "$XAUTHORITY" ]; then
    echo -n "Removing misplaced directory $XAUTHORITY... " | tee -a hnn_docker.log
    COMMAND="rmdir $XAUTHORITY"
    silent_run_command
    echo "done" | tee -a hnn_docker.log
  fi
fi

# set DISPLAY
if [[ "$OS" =~ "windows" ]]; then
  DISPLAY="localhost:0"
elif [[ "$OS" =~ "mac" ]]; then
  # DISPLAY may have been modified above
  [[ $DISPLAY ]] || DISPLAY=":0"
else
  # linux
  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    [[ $DISPLAY ]] || DISPLAY=":0"
  else
    DISPLAY=":0"
  fi
fi
export DISPLAY

if [ ! -e "$XAUTHORITY" ]; then
  # handle missing ~/.Xauthority on mac by restarting xquartz
  if [[ ! "$OS" =~ "mac" ]]; then
    echo -n "Generating $XAUTHORITY... " | tee -a hnn_docker.log
    echo >> hnn_docker.log
    echo "Command: ${XAUTH_BIN} -f $XAUTHORITY generate $DISPLAY ." >> hnn_docker.log
    OUTPUT=$("${XAUTH_BIN}" -f "$XAUTHORITY" generate $DISPLAY . >> hnn_docker.log 2>&1)
    COMMAND_STATUS=$?
    echo "Output: $OUTPUT" >> hnn_docker.log
    fail_on_bad_exit_except_travis $COMMAND_STATUS

    if [ ! -e "$XAUTHORITY" ]; then
      echo "Still no .Xauthority file at $XAUTHORITY" | tee -a hnn_docker.log
      cleanup_except_travis 1
    fi
  fi
fi

RETRY=0
get_xauth_keys
if [[ -z $OUTPUT ]]; then
  if [[ "$OS" =~ "mac" ]]; then
    # might be able to fix by restarting xquartz
    echo "failed." | tee -a hnn_docker.log
    echo "XQuartz authentication keys need to be updated" >> tee -a hnn_docker.log
    restart_xquartz

    # run xauth again
    RETRY=1
    get_xauth_keys
    if [[ -z $OUTPUT ]]; then
      echo "failed. Error with xauth: no valid keys" | tee -a hnn_docker.log
      cleanup 2
    else
      echo "done" | tee -a hnn_docker.log
    fi
  elif [[ "$OS" =~ "windows" ]]; then
    echo "warning. Couldn't validate xauth keys" | tee -a hnn_docker.log
  else
    echo "failed. Error with xauth: no valid keys" | tee -a hnn_docker.log
    cleanup 2
  fi
else
  echo "done" | tee -a hnn_docker.log
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

XAUTH_UPDATED=0
# ignore hostname in Xauthority by setting FamilyWild mask
# https://stackoverflow.com/questions/16296753/can-you-run-gui-applications-in-a-docker-container/25280523#25280523

# we can assume ~/.Xauthority exists because xauth nlist was successful
if [ -n "${XAUTH_BIN}" ]; then
  AUTH_KEYS=$("${XAUTH_BIN}" nlist :0 |grep -v '^ffff')
  if [[ -n $AUTH_KEYS ]]; then
    echo -n "Updating Xauthority file... " | tee -a hnn_docker.log
    echo >> hnn_docker.log
    echo "Command: \"${XAUTH_BIN}\" nlist :0 | sed -e 's/^..../ffff/' | \"${XAUTH_BIN}\" -f \"$XAUTHORITY\" -b -i nmerge -" >> hnn_docker.log
    OUTPUT=$("${XAUTH_BIN}" nlist :0 | sed -e 's/^..../ffff/' | "${XAUTH_BIN}" -f "$XAUTHORITY" -b -i nmerge - >> hnn_docker.log 2>&1)
    if [[ "$?" -ne "0" ]] || [[ -f "${XAUTHORITY}-n" ]]; then
      echo "failed"
      rm -f "${XAUTHORITY}-n"
      cleanup 2
    fi
    echo "done" | tee -a hnn_docker.log
    XAUTH_UPDATED=1
  fi
fi

if [[ $USE_SSH -eq 1 ]]; then
  # set up ssh keys
  SSH_PRIVKEY="./installer/docker/id_rsa_hnn"
  SSH_PUBKEY="./installer/docker/id_rsa_hnn.pub"
  SSH_AUTHKEYS="./installer/docker/authorized_keys"
  if [[ ! -f "$SSH_PRIVKEY" ]] || [[ ! -f "$SSH_PUBKEY" ]] || [[ ! -f "$SSH_AUTHKEYS" ]]; then
    if [[ -f "$SSH_PRIVKEY" ]]; then
      echo -n "Removing $SSH_PRIVKEY... " >> hnn_docker.log
      COMMAND="rm -f $SSH_PRIVKEY"
      silent_run_command
      if [[ $? -eq "0" ]]; then
        echo "done" >> hnn_docker.log
      else
        echo "failed" >> hnn_docker.log
        cleanup 2
      fi
    fi
    echo -n "Setting up SSH authentication files... " | tee -a hnn_docker.log
    echo >> hnn_docker.log
    echo "Command: echo -e \"\n\" | ssh-keygen -f $SSH_PRIVKEY -t rsa -N ''" >> hnn_docker.log
    echo -e "\n" | ssh-keygen -f $SSH_PRIVKEY -t rsa -N '' >> hnn_docker.log 2>&1
    if [[ $? -ne "0" ]]; then
      echo "Error: failed running ssh-keygen." | tee -a hnn_docker.log
      cleanup 2
    fi

    echo -n "command=\"/home/hnn_user/start_hnn.sh\" " > "$SSH_AUTHKEYS"
    cat "$SSH_PUBKEY" >> "$SSH_AUTHKEYS"
    echo "done" | tee -a hnn_docker.log
    COPY_SSH_FILES=1
  fi
fi

if [[ "$OS" =~ "linux" ]]; then
  echo -n "Updating permissions of hnn_out... " | tee -a hnn_docker.log
  find "$HOME/hnn_out" -type d -exec chmod o+rwx {} \; && find "$HOME/hnn_out" -type f -exec chmod o+rw {} \;
  fail_on_bad_exit $?
fi

echo | tee -a hnn_docker.log
echo "Starting HNN" | tee -a hnn_docker.log
echo "--------------------------------------" | tee -a hnn_docker.log

echo -n "Checking for running HNN container... " | tee -a hnn_docker.log
$DOCKER ps |grep hnn_container > /dev/null 2>&1
if [[ $? -eq "0" ]]; then
  echo "found" | tee -a hnn_docker.log
  if [[ "$XAUTH_UPDATED" -eq "1" ]]; then
    stop_container
  elif [[ "$RESTART_NEEDED" -eq "1" ]]; then
    prompt_stop_container
  else
    ALREADY_RUNNING=1
  fi
else
  ALREADY_RUNNING=0
  echo "not found" | tee -a hnn_docker.log
  find_existing_container
  if [[ $? -eq "0" ]]; then
    echo "found" | tee -a hnn_docker.log
  else
    echo "not found" | tee -a hnn_docker.log
    create_container
  fi
fi

if [[ $ALREADY_RUNNING -eq 0 ]]; then
  # start the container
  RETRY=0
  docker_compose_up
  if [[ $? -ne 0 ]]; then
    RETRY=1
    # try starting again
    docker_compose_up
    if [[ $? -ne 0 ]]; then
      cleanup 2
    fi
  fi
fi

# for windows and mac, this as far as we can go
if [[ $TRAVIS_TESTING -eq 1 ]] && ([[ "$OS" =~ "windows" ]] || [[ "$OS" =~ "mac" ]]); then
  echo "Skipping starting the GUI because container can't start in Travis" | tee -a hnn_docker.log
  echo "Travis CI testing finished successfully." | tee -a hnn_docker.log
  cleanup 0
fi

# start the GUI
if [[ $USE_SSH -eq 0 ]]; then
  echo -n "Starting HNN GUI... " | tee -a hnn_docker.log
  COMMAND="$DOCKER exec -e TRAVIS_TESTING=$TRAVIS_TESTING hnn_container /home/hnn_user/start_hnn.sh"
  run_command
else
  # start sshd if running linux
  if [[ "$OS" =~ "linux" ]]; then
    COMMAND="$DOCKER exec -d -u root hnn_container /start_ssh.sh"
    run_command
    # allow sshd to start
    sleep 2
  fi

  ssh_start_hnn
  HNN_STATUS=$?
  if [[ ${HNN_STATUS} -ne "0" ]]; then
    echo "failed" | tee -a hnn_docker.log
    stop_container

    # failure could be caused by bad ssh keys
    copy_ssh_files
    docker_compose_up
    if [[ $? -ne 0 ]]; then
      cleanup 2
    fi
    ssh_start_hnn
    fail_on_bad_exit $?
  else
    echo "done" | tee -a hnn_docker.log
  fi
fi

cleanup 0
