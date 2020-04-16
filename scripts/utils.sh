function check_args {
  # does not depend on any functions

  if [[ ! -n "LOGFILE" ]]; then
    echo -e "\n====================="
    echo "Error: ${FUNCNAME[1]} (L:${BASH_LINENO[1]}) expects LOGFILE to be set"
    cleanup 1
  fi

  if [[ $# -ne 3 ]]; then
    echo -e "\n=====================" >> $LOGFILE
    echo "Error: $FUNCNAME (L:$LINENO) must have 3 arguments: called from ${FUNCNAME[1]} (L:${BASH_LINENO[1]})" >> $LOGFILE
    echo "Instead $FUNCNAME (L:$LINENO) has $# arguments: $@" >> $LOGFILE
    cleanup 1
  fi

  if [[ $2 -ne $3 ]]; then
    echo -e "\n=====================" >> $LOGFILE
    if [[ "$3" =~ "1" ]]; then
      echo "Error: ${FUNCNAME[1]} (L:${BASH_LINENO[1]}) must have 1 argument" >> $LOGFILE
    else
      echo "Error: ${FUNCNAME[1]} (L:${BASH_LINENO[1]}) must have $3 arguments" >> $LOGFILE
    fi
    cleanup 1
  fi
}

function check_var {
  check_args "$@" $# 1
  if [[ ! -n $(eval echo \$$1) ]]; then
    echo -e "\n=====================" | tee -a $LOGFILE
    echo "Error: ${FUNCNAME[1]} (L:${BASH_LINENO[1]}) expects $1 to be set" | tee -a $LOGFILE
    cleanup 1
  fi
}

function get_os {
  OS_OUTPUT=$(uname -a)
  if [[ $OS_OUTPUT =~ "MINGW" ]] || [[ $OS_OUTPUT =~ "MSYS" ]]; then
    OS="windows"
  elif [[ $OS_OUTPUT =~ "Darwin" ]]; then
    OS="mac"
  elif [[ $OS_OUTPUT =~ "Linux" ]]; then
    OS="linux"
  fi
  echo $OS
}

function set_globals {
  check_var LOGFILE

  print_header_message "Checking OS version... "
  OS=$(get_os)
  echo "$OS" | tee -a $LOGFILE

  # defaults
  if [[ "$OS" =~ "linux" ]]; then
    [[ $USE_SSH ]] || USE_SSH=0
  else
    [[ $USE_SSH ]] || USE_SSH=1
  fi

  # globals
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
  NEW_XAUTH_KEYS=0
  ESC_STR="%;"

  export OS USE_SSH UPGRADE STOP START RETRY UNINSTALL HNN_DOCKER_IMAGE HNN_CONTAINER_NAME SYSTEM_USER_DIR ALREADY_RUNNING SSHD_STARTED NEW_XAUTH_KEYS ESC_STR
}

function errexit() {
  # from @ahendrix: https://gist.github.com/ahendrix/7030300
  check_var LOGFILE

  local __err
  local __code
  local __i

  __err=$?
  set +o xtrace
  __code="${1:-1}"
  # Print out the stack trace described by $function_stack
  if [ ${#FUNCNAME[@]} -gt 1 ]
  then
    echo -e "\n=====================" >> $LOGFILE
    echo "Call tree:" >> $LOGFILE
    for ((__i=1;__i<${#FUNCNAME[@]}-1;__i++)); do
      echo " $__i: ${BASH_SOURCE[$i+1]}:${BASH_LINENO[$i]} ${FUNCNAME[$i]}(...)" >> $LOGFILE
    done
  fi
  echo "Exiting with status ${__code}" >> $LOGFILE
  exit "${__code}"
}

function cleanup {
  check_var LOGFILE

  local __failed

  __failed=$1

  echo -e "\n=====================" >> $LOGFILE
  echo "cleanup() called from: ${FUNCNAME[1]} (L:${BASH_LINENO[0]})" >> $LOGFILE
  if [ ! -z "${VCXSRV_PID}" ]; then
    stop_vcxsrv
    if [[ $? -ne 0 ]]; then
      echo "Killing VcXsrv PID ${VCXSRV_PID}" >> $LOGFILE
      kill ${VCXSRV_PID} &> /dev/null
    fi
  fi

  if [[ $__failed -eq "0" ]]; then
    echo "Script hnn_docker.sh finished successfully" | tee -a $LOGFILE
    exit 0
  elif [[ $__failed -eq "1" ]]; then
    echo "Error: Script cannot continue" | tee -a $LOGFILE
  elif [[ $__failed -eq "2" ]]; then
    print_sshd_log
    echo -e "\n======================================"
    echo "Error: Please see $LOGFILE for more details"
  fi
  errexit $__failed
}

function fail_on_bad_exit {
  check_var LOGFILE

  check_args "$@" $# 1

  local  __statusvar
  __statusvar=$1

  if [[ $__statusvar -ne "0" ]]; then
    echo "*failed*" | tee -a $LOGFILE
    cleanup 2
  else
    echo "done" | tee -a $LOGFILE
  fi
}

function run_command_print_status {
  check_var LOGFILE

  check_args "$@" $# 1

  silent_run_command "$1"
  if [[ $? -ne "0" ]]; then
    echo "*failed*" | tee -a $LOGFILE
    false
  else
    echo "done" | tee -a $LOGFILE
  fi
}

function run_command_print_status_failure_exit {
  check_args "$@" $# 1

  silent_run_command "$1"
  fail_on_bad_exit $?
}

function output_run_piped_command {
  check_var LOGFILE
  check_var ESC_STR

  local __args
  local __args_for_check
  local __num_args
  __args=($@)
  __args_for_check=("${__args[@]}" $# 1)
  __num_args=4

  if [[ ${#__args[@]} -ne $__num_args ]]; then
    echo -e "\nError: $FUNCNAME (L:${BASH_LINENO[0]]}) has ${#__args[@]} args, must have $__num_args arguments" >> $LOGFILE
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

  echo -e "\n  ** Command: $__binary1 $__command_args1 | $__binary2 $__command_args2" >> $LOGFILE
  echo -n "  ** Stderr: " >> $LOGFILE
  __output=$("$__binary1" $__command_args1 | "$__binary2" $__command_args2 2>> $LOGFILE)
  __command_status=$?
  if [[ ! -z "$__output" ]]; then
    echo -e "\n  ** Stdout: $__output" | tr -d '\r' >> $LOGFILE
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
  check_var LOGFILE
  check_var ESC_STR

  local __args
  local __args_for_check
  local __num_args
  __args=($@)
  __args_for_check=("${__args[@]}" $# 1)
  __num_args=2

  if [[ ${#__args[@]} -ne $__num_args ]]; then
    echo -e "\nError: $FUNCNAME (L:${BASH_LINENO[0]}) must have $__num_args arguments" >> $LOGFILE
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

  echo -e "\n  ** Command: $__binary $__command_args" >> $LOGFILE
  echo -n "  ** Stderr: " >> $LOGFILE
  __output=$("$__binary" $__command_args 2>> $LOGFILE)
  __command_status=$?
  if [[ -n "$__output" ]]; then
    echo -e "\n  ** Stdout: $__output" | tr -d '\r' >> $LOGFILE
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

  check_var LOGFILE

  local __command
  local __output
  local __command_status
  __command=$1

  echo -e "\n  ** Command: $__command" >> $LOGFILE
  echo -n "  ** Stderr: " >> $LOGFILE
  __output=$($__command 2>> $LOGFILE)
  __command_status=$?
  if [[ -n "$__output" ]]; then
    echo -e "\n  ** Stdout: $__output" | tr -d '\r' >> $LOGFILE
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
  check_var HNN_CONTAINER_NAME

  run_command_print_status_failure_exit "$DOCKER rm -fv $HNN_CONTAINER_NAME"
}

function print_header_message {
  check_args "$@" $# 1
  check_var LOGFILE

  # first arg is message to print. surrounded by newlines in $LOGFILE
  echo >> $LOGFILE
  echo -n "$1" | tee -a $LOGFILE
  echo >> $LOGFILE
}

function print_header_message_short {
  check_args "$@" $# 1
  check_var LOGFILE

  # first arg is message to print. only have newline in front in $LOGFILE
  echo >> $LOGFILE
  echo -n "$1" | tee -a $LOGFILE
}

function stop_vcxsrv {
  check_var LOGFILE

  print_header_message "Stopping VcXsrv... "
  echo >> $LOGFILE
  run_command_print_status "cmd.exe //c taskkill //F //IM vcxsrv.exe"
  if [[ $? -eq "0" ]]; then
    VCXSRV_PID=
  else
    false
  fi
}

function prompt_remove_container {
  check_var TRAVIS_TESTING

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
  check_var HNN_CONTAINER_NAME
  check_var ALREADY_RUNNING

  print_header_message "Stopping HNN container... "
  run_command_print_status_failure_exit "$DOCKER stop $HNN_CONTAINER_NAME"
  ALREADY_RUNNING=0
}

function get_container_port {
  check_var LOGFILE
  check_var HNN_CONTAINER_NAME
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
      echo "failed to run ${__command[@]}" >> $LOGFILE
      return 1
    fi

    __ssh_port=$(echo $__port_string| cut -d':' -f 2)
    re='^[0-9]+$'
    if ! [[ $__ssh_port =~ $re ]] ; then
      echo "failed to get a port number from \"$__ssh_port\"" >> $LOGFILE
      return 1
    fi
  fi

  echo $__ssh_port
}

function start_gui {
  check_var LOGFILE
  check_var RETRY

  # first arg is the command to run to start the GUI (docker exec or ssh)
  check_args "$@" $# 1

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a $LOGFILE
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
  check_var SSH_PRIVKEY
  check_var SYSTEM_USER_DIR
  check_var ALREADY_RUNNING
  check_var DEBUG
  check_var VERBOSE
  check_var LOGFILE

  local __command
  local __ssh_port

  if [[ "${DOCKER_TOOLBOX}" -eq "1" ]]; then
    check_var DOCKER_HOST

    __docker_host_ip=${DOCKER_HOST##*://}
    __docker_host_ip=${__docker_host_ip%:*}
  else
    __docker_host_ip=localhost
  fi

  print_header_message "Looking up port to connect to HNN container... "
  __ssh_port=$(get_container_port)
  if [[ $? -ne 0 ]]; then
    # don't completely crash script here to allow a retry after "docker restart"
    echo "*failed*" | tee -a $LOGFILE
    return 1
  else
    echo "done" | tee -a $LOGFILE
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
    __command="$__command -v"
  fi

  start_gui "$__command"
}

function start_hnn {
  # no args
  # runs start_hnn.sh script directly in container using "docker exec"
  check_var DOCKER
  check_var TRAVIS_TESTING
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
  check_var RETRY

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a $LOGFILE
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
  check_var TRAVIS_TESTING
  check_var LOGFILE
  check_var RETRY

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a $LOGFILE
    RETRY=0
  fi

  print_header_message "Checking permissions of ${HOME}/hnn_out in container... "
  MSYS_NO_PATHCONV=1 run_command_print_status "$DOCKER exec -e SYSTEM_USER_DIR=$HOME $HNN_CONTAINER_NAME /home/hnn_user/check_hnn_out_perms.sh"
  if [[ $? -ne 0 ]]; then
    echo -n "Checking permissions of ${HOME}/hnn_out outside of container... " | tee -a $LOGFILE
    silent_run_command "test -x ${HOME}/hnn_out" && \
      silent_run_command "test -r ${HOME}/hnn_out" && \
        silent_run_command "test -w ${HOME}/hnn_out"
    if [[ $? -ne 0 ]]; then
      if [[ "$OS" == "linux" ]]; then
        print_header_message "Updating permissions of hnn_out... "
        find "$HOME/hnn_out" -type d -exec chmod o+rwx {} \;  >> $LOGFILE 2>&1 && \
          find "$HOME/hnn_out" -type f -exec chmod o+rw {} \; >> $LOGFILE 2>&1
      fi
      echo "failed" | tee -a $LOGFILE
      echo "Please make ${HOME}/hnn_out accessible by the user running docker (try making world readable/writable)" | tee -a $LOGFILE

    else
      echo "ok" | tee -a $LOGFILE
      echo -e "\nFailure seems to be an issue with docker container." | tee -a $LOGFILE
      echo "Please open an issue on github with $LOGFILE" | tee -a $LOGFILE
      echo "https://github.com/jonescompneurolab/hnn/issues" | tee -a $LOGFILE
    fi
    cleanup 2
  fi

  if [[ $TRAVIS_TESTING -ne 0 ]] || [[ "$OS" == "linux" ]]; then
    # This command will not work when a qemu VM is used with docker-machine.
    # That is, only when TRAVIS_TESTING=1 and (OS="mac" or OS="windows")
    silent_run_command "touch $HOME/hnn_out/THIS_DIRECTORY_IS_SHARED_BETWEEN_DOCKER_AND_YOUR_OS"
  fi
}

function check_x_authenticated {
  # no arguments
  check_var DISPLAY
  check_var OS

  if [[ ! "$OS" == "windows" ]]; then
    print_header_message "Checking if X server is reachable from container... "
    run_command_print_status "xset -display $DISPLAY -q"
  fi
}

function check_x_port_netcat {
  # no arguments
  # requires netcat (will no work on windows)
  # runs script on host to checks that port for $DISPLAY in container
  # is open
  check_var DISPLAY
  check_var LOGFILE
  check_var RETRY

  local __ip
  local __port
  local __index
  local __send_args
  local __command
  local __arg

  if [[ $RETRY -gt 1 ]]; then
    echo -n "(retry) " | tee -a $LOGFILE
  fi

  print_header_message "Checking if X server is reachable locally... "
  let __port=6000+${DISPLAY#*:}
  __ip=${DISPLAY%%:*}
  if [ -z $__ip ]; then
    __ip="127.0.0.1"
  fi
  run_command_print_status "nc -zvw3 $__ip $__port"
  if [[ $? -ne 0 ]]; then
    echo "Current XQuartz processes:" >> $LOGFILE
    __command=("ps" "auxw" "grep" "X11")
    let __index=0
    for __arg in "${__command[@]}"; do
      __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
      (( __index++ ))
    done
    output_run_piped_command "${__send_args[@]}" > /dev/null
    false
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

  print_header_message "Checking if X server is reachable from container... "
  MSYS_NO_PATHCONV=1 run_command_print_status "$DOCKER exec -e DISPLAY=$__display $HNN_CONTAINER_NAME /check_x_port.sh"
  if [[ $? -ne 0 ]]; then
    cleanup 2
  fi
}

function check_sshd_port {
  # no arguments
  # runs script in container that checks for port 22 open
  check_var DOCKER
  check_var HNN_CONTAINER_NAME
  check_var LOGFILE
  check_var RETRY

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a $LOGFILE
    RETRY=0
  fi

  print_header_message "Checking if port 22 is open in container... "
  MSYS_NO_PATHCONV=1 run_command_print_status "$DOCKER exec $HNN_CONTAINER_NAME /check_sshd_port.sh"
}


function prompt_stop_container {
  check_var LOGFILE
  check_var TRAVIS_TESTING

  local __str

  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    stop_container
    return
  fi

  while true; do
    echo | tee -a $LOGFILE
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
  check_var ESC_STR
  check_var HNN_CONTAINER_NAME

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
  check_var LOGFILE

  print_header_message "Looking for existing containers... "
  output_existing_container_command > /dev/null
  if [[ $? -eq "0" ]]; then
    echo "found" | tee -a $LOGFILE
  else
    echo "not found" | tee -a $LOGFILE
    false
  fi
}

function output_existing_container_command {
  # no arguments
  # will run "docker ps -a | grep HNN_CONTAINER_NAME"
  check_var DOCKER
  check_var ESC_STR
  check_var HNN_CONTAINER_NAME

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
  check_var LOGFILE

  local __command_status
  local __user
  __user="$1"

  if [ ! -e $XAUTHORITY ]; then
    echo "Couldn't find Xauthority file at $XAUTHORITY"
    cleanup 2
  fi

  print_header_message_short "Copying Xauthority file into container... "
  echo -e "\n  ** Command: $DOCKER cp $XAUTHORITY $HNN_CONTAINER_NAME:/tmp/.Xauthority" >> $LOGFILE
  run_command_print_status_failure_exit "$DOCKER cp $XAUTHORITY $HNN_CONTAINER_NAME:/tmp/.Xauthority"

  print_header_message "Changing Xauthority permissions in container... "
  echo -e "\n  ** Command: $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c \"chown $__user:hnn_group /tmp/.Xauthority\"" >> $LOGFILE
  echo -n "  ** Output: " >> $LOGFILE
  MSYS_NO_PATHCONV=1 $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c "chown $__user:hnn_group /tmp/.Xauthority" >> $LOGFILE 2>&1
  __command_status=$?
  echo >> $LOGFILE
  if [[ $__command_status -ne 0 ]]; then
    echo "*failed*" | tee -a $LOGFILE
    cleanup 2
  fi

  echo -e "\n  ** Command: $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c \"chmod g+rw /tmp/.Xauthority\"" >> $LOGFILE
  echo -n "  ** Output: " >> $LOGFILE
  MSYS_NO_PATHCONV=1 $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c "chmod g+rw /tmp/.Xauthority" >> $LOGFILE 2>&1
  __command_status=$?
  echo >> $LOGFILE
  if [[ $__command_status -ne 0 ]]; then
    echo "*failed*" | tee -a $LOGFILE
    cleanup 2
  fi

  echo "done" | tee -a $LOGFILE
}

function prepare_user_volumes {
  # copies $PWD to hnn_source_code and sets permissions for hnn_out directory
  # for the appropriate user
  check_var DOCKER
  check_var XAUTHORITY
  check_var HNN_CONTAINER_NAME
  check_var LOGFILE
  check_var USE_SSH
  check_var UID

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
  echo -e "\n  ** Command: $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c \"rm -rf /home/hnn_user/hnn_source_code\"" >> $LOGFILE
  echo -n "  ** Output: " >> $LOGFILE
  MSYS_NO_PATHCONV=1 $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c "rm -rf /home/hnn_user/hnn_source_code" >> $LOGFILE 2>&1
  fail_on_bad_exit $?

  print_header_message_short "Copying hnn_source_code into container... "
  echo -e "\n  ** Command: $DOCKER cp $PWD $HNN_CONTAINER_NAME:/home/hnn_user/hnn_source_code" >> $LOGFILE
  run_command_print_status_failure_exit "$DOCKER cp $PWD $HNN_CONTAINER_NAME:/home/hnn_user/hnn_source_code"

  print_header_message "Changing hnn_source_code permissions in container... "
  echo -e "\n  ** Command: $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c \"chown -R $__user /home/hnn_user/hnn_source_code\"" >> $LOGFILE
  echo -n "  ** Output: " >> $LOGFILE
  MSYS_NO_PATHCONV=1 $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c "chown -R $__user /home/hnn_user/hnn_source_code" >> $LOGFILE 2>&1
  fail_on_bad_exit $?

  print_header_message "Changing hnn_out permissions in container... "
  echo -e "\n  ** Command: $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c \"chown $__user $SYSTEM_USER_DIR/hnn_out\"" >> $LOGFILE
  echo -n "  ** Output: " >> $LOGFILE
  MSYS_NO_PATHCONV=1 $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c "chown $__user $SYSTEM_USER_DIR/hnn_out" >> $LOGFILE 2>&1
  fail_on_bad_exit $?
}

function copy_ssh_files_to_running_container {
  # no arguments
  check_var DOCKER
  check_var SSH_AUTHKEYS
  check_var SSH_PUBKEY

  print_header_message_short "Copying authorized_keys file into container... "
  echo -e "\n  ** Command: $DOCKER cp $SSH_AUTHKEYS $HNN_CONTAINER_NAME:/home/hnn_user/.ssh/authorized_keys" >> $LOGFILE
  run_command_print_status_failure_exit "$DOCKER cp $SSH_AUTHKEYS $HNN_CONTAINER_NAME:/home/hnn_user/.ssh/authorized_keys"

  print_header_message_short "Copying known_hosts file into container... "
  echo -e "\n  ** Command: $DOCKER cp $SSH_PUBKEY $HNN_CONTAINER_NAME:/home/hnn_user/.ssh/known_hosts" >> $LOGFILE
  run_command_print_status_failure_exit "$DOCKER cp $SSH_PUBKEY $HNN_CONTAINER_NAME:/home/hnn_user/.ssh/known_hosts"

  print_header_message_short "Updating permissions on ssh files in container... "
  echo -e "\n  ** Command: $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c \"chown -R hnn_user /home/hnn_user/.ssh\"" >> $LOGFILE
  echo -n "  ** Output: " >> $LOGFILE
  MSYS_NO_PATHCONV=1 $DOCKER exec -u root $HNN_CONTAINER_NAME bash -c "chown -R hnn_user /home/hnn_user/.ssh" >> $LOGFILE 2>&1
  __command_status=$?
  echo >> $LOGFILE
  fail_on_bad_exit $__command_status
}

function kill_xquartz {
  check_var LOGFILE

  local __command
  local __pid
  local __proc_arr
  local __pids
  local __proc

  let __retries=10
  while [[ $__retries -gt 0 ]]; do
    pgrep X11.bin > /dev/null 2>&1 || pgrep Xquartz > /dev/null 2>&1 || \
      pgrep quartz-wm > /dev/null 2>&1 || pgrep xinit > /dev/null 2>&1
    if [[ $? -eq 0 ]]; then
      __proc_arr=("launchd_startx" "X11.bin" "xterm" "Xquartz" "quartz-wm" "xinit")
      for __proc in ${__proc_arr[@]}; do
        __command="pgrep $__proc"
        __pids=($(output_run_command "$__command"))
        for __pid in ${__pids[@]}; do
          silent_run_command "kill $__pid"
          if [[ $? -eq 0 ]]; then
            echo "killed $__proc ($__pid)" >> $LOGFILE
          else
            silent_run_command "kill -9 $__pid"
            if [[ $? -eq 0 ]]; then
              echo "killed $__proc ($__pid)" >> $LOGFILE
            else
              echo "failed to kill $__proc ($__pid)" >> $LOGFILE
            fi
          fi
        done
      done
      sleep 2
    else
      break
    fi
    sleep 1
    (( __retries-- ))
  done

  if [[ $__retries -eq 0 ]]; then
    echo "couldn't stop all Xquartz procs after 5 retries" >> $LOGFILE
    false
  else
    if [[ -e /tmp/.X*-lock ]]; then
      echo "Removing locks: $(ls /tmp/.X*-lock)" >> $LOGFILE
      rm -f /tmp/.X*-lock
    fi
  fi
}

function get_xquartz_port {
  check_var LOGFILE

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
        echo "Started more than one Xquartz: $__pid" >> $LOGFILE
        __pid=$(echo $__pid|sed 's/\([0-9]\{1,\}\) [0-9]\{1,\}/\1/')
        echo "Using $__pid" >> $LOGFILE
      fi
      __xquartz_display=$(ps $__pid|grep $__pid|sed 's/.*\(\:[0-9]\{1,\}\).*/\1/')
      __display_int=$(echo $__xquartz_display|sed 's/\:\([0-9]\{1,\}\)/\1/')
      if [[ -e "/tmp/.X11-unix/X${__display_int}" ]]; then
        echo "Started XQuartz on DISPLAY $__xquartz_display" >> $LOGFILE
        break
      fi
    fi
    sleep 1
    (( __timeout-- ))
  done

  if [[ $__timeout -eq 0 ]]; then
    if [[ -n $__display_int ]]; then
      echo "/tmp/.X11-unix/X${__display_int} not found" >> $LOGFILE
    fi
    false
  fi

  echo $__display_int
}

function start_xquartz {
  check_var LOGFILE

  local __display_int
  local __command

  __command="open -a XQuartz"
  silent_run_command "$__command"
  if [[ $? -ne "0" ]]; then
    # this probably will never fail on a mac
    echo "*failed*" | tee -a $LOGFILE
    cleanup 2
  fi

  __display_int=$(get_xquartz_port)
  if [[ ! $__display_int == "0" ]]; then
    echo "unsupported display :${__display_int}. XQuartz must use :0" | tee -a $LOGFILE
    false
  fi
}

function restart_xquartz {
  print_header_message "Restarting XQuartz... "
  kill_xquartz && start_xquartz
  fail_on_bad_exit $?
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
  check_var LOGFILE
  check_var HNN_DOCKER_IMAGE
  check_var TRAVIS_TESTING

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
    echo "done" | tee -a $LOGFILE
    print_header_message "Looking for existing containers... "
    __docker_container=$(output_existing_container_command)
    if [[ $? -eq "0" ]]; then
      __last_used_image=$(echo ${__docker_container}|cut -d' ' -f 2)
      if [[ "${__last_used_image}" =~ "${HNN_DOCKER_IMAGE}" ]]; then
        echo "found, running up to date image" | tee -a $LOGFILE
        UPGRADE=0
      else
        echo "found, running outdated image" | tee -a $LOGFILE
        prompt_remove_container
      fi
    else
      echo "not found" | tee -a $LOGFILE
    fi
    true
  else
    false
  fi
}

function retry_docker_pull {
  check_var LOGFILE

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
    echo "*failed*" | tee -a $LOGFILE
    false
  fi
}

function docker_compose_up {
  # no arguments
  # will run the appropriate docker-compose command (either up or run)
  # to leave a running containers
  check_var TRAVIS_TESTING
  check_var LOGFILE
  check_var RETRY
  check_var OS
  check_var DOCKER_COMPOSE
  check_var COMPOSE_FILE
  check_var USE_SSH

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
    echo -n "(retry) " | tee -a $LOGFILE
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
    echo "*failed*" | tee -a $LOGFILE
    cleanup 2
  fi

  # make sure "docker ps | grep HNN_CONTAINER_NAME" succeeeds
  __started=$(wait_for_container_to_start $__timeout)
  if [[ ! "$__started" =~ "1" ]]; then
    echo "*failed*" | tee -a $LOGFILE
    echo "Waited for $__timeout seconds for container to start" >> $LOGFILE
    false
  else
    echo "done" | tee -a $LOGFILE
  fi

  # copy ssh auth files for TRAVIS_TESTING=1
  if [[ $USE_SSH -eq 1 ]]; then
    copy_ssh_files_to_running_container
  fi
}

function print_sshd_log {
  # no args
  # if sshd has been started and container exists,
  # run "docker logs --tail 100 HNN_CONTAINER_NAME"
  check_var SSHD_STARTED

  if [[ $SSHD_STARTED -eq 1 ]]; then
    check_var LOGFILE
    check_var DOCKER
    check_var HNN_CONTAINER_NAME
    echo -e "\n=====================" >> $LOGFILE
    echo "Logs from sshd in container: ">> $LOGFILE
    MSYS_NO_PATHCONV=1 silent_run_command "$DOCKER exec -u root $HNN_CONTAINER_NAME cat /var/log/sshd.log"
  fi
}

function create_container {
  # no arguments
  # if exiting image is not found, it will run docker pull first
  # else it will run "docker-compose up --no-start" to create
  # the container
  check_var LOGFILE
  check_var DOCKER
  check_var DOCKER_COMPOSE
  check_var COMPOSE_FILE
  check_var ESC_STR
  check_var HNN_DOCKER_IMAGE
  check_var ALREADY_RUNNING
  check_var TRAVIS_TESTING
  check_var OS

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
    echo "Skipping for TRAVIS_TESTING=1" | tee -a $LOGFILE
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
}

function get_docker_machine {
  check_var LOGFILE

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
    echo "*failed*" | tee -a $LOGFILE
    cleanup 2
  fi
  echo $__docker_machine
}

function get_xauth_keys {
  check_var LOGFILE
  check_var XAUTH_BIN
  check_var XAUTHORITY
  check_var DISPLAY

  local __binary
  local __command_args
  local __output
  local __command_status
  __binary="${XAUTH_BIN}"
  __command_args="-f $XAUTHORITY nlist $DISPLAY"

  echo -e "\n  ** Command: $__binary $__command_args" >> $LOGFILE
  echo -n "  ** Stderr: " >> $LOGFILE
  __output=$("$__binary" $__command_args 2>> $LOGFILE)
  __command_status=$?

  # don't print keys in log
  if [ -n "$__output" ]; then
    echo "Output: ** suppresed **" >> $LOGFILE
  else
    echo "Output: " >> $LOGFILE
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

function get_xauth_bin {
  check_var LOGFILE

  __command="which xauth"
  XAUTH_BIN=$(output_run_command "$__command")
  if [[ $? -ne 0 ]]; then
    echo "*failed*" | tee -a $LOGFILE
    echo "Could not find xauth binary in path" | tee -a $LOGFILE
    cleanup 1
  fi
  export XAUTH_BIN
}

function check_xauth_bin {
  # no arguments
  # if "which xauth" succeeds, run "xauth version" to check that it works
  check_var XAUTH_BIN
  check_var XAUTHORITY
  check_var LOGFILE

  local __command
  local __index
  local __send_args
  local __arg

  print_header_message "Checking that $XAUTH_BIN works... "
  echo >> $LOGFILE
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

  # version is already send to $LOGFILE in output_run_specific_command
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
  check_var OS
  check_var DOCKER_TOOLBOX

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


function get_host_xauth_key {
  # no arguments
  # retrieves xauth key from host
  check_var LOGFILE
  check_var DISPLAY

  local __key

  echo -e "\n  ** Command: xauth -ni nlist $DISPLAY | grep '^fff' | head -1 | awk '{print \$9}'" >> $LOGFILE
  __key=$(xauth -ni nlist $DISPLAY | grep '^fff' | head -1 | awk '{print $9}' 2>> $LOGFILE)
  if [[ $? -ne 0 ]]; then
    return 1
  else
    echo $__key
  fi
}

function get_container_xauth_key {
  # first argument is username inside container to check permissions for
  # checks that xauth run within container retuns valid keys

  check_args "$@" $# 1

  check_var LOGFILE
  check_var DOCKER
  check_var HNN_CONTAINER_NAME

  local __key
  local __user
  local __display
  __user="$1"
  __display=$(get_display_for_gui)


  echo -e "\n  ** Command: $DOCKER exec -u $__user $HNN_CONTAINER_NAME bash -c \"timeout 5 xauth -ni nlist $__display | grep '^ffff' | head -1 | awk '{print \$9}'\"" >> $LOGFILE
  echo -n "  ** Stderr: " >> $LOGFILE
  __key=$($DOCKER exec -u $__user $HNN_CONTAINER_NAME bash -c "timeout 5 xauth -ni nlist $__display | grep '^ffff' | head -1 | awk '{print \$9}'" 2>> $LOGFILE)
  if [[ $? -ne 0 ]]; then
    return 1
  else
    echo $__key
  fi
}

function check_container_xauth {
  # first argument is username inside container to check permissions for
  check_args "$@" $# 1

  check_var LOGFILE
  check_var RETRY

  local __user
  local __host_key
  __user=$1
  __host_key=$(get_host_xauth_key)
  if [[ $? -ne 0 ]] || [[ -z $__host_key ]]; then
    echo $__host_key
    # no output means no valid keys
    echo -e "  ** Error: no valid key **" >> $LOGFILE
    return 1
  fi

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a $LOGFILE
    RETRY=0
  fi
  print_header_message "Checking that xauth key in container matches... "
  __key=$(get_container_xauth_key $1)
  if [[ $? -ne 0 ]]; then
    echo "*failed*" | tee -a $LOGFILE
    echo -e " ** Error: could not retrieve keys from container **" >> $LOGFILE
    return 1
  elif [[ -z $__key ]]; then
    # no output means no valid keys
    echo "*failed*" | tee -a $LOGFILE
    echo -e " ** Error: no valid key **" >> $LOGFILE
    return 1
  elif [[ "$__host_key" == "$__key" ]]; then
    echo "ok" | tee -a $LOGFILE
  else
    echo "*failed*" | tee -a $LOGFILE
    echo -e "  ** Error: key mismatch **" >> $LOGFILE
    return 1
  fi
}

function setup_xauthority_in_container {
  # no arguments
  # on exit, xauth keys are valid and readable by the appropriate user
  # depending on whether SSH is used
  check_var USE_SSH
  check_var NEW_XAUTH_KEYS
  check_var ALREADY_RUNNING
  check_var RETRY

  local __user

  if [[ $USE_SSH -eq 0 ]]; then
    # since connecting directly with some UID,
    # will need xauth to work for that user
    __user="$UID"
  else
    # will need xauth to work for hnn_user via ssh
    __user="hnn_user"
  fi

  if [[ $NEW_XAUTH_KEYS -eq 0 ]] && [[ $ALREADY_RUNNING -eq 1 ]]; then
    check_container_xauth "$__user"
    if [[ $? -ne 0 ]]; then
      RETRY=1
      false
    fi
  else
    false
  fi

  if [[ $? -ne 0 ]]; then
    # copy the key, new or not
    copy_xauthority_file "$__user"
    # make sure that xauth works in container now
    check_container_xauth "$__user"
    if [[ $? -ne 0 ]]; then
      cleanup 2
    fi
  fi
}

function set_local_display_for_host {
  check_var DISPLAY
  check_var TRAVIS_TESTING
  check_var OS

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

function config_xquartz {
  check_var LOGFILE
  check_var RETRY

  local __restart_xquartz
  local __xquartz_output
  local __xquartz_noauth
  local __xquartz_nolisten

  # check if xquartz needs to be restarted to access preferences
  __xquartz_output=$(output_run_command "defaults read org.macosforge.xquartz.X11.plist")
  if [[ $? -ne 0 ]]; then
    __restart_xquartz=1
    return 1
  elif [[ -z "$__xquartz_output" ]]; then
    echo "*failed*" | tee -a $LOGFILE
    echo -e "\nNo valid output from org.macosforge.xquartz.X11.plist" | tee -a $LOGFILE
    cleanup 2
  fi

  while IFS= read -r line; do
    if [[ $line =~ "no_auth" ]]; then
      __xquartz_noauth=$(echo $line | cut -d'=' -f 2| sed 's/^[ \t]*\(.*\);/\1/')
    elif [[ $line =~ "nolisten_tcp" ]]; then
      __xquartz_nolisten=$(echo $line | cut -d'=' -f 2| sed 's/^[ \t]*\(.*\);/\1/')
    fi
  done <<< "$__xquartz_output"

  if [[ "$__xquartz_nolisten" == "1" ]] || [[ "$__xquartz_noauth" == "1" ]]; then
    if [[ $RETRY -gt 0 ]]; then
      echo -n "(retry) " | tee -a $LOGFILE
    fi

    __restart_xquartz=0
    if [[ "$__xquartz_nolisten" == "1" ]]; then
      __restart_xquartz=1
      print_header_message "Setting XQuartz preferences to listen for network connections... "
      run_command_print_status_failure_exit "defaults write org.macosforge.xquartz.X11.plist nolisten_tcp 0"
    fi

    if [[ "$__xquartz_noauth" == "1" ]]; then
      __restart_xquartz=1
      print_header_message "Setting XQuartz preferences to use authentication... "
      run_command_print_status_failure_exit "defaults write org.macosforge.xquartz.X11.plist no_auth 0"
    fi
  else
    check_x_port_netcat
    if [[ $? -ne 0 ]]; then
      __restart_xquartz=1
    else
      check_x_authenticated
      if [[ $? -ne 0 ]]; then
        return 1
      fi
      true
    fi
  fi

  if [[ $__restart_xquartz -eq 1 ]]; then
    return 1
  fi
}

function start_download {
  echo "Downloading $2"
  let __retries=5
  while [[ $__retries -gt 0 ]]; do
    if [[ "${TRAVIS_OSX_IMAGE}" =~ "xcode8" ]]; then
      curl -Lo "$1" --retry 5 --retry-delay 30 "$2" && break
    else
      curl -Lo "$1" --retry 5 --retry-delay 30 --retry-connrefused "$2" && break
    fi
    (( __retries-- ))
  done
  if [[ $__retries -eq 0 ]]; then
    echo "Error: failed to download $2."
    exit 1
  fi
}

function wait_for_pid {
  echo -n "Waiting for PID $1... "
  wait $1 && {
    echo "done"
    echo "Finished $2"
  } || {
    echo "failed"
    echo "Error: failed $2"
    exit 1
  }
}

function script_fail {
  # This function is specific to .travis.yml. always use hnn_docker.log and not
  # $LOGFILE

  echo -ne "\n*******  hnn_docker.sh failed. output from hnn_docker.log below  *******\n"
  cat hnn_docker.log
  exit 2
}

function download_docker_image {
  let __max=5
  let __retry=1
  while [[ $__retry -le $__max ]]; do
    echo "Downloading $1 (try $__retry/$__max)"
    "$HOME/download-frozen-image-v2.sh" "$HOME/docker_image" "$1" && break
    (( __retry++ ))
  done

  if [[ $__retry -gt $__max ]]; then
    echo "Error: failed to download $1."
    exit 1
  fi
}