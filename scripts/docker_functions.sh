function check_args {
  # does not depend on any functions

  if [[ ! -n "LOGFILE" ]]; then
    echo -e "\n====================="
    echo "Error: ${FUNCNAME[1]} (L:${BASH_LINENO[1]}) expects LOGFILE to be set"
    echo "*failed*" | tee -a "$LOGFILE"
    cleanup 1
  fi

  if [[ $# -ne 3 ]]; then
    echo -e "\n=====================" >> "$LOGFILE"
    echo "Error: $FUNCNAME (L:$LINENO) must have 3 arguments: called from ${FUNCNAME[1]} (L:${BASH_LINENO[1]})" >> "$LOGFILE"
    echo "Instead $FUNCNAME (L:$LINENO) has $# arguments: $@" >> "$LOGFILE"
    echo "*failed*" | tee -a "$LOGFILE"
    cleanup 1
  fi

  if [[ $2 -ne $3 ]]; then
    echo -e "\n=====================" >> "$LOGFILE"
    if [[ "$3" =~ "1" ]]; then
      echo "Error: ${FUNCNAME[1]} (L:${BASH_LINENO[1]}) must have 1 argument" >> "$LOGFILE"
    else
      echo "Error: ${FUNCNAME[1]} (L:${BASH_LINENO[1]}) must have $3 arguments" >> "$LOGFILE"
    fi
    echo "*failed*" | tee -a "$LOGFILE"
    cleanup 1
  fi
}

function check_var {
  check_args "$@" $# 1
  if [[ ! -n $(eval echo \$$1) ]]; then
    echo -e "\n=====================" | tee -a "$LOGFILE"
    echo "Error: ${FUNCNAME[1]} (L:${BASH_LINENO[1]}) expects $1 to be set" | tee -a "$LOGFILE"
    echo "*failed*" | tee -a "$LOGFILE"
    cleanup 1
  fi
}

function get_wsl_home_path {
  # no arguments
  check_var ESC_STR

  local __command
  local __index
  local __arg
  local __send_args
  local __home

  log_header_message "Getting path outside of WSL... "
  __command=("powershell.exe" "\$env:HOME" "tr" "-d '\r'")
  let __index=0
  for __arg in "${__command[@]}"; do
    __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
    (( __index++ ))
  done
  __home=$(output_run_piped_command "${__send_args[@]}")
  if [[ $? -ne 0 ]]; then
    echo "*failed*" >> "$LOGFILE"
    return 2
  else
    echo "done" >> "$LOGFILE"
  fi

  log_header_message "Turning into UNIX path... "
  COMMAND=(3 "cygpath.exe" "-u" "$__home")
  convert_COMMAND_to_escaped_array
  __home=$(output_run_command_arguments "${ESCAPED_COMMAND[@]}")
  if [[ $? -ne 0 ]]; then
    echo "*failed*" >> "$LOGFILE"
    return 2
  else
    echo "done" >> "$LOGFILE"
  fi

  echo "$__home"
}

function get_os {
  OS_OUTPUT=$(uname -a)
  if [[ $OS_OUTPUT =~ "MINGW" ]] || [[ $OS_OUTPUT =~ "MSYS" ]]; then
    OS="windows"
  elif [[ $OS_OUTPUT =~ "Microsoft" ]]; then
    OS="wsl"
  elif [[ $OS_OUTPUT =~ "Darwin" ]]; then
    OS="mac"
  elif [[ $OS_OUTPUT =~ "Linux" ]]; then
    OS="linux"
  fi
  echo $OS
}

function set_globals {
  [[ "$LOGFILE" ]] || LOGFILE=/dev/stdout

  # globals
  UPGRADE=0
  STOP=0
  START=0
  RETRY=0
  UNINSTALL=0
  HNN_DOCKER_IMAGE=jonescompneurolab/hnn
  HNN_CONTAINER_NAME=hnn_container
  SYSTEM_USER_DIR="$HOME"
  ALREADY_RUNNING=0
  SSHD_STARTED=0
  NEW_XAUTH_KEYS=0
  ESC_STR="%^%"
  VCXSRV_PID=

  SSH_PRIVKEY="$(pwd)/installer/docker/id_rsa_hnn"
  SSH_PUBKEY="$(pwd)/installer/docker/id_rsa_hnn.pub"
  SSH_AUTHKEYS="$(pwd)/installer/docker/authorized_keys"

  export USE_SSH UPGRADE STOP START RETRY UNINSTALL HNN_DOCKER_IMAGE HNN_CONTAINER_NAME
  export SYSTEM_USER_DIR ALREADY_RUNNING SSHD_STARTED NEW_XAUTH_KEYS ESC_STR VCXSRV_PID

  OS=$(get_os)
  __command_status=$?
  if [[ $__command_status -ne 0 ]]; then
    echo "Failed to get OS type" | tee -a "$LOGFILE"
    return $__command_status
  fi

  if [[ "$OS" == "wsl" ]]; then
    export SYSTEM_USER_DIR="$(get_wsl_home_path)"
    if [[ $? -ne 0 ]]; then
      return $?
    fi
    set_local_display_from_port 0
  fi
  # if display hasn't been set yet, give it a default value for the OS
  [[ "$DISPLAY" ]] || set_local_display_from_port 0

  if [[ "$OS" == "mac" ]]; then
    function timeout {
      perl -e 'alarm shift; exec @ARGV' "$@"
    }
    export timeout
  fi
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
    echo -e "\n=====================" >> "$LOGFILE"
    echo "Call tree:" >> "$LOGFILE"
    for ((__i=1;__i<${#FUNCNAME[@]}-1;__i++)); do
      echo " $__i: ${BASH_SOURCE[$i+1]}:${BASH_LINENO[$i]} ${FUNCNAME[$i]}(...)" >> "$LOGFILE"
    done
  fi
  echo "Exiting with status ${__code}" >> "$LOGFILE"
  exit "${__code}"
}

function cleanup {
  # set LOGFILE so that commands below succeed
  [[ "$LOGFILE" ]] || LOGFILE=/dev/stdout

  local __failed

  __failed=$1

  echo -e "\n=====================" >> "$LOGFILE"
  echo "cleanup() called from: ${FUNCNAME[1]} (L:${BASH_LINENO[0]})" >> "$LOGFILE"
  if [ ! -z "${VCXSRV_PID}" ]; then
    stop_vcxsrv
    if [[ $? -ne 0 ]]; then
      echo "Killing VcXsrv PID ${VCXSRV_PID}" >> "$LOGFILE"
      kill ${VCXSRV_PID} &> /dev/null
    fi
  fi

  if [[ $__failed -eq "0" ]]; then
    echo "Script hnn_docker.sh finished successfully" | tee -a "$LOGFILE"
    exit 0
  elif [[ $__failed -eq "1" ]]; then
    echo "Error: Script cannot continue" | tee -a "$LOGFILE"
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
    echo "*failed*" | tee -a "$LOGFILE"
    cleanup 2
  else
    echo "done" | tee -a "$LOGFILE"
  fi
}

function run_command_print_status {
  check_var LOGFILE

  check_args "$@" $# 1

  silent_run_command "$1"
  if [[ $? -ne "0" ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    false
  else
    echo "done" | tee -a "$LOGFILE"
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
  local __num_args
  __args=($@)
  __num_args=4

  if [[ ${#__args[@]} -ne $__num_args ]]; then
    echo -e "\nError: $FUNCNAME (L:${BASH_LINENO[0]]}) has ${#__args[@]} args, must have $__num_args arguments" >> "$LOGFILE"
    echo "*failed*" | tee -a "$LOGFILE"
    cleanup 1
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

  echo -e "\n  ** Command: $__binary1 $__command_args1 | $__binary2 $__command_args2" >> "$LOGFILE"
  echo -n "  ** Stderr: " >> "$LOGFILE"
  __output=$("$__binary1" $__command_args1 2>> "$LOGFILE" | "$__binary2" $__command_args2 2>> "$LOGFILE")
  __command_status=$?
  if [[ ! -z "$__output" ]]; then
    echo -e "\n  ** Stdout: $__output" | tr -d '\r' >> "$LOGFILE"
  fi

  # send output back to caller
  echo "$__output"

  if [[ $__command_status -eq 0 ]]; then
    true
  else
    false
  fi
}

# Convenience function to escape command arguments in COMMAND.
# Since bash doesn't have types (everything is a string) when passing return values
# we have to use a global variable ESCAPED_COMMAND
function convert_COMMAND_to_escaped_array {
  ESCAPED_COMMAND=()

  local __index
  local __arg

  # prepare command to send as array argument without spaces
  let __index=0
  for __arg in "${COMMAND[@]}"; do
    ESCAPED_COMMAND[$__index]="$(echo $__arg|sed 's/ /'$ESC_STR'/g')"
    (( __index++ ))
  done
}

function output_run_command_arguments {
  # first argument is the number of args
  # second argument is the binary to run
  # note that output here is not expected to go to stdout, so redirect to LOGFILE
  re='^[0-9]+$'
  if ! [[ $1 =~ $re ]] ; then
    echo -e "\nError: $FUNCNAME: argument '$1' is not a number" >> "$LOGFILE"
    exit 1
  fi

  check_var LOGFILE
  check_var ESC_STR

  local __args
  local __num_args
  __args=($@)
  __expected_num_args=$(($1))
  __num_args=$((${#__args[@]}-1))  # don't count first argument

  if [[ $__num_args -ne $__expected_num_args ]]; then
    echo -e "\nError: $FUNCNAME (L:${BASH_LINENO[0]}) must have $__expected_num_args arguments" >> "$LOGFILE"
    echo "Got $__num_args arguments: $@" >> "$LOGFILE"
    exit 1
  fi

  local __index
  local __arg
  local __arg_index
  local __command_args
  local __binary

  # arguments have spaces escaped. need to unescape
  __command_args=()
  let __index=0
  for __arg in ${__args[@]}; do
    if [[ $__index -eq 0 ]]; then
      # count of arguments
      (( __index++ ))
      continue
    elif [[ $__index -eq 1 ]]; then
      __binary="$(echo $__arg | sed 's/'$ESC_STR'/ /g')"
    else
      let __arg_index=__index-2
      if [[ "$__arg" =~ "$ESC_STR" ]]; then
        # put quotes around argument if there's a space
        __command_args[$__arg_index]="$(echo $__arg | sed 's/'$ESC_STR'/ /g')"
      else
        __command_args[$__arg_index]="$__arg"
      fi
    fi
    (( __index++ ))
  done

  local __output
  local __command_status

  echo >> "$LOGFILE"
  echo "  ** Command: $__binary ${__command_args[@]}" >> "$LOGFILE"
  echo -n "  ** Stderr: " >> "$LOGFILE"
  __output=$("$__binary" "${__command_args[@]}" 2>> "$LOGFILE")
  __command_status=$?
  if [[ -n "$__output" ]]; then
    echo >> "$LOGFILE"
    if [[ $SUPPRESS_OUTPUT -eq 1 ]]; then
      echo "  ** Stdout: ** suppresed **" >> "$LOGFILE"
      SUPPRESS_OUTPUT=1
    else
      echo "  ** Stdout: $__output" | tr -d '\r' >> "$LOGFILE"
    fi
  fi

  # send output back to caller
  echo "$__output" | tr -d '\r'

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
  local __num_args
  __args=($@)
  __num_args=2

  if [[ ${#__args[@]} -ne $__num_args ]]; then
    echo -e "\nError: $FUNCNAME (L:${BASH_LINENO[0]}) must have $__num_args arguments" >> "$LOGFILE"
    echo "*failed*" | tee -a "$LOGFILE"
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

  echo -e "\n  ** Command: $__binary $__command_args" >> "$LOGFILE"
  echo -n "  ** Stderr: " >> "$LOGFILE"
  __output=$("$__binary" $__command_args 2>> "$LOGFILE")
  __command_status=$?
  if [[ -n "$__output" ]]; then
    echo -e "\n  ** Stdout: $__output" | tr -d '\r' >> "$LOGFILE"
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

  echo -e "\n  ** Command: $__command" >> "$LOGFILE"
  echo -n "  ** Stderr: " >> "$LOGFILE"
  __output=$($__command 2>> "$LOGFILE")
  __command_status=$?
  if [[ -n "$__output" ]]; then
    echo -e "\n  ** Stdout: $__output" | tr -d '\r' >> "$LOGFILE"
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

function remove_container_fail {
  check_var docker_cmd
  check_var HNN_CONTAINER_NAME

  COMMAND=(4 "$docker_cmd" "rm" "-fv" "$HNN_CONTAINER_NAME")
  convert_COMMAND_to_escaped_array
  output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  if [[ $? -ne "0" ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    echo -e "\nFailure to remove container can sometimes be fixed by restarting Docker"
    cleanup 2
  else
    echo "done" | tee -a "$LOGFILE"
  fi
}

function print_header_message {
  check_args "$@" $# 1
  check_var LOGFILE

  # first arg is message to print. surrounded by newlines in "$LOGFILE"
  echo >> "$LOGFILE"
  echo -n "$1" | tee -a "$LOGFILE"
  echo >> "$LOGFILE"
}

function print_header_message_short {
  check_args "$@" $# 1
  check_var LOGFILE

  # first arg is message to print. only have newline in front in LOGFILE
  echo >> "$LOGFILE"
  echo -n "$1" | tee -a "$LOGFILE"
}

function log_header_message {
  check_args "$@" $# 1
  check_var LOGFILE

  # first arg is message to print. surrounded by newlines in "$LOGFILE"
  echo >> "$LOGFILE"
  echo -n "$1" >> "$LOGFILE"
  echo >> "$LOGFILE"
}

function start_vcxsrv_print {
  check_var LOGFILE
  check_var vcxsrv_cmd

  local __vcxsrv_dir

  # duplicate the functionality of the 'basename' command
  # (remove the part between the last '/' and the end of line '$')
  __vcxsrv_dir="$(echo ${vcxsrv_cmd}|sed 's/\/[^\/]\{1,\}$//')"
  if [[ ! -d "$__vcxsrv_dir" ]]; then
    echo "Could not find directory for ${vcxsrv_cmd}"
    cleanup 2
  fi

  print_header_message "Starting VcXsrv... "
  COMMAND=(3 "${__vcxsrv_dir}/vcxsrv.exe" "-wgl" "-multiwindow")
  convert_COMMAND_to_escaped_array
  output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null &
  VCXSRV_PID=$!

  log_header_message "Checking if VcXsrv is running..."
  COMMAND=(3 "kill" "-0" "$VCXSRV_PID")
  convert_COMMAND_to_escaped_array
  output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fail_on_bad_exit $?

  echo "Started VcXsrv with PID ${VCXSRV_PID}" >> "$LOGFILE"
}


function stop_vcxsrv {
  check_var LOGFILE

  print_header_message "Stopping VcXsrv... "
  echo >> "$LOGFILE"
  if [[ "$OS" == "wsl" ]]; then
    run_command_print_status "cmd.exe /c taskkill /F /IM vcxsrv.exe"
  else
    run_command_print_status "cmd.exe //c taskkill //F //IM vcxsrv.exe"
  fi
  if [[ $? -eq "0" ]]; then
    VCXSRV_PID=
  else
    false
  fi
}

function prompt_remove_container_fail {
  check_var TRAVIS_TESTING

  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    print_header_message "Removing old container... "
    remove_container_fail
  else
    while true; do
      echo
      read -p "Please confirm that you want to remove the old HNN container? (y/n)" yn
      case $yn in
        [Yy]* ) print_header_message "Removing old container... "
                remove_container_fail
                break;;
        [Nn]* ) cleanup 1
                break;;
        * ) echo "Please answer yes or no.";;
      esac
    done
  fi
}

function stop_container_silent {
  check_var docker_cmd
  check_var HNN_CONTAINER_NAME
  check_var ALREADY_RUNNING

  silent_run_command "$docker_cmd stop $HNN_CONTAINER_NAME" && ALREADY_RUNNING=0
}

function start_container_silent {
  check_var docker_cmd
  check_var HNN_CONTAINER_NAME
  check_var ALREADY_RUNNING

  silent_run_command "$docker_cmd start $HNN_CONTAINER_NAME" && ALREADY_RUNNING=1
}


function get_container_port {
  check_var LOGFILE
  check_var HNN_CONTAINER_NAME
  check_var docker_cmd
  check_var TRAVIS_TESTING

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
    log_header_message "Getting port that maps to docker container port 22... "
    __command=("$docker_cmd" "port $HNN_CONTAINER_NAME 22")
    let __index=0
    for __arg in "${__command[@]}"; do
      __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
      (( __index++ ))
    done

    __port_string=$(output_run_specific_command "${__send_args[@]}")
    if [[ $? -ne "0" ]]; then
      echo "*failed*" >> "$LOGFILE"
      echo "failed to run ${__command[@]}" >> "$LOGFILE"
      return 1
    fi

    __ssh_port=$(echo $__port_string| cut -d':' -f 2)
    re='^[0-9]+$'
    if ! [[ $__ssh_port =~ $re ]] ; then
      echo "*failed*" >> "$LOGFILE"
      echo "failed to get a port number from \"$__ssh_port\"" >> "$LOGFILE"
      return 1
    fi
    echo "done" >> "$LOGFILE"
  fi

  echo $__ssh_port
}

function ssh_start_hnn_print {
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
  check_var CONTAINER_TYPE
  check_var TRAVIS_TESTING

  local __verbose
  local __ssh_port
  local __command_status

  if [[ "${DOCKER_TOOLBOX}" -eq "1" ]]; then
    check_var DOCKER_HOST

    __docker_host_ip=${DOCKER_HOST##*://}
    __docker_host_ip=${__docker_host_ip%:*}
  else
    __docker_host_ip=localhost
  fi

  print_header_message "Looking up port to connect to HNN container... "
  __ssh_port=$(get_container_port)
  __command_status=$?
  if [[ $__command_status -ne 0 ]]; then
    # don't completely crash script here to allow a retry after "docker restart"
    echo "*failed*" | tee -a "$LOGFILE"
    return $__command_status
  else
    echo "done" | tee -a "$LOGFILE"
  fi

  # since we assigned port 6000, we can be certain of this DISPLAY
  export DISPLAY=127.0.0.1:0
  export TRAVIS_TESTING

  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    export XAUTHORITY="/c/home/hnn_user/.Xauthority"
  else
    export XAUTHORITY="/tmp/.Xauthority"
  fi

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a "$LOGFILE"
    RETRY=0
  fi

  if [[ $VERBOSE -eq 1 ]] || [[ $DEBUG -eq 1 ]]; then
    __verbose="-v"
  else
    __verbose="-q"
  fi

  # Start the ssh command that will run start_hnn.sh (limited by /home/hnn_user/.ssh/authorized_keys)
  # on connection it will set up reverse port forwarding between port 6000 on the host OS (where the X
  # server is running) and port 6000 in the container we are ssh'ing into. Other options are to avoid
  # warnings about hostkeychecking and to not prompt for a password if public key authentication fails.
  print_header_message "Starting HNN GUI... "

  COMMAND=(23 "ssh" "-o" "SendEnv=DISPLAY" "-o" "SendEnv=XAUTHORITY" "-o" "SendEnv=SYSTEM_USER_DIR" "-o" "SendEnv=TRAVIS_TESTING" \
               "-o" "PasswordAuthentication=no" "-o" "UserKnownHostsFile=/dev/null" "-o" "StrictHostKeyChecking=no" \
               "$__verbose" "-i" "$SSH_PRIVKEY" "-R" "6000:127.0.0.1:6000" "hnn_user@$__docker_host_ip" "-p" "$__ssh_port")
  convert_COMMAND_to_escaped_array
  output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  if [[ $? -ne "0" ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    false
  else
    echo "done" | tee -a "$LOGFILE"
  fi
}

function start_hnn_print {
  # no args
  # runs start_hnn.sh script directly in container using "docker exec"
  check_var docker_cmd
  check_var TRAVIS_TESTING
  check_var SYSTEM_USER_DIR
  check_var HNN_CONTAINER_NAME
  check_var LOGFILE
  check_var CONTAINER_TYPE
  check_var UID

  local __display

  # set DISPLAY for OS
  print_header_message "Setting DISPLAY variable for $CONTAINER_TYPE containers... "
  __display=$(get_display_for_gui)
  fail_on_bad_exit $?

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a "$LOGFILE"
    RETRY=0
  fi

  print_header_message "Starting HNN GUI... "
  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    __container_user="hnn_user"
    __start_script="/c/home/hnn_user/start_hnn.sh"
  else
    __container_user="$UID"
    __start_script="/home/hnn_user/start_hnn.sh"
  fi
  COMMAND=(13 "$docker_cmd" "exec" "--env" "TRAVIS_TESTING=$TRAVIS_TESTING" \
          "--env" "SYSTEM_USER_DIR=$SYSTEM_USER_DIR" "--env" "DISPLAY=$__display" \
          "-u" "$__container_user" "$HNN_CONTAINER_NAME" \
          "bash" "$__start_script")

  convert_COMMAND_to_escaped_array
  MSYS_NO_PATHCONV=1 output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  if [[ $? -ne "0" ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    false
  else
    echo "done" | tee -a "$LOGFILE"
  fi
}

function check_sshd_proc {
  # no arguments
  # runs script in container that checks for port 22 open
  check_var docker_cmd
  check_var HNN_CONTAINER_NAME
  check_var DOCKER_TOOLBOX
  check_var RETRY

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a "$LOGFILE"
    RETRY=0
  fi

  print_header_message "Checking if sshd is running in container... "
  MSYS_NO_PATHCONV=1 run_command_print_status "$docker_cmd exec $HNN_CONTAINER_NAME pgrep sshd"
}

function fix_hnn_out_perms_host_fail {
  # no arguments
  check_var HOME
  check_var TRAVIS_TESTING

  if [[ ! -e "${SYSTEM_USER_DIR}/hnn_out/" ]]; then
    print_header_message "Creating ${HOME}/hnn_out... "
    COMMAND=(2 "mkdir" "${HOME}/hnn_out")
    convert_COMMAND_to_escaped_array
    output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
    fail_on_bad_exit $?
    return
  fi

  print_header_message "Updating hnn_out permissions on host... "
  find "${SYSTEM_USER_DIR}/hnn_out" -type d -exec chmod 777 {} \;  >> "$LOGFILE" 2>&1 && \
    find "${SYSTEM_USER_DIR}/hnn_out" -type f -exec chmod 666 {} \; >> "$LOGFILE" 2>&1
  fail_on_bad_exit $?

  if [[ $TRAVIS_TESTING -eq 1 ]] && [[ "$OS" == "mac" ]]; then
    COMMAND=(2 "touch" "${SYSTEM_USER_DIR}/hnn_out/THIS_DIRECTORY_IS_SHARED_BETWEEN_DOCKER_AND_YOUR_OS")
    convert_COMMAND_to_escaped_array
    output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fi
}

function check_hnn_out_perms_host {
  # no arguments
  check_var LOGFILE
  check_var HOME

  installer/docker/check_hnn_out_perms.sh
  if [[ $? -ne 0 ]]; then
    return 1
  fi
}

function check_hnn_out_perms_container_print {
  # no arguments
  # runs script in container that checks permissions for hnn_out are okay
  check_var docker_cmd
  check_var HNN_CONTAINER_NAME
  check_var CONTAINER_TYPE
  check_var LOGFILE
  check_var RETRY
  check_var SYSTEM_USER_DIR

  local __script_path
  local __user


  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a "$LOGFILE"
    RETRY=0
  fi

  print_header_message "Checking permissions of ${SYSTEM_USER_DIR}/hnn_out in container... "
  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    __script_path="bash -c /c/home/hnn_user/check_hnn_out_perms.sh"
  else
    __script_path="/home/hnn_user/check_hnn_out_perms.sh"
  fi
  COMMAND=(6 "$docker_cmd" "exec" "$HNN_CONTAINER_NAME" "bash" "-c" "$__script_path")
  convert_COMMAND_to_escaped_array
  MSYS_NO_PATHCONV=1 output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  if [[ $? -ne 0 ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    false
  else
    echo "done"
  fi
}

function fix_hnn_out_perms_container_print {
  # no arguments
  # runs command in container to change permissions of hnn_out
  check_var docker_cmd
  check_var HNN_CONTAINER_NAME
  check_var CONTAINER_TYPE
  check_var LOGFILE
  check_var SYSTEM_USER_DIR

  local __container_user

  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    return 0
  else
    __container_user="root"
  fi

  check_hnn_out_perms_container_print
  if [[ $? -ne 0 ]]; then
    print_header_message "Updating hnn_out permissions inside container... "
    COMMAND=(8 "$docker_cmd" "exec" "-u" "$__container_user" "$HNN_CONTAINER_NAME" "bash" "-c" \
            "find \"${SYSTEM_USER_DIR}/hnn_out\" -type d -exec chmod 777 {} \; && \
                find \"${SYSTEM_USER_DIR}/hnn_out\" -type f -exec chmod 666 {} \;")
    convert_COMMAND_to_escaped_array
    MSYS_NO_PATHCONV=1 output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
    fail_on_bad_exit $?

    RETRY=1
    check_hnn_out_perms_container_print
  fi
}

function check_x_authenticated {
  # no arguments
  check_var DISPLAY
  check_var OS
  check_var LOGFILE

  if [[ "$OS" == "wsl" ]]; then
    find_program_print xset
    if [[ $? -ne 0 ]]; then
      echo -e "Skipping X server test: install xset with 'sudo apt-get install x11-xserver-utils'\n" | tee -a "$LOGFILE"
    fi
  fi

  if [[ ! "$OS" == "windows" ]]; then
    print_header_message "Checking if we can authenticate with X server... "
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
    echo -n "(retry) " | tee -a "$LOGFILE"
  fi

  __ip=${DISPLAY%%:*}
  let __port=6000+${DISPLAY#*:}

  getent hosts $__ip > /dev/null 2>&1
  if [[ $? -ne 0 ]]; then
    echo "Skipping netcat test for local DISPLAY $DISPLAY" >> "$LOGFILE"
    return
  fi

  print_header_message "Checking if X server is reachable at $DISPLAY... "
  run_command_print_status "nc -nzvw3 $__ip $__port"
  if [[ $? -ne 0 ]]; then
    echo "Current XQuartz processes:" >> "$LOGFILE"
    __command=("ps" "auxw" "grep" "X11")
    let __index=0
    for __arg in "${__command[@]}"; do
      __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
      (( __index++ ))
    done
    output_run_piped_command "${__send_args[@]}" >> "$LOGFILE"
    false
  fi
}

function check_x_port_container_fail {
  # no arguments
  # runs script in container that checks that port for $DISPLAY in container
  # is open
  check_var docker_cmd
  check_var HNN_CONTAINER_NAME

  local __display

  # set DISPLAY for OS
  __display=$(get_display_for_gui)
  if [[ $? -ne 0 ]]; then
    cleanup 2
  fi

  print_header_message "Checking if X server is reachable from container... "
  MSYS_NO_PATHCONV=1 run_command_print_status "$docker_cmd exec -e DISPLAY=$__display $HNN_CONTAINER_NAME /check_x_port.sh"
  if [[ $? -ne 0 ]]; then
    cleanup 2
  fi
}

function check_sshd_port_print {
  # no arguments
  # runs script in container that checks for port 22 open
  check_var docker_cmd
  check_var HNN_CONTAINER_NAME
  check_var LOGFILE
  check_var RETRY

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a "$LOGFILE"
    RETRY=0
  fi

  print_header_message "Checking if port 22 is open in container... "
  MSYS_NO_PATHCONV=1 run_command_print_status "$docker_cmd exec $HNN_CONTAINER_NAME /check_sshd_port.sh"
}


function prompt_stop_container {
  check_var LOGFILE
  check_var TRAVIS_TESTING

  local __str

  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    print_header_message "Stopping HNN container... "
    stop_container_silent
    fail_on_bad_exit $?
    return
  fi

  while true; do
    echo | tee -a "$LOGFILE"
    if [[ "$UPGRADE" -eq "1" ]]; then
      __str=" for upgrade"
    else
      __str=
    fi

    read -p "Restart needed$__str. Please confirm that you want to force stopping the HNN container? (y/n)" yn
    case $yn in
        [Yy]* ) print_header_message "Stopping HNN container... "
                stop_container_fail
                fail_on_bad_exit $?
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
  check_var docker_cmd
  check_var ESC_STR
  check_var HNN_CONTAINER_NAME

  local __index
  local __send_args
  local __command
  local __arg

  __command=("$docker_cmd" ps grep "$HNN_CONTAINER_NAME")

  # prepare command to send as array argument without spaces
  let __index=0
  for __arg in "${__command[@]}"; do
    __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
    (( __index++ ))
  done

  output_run_piped_command "${__send_args[@]}" > /dev/null
}

function find_existing_container_print {
  check_var LOGFILE

  print_header_message "Looking for existing containers... "
  output_existing_container_command > /dev/null
  if [[ $? -eq "0" ]]; then
    echo "found" | tee -a "$LOGFILE"
  else
    echo "not found" | tee -a "$LOGFILE"
    false
  fi
}

function output_existing_container_command {
  # no arguments
  # will run "docker ps -a | grep HNN_CONTAINER_NAME"
  check_var docker_cmd
  check_var ESC_STR
  check_var HNN_CONTAINER_NAME

  local __index
  local __send_args
  local __command
  local __arg

  __command=("$docker_cmd" "ps -a" grep "$HNN_CONTAINER_NAME")

  # prepare command to send as array argument without spaces
  let __index=0
  for __arg in "${__command[@]}"; do
    __send_args[$__index]=$(echo $__arg|sed "s/ /$ESC_STR/g")
    (( __index++ ))
  done

  output_run_piped_command "${__send_args[@]}"
}

function copy_xauthority_file_fail {
  # first argument is username inside container to check permissions for
  # copies ~/.Xauthority (given by $XAUTHORITY) to /tmp/.Xauthority inside
  # container and updates permissions to the specified user
  check_args "$@" $# 1

  check_var docker_cmd
  check_var XAUTHORITY
  check_var HNN_CONTAINER_NAME
  check_var LOGFILE
  check_var CONTAINER_TYPE

  local __container_xauthority_path
  local __xauthority_path
  local __command_status
  local __user
  __user="$1"

  if [ ! -e "$XAUTHORITY" ]; then
    echo "Couldn't find Xauthority file at \"$XAUTHORITY\"" | tee -a "$LOGFILE"
    cleanup 2
  fi

  __container_xauthority_path="/tmp/.Xauthority"
  __xauthority_path="$XAUTHORITY"

  # exceptions for windows containers
  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    __container_xauthority_path="/home/hnn_user/.Xauthority"

    if [[ ! "$OS" == "wsl" ]]; then
      COMMAND=(3 "cygpath.exe" "-w" "$__xauthority_path")
      convert_COMMAND_to_escaped_array
      __xauthority_path=$(output_run_command_arguments "${ESCAPED_COMMAND[@]}")
      if [[ $? -ne 0 ]]; then
        cleanup 2
      fi
    fi

    stop_container_silent
  fi

  print_header_message_short "Copying Xauthority file into container... "
  COMMAND=(4 "$docker_cmd" "cp" "$__xauthority_path" "$HNN_CONTAINER_NAME:$__container_xauthority_path")
  convert_COMMAND_to_escaped_array
  MSYS_NO_PATHCONV=1 output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fail_on_bad_exit $?
  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    start_container_silent
    return
  fi

  print_header_message "Changing Xauthority permissions in container... "
  COMMAND=(8 "$docker_cmd" "exec" "-u" "root" "$HNN_CONTAINER_NAME" "bash" "-c" \
           "chown $__user:hnn_group \"$__container_xauthority_path\" && chmod g+rw \"$__container_xauthority_path\"")
  convert_COMMAND_to_escaped_array
  output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fail_on_bad_exit $?

}

function copy_hnn_source_fail {
  # copies $PWD to hnn_source_code
  check_var docker_cmd
  check_var HNN_CONTAINER_NAME
  check_var LOGFILE
  check_var CONTAINER_TYPE

  local __source_code_path
  local __current_directory

  if [[ ! -e "$PWD/hnn.py" ]]; then
    echo -e "\nBad hnn_source_code directory at $PWD" | tee -a "$LOGFILE"
    cleanup 2
  fi

  if [[ "$CONTAINER_TYPE" == "linux" ]]; then
    __source_code_path="/home/hnn_user/hnn_source_code"
  else
    __source_code_path="/c/home/hnn_user/hnn_source_code"
  fi

  print_header_message "Removing old hnn_source_code from container... "
  COMMAND=(6 "$docker_cmd" "exec" "$HNN_CONTAINER_NAME" "bash" "-c" "rm -rf $__source_code_path/*")
  convert_COMMAND_to_escaped_array
  output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fail_on_bad_exit $?

  # exceptions for windows containers
  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    COMMAND=(3 "cygpath.exe" "-w" "$PWD")
    convert_COMMAND_to_escaped_array
    __current_directory=$(output_run_command_arguments "${ESCAPED_COMMAND[@]}")
    if [[ $? -ne 0 ]]; then
      cleanup 2
    fi
    __current_directory="$__current_directory\."

    stop_container_silent
  else
    __current_directory="$PWD/."
  fi
  print_header_message_short "Copying hnn_source_code into container... "
  COMMAND=(4 "$docker_cmd" "cp" "$__current_directory" "$HNN_CONTAINER_NAME:/home/hnn_user/hnn_source_code/")
  convert_COMMAND_to_escaped_array
  MSYS_NO_PATHCONV=1 output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fail_on_bad_exit $?
  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    start_container_silent
  fi
}

function copy_hnn_out_fail {
  # copies $SYSTEM_USER_DIR/hnn_out to hnn_source_code
  check_var docker_cmd
  check_var HNN_CONTAINER_NAME
  check_var LOGFILE
  check_var CONTAINER_TYPE
  check_var TRAVIS_TESTING

  local __hnn_out
  __hnn_out="$SYSTEM_USER_DIR/hnn_out"

  if [[ ! -e "$__hnn_out" ]]; then
    echo -e "\nError: hnn_out doesn't exist at $__hnn_out" | tee -a "$LOGFILE"
    cleanup 2
  fi

  if [[ "$OS" == "mac" ]] && [[ $TRAVIS_TESTING -eq 1 ]]; then
    print_header_message "Creating hnn_out in container... "
    COMMAND=(8 "$docker_cmd" "exec" "-u" "root" "$HNN_CONTAINER_NAME" "bash" "-c" \
             "mkdir -p \"$__hnn_out/data\" && \
              mkdir -p \"$__hnn_out/param\" && \
              chown -R hnn_user:hnn_group \"$__hnn_out\" && \
              chmod 777 -R \"$__hnn_out\"")
    convert_COMMAND_to_escaped_array
    output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
    fail_on_bad_exit $?
  else
    print_header_message "Removing old hnn_out from container... "

    if [[ "$CONTAINER_TYPE" == "windows" ]]; then
      COMMAND=(6 "$docker_cmd" "exec" "$HNN_CONTAINER_NAME" "bash" "-c" "rm -rf $__hnn_out/*")
    else
     COMMAND=(8 "$docker_cmd" "exec" "-u" "root" "$HNN_CONTAINER_NAME" "bash" "-c" "rm -rf $__hnn_out/*")
    fi
    convert_COMMAND_to_escaped_array
    output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
    fail_on_bad_exit $?
  fi

  __hnn_out_contents="$__hnn_out/."
  # exceptions for windows containers
  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    COMMAND=(3 "cygpath.exe" "-w" "$__hnn_out_contents")
    convert_COMMAND_to_escaped_array
    __hnn_out_contents=$(output_run_command_arguments "${ESCAPED_COMMAND[@]}")
    if [[ $? -ne 0 ]]; then
      cleanup 2
    fi

    # remove leading /c/
    __hnn_out="$(echo $__hnn_out | sed 's/^\/[cC]\(.*\)$/\1/')"
    stop_container_silent
  fi
  print_header_message_short "Copying hnn_out into container... "
  COMMAND=(4 "$docker_cmd" "cp" "$__hnn_out_contents" "$HNN_CONTAINER_NAME:$__hnn_out")
  convert_COMMAND_to_escaped_array
  MSYS_NO_PATHCONV=1 output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fail_on_bad_exit $?
  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    start_container_silent
  fi
}

function change_hnn_source_perms_fail {
  check_var docker_cmd
  check_var HNN_CONTAINER_NAME
  check_var CONTAINER_TYPE
  check_var USE_SSH
  check_var UID

  local __container_user
  local __user

  if [[ $USE_SSH -eq 0 ]]; then
    __user="$UID"
  else
    __user="hnn_user"
  fi

  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    return 0
  else
    __container_user="root"
    __source_code_path="/home/hnn_user/hnn_source_code"
  fi
  print_header_message "Changing hnn_source_code permissions in container... "
  COMMAND=(8 "$docker_cmd" "exec" "-u" "$__container_user" "$HNN_CONTAINER_NAME" "bash" "-c" \
          "chown -R $__user $__source_code_path")
  convert_COMMAND_to_escaped_array
  output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fail_on_bad_exit $?
}

function copy_ssh_files_to_container_fail {
  # no arguments
  # *** This probably won't work with windows containers because paths are in UNIX format *****
  check_var docker_cmd
  check_var SSH_AUTHKEYS
  check_var SSH_PUBKEY
  check_var CONTAINER_TYPE

  local __authkeys
  local __pubkey
  __authkeys="$SSH_AUTHKEYS"
  __pubkey="$SSH_PUBKEY"

  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    COMMAND=(3 "cygpath.exe" "-w" "$__authkeys")
    convert_COMMAND_to_escaped_array
    __authkeys=$(output_run_command_arguments "${ESCAPED_COMMAND[@]}")
    if [[ $? -ne 0 ]]; then
      cleanup 2
    fi

    COMMAND=(3 "cygpath.exe" "-w" "$__pubkey")
    convert_COMMAND_to_escaped_array
    __pubkey=$(output_run_command_arguments "${ESCAPED_COMMAND[@]}")
    if [[ $? -ne 0 ]]; then
      cleanup 2
    fi

    stop_container_silent
  fi

  print_header_message_short "Copying authorized_keys file into container... "
  COMMAND=(4 "$docker_cmd" "cp" "$__authkeys" "$HNN_CONTAINER_NAME:/home/hnn_user/.ssh/authorized_keys")
  convert_COMMAND_to_escaped_array
  MSYS_NO_PATHCONV=1 output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fail_on_bad_exit $?

  print_header_message_short "Copying known_hosts file into container... "
  COMMAND=(4 "$docker_cmd" "cp" "$__pubkey" "$HNN_CONTAINER_NAME:/home/hnn_user/.ssh/known_hosts")
  convert_COMMAND_to_escaped_array
  MSYS_NO_PATHCONV=1 output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fail_on_bad_exit $?
  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    start_container_silent
    # don't bother updating unix permissions
    return 0
  fi

  print_header_message_short "Updating ownership on ssh files in container... "
  COMMAND=(8 "$docker_cmd" "exec" "-u" "root" "$HNN_CONTAINER_NAME" "bash" "-c" "chown -R hnn_user /home/hnn_user/.ssh")
  convert_COMMAND_to_escaped_array
  output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fail_on_bad_exit $?

  print_header_message_short "Updating permissions on ssh authorized_keys file in container... "
  COMMAND=(8 "$docker_cmd" "exec" "-u" "root" "$HNN_CONTAINER_NAME" "bash" "-c" "chmod 600 /home/hnn_user/.ssh/authorized_keys")
  convert_COMMAND_to_escaped_array
  output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fail_on_bad_exit $?
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
            echo "killed $__proc ($__pid)" >> "$LOGFILE"
          else
            silent_run_command "kill -9 $__pid"
            if [[ $? -eq 0 ]]; then
              echo "killed $__proc ($__pid)" >> "$LOGFILE"
            else
              echo "failed to kill $__proc ($__pid)" >> "$LOGFILE"
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
    echo "couldn't stop all Xquartz procs after 5 retries" >> "$LOGFILE"
    false
  else
    if [[ -e /tmp/.X*-lock ]]; then
      echo "Removing locks: $(ls /tmp/.X*-lock)" >> "$LOGFILE"
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
    log_header_message "Getting running Xquartz processes... "
    __command="pgrep Xquartz"
    __pid=$(output_run_command "$__command")
    if [[ $? -eq 0 ]]; then
      if [[ "$__pid" =~ ' ' ]]; then
        echo "Started more than one Xquartz: $__pid" >> "$LOGFILE"
        __pid=$(echo $__pid|sed 's/\([0-9]\{1,\}\) [0-9]\{1,\}/\1/')
        echo "Using $__pid" >> "$LOGFILE"
      fi
      __xquartz_display=$(ps $__pid|grep $__pid|sed 's/.*\(\:[0-9]\{1,\}\).*/\1/')
      __display_int=$(echo $__xquartz_display|sed 's/\:\([0-9]\{1,\}\)/\1/')
      if [[ -e "/tmp/.X11-unix/X${__display_int}" ]]; then
        echo "done" >> "$LOGFILE"
        echo "Started XQuartz on DISPLAY $__xquartz_display" >> "$LOGFILE"
        break
      fi
    fi
    echo "done" >> "$LOGFILE"
    sleep 1
    (( __timeout-- ))
  done

  if [[ $__timeout -eq 0 ]]; then
    if [[ -n $__display_int ]]; then
      echo "/tmp/.X11-unix/X${__display_int} not found" >> "$LOGFILE"
    fi
    false
  fi

  echo $__display_int
}

function start_xquartz {
  check_var LOGFILE

  local __port
  local __command

  __command="open -a XQuartz"
  silent_run_command "$__command"
  if [[ $? -ne "0" ]]; then
    # this probably will never fail on a mac
    cleanup 2
  fi

  re='^[0-9]+$'
  __port=$(get_xquartz_port)
  if [[ $? -ne 0 ]]; then
    exit 2
  elif ! [[ $__port =~ $re ]] ; then
    echo "bad xquartz port number \"$__port\"" >> "$LOGFILE"
    false
  else
    # update DISPLAY
    set_local_display_from_port $__port
  fi
}

function restart_xquartz_fail {
  # no arguments
  # kills all xquartz processes that then starts one
  # returns port number of listening xquartz process
  local __xquartz_port

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
  check_var docker_cmd
  check_var LOGFILE
  check_var OS
  check_var HNN_DOCKER_IMAGE
  check_var TRAVIS_TESTING
  check_var CONTAINER_TYPE

  local __command
  local __docker_container
  local __last_used_image
  local __docker_image

  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    __docker_image="${HNN_DOCKER_IMAGE}:win64"
  else
    __docker_image="${HNN_DOCKER_IMAGE}"
  fi

  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    __command="$docker_cmd pull --disable-content-trust ${__docker_image}"
  else
    __command="$docker_cmd pull ${__docker_image}"
  fi

  silent_run_command "$__command"
  if [[ $? -eq "0" ]]; then
    echo "done" | tee -a "$LOGFILE"
    print_header_message "Looking for existing containers... "
    __docker_container=$(output_existing_container_command)
    if [[ $? -eq "0" ]]; then
      __last_used_image=$(echo ${__docker_container}|cut -d' ' -f 2)
      if [[ "${__last_used_image}" =~ "${HNN_DOCKER_IMAGE}" ]]; then
        echo "found, running up to date image" | tee -a "$LOGFILE"
        UPGRADE=0
      else
        echo "found, running outdated image" | tee -a "$LOGFILE"
        prompt_remove_container_fail
      fi
    else
      echo "not found" | tee -a "$LOGFILE"
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
    echo "*failed*" | tee -a "$LOGFILE"
    false
  fi
}

function docker_run_fail {
  # no arguments
  # will run the appropriate docker command
  # to leave a running containers
  check_var TRAVIS_TESTING
  check_var LOGFILE
  check_var OS
  check_var USE_SSH
  check_var CONTAINER_TYPE

  local __timeout
  local __started
  local __command_status
  local __command
  local __index
  local __arg
  local __send_args
  local __docker_image
  local __home
  local __hnn_out
  local __container_xauthority

  __timeout=20

  print_header_message "Creating HNN container... "

  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    # Interesting that HOME still gets turned into a windows path. Easy to avoid
    # by passing the HOME variable under a new name HOME_UNIX
    export HOME_UNIX="${HOME}"
    __docker_image="${HNN_DOCKER_IMAGE}:win64"
  else
    __docker_image="${HNN_DOCKER_IMAGE}"
  fi

  # exceptions for windows containers
  __hnn_out="$SYSTEM_USER_DIR/hnn_out"
  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    COMMAND=(3 "cygpath.exe" "-w" "$__hnn_out")
    convert_COMMAND_to_escaped_array
    __hnn_out=$(output_run_command_arguments "${ESCAPED_COMMAND[@]}")
    if [[ $? -ne 0 ]]; then
      cleanup 2
    fi
  fi

  __container_xauthority="/tmp/.Xauthority"
  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    __container_xauthority="/c/home/hnn_user/.Xauthority"
  fi

  if [[ "$OS" == "mac" ]] && [[ $TRAVIS_TESTING -eq 1 ]]; then
    # Workarounds for qemu docker-machine driver that doesn't support port forwarding and volume
    # mounts properly.
    # This binds port 22 in the container (for sshd) to 5000 on the host, which on docker toolbox
    # is a VM. We can then configure the VM with docker-machine to allow connections to port 5000 from
    # the base OS. Also connect port 6000 to allow for xforwarding of the xserver.
    COMMAND=(14 "${docker_cmd}" "run" "-d" \
              "-p" "6000:6000" "-p" "5000:22" \
              "--env" "XAUTHORITY=$__container_xauthority" "--env" "SYSTEM_USER_DIR=$SYSTEM_USER_DIR" \
              "--name" "$HNN_CONTAINER_NAME" "$__docker_image")
  elif [[ "$OS" == "linux" ]]; then
    COMMAND=(16 "${docker_cmd}" "run" "-d" \
              "-p" "22" \
              "-v" "/tmp/.X11-unix:/tmp/.X11-unix" \
              "-v" "$__hnn_out:$__hnn_out" \
              "--env" "XAUTHORITY=$__container_xauthority" "--env" "SYSTEM_USER_DIR=$SYSTEM_USER_DIR" \
              "--name" "$HNN_CONTAINER_NAME" "$__docker_image")
  else # windows and mac (TRAVIS_TESTING=0)
    COMMAND=(14 "${docker_cmd}" "run" "-d" \
            "-p" "22" \
            "-v" "$__hnn_out:$__hnn_out" \
            "--env" "XAUTHORITY=$__container_xauthority" "--env" "SYSTEM_USER_DIR=$SYSTEM_USER_DIR" \
            "--name" "$HNN_CONTAINER_NAME" "$__docker_image")
  fi

  convert_COMMAND_to_escaped_array
  MSYS_NO_PATHCONV=1 output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  if [[ $? -ne 0 ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    cleanup 2
  fi

  # make sure "docker ps | grep HNN_CONTAINER_NAME" succeeeds
  __started=$(wait_for_container_to_start $__timeout)
  if [[ ! "$__started" =~ "1" ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    echo "Waited for $__timeout seconds for container to start" >> "$LOGFILE"
    cleanup 2
  else
    echo "done" | tee -a "$LOGFILE"
  fi
}

function print_sshd_log {
  # no args
  # if sshd has been started and container exists,
  # run "docker logs --tail 100 HNN_CONTAINER_NAME"
  check_var SSHD_STARTED

  if [[ $SSHD_STARTED -eq 1 ]]; then
    check_var LOGFILE
    check_var docker_cmd
    check_var HNN_CONTAINER_NAME
    echo -e "\n=====================" >> "$LOGFILE"
    echo "Logs from sshd in container: ">> "$LOGFILE"
    MSYS_NO_PATHCONV=1 silent_run_command "$docker_cmd exec -u root $HNN_CONTAINER_NAME cat /var/log/sshd.log"
  fi
}

function generate_xauth_keys_fail {
  check_var xauth_cmd
  check_var XAUTHORITY
  check_var DISPLAY

  local __binary
  local __command_args
  local __output

  print_header_message "Generating xauth key for display $DISPLAY... "
  COMMAND=(6 "${xauth_cmd}" "-f" "$XAUTHORITY" "generate" "$DISPLAY" ".")
  convert_COMMAND_to_escaped_array
  output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fail_on_bad_exit $?
}

function get_host_xauth_keys {
  check_var LOGFILE
  check_var xauth_cmd
  check_var XAUTHORITY
  check_var DISPLAY
  check_var DEBUG

  local __output
  local __suppress_output
  local __keys
  local __command_status

  if [[ $DEBUG -eq 1 ]]; then
    __suppress_output=0
  else
    # don't display the keys in the log file
    __suppress_output=1
  fi

  log_header_message "Retrieving host xauth keys... "
  COMMAND=(6 "${xauth_cmd}" "-f" "$XAUTHORITY" "-ni" "nlist" "$DISPLAY")
  convert_COMMAND_to_escaped_array
  __keys=$(SUPPRESS_OUTPUT=$__suppress_output output_run_command_arguments "${ESCAPED_COMMAND[@]}")
  __command_status=$?
  if [[ $__command_status -ne 0 ]]; then
    echo "*failed*" >> "$LOGFILE"
    exit $__command_status
  else
    echo "done" >> "$LOGFILE"
    echo "$__keys"
  fi
}

function check_xauth_keys_print {
  # no arguments
  check_var LOGFILE

  local __output
  local __command_status

  print_header_message "Checking for X11 authentication keys... "
  __output=$(get_host_xauth_keys)
  __command_status=$?
  echo >> "$LOGFILE"
  if [[ $__command_status -ne 0 ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    exit $__command_status
  elif [[ -z "$__output" ]]; then
    echo "no valid keys" | tee -a "$LOGFILE"
    false
  else
    echo "done" | tee -a "$LOGFILE"
  fi
}

function start_check_container_sshd_fail {
  # no arguemnts
  # run /start_ssh.sh within container and detach, leaving sshd running
  check_var docker_cmd
  check_var HNN_CONTAINER_NAME
  check_var DEBUG

  print_header_message "Starting sshd in container... "
  # using -d to detach, as the sshd command will hold on to the shell and freeze the script
  MSYS_NO_PATHCONV=1 run_command_print_status_failure_exit "$docker_cmd exec -d -e DEBUG=$DEBUG -u root $HNN_CONTAINER_NAME /start_ssh.sh"

  # check that sshd is running on container port 22 and fail if not
  check_sshd_port_print
  if [[ $? -ne 0 ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    cleanup 2
  fi

  SSHD_STARTED=1
}

function check_xauth_cmd_print {
  # no arguments
  # if "which xauth" succeeds, run "xauth version" to check that it works
  check_var xauth_cmd
  check_var XAUTHORITY
  check_var LOGFILE

  local __command
  local __index
  local __send_args
  local __arg

  print_header_message "Checking that $xauth_cmd works... "
  echo >> "$LOGFILE"
  __command=("${xauth_cmd}" version)

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
    echo "done" | tee -a "$LOGFILE"
  else
    echo "*failed*" | tee -a "$LOGFILE"
    false
  fi
}

function get_display_for_gui {
  # no arguments
  # set DISPLAY environment variable for the appropriate OS and/or testing environment
  check_var DOCKER_TOOLBOX
  check_var CONTAINER_TYPE
  check_var TRAVIS_TESTING

  local __display
  local __port

  if [ -n $DISPLAY ]; then
    __port=${DISPLAY#*:}
  else
    __port="0"
  fi

  # set DISPLAY for GUI
  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    log_header_message "Getting IP for DISPLAY from container... "
    COMMAND=(6 "$docker_cmd" "exec" "$HNN_CONTAINER_NAME" "bash" "-c" "ipconfig.exe | grep 'Default Gateway'| sed -e 's/^.*:[ \t]*\(.*\)/\1/'")
    convert_COMMAND_to_escaped_array
    __ip=$(output_run_command_arguments "${ESCAPED_COMMAND[@]}")
    if [[ $? -ne 0 ]]; then
      echo "*failed*" >> "$LOGFILE"
      exit 2
    else
      echo "done" >> "$LOGFILE"
    fi
    __display="$__ip:$__port"
  else
    if [[ "$OS" =~ "linux" ]]; then
      # linux can use direct port
      if [[ $TRAVIS_TESTING -eq 1 ]]; then
        [[ $DISPLAY ]] && __display=$DISPLAY || __display=":$__port"
      else
        __display=":$__port"
      fi
    else
      if [[ $TRAVIS_TESTING -eq 1 ]]; then
        # qemu driver
        __display="10.0.2.2:$__port"
      elif [[ $DOCKER_TOOLBOX -eq 1 ]]; then
        # virtualbox driver
        __display="192.168.99.1:$__port"
      else
        # docker desktop
        __display="host.docker.internal:$__port"
      fi
    fi
  fi

  echo $__display
}


function get_valid_host_xauth_key {
  # no arguments
  # retrieves xauth key from host
  check_var DISPLAY
  check_var xauth_cmd
  check_var XAUTHORITY
  check_var DEBUG

  local __keys
  local __key
  local __command_status

  __keys=$(get_host_xauth_keys)
  __command_status=$?
  if [[ $? -ne 0 ]]; then
    return $__command_status
  else
    log_header_message "Validating host xauth keys... "
    __key="$(echo $__keys | grep 'ffff' | head -1 | awk '{print $NF}')"
    if [[ -z "$__key" ]]; then
      # no output means no valid keys
      echo "*failed*" >> "$LOGFILE"
      echo -e "  ** Error: no valid key **" >> "$LOGFILE"
      return 1
    else
      echo "done" >> "$LOGFILE"
      if [[ $DEBUG -eq 1 ]]; then
        echo "Valid key: =START=$__key=END=" >> "$LOGFILE"
      fi
      echo "$__key"
    fi
  fi
}

function get_container_xauth_key {
  # first argument is username inside container to check permissions for
  # checks that xauth run within container retuns valid keys

  check_args "$@" $# 1

  check_var docker_cmd
  check_var HNN_CONTAINER_NAME
  check_var DEBUG

  local __keys
  local __key
  local __user
  local __display
  local __suppress_output
  local __command_status
  __user="$1"
  __display=$(get_display_for_gui)
  if [[ $? -ne 0 ]]; then
    cleanup 2
  fi

  log_header_message "Retrieving container xauth keys... "
  COMMAND=(8 "$docker_cmd" exec "-u" "$__user" "$HNN_CONTAINER_NAME" "bash" "-c" "timeout 5 xauth -ni nlist $__display")
  convert_COMMAND_to_escaped_array
  # don't display the keys in the log file
  if [[ $DEBUG -eq 1 ]]; then
    __suppress_output=0
  else
    __suppress_output=1
  fi
  __keys=$(SUPPRESS_OUTPUT=$__suppress_output output_run_command_arguments "${ESCAPED_COMMAND[@]}")
  __command_status=$?
  if [[ $__command_status -ne 0 ]]; then
    echo "*failed*" >> "$LOGFILE"
    exit $__command_status
  else
    echo "done" >> "$LOGFILE"

    log_header_message "Validating container xauth keys... "
    __key="$(echo $__keys | grep 'ffff' | head -1 | awk '{print $NF}')"
    if [[ -z "$__key" ]]; then
      # no output means no valid keys
      echo "*failed*" >> "$LOGFILE"
      echo -e "  ** Error: no valid key **" >> "$LOGFILE"
      return 1
    else
      echo "done" >> "$LOGFILE"
    fi

    if [[ $DEBUG -eq 1 ]]; then
      echo "Valid key: =START=$__key=END=" >> "$LOGFILE"
    fi
    echo "$__key"
  fi
}

function check_container_xauth_print {
  # first argument is username inside container to check permissions for
  check_args "$@" $# 1

  check_var LOGFILE
  check_var RETRY
  check_var CONTAINER_TYPE

  local __user
  local __command_status
  local __host_key
  local __key

  __user=$1
  __host_key=$(get_valid_host_xauth_key)
  __command_status=$?
  if [[ $__command_status -ne 0 ]]; then
    cleanup 2
  fi

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a "$LOGFILE"
    RETRY=0
  fi

  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    __key=$(get_container_xauth_key "hnn_user")
  else
    __key=$(get_container_xauth_key $1)
  fi
  __command_status=$?


  print_header_message "Checking that xauth key in container matches... "
  if [[ $__command_status -ne 0 ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    echo -e " ** Error: could not retrieve keys from container **" >> "$LOGFILE"
    return 1
  elif [[ "$__host_key" == "$__key" ]]; then
    echo "done" | tee -a "$LOGFILE"
  else
    echo "*$__host_key* != *$__key*" >> "$LOGFILE"
    echo "*failed*" | tee -a "$LOGFILE"
    echo -e "  ** Error: key mismatch **" >> "$LOGFILE"
    return 1
  fi
}

function setup_xauthority_in_container_fail {
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
    check_container_xauth_print "$__user"
    if [[ $? -ne 0 ]]; then
      RETRY=1
      false
    fi
  else
    false
  fi

  if [[ $? -ne 0 ]]; then
    # copy the key, new or not
    copy_xauthority_file_fail "$__user"
    # make sure that xauth works in container now
    check_container_xauth_print "$__user"
    if [[ $? -ne 0 ]]; then
      cleanup 2
    fi
  fi
}

function set_local_display_from_port {
  # first argument in port number (e.g. 0, not :0)
  check_args "$@" $# 1

  check_var TRAVIS_TESTING

  local __port="$1"

  # no arguments
  # set DISPLAY for local actions (e.g. generating xauth keys)
  if [[ "$OS" =~ "windows" ]]; then
    DISPLAY="localhost:$__port"
  elif [[ "$OS" =~ "mac" ]]; then
    DISPLAY=":$__port"
  else
    # linux
    if [[ $TRAVIS_TESTING -eq 1 ]]; then
      [[ $DISPLAY ]] || DISPLAY=":$__port"
    else
      DISPLAY=":$__port"
    fi
  fi
  export DISPLAY
}

function check_xquartz_listening {
  # no args
  # will return when xquartz is configured and listening on tcp port
  # DISPLAY will be updated

  local __retry
  local __current_port

  [[ $OS ]] || export OS=$(get_os)
  if [[ $? -ne 0 ]]; then
    cleanup 2
  fi

  # before assuming port 0, check if xquartz is already running
  __current_port=$(get_xquartz_port)
  if [[ $? -ne 0 ]]; then
    exit 2
  elif [[ -z $__current_port ]]; then
    __current_port="0"
  fi
  set_local_display_from_port $__current_port

  let __retry=0
  while ! config_xquartz_for_tcp; do
    if [[ $__retry -eq 3 ]]; then
      false
      return
    fi
    __current_port=$(restart_xquartz_fail)
    if [[ $? -ne 0 ]]; then
      exit 2
    fi
    sleep 1
    (( __retry++ ))
  done

  true
}

function config_xquartz_for_tcp {
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
    echo "*failed*" | tee -a "$LOGFILE"
    echo -e "\nNo valid output from org.macosforge.xquartz.X11.plist" | tee -a "$LOGFILE"
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
      echo -n "(retry) " | tee -a "$LOGFILE"
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

function check_local_ssh_keys_print {
  check_var LOGFILE
  check_var SSH_PRIVKEY
  check_var SSH_PUBKEY
  check_var SSH_AUTHKEYS

  print_header_message "Checking for SSH authentication files... "
  if [[ ! -f "$SSH_PRIVKEY" ]] || [[ ! -f "$SSH_PUBKEY" ]] || [[ ! -f "$SSH_AUTHKEYS" ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    echo "One or more ssh key missing. Keys need to be recreated" >> "$LOGFILE"
    if [[ -f "$SSH_PRIVKEY" ]]; then
      print_header_message "Removing $SSH_PRIVKEY... "
      run_command_print_status_failure_exit "rm -f $SSH_PRIVKEY"
    fi
    false
  else
    echo "done" | tee -a "$LOGFILE"
    true
  fi
}

function generate_ssh_auth_keys_fail {
  check_var LOGFILE
  check_var SSH_PRIVKEY
  check_var SSH_PUBKEY
  check_var SSH_AUTHKEYS

  print_header_message "Setting up SSH authentication files... "
  echo -e "\n  ** Command: echo -e \"\n\" | ssh-keygen -f $SSH_PRIVKEY -t rsa -N ''" >> "$LOGFILE"
  echo -n "  ** Output: " >> "$LOGFILE"
  echo -e "\n" | ssh-keygen -f "$SSH_PRIVKEY" -t rsa -N '' >> "$LOGFILE" 2>&1
  if [[ $? -ne "0" ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    cleanup 2
  fi

  COMMAND=(3 "chmod" "600" "$SSH_PRIVKEY")
  convert_COMMAND_to_escaped_array
  output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  if [[ $? -ne "0" ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    cleanup 2
  fi
  echo >> "$LOGFILE"

  echo -e "\n  ** Command: { echo -n 'command=\"/home/hnn_user/start_hnn.sh\" '; cat \"$SSH_PUBKEY\"; } > \"$SSH_AUTHKEYS\"" >> "$LOGFILE"
  echo -n "  ** Stderr: " >> "$LOGFILE"
  { echo -n 'command="/home/hnn_user/start_hnn.sh" '; cat "$SSH_PUBKEY"; } > "$SSH_AUTHKEYS" 2>> "$LOGFILE"
  if [[ $? -ne "0" ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    cleanup 2
  fi
  echo >> "$LOGFILE"

  echo "done" | tee -a "$LOGFILE"
}

function find_program_print {
  # first arg is name of program to look for
  check_args "$@" $# 1

  check_var LOGFILE

  local __executable_name
  local __var_name
  local __program
  __program="$1"

  print_header_message "Checking if $__program is installed... "
  if [[ "$OS" =~ "windows" ]]; then
    __executable_name="$__program.exe"
  else
    __executable_name="$__program"
  fi
  run_command_print_status "which $__executable_name"
  if [[ $? -ne 0 ]]; then
    echo "$__program could not be found. Please check its installation." | tee -a "$LOGFILE"
    false
  else
    __var_name=$(echo ${__program}_cmd | sed 's/-/_/g')
    eval $__var_name="$__executable_name"
    export "$__var_name"
  fi
}

function start_docker_machine_fail {
  print_header_message "Starting docker machine... "
  COMMAND=(2 "${docker_machine_cmd}" "start")
  convert_COMMAND_to_escaped_array
  output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fail_on_bad_exit $?
}

function check_docker_working_print {
  check_var LOGFILE
  check_var docker_cmd
  check_var OS
  check_var RETRY


  local __output
  local __toolbox_str

  if  [[ ! -z "${DOCKER_MACHINE_NAME}" ]]; then
    __toolbox_str=" (Toolbox)"
  fi

  if [[ $RETRY -eq 1 ]]; then
    echo -n "(retry) " | tee -a "$LOGFILE"
    RETRY=0
  fi

  print_header_message "Checking if Docker$__toolbox_str is working... "
  COMMAND=(4 "timeout" "5" "$docker_cmd" version)
  convert_COMMAND_to_escaped_array
  __output=$(output_run_command_arguments "${ESCAPED_COMMAND[@]}")
  if [[ $? -ne 0 ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    false
  elif [[ -z "$__output" ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    false
  elif [[ $? -eq 124 ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    echo "Error: timed out connecting to Docker. Please check Docker install" | tee -a "$LOGFILE"
    false
  else
    echo "done" | tee -a "$LOGFILE"
  fi
}

function get_docker_container_type {
  check_var LOGFILE
  check_var docker_cmd

  local __output

  print_header_message "Checking Docker container type... "
  COMMAND=(4 "timeout" "5" "$docker_cmd" info)
  convert_COMMAND_to_escaped_array
  __output=$(output_run_command_arguments "${ESCAPED_COMMAND[@]}")
  if [[ $? -ne 0 ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    cleanup 2
  elif [[ -z "$__output" ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    cleanup 2
  elif [[ $? -eq 124 ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    echo "Error: timed out connecting to Docker. Please check Docker install" | tee -a "$LOGFILE"
    cleanup 2
  else
    if [[ "$(echo $__output | grep "Storage Driver:")" =~ "windowsfilter" ]]; then
      CONTAINER_TYPE="windows"
    else
      CONTAINER_TYPE="linux"
    fi
    echo "$CONTAINER_TYPE" | tee -a "$LOGFILE"
  fi

  if [[ "$CONTAINER_TYPE" == "windows" ]] && [[ "$OS" == "wsl" ]]; then
    echo "** Windows containers not supported in WSL. Use Linux containers. **" | tee -a "$LOGFILE"
    cleanup 1
  fi

  export CONTAINER_TYPE
}

function remove_hnn_image_fail {
  check_var docker_cmd
  check_var HNN_DOCKER_IMAGE
  check_var OS

  local __docker_image

  if [[ "$OS" =~ "windows" ]]; then
    # Interesting that HOME still gets turned into a windows path. Easy to avoid
    # by passing the HOME variable under a new name HOME_UNIX
    export HOME_UNIX="${HOME}"
    __docker_image="${HNN_DOCKER_IMAGE}:win64"
  else
    __docker_image="${HNN_DOCKER_IMAGE}"
  fi


  print_header_message "Removing HNN image... "
  COMMAND=(4 "${docker_cmd}" "rmi" "-f" "${__docker_image}")
  convert_COMMAND_to_escaped_array
  output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fail_on_bad_exit $?
}

function check_vcxsrv_running_print {
  check_var LOGFILE
  check_var TRAVIS_TESTING

  print_header_message_short "Checking if VcXsrv is running... "
  if [[ "$OS" == "wsl" ]]; then
    TASKS=$(powershell.exe -c '& tasklist')
    if [[ $? -ne 0 ]]; then
      echo "*failed*" | tee -a "$LOGFILE"
      cleanup 2
    fi
    export VCXSRV_PID=$(echo "$TASKS"| grep vcxsrv | awk '{print $2}' 2> /dev/null)
  else
    export VCXSRV_PID=$(tasklist | grep vcxsrv | awk '{print $2}' 2> /dev/null)
  fi

  if [ -n "${VCXSRV_PID}" ]; then
    echo -e "\nVcXsrv running with PID $VCXSRV_PID" >> "$LOGFILE"
    echo "yes" | tee -a "$LOGFILE"
    if [[ $TRAVIS_TESTING -eq 1 ]]; then
      echo -e "\nError: Travis expects that VcXsrv will be started every time"
      cleanup 1
    else
      echo "WARNING: continuing with existing VcXsrv process. You many need to stop it and let this script start VcXsrv for the GUI to display"
    fi
  else
    echo "no" | tee -a "$LOGFILE"
    export VCXSRV_PID=
    false
  fi
}

function find_command_suggested_path {
  # first arg is the program to look for
  # second arg is suggested path
  # will export the variable containing the path

  local __new_args

  # check_args is not useful in this case because the path might have spaces

  check_var LOGFILE

  local __path
  local __program
  local __var_name
  local __executable_name
  local __arguments
  __program="$1"
  __path="$2"

  if [[ "$OS" == "windows" ]] || [[ "$OS" == "wsl" ]]; then
    __executable_name="$__program.exe"
  else
    __executable_name="$__program"
  fi

  print_header_message "Checking for $__program... "
  if [ -f "$__path/$__executable_name" ]; then
    echo "found" | tee -a "$LOGFILE"
    __var_name="$(echo ${__program}_cmd | sed 's/-/_/g')"
    eval $__var_name=\"$__path/$__executable_name\"
    export "$__var_name"
  else
    echo "not in $__path" | tee -a "$LOGFILE"
    find_program_print ${__program}
  fi
}

function set_xauthority {
  if [[ "$OS" =~ "linux" ]] && [[ ! -f "$XAUTHORITY" ]]; then
    XAUTHORITY=
  fi

  if [[ -z "$XAUTHORITY" ]]; then
    XAUTHORITY="$HOME/.Xauthority"
  fi

  if [ -d "$XAUTHORITY" ]; then
    print_header_message "Removing misplaced directory $XAUTHORITY... "
    COMMAND=(2 "rmdir" "$XAUTHORITY")
    convert_COMMAND_to_escaped_array
    output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
    fail_on_bad_exit $?
  fi
  export XAUTHORITY
}

function stop_docker_machine_fail {
  check_var $docker_machine_cmd

  print_header_message "Stopping docker machine... "
  COMMAND=(2 "${docker_machine_cmd}" "stop")
  convert_COMMAND_to_escaped_array
  output_run_command_arguments "${ESCAPED_COMMAND[@]}" &> /dev/null
  fail_on_bad_exit $?
}
