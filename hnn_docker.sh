#!/bin/bash

[[ $TRAVIS_TESTING ]] || TRAVIS_TESTING=0
[[ $VERBOSE ]] || VERBOSE=0
[[ $DEBUG ]] || DEBUG=0

function check_args {
  if [[ $# -ne 3 ]]; then
    echo -e "\nError: $FUNCNAME (L:$LINENO) must have 3 arguments: called from ${FUNCNAME[1]} (L:${BASH_LINENO[1]})" >> hnn_docker.log
    echo "Instead $FUNCNAME (L:$LINENO) has $# arguments: $@" >> hnn_docker.log
    cleanup 1
  fi

  if [[ $2 -ne $3 ]]; then
    if [[ "$3" =~ "1" ]]; then
      echo -e "\nError: ${FUNCNAME[1]} (L:${BASH_LINENO[1]}) must have 1 argument" >> hnn_docker.log
    else
      echo -e "\nError: ${FUNCNAME[1]} (L:${BASH_LINENO[1]}) must have $3 arguments" >> hnn_docker.log
    fi
    cleanup 1
  fi
}

function check_var {
  check_args "$@" $# 1

  if [[ ! -n "\$$1" ]]; then
    echo -e "\nError: ${FUNCNAME[1]} (L:${BASH_LINENO[1]}) expects $1 to be set" >> hnn_docker.log
    cleanup 1
  fi
}

[[ $UID ]] || {
  echo -e "\nError: ${BASH_SOURCE[0]} (L:$BASH_LINENO) expects UID to be set" >> hnn_docker.log
  cleanup 1
}

OS=
UPGRADE=0
STOP=0
START=0
RETRY=0
UNINSTALL=0
if [[ $TRAVIS_TESTING -eq 1 ]]; then
  HNN_DOCKER_IMAGE=jonescompneurolab/hnn:flat
else
  HNN_DOCKER_IMAGE=jonescompneurolab/hnn
fi
HNN_CONTAINER_NAME=hnn_container
HNN_CONTAINER_GROUP=hnn_group
SYSTEM_USER_DIR=$HOME
ALREADY_RUNNING=0
START_SSHD=0
COPY_SSH_FILES=0
ESC_STR="%;"

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

# from @ahendrix: https://gist.github.com/ahendrix/7030300
function errexit() {
  local err=$?
  set +o xtrace
  local code="${1:-1}"
  # Print out the stack trace described by $function_stack
  if [ ${#FUNCNAME[@]} -gt 1 ]
  then
    echo "Call tree:" >> hnn_docker.log
    for ((i=1;i<${#FUNCNAME[@]}-1;i++))
    do
      echo " $i: ${BASH_SOURCE[$i+1]}:${BASH_LINENO[$i]} ${FUNCNAME[$i]}(...)" >> hnn_docker.log
    done
  fi
  echo "Exiting with status ${code}" >> hnn_docker.log
  exit "${code}"
}

function cleanup {
  local __failed=$1

  if [[ "$OS"  =~ "windows" ]]; then
    check_var VCXSRV_PID
    if [ ! -z "${VCXSRV_PID}" ]; then
      echo "Killing VcXsrv PID ${VCXSRV_PID}" >> hnn_docker.log
      kill ${VCXSRV_PID} &> /dev/null
    fi
  fi

  echo -e "cleanup() called from: ${FUNCNAME[1]} (L:${BASH_LINENO[0]})" >> hnn_docker.log
  if [[ $__failed -eq "0" ]]; then
    echo "Script hnn_docker.sh finished successfully" | tee -a hnn_docker.log
    exit 0
  elif [[ $__failed -eq "1" ]]; then
    echo "Error: Script cannot conntinue" | tee -a hnn_docker.log
  elif [[ $__failed -eq "2" ]]; then
    echo "Error: Please see hnn_docker.log for more details"
  fi
  errexit $__failed
}

function cleanup_except_travis {
  check_args "$@" $# 1

  if [[ $TRAVIS_TESTING -eq 1 ]] && [[ "$OS" =~ "windows" ]]; then
    :
  else
    cleanup $1
  fi
}

function silent_run_command {
  check_args "$@" $# 1

  echo -e "Command: $1" >> hnn_docker.log
  $1 >> hnn_docker.log 2>&1
}

function fail_on_bad_exit {
  check_args "$@" $# 1

  local  __statusvar=$1

  if [[ $__statusvar -ne "0" ]]; then
    echo "failed" | tee -a hnn_docker.log
    cleanup 2
  else
    echo "done" | tee -a hnn_docker.log
  fi
}

function fail_on_bad_exit_except_travis {
  check_args "$@" $# 1

  local  __statusvar=$1

  if [[ $__statusvar -ne "0" ]]; then
    echo "failed" | tee -a hnn_docker.log
    cleanup_except_travis 2
  else
    echo "done" | tee -a hnn_docker.log
  fi
}

function run_command {
  check_args "$@" $# 1

  silent_run_command "$1"
  fail_on_bad_exit_except_travis $?
}

function output_run_piped_command {
  local __args=($@)
  local __args_for_check=("${__args[@]}" $# 1)
  local __num_args=4

  if [[ ${#__args[@]} -ne $__num_args ]]; then
    echo -e "\nError: $FUNCNAME (L:${BASH_LINENO[0]]}) has ${#__args[@]} args, must have $__num_args arguments" >> hnn_docker.log
    # cleanup 1
  fi

  local __index
  local __arg
  let __index=0
  for __arg in ${__args[@]}; do
    __args[$__index]=$(echo ${__args[$__index]} | sed "s/$ESC_STR/ /g")
    (( __index++ ))
  done

  local __binary1=${__args[0]}
  local __command_args1=${__args[1]}
  local __binary2=${__args[2]}
  local __command_args2=${__args[3]}
  local __output=
  local __command_status=

  echo "Command: $__binary1 $__command_args1 $__binary2 $__command_args2" >> hnn_docker.log
  __output=$("$__binary1" $__command_args1 | "$__binary2" $__command_args2 2>> hnn_docker.log)
  __command_status=$?
  echo "Output: $__output" >> hnn_docker.log
  echo "$__output"
  if [[ $__command_status -eq 0 ]]; then
    true
  else
    false
  fi
}

function output_run_specific_command {
  local __args=($@)
  local __args_for_check=("${__args[@]}" $# 1)
  local __num_args=2

  if [[ ${#__args[@]} -ne $__num_args ]]; then
    echo -e "\nError: $FUNCNAME (L:${BASH_LINENO[0]}) must have $__num_args arguments" >> hnn_docker.log
    cleanup 1
  fi

  local __index
  local __arg
  let __index=0
  for __arg in ${__args[@]}; do
    __args[$__index]=$(echo ${__args[$__index]} | sed "s/$ESC_STR/ /g")
    (( __index++ ))
  done

  local __binary=${__args[0]}
  local __command_args=${__args[1]}
  local __output=
  local __command_status=

  echo "Command: $__binary $__command_args" >> hnn_docker.log
  __output=$("$__binary" $__command_args 2>> hnn_docker.log)
  __command_status=$?
  echo "Output: $__output" >> hnn_docker.log
  echo "$__output"
  if [[ $__command_status -eq 0 ]]; then
    true
  else
    false
  fi
}

function output_run_command {
  check_args "$@" $# 1

  local __command=$1
  local __output=
  local __command_status=

  echo "Command: $__command" >> hnn_docker.log
  __output=$($__command 2>> hnn_docker.log)
  __command_status=$?
  echo "Output: $__output" >> hnn_docker.log
  echo "$__output"
  if [[ $__command_status -eq "0" ]]; then
    true
  else
    false
  fi
}

function remove_container {
  check_var DOCKER
  run_command "$DOCKER rm -fv $HNN_CONTAINER_NAME"
}

function prompt_remove_container {
  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    echo -n "Removing old container... " | tee -a hnn_docker.log
    echo >> hnn_docker.log
    remove_container
  else
    while true; do
      echo
      read -p "Please confirm that you want to remove the old HNN container? (y/n)" yn
      case $yn in
        [Yy]* ) echo -n "Removing old container... " | tee -a hnn_docker.log
                echo >> hnn_docker.log
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
  check_var DOCKER

  echo -n "Stopping HNN container... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  run_command "$DOCKER stop $HNN_CONTAINER_NAME"
  ALREADY_RUNNING=0
}

function get_container_port {
  check_var DOCKER

  local __index
  local __send_args
  local __command
  local __arg

  echo -n "Looking up port to connect to HNN container... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  __command=("$DOCKER" "port $HNN_CONTAINER_NAME 22")
  let __index=0
  for __arg in "${__command[@]}"; do
    __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
    (( __index++ ))
  done

  PORT_STRING=$(output_run_specific_command "${__send_args[@]}")
  if [[ $? -ne "0" ]]; then
    silent_run_command "$DOCKER restart $HNN_CONTAINER_NAME"
    PORT_STRING=$(output_run_specific_command "${__send_args[@]}")
    if [[ $? -ne "0" ]]; then
      echo "failed" | tee -a hnn_docker.log
      cleanup 2
    fi
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
  check_var DOCKER_TOOLBOX
  check_var SSH_PRIVKEY
  check_var SSH_PORT
  check_var SYSTEM_USER_DIR

  local __command=

  get_container_port

  if [[ "${DOCKER_TOOLBOX}" -eq "1" ]]; then
    __docker_host_ip=192.168.99.100
  else
    __docker_host_ip=localhost
  fi
  export DISPLAY=localhost:0
  export TRAVIS_TESTING
  export SYSTEM_USER_DIR

  echo -n "Starting HNN GUI... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  __command="ssh -o SendEnv=DISPLAY -o SendEnv=SYSTEM_USER_DIR -o SendEnv=TRAVIS_TESTING \
               -o PasswordAuthentication=no -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no \
               -q -T -i $SSH_PRIVKEY -R 6000:localhost:6000 hnn_user@$__docker_host_ip -p $SSH_PORT"
  if [[ $VERBOSE -eq 1 ]]; then
    __command="$__command -v"
  fi
  silent_run_command "$__command"
}

function check_container_sshd {
  check_var DOCKER

  echo -n "Checking if sshd is running in container... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  silent_run_command "$DOCKER exec $HNN_CONTAINER_NAME /home/hnn_user/check_sshd.sh"
  if [[ $? -ne 0 ]]; then
    echo "failed"
    false
  else
    echo "ok"
  fi
}

function get_sshd_log {
  check_var DOCKER

  echo -e "\nLogs from sshd in container: ">> hnn_docker.log
  silent_run_command "$DOCKER exec -d -u root $HNN_CONTAINER_NAME cat /tmp/sshd.log"
}

function prompt_stop_container {
  local __str=

  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    stop_container
    return
  fi

  while true; do
    echo | tee -a hnn_docker.log
    if [[ "$UPGRADE" -eq "1" ]]; then
      __str=" for upgrade"
    else
      __str=
    fi

    read -p "Restart needed$__str. Please confirm that you want to force stopping the HNN container? (y/n)" yn
    case $yn in
        [Yy]* ) stop_container
                break;;
        [Nn]* ) echo "Continuing without restarting container"
                break;;
        * ) echo "Please answer yes or no.";;
    esac
  done
}

function check_for_running_container_command {
  check_var DOCKER

  local __index
  local __send_args
  local __command
  local __arg

  __command=("$DOCKER" ps grep "$HNN_CONTAINER_NAME")
  let __index=0
  for __arg in "${__command[@]}"; do
    __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
    (( __index++ ))
  done
  output_run_piped_command "${__send_args[@]}" > /dev/null
}

function find_existing_container {
  echo -n "Looking for existing containers... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  output_existing_container_command > /dev/null
  if [[ $? -eq "0" ]]; then
    echo "found" | tee -a hnn_docker.log
  else
    echo "not found" | tee -a hnn_docker.log
    false
  fi
}

function output_existing_container_command {
  check_var DOCKER

  local __index
  local __send_args
  local __command
  local __arg

  __command=("$DOCKER" "ps -a" grep "$HNN_CONTAINER_NAME")
  let __index=0
  for __arg in "${__command[@]}"; do
    __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
    (( __index++ ))
  done
  output_run_piped_command "${__send_args[@]}"
}

function copy_ssh_files {
  check_var DOCKER
  check_var SSH_AUTHKEYS
  check_var SSH_PUBKEY

  echo -n "Copying authorized_keys file into container... " | tee -a hnn_docker.log
  $DOCKER cp $SSH_AUTHKEYS $HNN_CONTAINER_NAME:/home/hnn_user/.ssh/authorized_keys >> hnn_docker.log 2>&1
  fail_on_bad_exit_except_travis $?

  echo -n "Copying known_hosts file into container... " | tee -a hnn_docker.log
  $DOCKER cp $SSH_PUBKEY $HNN_CONTAINER_NAME:/home/hnn_user/.ssh/known_hosts >> hnn_docker.log 2>&1
  fail_on_bad_exit_except_travis $?
}

function kill_xquartz {
  echo -n "Stopping XQuartz... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  local __command=
  local __pids=
  local __proc=

  let __retries=5
  while [[ $__retries -gt 0 ]]; do
    pgrep X11.bin > /dev/null 2>&1 || pgrep Xquartz > /dev/null 2>&1 || \
      pgrep quartz-wm > /dev/null 2>&1 || pgrep xinit > /dev/null 2>&1
    if [[ $? -eq 0 ]]; then
      for __proc in "X11.bin" "Xquartz" "quartz-wm" "xinit"; do
        __command="pgrep -d ' ' $__proc"
        __pids=$(output_run_command "$__command")
        if [[ $? -eq 0 ]]; then
          silent_run_command "pkill $__proc"
          if [[ $? -eq 0 ]]; then
            echo "killed $__proc ($__pids)" >> hnn_docker.log
          else
            echo "failed to kill $__proc ($__pids)" >> hnn_docker.log
          fi
        fi
      done
      sleep 1
    else
      break
    fi
    sleep 1
    (( __retries-- ))
  done

  if [[ $__retries -eq 0 ]]; then
    echo "failed" | tee -a hnn_docker.log
    echo "couldn't stop all Xquartz procs after 5 retries" >> hnn_docker.log
    cleanup 2
  else
    echo "done" | tee -a hnn_docker.log
  fi

  if [[ -e /tmp/.X*-lock ]]; then
    echo "Removing locks: $(ls /tmp/.X*-lock)" >> hnn_docker.log
    rm -f /tmp/.X*-lock
  fi
}

function get_xquartz_port {
  local __display_int=
  local __xquartz_display=
  local __timeout=0
  local __retries=0
  local __command=
  local __pid=

  let __timeout=30
  while [[ $__timeout -gt 0 ]]; do
    __command="pgrep Xquartz"
    __pid=$(output_run_command "$__command")
    if [[ $? -eq 0 ]]; then
      if [[ "$__pid" =~ ' ' ]]; then
        echo "Started more than one Xquartz: $__pid" >> hnn_docker.log
        __pid=$(echo $__pid|sed 's/\([0-9]\{1,\}\) [0-9]\{1,\}/\1/')
        echo "Using $__pid" >> hnn_docker.log
      fi
      __xquartz_display=$(ps $__pid|grep $__pid|sed 's/.*\(\:[0-9]\{1,\}\).*/\1/')
      __display_int=$(echo $__xquartz_display|sed 's/\:\([0-9]\{1,\}\)/\1/')
      if [[ -e "/tmp/.X11-unix/X${__display_int}" ]]; then
        echo "Started XQuartz on DISPLAY $__xquartz_display" >> hnn_docker.log
        break
      fi
    fi
    sleep 1
    (( __timeout-- ))
  done

  if [[ $__timeout -eq 0 ]]; then
    if [[ -n $__display_int ]]; then
      echo "/tmp/.X11-unix/X${__display_int} not found" >> hnn_docker.log
    fi
    false
  fi

  echo $__display_int
}

function start_xquartz {
  local __display_int=
  local __command=

  echo -n "Starting XQuartz... " | tee -a hnn_docker.log
  echo >> hnn_docker.log

  __command="open -a XQuartz"
  silent_run_command "$__command"

  __display_int=$(get_xquartz_port)
  if [[ ! $__display_int == "0" ]]; then
    echo "unsupported display :${__display_int}. XQuartz must use :0" | tee -a hnn_docker.log
    false
  fi
  fail_on_bad_exit $?
}

function restart_xquartz {
  kill_xquartz
  start_xquartz
}

function wait_for_container_to_start {
  check_args "$@" $# 1

  check_var DOCKER

  local __timeout=0
  local __started=0

  let __timeout=$1
  while true; do
    check_for_running_container_command
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

function docker_pull {
  check_var DOCKER

  local __command
  local __docker_container
  local __last_used_image
  local __index
  local __send_args
  local __arg

  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    __command="$DOCKER pull --disable-content-trust ${HNN_DOCKER_IMAGE}"
  else
    __command="$DOCKER pull ${HNN_DOCKER_IMAGE}"
  fi

  output_run_command "$__command" > /dev/null
  if [[ $? -eq "0" ]]; then
    echo "done" | tee -a hnn_docker.log
    echo -n "Looking for existing containers... " | tee -a hnn_docker.log
    echo >> hnn_docker.log
    __docker_container=$(output_existing_container_command)
    if [[ $? -eq "0" ]]; then
      __last_used_image=$(echo ${__docker_container}|cut -d' ' -f 2)
      if [[ "${__last_used_image}" =~ "${HNN_DOCKER_IMAGE}" ]]; then
        echo "found, running up to date image" | tee -a hnn_docker.log
        UPGRADE=0
      else
        echo "found, running outdated image" | tee -a hnn_docker.log
        prompt_remove_container
      fi
    else
      echo "not found" | tee -a hnn_docker.log
    fi
    true
  else
    false
  fi
}

function retry_docker_pull {
  local __retry=0
  local __retries

  echo -n "Downloading new HNN image from Docker Hub... " | tee -a hnn_docker.log
  echo >> hnn_docker.log

  let __retries=3
  while [[ $__retry -lt $__retries ]]; do
    docker_pull && break
    if [[ $__retry -eq 0 ]]; then
      echo -n "retry: "
    fi
    (( __retry++ ))
    echo -n "$__retry "
    sleep 1
  done

  if [[ $__retry -eq $__retries ]]; then
    echo "failed" | tee -a hnn_docker.log
    false
  fi

}

function docker_compose_up {
  check_var DOCKER_COMPOSE
  check_var COMPOSE_FILE

  local __timeout=20
  local __started=

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a hnn_docker.log
  fi
  echo -n "Starting HNN container... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  echo -e "Command: ${DOCKER_COMPOSE} --no-ansi -f $COMPOSE_FILE up -d --no-recreate hnn" >> hnn_docker.log
  ${DOCKER_COMPOSE} --no-ansi -f $COMPOSE_FILE up -d --no-recreate hnn 2>&1 | tr -d '\r' >> hnn_docker.log
  if [[ $? -ne 0 ]]; then
    echo "failed" | tee -a hnn_docker.log
    cleanup_except_travis 2
  else
    __started=$(wait_for_container_to_start $__timeout)
    if [[ ! "$__started" =~ "1" ]]; then
      echo "failed" | tee -a hnn_docker.log
      echo "Waited for $__timeout seconds for container to start" >> hnn_docker.log
      false
    else
      echo "done" | tee -a hnn_docker.log
    fi
  fi
}

function print_docker_logs {
  # Not used
  check_var DOCKER

  find_existing_container
  if [[ $? -eq "0" ]]; then
    echo -e "\n Docker logs (100 lines):" >> hnn_docker.log
    $DOCKER logs --tail 100 $HNN_CONTAINER_NAME >> hnn_docker.log 2>&1
    echo >> hnn_docker.log
  fi
}

function create_container {
  check_var DOCKER
  check_var DOCKER_COMPOSE
  check_var DOCKER_FILE

  local __command
  local __index
  local __send_args
  local __arg

  echo -n "Looking for existing images... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  __command=("$DOCKER" images grep "$HNN_DOCKER_IMAGE")
  let __index=0
  for __arg in "${__command[@]}"; do
    __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
    (( __index++ ))
  done

  output_run_piped_command "${__send_args[@]}" > /dev/null
  if [[ $? -ne "0" ]]; then
    echo "not found"
    retry_docker_pull
    if [[ $? -ne "0" ]]; then
      cleanup_except_travis 2
    fi
  else
    echo "found"
  fi

  echo -n "Creating HNN container... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  echo -e "Command: ${DOCKER_COMPOSE} --no-ansi -f $COMPOSE_FILE up --no-start hnn" >> hnn_docker.log
  ${DOCKER_COMPOSE} --no-ansi -f $COMPOSE_FILE up --no-start hnn 2>&1 | tr -d '\r' >> hnn_docker.log
  fail_on_bad_exit_except_travis $?

  if [[ $USE_SSH -eq 1 ]]; then
    copy_ssh_files
  fi
}

function check_docker_machine {
  local __command=
  local __docker_machine=

  if [[ "$OS" =~ "windows" ]]; then
    __command="which docker-machine.exe"
    __docker_machine="docker-machine.exe"
  else
    __command="which docker-machine"
    __docker_machine="docker-machine"
  fi
  silent_run_command "$__command"
  if [[ $? -ne 0 ]]; then
    echo "failed" | tee -a hnn_docker.log
    cleanup 2
  fi
  echo $__docker_machine
}

function get_xauth_keys {
  check_var XAUTH_BIN
  check_var XAUTHORITY
  check_var DISPLAY

  local __command
  local __index
  local __send_args
  local __arg

  __command=("${XAUTH_BIN}" "-f $XAUTHORITY nlist $DISPLAY")
  let __index=0
  for __arg in "${__command[@]}"; do
    __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
    (( __index++ ))
  done
  output_run_specific_command "${__send_args[@]}"
  if [[ $? -eq 0 ]]; then
    true
  else
    false
  fi
}

function start_container_sshd {
  check_var DOCKER

  local __statusvar

  echo -n "Starting sshd in container... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  run_command "$DOCKER exec -d -u root $HNN_CONTAINER_NAME /start_ssh.sh"
  __statusvar=$?
  # allow sshd to start
  sleep 1
  return $__statusvar
}

function check_xauth_bin {
  check_var "XAUTH_BIN"
  check_var "XAUTHORITY"

  local __command
  local __index
  local __send_args
  local __arg

  if [[ -z $XAUTH_BIN ]]; then
    echo -n "Checking for xauth... " | tee -a hnn_docker.log
    echo >> hnn_docker.log
    __command="which xauth"
    XAUTH_BIN=$(output_run_command "$__command")
    fail_on_bad_exit $?
  fi

  echo -n "Checking that $XAUTH_BIN works... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  __command=("${XAUTH_BIN}" version)
  let __index=0
  for __arg in "${__command[@]}"; do
    __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
    (( __index++ ))
  done

  # avoid messages for nonexistent XAUTHORITY
  if [ ! -e "$XAUTHORITY" ]; then
    touch "$XAUTHORITY"
  fi

  # version is already send to hnn_docker.log in output_run_specific_command
  output_run_specific_command "${__send_args[@]}" > /dev/null
  if [[ $? -eq 0 ]]; then
    true
  else
    false
  fi
}

# ******************************************************************
# ********************** Start of main script **********************
# ******************************************************************

if [[ $START -eq "0" ]] && [[ $STOP -eq "0" ]] && [[ $UNINSTALL -eq "0" ]] && [[ $UPGRADE -eq "0" ]]; then
  echo "No valid action provided. Available actions are start, stop, upgrade, and uninstall" | tee -a hnn_docker.log
  cleanup 1
fi

echo -e "\n" >> hnn_docker.log
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
echo >> hnn_docker.log
if [[ "$OS" =~ "windows" ]]; then
  DOCKER="docker.exe"
else
  DOCKER="docker"
fi
silent_run_command "which $DOCKER"
if [[ $? -eq 0 ]]; then
  echo "ok" | tee -a hnn_docker.log
else
  echo "failed" | tee -a hnn_docker.log
  echo "docker could not be found. Please check its installation." | tee -a hnn_docker.log
  cleanup 1
fi

echo -n "Checking if docker-compose is found... " | tee -a hnn_docker.log
echo >> hnn_docker.log
if [[ "$OS" =~ "windows" ]]; then
  DOCKER_COMPOSE="docker-compose.exe"
else
  DOCKER_COMPOSE="docker-compose"
fi
silent_run_command "which $DOCKER_COMPOSE"
if [[ $? -eq 0 ]]; then
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
  DOCKER_MACHINE=$(check_docker_machine)
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
  DOCKER_MACHINE=$(check_docker_machine)
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
    echo >> hnn_docker.log
    run_command "${DOCKER_MACHINE} start"
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
  retry_docker_pull
  if [[ $? -ne "0" ]]; then
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
    echo >> hnn_docker.log
    run_command "${DOCKER_MACHINE} stop"
  fi
  cleanup 0
fi

if [[ "$UNINSTALL" -eq "1" ]]; then
  find_existing_container
  if [[ $? -eq "0" ]]; then
    prompt_remove_container
  fi

  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    echo -n "Removing HNN image... " | tee -a hnn_docker.log
    echo >> hnn_docker.log
    run_command "$DOCKER rmi -f ${HNN_DOCKER_IMAGE}"
    cleanup 0
  fi

  while true; do
    echo
    read -p "Are you sure that you want to remove the HNN image? (y/n)" yn
    case $yn in
      [Yy]* ) echo -n "Removing HNN image... " | tee -a hnn_docker.log
              echo >> hnn_docker.log
              run_command "$DOCKER rmi -f ${HNN_DOCKER_IMAGE}"
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
    echo >> hnn_docker.log
    silent_run_command "cmd.exe //c taskkill //F //IM vcxsrv.exe"
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
    echo "failed" | tee -a hnn_docker.log
    echo "Could not find xauth.exe at ${XAUTH_BIN}. Please set XAUTH_BIN variable at the beginning of this file." | tee -a hnn_docker.log
    cleanup 1
  else
    echo "done" | tee -a hnn_docker.log
  fi
elif [[ "$OS" =~ "mac" ]]; then
  echo -n "Checking if XQuartz is installed... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  silent_run_command "defaults read org.macosforge.xquartz.X11.plist"
  if [[ $? -ne 0 ]]; then
    echo "failed" | tee -a hnn_docker.log
    restart_xquartz
    echo -n "(retry) Checking if XQuartz is installed... " | tee -a hnn_docker.log
    echo >> hnn_docker.log
    silent_run_command "defaults read org.macosforge.xquartz.X11.plist"
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
    echo >> hnn_docker.log
    run_command "defaults write org.macosforge.xquartz.X11.plist nolisten_tcp 0"
  fi

  if [[ "$XQUARTZ_NOAUTH" =~ "1" ]]; then
    NEED_RESTART_XQUARTZ=1
    echo -n "Setting XQuartz preferences to use authentication... " | tee -a hnn_docker.log
    echo >> hnn_docker.log
    run_command "defaults write org.macosforge.xquartz.X11.plist no_auth 0"
  fi

  if [[ "$NEED_RESTART_XQUARTZ" =~ "1" ]]; then
    restart_xquartz
  fi
fi

# check if XAUTHORITY can be used (Linux)
if [[ "$OS" =~ "linux" ]] && [[ -f "$XAUTHORITY" ]]; then
  :
else
  export XAUTHORITY=~/.Xauthority
  if [ -d "$XAUTHORITY" ]; then
    echo -n "Removing misplaced directory $XAUTHORITY... " | tee -a hnn_docker.log
    echo >> hnn_docker.log
    silent_run_command "rmdir $XAUTHORITY"
    echo "done" | tee -a hnn_docker.log
  fi
fi

if [[ ! "$OS" =~ "windows" ]]; then
  # test xauth
  check_xauth_bin
  if [[ $? -ne "0" ]]; then
    echo "failed" | tee -a hnn_docker.log
    if [[ "$OS" =~ "mac" ]]; then
      if [[ ! "${XAUTH_BIN}" =~ "/opt/X11/bin/xauth" ]] &&
        [[ -f "/opt/X11/bin/xauth" ]]; then
        XAUTH_BIN=/opt/X11/bin/xauth
        check_xauth_bin
        fail_on_bad_exit $?
      else
        cleanup 2
      fi
    else
      cleanup 2
    fi
  else
    echo "done" | tee -a hnn_docker.log
  fi
fi

# XAUTH_BIN should be set
if [[ ! -n "${XAUTH_BIN}" ]]; then
  echo "xauth binary could not be located." | tee -a hnn_docker.log
  cleanup 1
fi

# set DISPLAY for generating xauth keys
if [[ "$OS" =~ "windows" ]]; then
  DISPLAY="localhost:0"
elif [[ "$OS" =~ "mac" ]]; then
  DISPLAY=":0"
else
  # linux
  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    [[ $DISPLAY ]] || DISPLAY=":0"
  else
    DISPLAY=":0"
  fi
fi
export DISPLAY

echo -n "Checking for X11 authentication keys... " | tee -a hnn_docker.log
echo >> hnn_docker.log
OUTPUT=$(get_xauth_keys)
if [[ -z $OUTPUT ]]; then
  echo "no valid keys" | tee -a hnn_docker.log

  if [[ "$OS" =~ "mac" ]]; then
    # might be able to fix by restarting xquartz
    echo "XQuartz authentication keys need to be updated" | tee -a hnn_docker.log
    restart_xquartz

    # run xauth again
    echo -n "(retry) Checking for X11 authentication keys... " | tee -a hnn_docker.log
    echo >> hnn_docker.log
    OUTPUT=$(get_xauth_keys)
    if [[ -z $OUTPUT ]]; then
      echo "failed. Error with xauth: no valid keys" | tee -a hnn_docker.log
      cleanup 2
    else
      echo "done" | tee -a hnn_docker.log
    fi
  else
    echo -n "Generating xauth key for display $DISPLAY... " | tee -a hnn_docker.log
    echo >> hnn_docker.log

    __command=("${XAUTH_BIN}" "-f $XAUTHORITY generate $DISPLAY .")
    let __index=0
    for __arg in "${__command[@]}"; do
      __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
      (( __index++ ))
    done
    output_run_specific_command "${__send_args[@]}" > /dev/null
    fail_on_bad_exit_except_travis $?
    echo -n "(retry) Checking for X11 authentication keys... " | tee -a hnn_docker.log
    OUTPUT=$(get_xauth_keys)
    if [[ -z $OUTPUT ]]; then
      echo "warning: couldn't validate xauth keys" | tee -a hnn_docker.log
    else
      echo "done" | tee -a hnn_docker.log
    fi
  fi
else
  echo "done" | tee -a hnn_docker.log
fi

# ignore hostname in Xauthority by setting FamilyWild mask
# https://stackoverflow.com/questions/16296753/can-you-run-gui-applications-in-a-docker-container/25280523#25280523

KEYS_TO_CONVERT=$(echo $OUTPUT | grep -v '^ffff')
if [[ -n $KEYS_TO_CONVERT ]]; then
  echo -n "Updating xauth keys for use with docker... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  echo "Command: \"${XAUTH_BIN}\" nlist :0 | sed -e 's/^..../ffff/' | \"${XAUTH_BIN}\" -f \"$XAUTHORITY\" -b -i nmerge -" >> hnn_docker.log
  OUTPUT=$("${XAUTH_BIN}" nlist :0 | sed -e 's/^..../ffff/' | "${XAUTH_BIN}" -f "$XAUTHORITY" -b -i nmerge - >> hnn_docker.log 2>&1)
  if [[ "$?" -ne "0" ]] || [[ -f "${XAUTHORITY}-n" ]]; then
    echo "failed"
    rm -f "${XAUTHORITY}-n"
    cleanup 2
  fi
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

if [[ $USE_SSH -eq 1 ]]; then
  # set up ssh keys
  SSH_PRIVKEY="./installer/docker/id_rsa_hnn"
  SSH_PUBKEY="./installer/docker/id_rsa_hnn.pub"
  SSH_AUTHKEYS="./installer/docker/authorized_keys"
  if [[ ! -f "$SSH_PRIVKEY" ]] || [[ ! -f "$SSH_PUBKEY" ]] || [[ ! -f "$SSH_AUTHKEYS" ]]; then
    if [[ -f "$SSH_PRIVKEY" ]]; then
      echo -n "Removing $SSH_PRIVKEY... " >> hnn_docker.log
      echo >> hnn_docker.log
      silent_run_command "rm -f $SSH_PRIVKEY"
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
  find "$HOME/hnn_out" -type d -exec chmod o+rwx {} \;  >> hnn_docker.log 2>&1 && \
    find "$HOME/hnn_out" -type f -exec chmod o+rw {} \; >> hnn_docker.log 2>&1 && \
    touch "$HOME/THIS_DIRECTORY_IS_SHARED_BETWEEN_DOCKER_AND_YOUR_OS"
  fail_on_bad_exit $?
fi

echo | tee -a hnn_docker.log
echo "Starting HNN" | tee -a hnn_docker.log
echo "--------------------------------------" | tee -a hnn_docker.log

find_existing_container
if [[ $? -eq "0" ]]; then
  echo -n "Checking for running HNN container... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  check_for_running_container_command
  if [[ $? -eq "0" ]]; then
    echo "found" | tee -a hnn_docker.log
    if [[ "$RESTART_NEEDED" -eq "1" ]]; then
      prompt_stop_container
    else
      ALREADY_RUNNING=1
    fi
  else
    ALREADY_RUNNING=0
    echo "not found" | tee -a hnn_docker.log
  fi
else
  create_container
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

# for some tests, this is as far as we can go
if [[ $TRAVIS_TESTING -eq 1 ]] && ([[ "$OS" =~ "windows" ]] || [[ "$OS" =~ "mac" ]]); then
  echo "Skipping starting the GUI because container can't start in Travis" | tee -a hnn_docker.log
  echo "Travis CI testing finished successfully." | tee -a hnn_docker.log
  cleanup 0
fi

if [[ "$OS" =~ "mac" ]] && [[ $TRAVIS_TESTING -eq 1 ]]; then
  $DOCKER exec -u root $HNN_CONTAINER_NAME mkdir -p $HOME/hnn_out
  $DOCKER exec -u root $HNN_CONTAINER_NAME chown $UID:$HNN_CONTAINER_GROUP $HOME/hnn_out
fi

# set DISPLAY for GUI
if [[ "$OS" =~ "linux" ]]; then
  # linux can use direct port
  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    [[ $DISPLAY ]] || DISPLAY=":0"
  else
    DISPLAY=":0"
  fi
else
  # others need to use IP socket (only :0 is supported)
  DISPLAY="host.docker.internal:0"
fi
export DISPLAY

# start the GUI
if [[ $USE_SSH -eq 0 ]]; then
  echo -n "Starting HNN GUI... " | tee -a hnn_docker.log
  echo >> hnn_docker.log
  run_command "$DOCKER exec -e TRAVIS_TESTING=$TRAVIS_TESTING -e DISPLAY=$DISPLAY -u $UID:$HNN_CONTAINER_GROUP $HNN_CONTAINER_NAME /home/hnn_user/start_hnn.sh"
  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    echo "Testing mode: exited succesfully" | tee -a hnn_docker.log
  fi
else
  # start sshd if running mac or linux
  if [[ $ALREADY_RUNNING -eq 0 ]]; then
    START_SSHD=1
  else
    # container is stull running. check that sshd is running too
    check_container_sshd
    if [[ $? -ne 0 ]]; then
      START_SSHD=1
    fi
  fi

  if [[ $START_SSHD -eq 1 ]]; then
    start_container_sshd
    if [[ $? -ne 0 ]]; then
      get_sshd_log
      cleanup 2
    fi
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
    export DEBUG=1
    start_container_sshd
    if [[ $? -ne 0 ]]; then
      get_sshd_log
      cleanup 2
    fi
    check_container_sshd
    if [[ $? -ne 0 ]]; then
      cleanup 2
      get_sshd_log
    fi
    ssh_start_hnn
    fail_on_bad_exit $?
  else
    echo "done" | tee -a hnn_docker.log
  fi

  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    echo "Testing mode: exited succesfully" | tee -a hnn_docker.log
  fi
fi

cleanup 0
