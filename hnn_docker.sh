#!/bin/bash

[[ $TRAVIS_TESTING ]] || TRAVIS_TESTING=0
[[ $VERBOSE ]] || VERBOSE=0
[[ $DEBUG ]] || DEBUG=0

function check_args {
  if [[ $# -ne 3 ]]; then
    echo -e "\n=====================" >> hnn_docker.log
    echo "Error: $FUNCNAME (L:$LINENO) must have 3 arguments: called from ${FUNCNAME[1]} (L:${BASH_LINENO[1]})" >> hnn_docker.log
    echo "Instead $FUNCNAME (L:$LINENO) has $# arguments: $@" >> hnn_docker.log
    cleanup 1
  fi

  if [[ $2 -ne $3 ]]; then
    echo -e "\n=====================" >> hnn_docker.log
    if [[ "$3" =~ "1" ]]; then
      echo "Error: ${FUNCNAME[1]} (L:${BASH_LINENO[1]}) must have 1 argument" >> hnn_docker.log
    else
      echo "Error: ${FUNCNAME[1]} (L:${BASH_LINENO[1]}) must have $3 arguments" >> hnn_docker.log
    fi
    cleanup 1
  fi
}

function check_var {
  check_args "$@" $# 1

  if [[ ! -n "\$$1" ]]; then
    echo -e "\n=====================" >> hnn_docker.log
    echo "Error: ${FUNCNAME[1]} (L:${BASH_LINENO[1]}) expects $1 to be set" >> hnn_docker.log
    cleanup 1
  fi
}

[[ $UID ]] || {
  echo -e "\n=====================" >> hnn_docker.log
  echo "Error: ${BASH_SOURCE[0]} (L:$BASH_LINENO) expects UID to be set" >> hnn_docker.log
  cleanup 1
}

OS=
RUN_OPTS=
UPGRADE=0
STOP=0
START=0
RETRY=0
UNINSTALL=0
HNN_DOCKER_IMAGE=jonescompneurolab/hnn
HNN_CONTAINER_NAME=hnn_container
SYSTEM_USER_DIR=$HOME
ALREADY_RUNNING=0
SSHD_STARTED=0
START_SSHD=0
COPY_SSH_FILES=0
NEW_XAUTH_KEYS=0
ESC_STR="%;"

echo -e "======================================"
while [ -n "$1" ]; do
    case "$1" in
    -v) VERBOSE=1 echo -e "Verbose output requested\n" ;;
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
  local err
  local code

  err=$?
  set +o xtrace
  code="${1:-1}"
  # Print out the stack trace described by $function_stack
  if [ ${#FUNCNAME[@]} -gt 1 ]
  then
    echo -e "\n=====================" >> hnn_docker.log
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
  local __failed

  __failed=$1

  echo -e "\n=====================" >> hnn_docker.log
  echo "cleanup() called from: ${FUNCNAME[1]} (L:${BASH_LINENO[0]})" >> hnn_docker.log
  if [[ "$OS"  =~ "windows" ]]; then
    check_var VCXSRV_PID
    stop_vcxsrv
    if [ ! -z "${VCXSRV_PID}" ]; then
      echo "Killing VcXsrv PID ${VCXSRV_PID}" >> hnn_docker.log
      kill ${VCXSRV_PID} &> /dev/null
    fi
  fi

  if [[ $__failed -eq "0" ]]; then
    echo "Script hnn_docker.sh finished successfully" | tee -a hnn_docker.log
    exit 0
  elif [[ $__failed -eq "1" ]]; then
    echo "Error: Script cannot continue" | tee -a hnn_docker.log
  elif [[ $__failed -eq "2" ]]; then
    print_sshd_log
    echo -e "\n======================================"
    echo "Error: Please see hnn_docker.log for more details"
  fi
  errexit $__failed
}

function fail_on_bad_exit {
  check_args "$@" $# 1

  local  __statusvar
  __statusvar=$1

  if [[ $__statusvar -ne "0" ]]; then
    echo "*failed*" | tee -a hnn_docker.log
    cleanup 2
  else
    echo "done" | tee -a hnn_docker.log
  fi
}

function run_command_print_status {
  check_args "$@" $# 1

  silent_run_command "$1"
  if [[ $? -ne "0" ]]; then
    echo "*failed*" | tee -a hnn_docker.log
    false
  else
    echo "done" | tee -a hnn_docker.log
  fi
}

function run_command_print_status_failure_exit {
  check_args "$@" $# 1

  silent_run_command "$1"
  fail_on_bad_exit $?
}

function output_run_piped_command {
  local __args
  local __args_for_check
  local __num_args
  __args=($@)
  __args_for_check=("${__args[@]}" $# 1)
  __num_args=4

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

  local __binary1
  local __command_args1
  local __binary2
  local __command_args2
  local __output
  local __command_status
  __binary1=${__args[0]}
  __command_args1=${__args[1]}
  __binary2=${__args[2]}
  __command_args2=${__args[3]}

  echo -e "\n  ** Command: $__binary1 $__command_args1 | $__binary2 $__command_args2" >> hnn_docker.log
  echo -n "  ** Stderr: " >> hnn_docker.log
  __output=$("$__binary1" $__command_args1 | "$__binary2" $__command_args2 2>> hnn_docker.log)
  __command_status=$?
  if [[ ! -z "$__output" ]]; then
    echo -e "\n  ** Stdout: $__output" | tr -d '\r' >> hnn_docker.log
  fi

  # send output back to caller
  echo "$__output"

  if [[ $__command_status -eq 0 ]]; then
    true
  else
    false
  fi
}

function output_run_specific_command {
  local __args
  local __args_for_check
  local __num_args
  __args=($@)
  __args_for_check=("${__args[@]}" $# 1)
  __num_args=2

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

  local __binary
  local __command_args
  local __output
  local __command_status
  __binary=${__args[0]}
  __command_args=${__args[1]}

  echo -e "\n  ** Command: $__binary $__command_args" >> hnn_docker.log
  echo -n "  ** Stderr: " >> hnn_docker.log
  __output=$("$__binary" $__command_args 2>> hnn_docker.log)
  __command_status=$?
  if [[ -n "$__output" ]]; then
    echo -e "\n  ** Stdout: $__output" | tr -d '\r' >> hnn_docker.log
  fi

  # send output back to caller
  echo "$__output"

  if [[ $__command_status -eq 0 ]]; then
    true
  else
    false
  fi
}

function output_run_command {
  check_args "$@" $# 1

  local __command
  local __output
  local __command_status
  __command=$1

  echo -e "\n  ** Command: $__command" >> hnn_docker.log
  echo -n "  ** Stderr: " >> hnn_docker.log
  __output=$($__command 2>> hnn_docker.log)
  __command_status=$?
  if [[ -n "$__output" ]]; then
    echo -e "\n  ** Stdout: $__output" | tr -d '\r' >> hnn_docker.log
  fi

  # send output back to caller
  echo "$__output"

  if [[ $__command_status -eq "0" ]]; then
    true
  else
    false
  fi
}

function silent_run_command {
  check_args "$@" $# 1
  output_run_command "$1" > /dev/null
}

function remove_container {
  check_var DOCKER
  run_command_print_status_failure_exit "$DOCKER rm -fv $HNN_CONTAINER_NAME"
}

function print_header_message {
  check_args "$@" $# 1

  # first arg is message to print. surrounded by newlines in hnn_docker.log
  echo >> hnn_docker.log
  echo -n "$1" | tee -a hnn_docker.log
  echo >> hnn_docker.log
}

function print_header_message_short {
  check_args "$@" $# 1

  # first arg is message to print. only have newline in front in hnn_docker.log
  echo >> hnn_docker.log
  echo -n "$1" | tee -a hnn_docker.log
}

function stop_vcxsrv {
  print_header_message "Stopping VcXsrv... "
  echo >> hnn_docker.log
  run_command_print_status "cmd.exe //c taskkill //F //IM vcxsrv.exe"
  if [[ $? -eq "0" ]]; then
    VCXSRV_PID=
  fi
}

function prompt_remove_container {
  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    print_header_message "Removing old container... "
    remove_container
  else
    while true; do
      echo
      read -p "Please confirm that you want to remove the old HNN container? (y/n)" yn
      case $yn in
        [Yy]* ) print_header_message "Removing old container... "
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

  print_header_message "Stopping HNN container... "
  run_command_print_status_failure_exit "$DOCKER stop $HNN_CONTAINER_NAME"
  ALREADY_RUNNING=0
}

function get_container_port {
  check_var DOCKER

  local __index
  local __send_args
  local __command
  local __arg
  local __ssh_port
  local __port_string


  if [[ $TRAVIS_TESTING -eq 1 ]] && [[ ! "$OS" =~ "linux" ]]; then
    # this is hardcoded in docker-machine-driver-qemu
    __ssh_port="5000"
  else
    __command=("$DOCKER" "port $HNN_CONTAINER_NAME 22")
    let __index=0
    for __arg in "${__command[@]}"; do
      __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
      (( __index++ ))
    done

    __port_string=$(output_run_specific_command "${__send_args[@]}")
    if [[ $? -ne "0" ]]; then
      echo "failed to run ${__command[@]}" >> hnn_docker.log
      return 1
    fi

    __ssh_port=$(echo $__port_string| cut -d':' -f 2)
    re='^[0-9]+$'
    if ! [[ $__ssh_port =~ $re ]] ; then
      echo "failed to get a port number from \"$__ssh_port\"" >> hnn_docker.log
      return 1
    fi
  fi

  echo $__ssh_port
}

function start_gui {
  # first arg is the command to run to start the GUI (docker exec or ssh)
  check_args "$@" $# 1

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a hnn_docker.
    RETRY=0
  fi
  print_header_message "Starting HNN GUI... "

  MSYS_NO_PATHCONV=1 run_command_print_status "$1"
}

function ssh_start_hnn {
  # no args
  # Will try to ssh into container to start HNN. Designed to be called
  # multiple times beause the function could fail due to trouble
  # getting the container port or the ssh command fails (bad keys maybe).
  check_var DOCKER_TOOLBOX
  check_var DOCKER_HOST
  check_var SSH_PRIVKEY
  check_var SYSTEM_USER_DIR
  check_var ALREADY_RUNNING
  check_var DEBUG
  check_var VERBOSE

  local __command
  local __ssh_port

  if [[ "${DOCKER_TOOLBOX}" -eq "1" ]]; then
    __docker_host_ip=${DOCKER_HOST##*://}
    __docker_host_ip=${__docker_host_ip%:*}
  else
    __docker_host_ip=localhost
  fi

  print_header_message "Looking up port to connect to HNN container... "
  __ssh_port=$(get_container_port)
  if [[ $? -ne 0 ]]; then
    # don't completely crash script here to allow a retry after "docker restart"
    echo "*failed*" | tee -a hnn_docker.log
    return 1
  else
    echo "done" | tee -a hnn_docker.log
  fi

  export DISPLAY=localhost:0
  export XAUTHORITY=/tmp/.Xauthority
  export TRAVIS_TESTING
  export SYSTEM_USER_DIR

  # Start the ssh command that will run start_hnn.sh (limited by /home/hnn_user/.ssh/authorized_keys)
  # on connection it will set up reverse port forwarding between port 6000 on the host OS (where the X
  # server is running) and port 6000 in the container we are ssh'ing into. Other options are to avoid
  # warnings about hostkeychecking and to not prompt for a password if public key authentication fails.
  __command="ssh -o SendEnv=DISPLAY -o SendEnv=XAUTHORITY -o SendEnv=SYSTEM_USER_DIR -o SendEnv=TRAVIS_TESTING \
               -o PasswordAuthentication=no -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no \
               -q -i $SSH_PRIVKEY -R 6000:127.0.0.1:6000 hnn_user@$__docker_host_ip -p $__ssh_port"
  if [[ $VERBOSE -eq 1 ]] || [[ $DEBUG -eq 1 ]]; then
    __command="$__command -vvv"
  fi

  start_gui "$__command"
}

function start_hnn {
  # no args
  # runs start_hnn.sh script directly in container using "docker exec"
  check_var DOCKER
  check_var HNN_CONTAINER_NAME

  local __run_opts
  local __run_command
  local __display

  # set DISPLAY for OS
  __display=$(get_display_for_gui)

  __run_opts="-e SYSTEM_USER_DIR=$HOME -e TRAVIS_TESTING=$TRAVIS_TESTING -e DISPLAY=$__display -u $UID"
  __run_command="$DOCKER exec $__run_opts $HNN_CONTAINER_NAME /home/hnn_user/start_hnn.sh"
  start_gui "$__run_command"
}

function check_sshd_proc {
  # no arguments
  # runs script in container that checks for port 22 open
  check_var DOCKER
  check_var HNN_CONTAINER_NAME
  check_var DOCKER_TOOLBOX

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a hnn_docker.log
    RETRY=0
  fi

  print_header_message "Checking if sshd is running in container... "
  MSYS_NO_PATHCONV=1 run_command_print_status "$DOCKER exec $HNN_CONTAINER_NAME pgrep sshd"
}

function check_hnn_out_perms {
  # no arguments
  # runs script in container that checks permissions for hnn_out are okay
  check_var DOCKER
  check_var HNN_CONTAINER_NAME

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a hnn_docker.log
    RETRY=0
  fi

  print_header_message "Checking permissions of ${HOME}/hnn_out in container... "
  MSYS_NO_PATHCONV=1 run_command_print_status "$DOCKER exec -e SYSTEM_USER_DIR=$HOME $HNN_CONTAINER_NAME /home/hnn_user/check_hnn_out_perms.sh"
  if [[ $? -ne 0 ]]; then
    echo -n "Checking permissions of ${HOME}/hnn_out outside of container... " | tee -a hnn_docker.log
    silent_run_command "test -x ${HOME}/hnn_out" && \
      silent_run_command "test -r ${HOME}/hnn_out" && \
        silent_run_command "test -w ${HOME}/hnn_out"
    if [[ $? -ne 0 ]]; then
      if [[ "$OS" == "linux" ]]; then
        print_header_message "Updating permissions of hnn_out... "
        find "$HOME/hnn_out" -type d -exec chmod o+rwx {} \;  >> hnn_docker.log 2>&1 && \
          find "$HOME/hnn_out" -type f -exec chmod o+rw {} \; >> hnn_docker.log 2>&1
      fi
      echo "failed" | tee -a hnn_docker.log
      echo "Please make ${HOME}/hnn_out accessible by the user running docker (try making world readable/writable)" | tee -a hnn_docker.log

    else
      echo "ok" | tee -a hnn_docker.log
      echo -e "\nFailure seems to be an issue with docker container." | tee -a hnn_docker.log
      echo "Please open an issue on github with hnn_docker.log" | tee -a hnn_docker.log
      echo "https://github.com/jonescompneurolab/hnn/issues" | tee -a hnn_docker.log
    fi
    cleanup 2
  fi

  if [[ $TRAVIS_TESTING -ne 0 ]] || [[ "$OS" == "linux" ]]; then
    # This command will not work when a qemu VM is used with docker-machine.
    # That is, only when TRAVIS_TESTING=1 and (OS="mac" or OS="windows")
    silent_run_command "touch $HOME/hnn_out/THIS_DIRECTORY_IS_SHARED_BETWEEN_DOCKER_AND_YOUR_OS"
  fi
}

function check_x_port_host {
  # no arguments
  # runs script on host to checks that port for $DISPLAY in container
  # is open
  check_var DOCKER
  check_var DISPLAY
  check_var HNN_CONTAINER_NAME

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a hnn_docker.log
    RETRY=0
  fi

  print_header_message "Checking if X server is reachable locally... "
  run_command_print_status "bash installer/docker/check_x_port.sh"
  if [[ $? -ne 0 ]]; then
    if [[ "$OS" == "linux" ]]; then
      X_SERVER="X server"
    elif [[ "$OS" == "mac" ]]; then
      X_SERVER="XQuartz"
    elif [[ "$OS" == "windows" ]]; then
      X_SERVER="VcXsrv"
    fi
    echo -e "\nFailure could be from ${X_SERVER} on the host not allowing TCP connections." | tee -a hnn_docker.log
    cleanup 2
  fi
}

function check_x_port_container {
  # no arguments
  # runs script in container that checks that port for $DISPLAY in container
  # is open
  check_var DOCKER
  check_var HNN_CONTAINER_NAME

  local __display

  # set DISPLAY for OS
  __display=$(get_display_for_gui)

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a hnn_docker.log
    RETRY=0
  fi

  print_header_message "Checking if X server is reachable from container... "
  MSYS_NO_PATHCONV=1 run_command_print_status "$DOCKER exec -e DISPLAY=$__display $HNN_CONTAINER_NAME /check_x_port.sh"
  if [[ $? -ne 0 ]]; then
    check_x_port_host
    if [[ "$OS" == "linux" ]]; then
      X_SERVER="X server"
    elif [[ "$OS" == "mac" ]]; then
      X_SERVER="XQuartz"
    elif [[ "$OS" == "windows" ]]; then
      X_SERVER="VcXsrv"
    fi
    echo -e "\n${X_SERVER} on the host is allowing TCP connections." | tee -a hnn_docker.log
    echo -e "Failure is with opening port up inside container." | tee -a hnn_docker.log
    cleanup 2
  fi
}

function check_sshd_port {
  # no arguments
  # runs script in container that checks for port 22 open
  check_var DOCKER
  check_var HNN_CONTAINER_NAME

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a hnn_docker.log
    RETRY=0
  fi

  print_header_message "Checking if port 22 is open in container... "
  MSYS_NO_PATHCONV=1 run_command_print_status "$DOCKER exec $HNN_CONTAINER_NAME /check_sshd_port.sh"
}


function prompt_stop_container {
  local __str

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
  # no arguments
  # will run "docker ps | grep HNN_CONTAINER_NAME"
  check_var DOCKER

  local __index
  local __send_args
  local __command
  local __arg

  __command=("$DOCKER" ps grep "$HNN_CONTAINER_NAME")

  # prepare command to send as array argument without spaces
  let __index=0
  for __arg in "${__command[@]}"; do
    __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
    (( __index++ ))
  done

  output_run_piped_command "${__send_args[@]}" > /dev/null
}

function find_existing_container {
  print_header_message "Looking for existing containers... "
  output_existing_container_command > /dev/null
  if [[ $? -eq "0" ]]; then
    echo "found" | tee -a hnn_docker.log
  else
    echo "not found" | tee -a hnn_docker.log
    false
  fi
}

function output_existing_container_command {
  # no arguments
  # will run "docker ps -a | grep HNN_CONTAINER_NAME"
  check_var DOCKER

  local __index
  local __send_args
  local __command
  local __arg

  __command=("$DOCKER" "ps -a" grep "$HNN_CONTAINER_NAME")

  # prepare command to send as array argument without spaces
  let __index=0
  for __arg in "${__command[@]}"; do
    __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
    (( __index++ ))
  done

  output_run_piped_command "${__send_args[@]}"
}

function copy_xauthority_file {
  # first argument is username inside container to check permissions for
  # copies ~/.Xauthority (given by $XAUTHORITY) to /tmp/.Xauthority inside
  # container and updates permissions to the specified user
  check_args "$@" $# 1

  check_var DOCKER
  check_var XAUTHORITY
  check_var HNN_CONTAINER_NAME

  local __user
  __user="$1"

  if [ ! -e $XAUTHORITY ]; then
    echo "Couldn't find Xauthority file at $XAUTHORITY"
    cleanup 2
  fi

  print_header_message_short "Copying Xauthority file into container... "
  echo -e "\n  ** Command: $DOCKER cp $XAUTHORITY $HNN_CONTAINER_NAME:/tmp/.Xauthority" >> hnn_docker.log
  run_command_print_status_failure_exit "$DOCKER cp $XAUTHORITY $HNN_CONTAINER_NAME:/tmp/.Xauthority"

  print_header_message "Changing Xauthority permissions in container... "
  echo -e "\n  ** Command: $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c \"chown $__user /tmp/.Xauthority\"" >> hnn_docker.log
  echo -n "  ** Output: " >> hnn_docker.log
  MSYS_NO_PATHCONV=1 $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c "chown $__user /tmp/.Xauthority" >> hnn_docker.log 2>&1
  echo >> hnn_docker.log
  fail_on_bad_exit $?
}

function prepare_user_volumes {
  # copies $PWD to hnn_source_code and sets permissions for hnn_out directory
  # for the appropriate user
  check_var DOCKER
  check_var XAUTHORITY
  check_var HNN_CONTAINER_NAME

  local __user

  if [[ $USE_SSH -eq 0 ]]; then
    __user="$UID"
  else
    __user="hnn_user"
  fi

  if [ ! -e $PWD/hnn.py ]; then
    echo "Bad hnn_source_code directory at $PWD"
    cleanup 2
  fi

  print_header_message "Removing old hnn_source_code from container... "
  echo -e "\n  ** Command: $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c \"rm -rf /home/hnn_user/hnn_source_code\"" >> hnn_docker.log
  echo -n "  ** Output: " >> hnn_docker.log
  MSYS_NO_PATHCONV=1 $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c "rm -rf /home/hnn_user/hnn_source_code" >> hnn_docker.log 2>&1
  fail_on_bad_exit $?

  print_header_message_short "Copying hnn_source_code into container... "
  echo -e "\n  ** Command: $DOCKER cp $PWD $HNN_CONTAINER_NAME:/home/hnn_user/hnn_source_code" >> hnn_docker.log
  run_command_print_status_failure_exit "$DOCKER cp $PWD $HNN_CONTAINER_NAME:/home/hnn_user/hnn_source_code"

  print_header_message "Changing hnn_source_code permissions in container... "
  echo -e "\n  ** Command: $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c \"chown -R $__user /home/hnn_user/hnn_source_code\"" >> hnn_docker.log
  echo -n "  ** Output: " >> hnn_docker.log
  MSYS_NO_PATHCONV=1 $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c "chown -R $__user /home/hnn_user/hnn_source_code" >> hnn_docker.log 2>&1
  fail_on_bad_exit $?

  print_header_message "Changing hnn_out permissions in container... "
  echo -e "\n  ** Command: $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c \"chown $__user $SYSTEM_USER_DIR/hnn_out\"" >> hnn_docker.log
  echo -n "  ** Output: " >> hnn_docker.log
  MSYS_NO_PATHCONV=1 $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c "chown $__user $SYSTEM_USER_DIR/hnn_out" >> hnn_docker.log 2>&1
  fail_on_bad_exit $?
}

function copy_ssh_files {
  check_var DOCKER
  check_var SSH_AUTHKEYS
  check_var SSH_PUBKEY

  print_header_message_short "Copying authorized_keys file into container... "
  echo -e "\n  ** Command: $DOCKER cp $SSH_AUTHKEYS $HNN_CONTAINER_NAME:/home/hnn_user/.ssh/authorized_keys" >> hnn_docker.log
  run_command_print_status_failure_exit "$DOCKER cp $SSH_AUTHKEYS $HNN_CONTAINER_NAME:/home/hnn_user/.ssh/authorized_keys"

  print_header_message_short "Copying known_hosts file into container... "
  echo -e "\n  ** Command: $DOCKER cp $SSH_PUBKEY $HNN_CONTAINER_NAME:/home/hnn_user/.ssh/known_hosts" >> hnn_docker.log
  run_command_print_status_failure_exit "$DOCKER cp $SSH_PUBKEY $HNN_CONTAINER_NAME:/home/hnn_user/.ssh/known_hosts"

  print_header_message_short "Updating permissions on ssh files in container... "
  echo -e "\n  ** Command: $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c \"chown -R hnn_user /home/hnn_user/.ssh\"" >> hnn_docker.log
  echo -n "  ** Output: " >> hnn_docker.log
  MSYS_NO_PATHCONV=1 $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c "chown -R hnn_user /home/hnn_user/.ssh" >> hnn_docker.log 2>&1
  echo >> hnn_docker.log
  fail_on_bad_exit $?
}

function kill_xquartz {
  print_header_message "Stopping XQuartz... "
  local __command
  local __pids
  local __proc

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
    echo "*failed*" | tee -a hnn_docker.log
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
  local __display_int
  local __xquartz_display
  local __timeout
  local __retries
  local __command
  local __pid
  __timeout=0
  __retries=0

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
  local __display_int
  local __command

  print_header_message "Starting XQuartz... "
  __command="open -a XQuartz"
  silent_run_command "$__command"
  if [[ $? -ne "0" ]]; then
    # this probably will never fail on a mac
    echo "*failed*" | tee -a hnn_docker.log
    clenup 2
  fi

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
  # first and only argument is timeout value
  # waiting timeout seconds for "docker ps | grep HNN_CONTAINER_NAME" to succeed
  check_args "$@" $# 1

  local __timeout
  local __started
  __timeout=0
  __started=0

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
  # no arguments
  # will run "docker pull HNN_DOCKER_IMAGE" and remove old container
  # if it was using the old image
  check_var DOCKER

  local __command
  local __docker_container
  local __last_used_image

  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    __command="$DOCKER pull --disable-content-trust ${HNN_DOCKER_IMAGE}"
  else
    __command="$DOCKER pull ${HNN_DOCKER_IMAGE}"
  fi

  silent_run_command "$__command"
  if [[ $? -eq "0" ]]; then
    echo "done" | tee -a hnn_docker.log
    print_header_message "Looking for existing containers... "
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
  local __retry
  local __retries
  __retry=0

  print_header_message "Downloading new HNN image from Docker Hub... "

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
    echo "*failed*" | tee -a hnn_docker.log
    false
  fi
}

function docker_compose_up {
  # no arguments
  # will run the appropriate docker-compose command (either up or run)
  # to leave a running containers
  check_var DOCKER_COMPOSE
  check_var COMPOSE_FILE

  local __timeout
  local __started
  local __command_status
  local __run_opts
  __timeout=20

  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    find_existing_container
    if [[ $? -eq "0" ]]; then
      print_header_message "Removing old container... "
      remove_container
    fi
  fi

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a hnn_docker.log
    RETRY=0
  fi
  print_header_message "Starting HNN container... "

  # Since the default command for the container is sleep infinity, we have
  # to detach the docker-compose command
  __run_opts="-d"

  if [[ "$OS" =~ "windows" ]]; then
    # For windows, we don't want MSYS to mangle paths in environment variables.
    # So we run the docker-compose commands with MSYS_NO_PATHCONV=1. However,
    # this will cause the COMPOSE_FILE path to be in unix format, which will not
    # work for docker-compose. Convert COMPOSE_FILE to windows format with
    # cygpath.exe since MSYS won't do that anymore
    COMPOSE_FILE=$(cygpath.exe -w $COMPOSE_FILE)

    # Interesting that HOME still gets turned into a windows path. Easy to avoid
    # by passing the HOME variable under a new name HOME_UNIX that is used by
    # installer/windows/docker-compose.yml
    export HOME_UNIX=${HOME}
  fi

  if [[ $TRAVIS_TESTING -eq 1 ]] && [[ "$OS" =~ "linux" ]]; then
      # Use docker-compose run for TRAVIS_TESTING=1. This allows volumes to be specified
      # Importantly, the volume containing the current directory is bind mounted into
      # the container and seen as /home/hnn_user/hnn_source_code, which enables tests
      # inside the container to use code which has not yet been merged and been built
      # as part of a container on Docker Hub.

      # Extra options that are missing from sevice configuration by not using "docker-compse up"
      __run_opts+=" --service-ports -v $(pwd):/home/hnn_user/hnn_source_code --name $HNN_CONTAINER_NAME -u root"
      MSYS_NO_PATHCONV=1 silent_run_command "${DOCKER_COMPOSE} --no-ansi -f $COMPOSE_FILE run $__run_opts hnn sleep infinity"
  elif [[ $TRAVIS_TESTING -eq 1 ]] && [[ ! "$OS" =~ "linux" ]]; then
      # This binds port 22 in the container (for sshd) to 5000 on the host, which on docker toolbox
      # is a VM. We can then configure the VM with docker-machine to allow connections to port 5000 from
      # the base OS. Also connect port 6000 to allow for xforwarding of the xserver. 
      __run_opts+=" -p 6000:6000 -p 5000:22 --name $HNN_CONTAINER_NAME -u root"
      MSYS_NO_PATHCONV=1 silent_run_command "${DOCKER_COMPOSE} --no-ansi -f $COMPOSE_FILE run $__run_opts hnn sleep infinity"
  else
    # Otherwise use docker-compose up and rely on docker-compose.yml to specify ports and volumes
    MSYS_NO_PATHCONV=1 silent_run_command "${DOCKER_COMPOSE} --no-ansi -f $COMPOSE_FILE up $__run_opts --no-recreate hnn"
  fi
  if [[ $? -ne 0 ]]; then
    echo "*failed*" | tee -a hnn_docker.log
    cleanup 2
  fi

  # make sure "docker ps | grep HNN_CONTAINER_NAME" succeeeds
  __started=$(wait_for_container_to_start $__timeout)
  if [[ ! "$__started" =~ "1" ]]; then
    echo "*failed*" | tee -a hnn_docker.log
    echo "Waited for $__timeout seconds for container to start" >> hnn_docker.log
    false
  else
    echo "done" | tee -a hnn_docker.log
  fi

  # copy ssh auth files for TRAVIS_TESTING=1
  if [[ $TRAVIS_TESTING -eq 1 ]] && [[ $USE_SSH -eq 1 ]]; then
    copy_ssh_files
  fi
}

function print_sshd_log {
  # no args
  # if sshd has been started and container exists,
  # run "docker logs --tail 100 HNN_CONTAINER_NAME"
  check_var DOCKER
  check_var START_SSHD

  if [[ $SSHD_STARTED -eq 1 ]]; then
    echo -e "\n=====================" >> hnn_docker.log
    echo "Logs from sshd in container: ">> hnn_docker.log
    MSYS_NO_PATHCONV=1 silent_run_command "$DOCKER exec -u root $HNN_CONTAINER_NAME cat /var/log/sshd.log"
  fi
}

function create_container {
  # no arguments
  # if exiting image is not found, it will run docker pull first
  # else it will run "docker-compose up --no-start" to create
  # the container
  check_var DOCKER
  check_var DOCKER_COMPOSE
  check_var DOCKER_FILE
  check_var ALREADY_RUNNING

  local __command
  local __index
  local __send_args
  local __arg

  print_header_message "Looking for existing images... "
  __command=("$DOCKER" images grep "$HNN_DOCKER_IMAGE")

  # prepare command to send as array argument without spaces
  let __index=0
  for __arg in "${__command[@]}"; do
    __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
    (( __index++ ))
  done

  # run "docker images | grep HNN_DOCKER_IMAGE"
  output_run_piped_command "${__send_args[@]}" > /dev/null
  if [[ $? -ne "0" ]]; then
    echo "not found"
    retry_docker_pull
    if [[ $? -ne "0" ]]; then
      cleanup 2
    fi
  else
    echo "found"
  fi

  print_header_message "Creating HNN container... "
  if [[ $TRAVIS_TESTING -eq 1 ]] && [[ ! "$OS" =~ "linux" ]]; then
    echo "Skipping for TRAVIS_TESTING=1" | tee -a hnn_docker.log
    return
  else
    if [[ "$OS" =~ "windows" ]]; then
      # For windows, we don't want MSYS to mangle paths in environment variables.
      # So we run the docker-compose commands with MSYS_NO_PATHCONV=1. However,
      # this will cause the COMPOSE_FILE path to be in unix format, which will not
      # work for docker-compose. Convert COMPOSE_FILE to windows format with
      # cygpath.exe since MSYS won't do that anymore
      COMPOSE_FILE=$(cygpath.exe -w $COMPOSE_FILE)

      # Interesting that HOME still gets turned into a windows path. Easy to avoid
      # by passing the HOME variable under a new name HOME_UNIX that is used by
      # installer/windows/docker-compose.yml
      export HOME_UNIX=${HOME}
    fi

    MSYS_NO_PATHCONV=1 run_command_print_status_failure_exit "${DOCKER_COMPOSE} --no-ansi -f $COMPOSE_FILE up --no-start hnn"
  fi

  # copy ssh auth files if necessary
  if [[ $USE_SSH -eq 1 ]]; then
    copy_ssh_files
  fi
}

function get_docker_machine {
  local __command
  local __docker_machine

  if [[ "$OS" =~ "windows" ]]; then
    __command="which docker-machine.exe"
    __docker_machine="docker-machine.exe"
  else
    __command="which docker-machine"
    __docker_machine="docker-machine"
  fi
  silent_run_command "$__command"
  if [[ $? -ne 0 ]]; then
    echo "*failed*" | tee -a hnn_docker.log
    cleanup 2
  fi
  echo $__docker_machine
}

function get_xauth_keys {
  check_var XAUTH_BIN
  check_var XAUTHORITY
  check_var DISPLAY

  local __binary
  local __command_args
  local __output
  local __command_status
  __binary="${XAUTH_BIN}"
  __command_args="-f $XAUTHORITY nlist $DISPLAY"

  echo -e "\n  ** Command: $__binary $__command_args" >> hnn_docker.log
  echo -n "  ** Stderr: " >> hnn_docker.log
  __output=$("$__binary" $__command_args 2>> hnn_docker.log)
  __command_status=$?

  # don't print keys in log
  if [ -n "$__output" ]; then
    echo "Output: ** suppresed **" >> hnn_docker.log
  else
    echo "Output: " >> hnn_docker.log
  fi
  echo "$__output"
  if [[ $__command_status -eq 0 ]]; then
    true
  else
    false
  fi
}

function start_check_container_sshd {
  # no arguemnts
  # run /start_ssh.sh within container and detach, leaving sshd running
  check_var DOCKER
  check_var HNN_CONTAINER_NAME
  check_var DEBUG

  print_header_message "Starting sshd in container... "
  # using -d to detach, as the sshd command will hold on to the shell and freeze the script
  MSYS_NO_PATHCONV=1 run_command_print_status_failure_exit "$DOCKER exec -d -e DEBUG=$DEBUG -u root $HNN_CONTAINER_NAME /start_ssh.sh"

  # check that sshd is running on container port 22 and fail if not
  check_sshd_port
  if [[ $? -ne 0 ]]; then
    cleanup 2
  fi

  SSHD_STARTED=1
}

function check_xauth_bin {
  # no arguments
  # if "which xauth" succeeds, run "xauth version" to check that it works
  check_var "XAUTH_BIN"
  check_var "XAUTHORITY"

  local __command
  local __index
  local __send_args
  local __arg

  if [[ -z $XAUTH_BIN ]]; then
    print_header_message "Checking for xauth... "
    __command="which xauth"
    XAUTH_BIN=$(output_run_command "$__command")
    fail_on_bad_exit $?
  fi

  print_header_message "Checking that $XAUTH_BIN works... "
  echo >> hnn_docker.log
  __command=("${XAUTH_BIN}" version)

  # prepare command to send as array argument without spaces
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

function get_display_for_gui {
  # no arguments
  # set DISPLAY environment variable for the appropriate OS and/or testing environment
  check_var "DOCKER_TOOLBOX"

  local __display

  # set DISPLAY for GUI
  if [[ "$OS" =~ "linux" ]]; then
    # linux can use direct port
    if [[ $TRAVIS_TESTING -eq 1 ]]; then
      [[ $DISPLAY ]] && __display=$DISPLAY || __display=":0"
    else
      __display=":0"
    fi
  else
    if [[ $TRAVIS_TESTING -eq 1 ]]; then
      # qemu driver
      __display="10.0.2.2:0"
    elif [[ $DOCKER_TOOLBOX -eq 1 ]]; then
      # virtualbox driver
      __display="192.168.99.1:0"
    else
      # docker desktop
      __display="host.docker.internal:0"
    fi
  fi

  echo $__display
}

function silent_check_container_xauth {
  # first argument is username inside container to check permissions for
  # checks that xauth run within container retuns valid keys

  check_args "$@" $# 1

  check_var "DOCKER"
  check_var "HNN_CONTAINER_NAME"

  local __output
  local __command_status
  local __user
  __user="$1"

  echo -e "\n  ** Command: $DOCKER exec -u $__user $HNN_CONTAINER_NAME bash -c \"timeout 5 xauth -ni nlist :0\"" >> hnn_docker.log
  echo -n "  ** Stderr: " >> hnn_docker.log
  __output=$($DOCKER exec -u $__user $HNN_CONTAINER_NAME bash -c "timeout 5 xauth -ni nlist :0" 2>> hnn_docker.log)
  __command_status=$?
  if [[ -n "$__output" ]]; then
    echo -ne "\n  ** Stdout: ** suppresed **" >> hnn_docker.log
  fi
  if [[ $__command_status -ne 0 ]]; then
    return 1
  else
    if [[ -z $__output ]]; then
      # no output means no valid keys
      return 1
    fi
  fi
}

function check_container_xauth {
  # first argument is username inside container to check permissions for
  check_args "$@" $# 1

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a hnn_docker.log
    RETRY=0
  fi

  print_header_message "Checking that xauth works in container... "
  silent_check_container_xauth $1
  if [[ $? -ne 0 ]]; then
    echo "*failed*" | tee -a hnn_docker.log
    false
  else
    echo "ok" | tee -a hnn_docker.log
  fi
}

function setup_xauthority_in_container {
  # no arguments
  # on exit, xauth keys are valid and readable by the appropriate user
  # depending on whether SSH is used
  check_var USE_SSH
  check_var NEW_XAUTH_KEYS

  local __user

  if [[ $USE_SSH -eq 0 ]]; then
    # since connecting directly with some UID,
    # will need xauth to work for that user
    __user="$UID"
  else
    # will need xauth to work for hnn_user via ssh
    __user="hnn_user"
  fi

  if [[ $NEW_XAUTH_KEYS -eq 1 ]]; then
    # definitely need to copy new key
    copy_xauthority_file "$__user"
    # make sure that xauth works in container now
    check_container_xauth "$__user"
    if [[ $? -ne 0 ]]; then
      cleanup 2
    fi
  else
    # maybe xauth already works in container
    silent_check_container_xauth "$__user"
    if [[ $? -ne 0 ]]; then
      # need to copy the key, new or not, because it didn't work
      copy_xauthority_file "$__user"
      # make sure that xauth works in container now
      check_container_xauth "$__user"
      if [[ $? -ne 0 ]]; then
        cleanup 2
      fi
    fi
  fi
}

function set_local_display_for_host {
  # no arguments
  # set DISPLAY for local actions (e.g. generating xauth keys)
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
}

# ******************************************************************
# ********************** Start of main script **********************
# ******************************************************************

if [[ $START -eq "0" ]] && [[ $STOP -eq "0" ]] && [[ $UNINSTALL -eq "0" ]] && [[ $UPGRADE -eq "0" ]]; then
  echo "No valid action provided. Available actions are start, stop, upgrade, and uninstall" | tee -a hnn_docker.log
  cleanup 1
fi

echo >> hnn_docker.log
echo "Performing pre-checks before starting HNN" | tee -a hnn_docker.log
echo "--------------------------------------" | tee -a hnn_docker.log

print_header_message "Checking OS version... "
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

print_header_message "Checking if Docker is installed... "
if [[ "$OS" =~ "windows" ]]; then
  DOCKER="docker.exe"
else
  DOCKER="docker"
fi
run_command_print_status "which $DOCKER"
if [[ $? -ne 0 ]]; then
  echo "docker could not be found. Please check its installation." | tee -a hnn_docker.log
  cleanup 1
fi

print_header_message "Checking if docker-compose is found... "
if [[ "$OS" =~ "windows" ]]; then
  DOCKER_COMPOSE="docker-compose.exe"
else
  DOCKER_COMPOSE="docker-compose"
fi
run_command_print_status "which $DOCKER_COMPOSE"
if [[ $? -ne 0 ]]; then
  echo "docker-compose could not be found. Please make sure it was installed with docker." | tee -a hnn_docker.log
  cleanup 1
fi

DOCKER_TOOLBOX=0
if  [[ -n "${DOCKER_MACHINE_NAME}" ]]; then
  DOCKER_TOOLBOX=1
  toolbox_str=" (Docker Toolbox)"
  DOCKER_MACHINE=$(get_docker_machine)
  eval $(${DOCKER_MACHINE} env -u 2> /dev/null)
  eval $(${DOCKER_MACHINE} env 2> /dev/null)
fi

print_header_message "Checking if Docker is working... "
if [[ "$OS" =~ "mac" ]]; then
  DOCKER_OUTPUT=$($DOCKER version 2>> hnn_docker.log)
else
  DOCKER_OUTPUT=$(timeout 5 $DOCKER version 2>> hnn_docker.log)
fi
DOCKER_STATUS=$?
if [[ $DOCKER_STATUS -ne "0" ]] && [[ $TRAVIS_TESTING -eq 1 ]]; then
    echo "*failed*" | tee -a hnn_docker.log
elif [[ $DOCKER_STATUS -ne "0" ]]; then
  DOCKER_MACHINE=$(get_docker_machine)
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
    echo "*failed*" | tee -a hnn_docker.log
    print_header_message "Starting docker machine... "
    run_command_print_status_failure_exit "${DOCKER_MACHINE} start"
    # rerun env commands in case IP address changed
    eval $(${DOCKER_MACHINE} env -u 2> /dev/null)
    eval $(${DOCKER_MACHINE} env 2> /dev/null)
    print_header_message "Checking again if Docker is working... "
    if [[ "$OS" =~ "mac" ]]; then
      DOCKER_OUTPUT=$($DOCKER version 2>> hnn_docker.log)
    else
      DOCKER_OUTPUT=$(timeout 5 $$DOCKER version 2>> hnn_docker.log)
    fi
    DOCKER_STATUS=$?
    if [[ $DOCKER_STATUS -ne "0" ]]; then
      echo "*failed*" | tee -a hnn_docker.log
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
  cleanup 1
fi

if [[ $UPGRADE -eq "1" ]]; then
  retry_docker_pull
  if [[ $? -ne "0" ]]; then
    cleanup 2
  fi

  if [[ $START -eq "0" ]]; then
    # just doing upgrade
    cleanup 0
  fi
fi

if [[ "$STOP" -eq "1" ]]; then
  stop_container
  if [[ "${DOCKER_TOOLBOX}" -eq "1" ]]; then
    print_header_message "Stopping docker machine... "
    run_command_print_status_failure_exit "${DOCKER_MACHINE} stop"
  fi
  cleanup 0
fi

if [[ "$UNINSTALL" -eq "1" ]]; then
  find_existing_container
  if [[ $? -eq "0" ]]; then
    prompt_remove_container
  fi

  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    print_header_message "Removing HNN image... "
    run_command_print_status_failure_exit "$DOCKER rmi -f ${HNN_DOCKER_IMAGE}"
    cleanup 0
  fi

  while true; do
    echo
    read -p "Are you sure that you want to remove the HNN image? (y/n)" yn
    case $yn in
      [Yy]* ) print_header_message "Removing HNN image... "
              run_command_print_status_failure_exit "$DOCKER rmi -f ${HNN_DOCKER_IMAGE}"
              break;;
      [Nn]* ) cleanup 1
              break;;
      * ) echo "Please answer yes or no.";;
    esac
  done

  cleanup 0
fi

if [[ "$OS" =~ "windows" ]]; then
  print_header_message_short "Checking if VcXsrv is running... "
  VCXSRV_PID=$(tasklist | grep vcxsrv | awk '{print $2}' 2> /dev/null)
  if [ -n "${VCXSRV_PID}" ]; then
    echo -e "\nVcXsrv running with PID $VCXSRV_PID" >> hnn_docker.log
    echo "yes" | tee -a hnn_docker.log
    stop_vcxsrv
    if [[ $? -ne "0" ]]; then
      echo "WARNING: continuing with existing VcXsrv process. You many need to quit manually for GUI to display"
    fi
  else
    echo "no" | tee -a hnn_docker.log
    VCXSRV_PID=
  fi

  VCXSRV_DIR="/c/Program Files/VcXsrv"
  if [ -z "${VCXSRV_PID}" ]; then
    print_header_message_short "Checking if VcXsrv is installed... "
    if [ -f "${VCXSRV_DIR}/vcxsrv.exe" ]; then
      echo "done" | tee -a hnn_docker.log
    else
      echo "failed. Could not find 'C:\Program Files\VcXsrv'. Please run XLaunch manually" | tee -a hnn_docker.log
      cleanup 1
    fi

    print_header_message "Starting VcXsrv... "
    echo -e "\n  ** Command: ${VCXSRV_DIR}/vcxsrv.exe -wgl -multiwindow 2>&1 &" >> hnn_docker.log
    if [[ $DEBUG -eq 1 ]] || [[ $VERBOSE -eq 1 ]]; then
      echo -n "  ** Output: " >> hnn_docker.log
      "${VCXSRV_DIR}/vcxsrv.exe" -wgl -multiwindow >> hnn_docker.log 2>&1 &
    else
      "${VCXSRV_DIR}/vcxsrv.exe" -wgl -multiwindow > /dev/null 2>&1 &
    fi
    VCXSRV_PID=$!
    echo "done" | tee -a hnn_docker.log
    echo "Started VcXsrv with PID ${VCXSRV_PID}" >> hnn_docker.log
  fi

  print_header_message_short "Checking for xauth.exe... "
  [[ ${XAUTH_BIN} ]] || XAUTH_BIN="${VCXSRV_DIR}/xauth.exe"
  if [[ ! -f "${XAUTH_BIN}" ]]; then
    echo "*failed*" | tee -a hnn_docker.log
    echo "Could not find xauth.exe at ${XAUTH_BIN}. Please set XAUTH_BIN variable at the beginning of this file." | tee -a hnn_docker.log
    cleanup 1
  else
    echo "done" | tee -a hnn_docker.log
  fi
elif [[ "$OS" =~ "mac" ]]; then
  print_header_message "Checking if XQuartz is configured... "
  XQUARTZ_OUTPUT=$(output_run_command "defaults read org.macosforge.xquartz.X11.plist")
  if [[ $? -ne 0 ]]; then
    echo "*failed*" | tee -a hnn_docker.log
    restart_xquartz
    print_header_message "(retry) Checking if XQuartz is configured... "
    XQUARTZ_OUTPUT=$(output_run_command "defaults read org.macosforge.xquartz.X11.plist")
    fail_on_bad_exit $?
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
    print_header_message "Setting XQuartz preferences to listen for network connections... "
    run_command_print_status_failure_exit "defaults write org.macosforge.xquartz.X11.plist nolisten_tcp 0"
  fi

  if [[ "$XQUARTZ_NOAUTH" =~ "1" ]]; then
    NEED_RESTART_XQUARTZ=1
    print_header_message "Setting XQuartz preferences to use authentication... "
    run_command_print_status_failure_exit "defaults write org.macosforge.xquartz.X11.plist no_auth 0"
  fi

  if [[ "$NEED_RESTART_XQUARTZ" =~ "1" ]]; then
    restart_xquartz
  fi
fi

# should have X server running by now
set_local_display_for_host

# can now use DISPLAY variable
check_x_port_host

# check if XAUTHORITY can be used (Linux)
if [[ "$OS" =~ "linux" ]] && [[ -f "$XAUTHORITY" ]]; then
  :
else
  export XAUTHORITY=~/.Xauthority
  if [ -d "$XAUTHORITY" ]; then
    print_header_message "Removing misplaced directory $XAUTHORITY... "
    run_command_print_status_failure_exit "rmdir $XAUTHORITY"
  fi
fi

if [[ ! "$OS" =~ "windows" ]]; then
  # test xauth
  check_xauth_bin
  if [[ $? -ne "0" ]]; then
    echo "*failed*" | tee -a hnn_docker.log
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

print_header_message "Checking for X11 authentication keys... "
OUTPUT=$(get_xauth_keys)
if [[ -z $OUTPUT ]]; then
  echo "no valid keys" | tee -a hnn_docker.log
  NEW_XAUTH_KEYS=1
  if [[ "$OS" =~ "mac" ]]; then
    # might be able to fix by restarting xquartz
    echo "XQuartz authentication keys need to be updated" | tee -a hnn_docker.log
    restart_xquartz

    # run xauth again
    print_header_message "(retry) Checking for X11 authentication keys... "
    OUTPUT=$(get_xauth_keys)
    if [[ -z $OUTPUT ]]; then
      echo "failed. Error with xauth: no valid keys" | tee -a hnn_docker.log
      cleanup 2
    else
      echo "done" | tee -a hnn_docker.log
    fi
  else
    print_header_message "Generating xauth key for display $DISPLAY... "
    echo >> hnn_docker.log

    __command=("${XAUTH_BIN}" "-f $XAUTHORITY generate $DISPLAY .")
    let __index=0
    for __arg in "${__command[@]}"; do
      __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
      (( __index++ ))
    done
    output_run_specific_command "${__send_args[@]}" > /dev/null
    fail_on_bad_exit $?
    print_header_message "(retry) Checking for X11 authentication keys... "
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
  print_header_message "Updating xauth keys for use with docker... "
  echo -e "\n  ** Command: \"${XAUTH_BIN}\" nlist $DISPLAY | sed -e 's/^..../ffff/' | \"${XAUTH_BIN}\" -f \"$XAUTHORITY\" -b -i nmerge -" >> hnn_docker.log
  echo -n "  ** Output: " >> hnn_docker.log
  "${XAUTH_BIN}" nlist $DISPLAY | sed -e 's/^..../ffff/' | "${XAUTH_BIN}" -f "$XAUTHORITY" -b -i nmerge - >> hnn_docker.log 2>&1
  if [[ "$?" -ne "0" ]] || [[ -f "${XAUTHORITY}-n" ]]; then
    echo "*failed*" | tee -a hnn_docker.log
    rm -f "${XAUTHORITY}-n"
    cleanup 2
  fi
  echo "done" | tee -a hnn_docker.log
fi

print_header_message_short "Locating HNN source code... "
# find the source code directory
CWD=$(pwd)

if [[ "$OS" =~ "linux" ]]; then
  COMPOSE_FILE="$CWD/installer/docker/docker-compose.yml"
else
  COMPOSE_FILE="$CWD/installer/$OS/docker-compose.yml"
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "*failed*"
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
      print_header_message "Removing $SSH_PRIVKEY... "
      run_command_print_status_failure_exit "rm -f $SSH_PRIVKEY"
    fi
    print_header_message "Setting up SSH authentication files... "
    echo -e "\n  ** Command: echo -e \"\n\" | ssh-keygen -f $SSH_PRIVKEY -t rsa -N ''" >> hnn_docker.log
    echo -n "  ** Output: " >> hnn_docker.log
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

echo | tee -a hnn_docker.log
echo "Starting HNN" | tee -a hnn_docker.log
echo "--------------------------------------" | tee -a hnn_docker.log

# check if container exists
output_existing_container_command > /dev/null
if [[ $? -eq "0" ]]; then
  # container does exist, so check if it is running
  print_header_message "Checking for running HNN container... "
  check_for_running_container_command
  if [[ $? -eq "0" ]]; then
    echo "found" | tee -a hnn_docker.log
    ALREADY_RUNNING=1
  else
    ALREADY_RUNNING=0
    echo "not found" | tee -a hnn_docker.log
  fi
else
  # container doesn't exist, so go ahead and create it
  create_container
  ALREADY_RUNNING=0
fi
# Container exists if not TRAVIS_TESTING=1. If TRAVIS_TESTING=1, the image has just been pulled.
# The reason for this separation is to use the retry mechanism in retry_docker_pull since
# qemu virtualized docker on Travis with docker toolbox is slow and prone to failures.

if [[ $ALREADY_RUNNING -eq 0 ]]; then
  # start the container
  docker_compose_up
  if [[ $? -ne 0 ]]; then
    RETRY=1
    # try starting again
    docker_compose_up
    if [[ $? -ne 0 ]]; then
      cleanup 2
    fi
  fi
  # container is up

  # Workaround because in the qemu docker-machine (used with mac and windows).
  # volume mounts don't work (hnn_out and hnn_source_code).
  if [[ $TRAVIS_TESTING -eq 1 ]] && [[ ! "$OS" =~ "linux" ]]; then
    prepare_user_volumes
  fi
fi

setup_xauthority_in_container
# xauth is good

check_hnn_out_perms
# can read/write to hnn_out directory

if [[ $USE_SSH -eq 0 ]]; then
  # start the GUI without SSH

  check_x_port_container
  # x port is reachable via TCP

  # start the GUI
  start_hnn
else
  if [[ $ALREADY_RUNNING -eq 0 ]]; then
    # need to start sshd
    start_check_container_sshd
  else
    # container is still running. check that sshd is running too
    check_sshd_port
    if [[ $? -ne 0 ]]; then
      start_check_container_sshd
    fi
  fi
  # sshd is working with container

  # start the GUI with SSH (will confirm that X server port is open)
  # a failure wi
  ssh_start_hnn
  if [[ $? -ne 0 ]]; then
    # failure could be caused by bad ssh keys
    copy_ssh_files

    RETRY=1
    DEBUG=1
    # start the GUI
    ssh_start_hnn
    if [[ $? -ne 0 ]]; then
      cleanup 2
    fi
  fi
fi

if [[ $TRAVIS_TESTING -eq 1 ]]; then
  echo "Testing mode: exited succesfully" | tee -a hnn_docker.log
fi

## DONE! all successful cases reach here
cleanup 0
