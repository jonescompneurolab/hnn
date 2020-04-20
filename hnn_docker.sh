#!/bin/bash

[[ $TRAVIS_TESTING ]] || TRAVIS_TESTING=0
[[ $VERBOSE ]] || VERBOSE=0
[[ $DEBUG ]] || DEBUG=0

[[ $UID ]] || {
  echo -e "\n=====================" >> $LOGFILE
  echo "Error: ${BASH_SOURCE[0]} (L:$BASH_LINENO) expects UID to be set" >> $LOGFILE
  cleanup 1
}

source scripts/utils.sh
export LOGFILE="hnn_docker.log"
set_globals

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

if [[ $START -eq 0 ]] && [[ $STOP -eq 0 ]] && [[ $UNINSTALL -eq 0 ]] && [[ $UPGRADE -eq 0 ]]; then
  echo "No valid action provided. Available actions are start, stop, upgrade, and uninstall" | tee -a $LOGFILE
  cleanup 1
fi

echo >> $LOGFILE
echo "Performing pre-checks before starting HNN" | tee -a $LOGFILE
echo "--------------------------------------" | tee -a $LOGFILE

print_header_message "Checking OS version... "
OS=$(get_os)
echo "$OS" | tee -a $LOGFILE

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
  echo "docker could not be found. Please check its installation." | tee -a $LOGFILE
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
  echo "docker-compose could not be found. Please make sure it was installed with docker." | tee -a $LOGFILE
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
  DOCKER_OUTPUT=$($DOCKER version 2>> $LOGFILE)
else
  DOCKER_OUTPUT=$(timeout 5 $DOCKER version 2>> $LOGFILE)
fi
DOCKER_STATUS=$?
if [[ $DOCKER_STATUS -ne "0" ]] && [[ $TRAVIS_TESTING -eq 1 ]]; then
    echo "*failed*" | tee -a $LOGFILE
elif [[ $DOCKER_STATUS -ne "0" ]]; then
  DOCKER_MACHINE=$(get_docker_machine)
  eval $(${DOCKER_MACHINE} env -u 2> /dev/null)
  eval $(${DOCKER_MACHINE} env 2> /dev/null)
  if [[ "$OS" =~ "mac" ]]; then
    DOCKER_OUTPUT=$($DOCKER version 2>> $LOGFILE)
  else
    DOCKER_OUTPUT=$(timeout 5 $DOCKER version 2>> $LOGFILE)
  fi

  if [[ "$?" -eq "0" ]]; then
    echo "ok (Docker Toolbox)" | tee -a $LOGFILE
  else
    echo "*failed*" | tee -a $LOGFILE
    print_header_message "Starting docker machine... "
    run_command_print_status_failure_exit "${DOCKER_MACHINE} start"
    # rerun env commands in case IP address changed
    eval $(${DOCKER_MACHINE} env -u 2> /dev/null)
    eval $(${DOCKER_MACHINE} env 2> /dev/null)
    print_header_message "Checking again if Docker is working... "
    if [[ "$OS" =~ "mac" ]]; then
      DOCKER_OUTPUT=$($DOCKER version 2>> $LOGFILE)
    else
      DOCKER_OUTPUT=$(timeout 5 $$DOCKER version 2>> $LOGFILE)
    fi
    DOCKER_STATUS=$?
    if [[ $DOCKER_STATUS -ne "0" ]]; then
      echo "*failed*" | tee -a $LOGFILE
      cleanup 2
    fi
    echo "ok (Docker Toolbox)" | tee -a $LOGFILE
  fi
elif [[ $? -eq "124" ]]; then
  echo "Error: timed out connecting to Docker. Please check Docker install" | tee -a $LOGFILE
  cleanup 2
else
  echo "ok${toolbox_str}" | tee -a $LOGFILE
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
  echo "Docker version could not be determined. Please make sure it is installed correctly." | tee -a $LOGFILE
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
    echo -e "\nVcXsrv running with PID $VCXSRV_PID" >> $LOGFILE
    echo "yes" | tee -a $LOGFILE
    stop_vcxsrv
    if [[ $? -ne "0" ]]; then
      echo "WARNING: continuing with existing VcXsrv process. You many need to quit manually for GUI to display"
    fi
  else
    echo "no" | tee -a $LOGFILE
    VCXSRV_PID=
  fi

  VCXSRV_DIR="/c/Program Files/VcXsrv"
  if [ -z "${VCXSRV_PID}" ]; then
    print_header_message_short "Checking if VcXsrv is installed... "
    if [ -f "${VCXSRV_DIR}/vcxsrv.exe" ]; then
      echo "done" | tee -a $LOGFILE
    else
      echo "failed. Could not find 'C:\Program Files\VcXsrv'. Please run XLaunch manually" | tee -a $LOGFILE
      cleanup 1
    fi

    print_header_message "Starting VcXsrv... "
    echo -e "\n  ** Command: ${VCXSRV_DIR}/vcxsrv.exe -wgl -multiwindow 2>&1 &" >> $LOGFILE
    if [[ $DEBUG -eq 1 ]] || [[ $VERBOSE -eq 1 ]]; then
      echo -n "  ** Output: " >> $LOGFILE
      "${VCXSRV_DIR}/vcxsrv.exe" -wgl -multiwindow >> $LOGFILE 2>&1 &
    else
      "${VCXSRV_DIR}/vcxsrv.exe" -wgl -multiwindow > /dev/null 2>&1 &
    fi
    VCXSRV_PID=$!
    echo "done" | tee -a $LOGFILE
    echo "Started VcXsrv with PID ${VCXSRV_PID}" >> $LOGFILE
  fi

  print_header_message_short "Checking for xauth.exe... "
  [[ ${XAUTH_BIN} ]] || XAUTH_BIN="${VCXSRV_DIR}/xauth.exe"
  if [[ ! -f "${XAUTH_BIN}" ]]; then
    echo "*failed*" | tee -a $LOGFILE
    echo "Could not find xauth.exe at ${XAUTH_BIN}. Please set XAUTH_BIN variable at the beginning of this file." | tee -a $LOGFILE
    cleanup 2
  else
    echo "done" | tee -a $LOGFILE
  fi

  set_local_display_from_port 0

elif [[ "$OS" =~ "mac" ]]; then
  check_xquartz_listening
  if [[ $? -ne 0 ]]; then
    cleanup 2
  fi
  # DISPLAY updated with current xquartz port number
fi
# should have X server running by now

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
  get_xauth_bin

  # test xauth
  check_xauth_bin
  if [[ $? -ne "0" ]]; then
    echo "*failed*" | tee -a $LOGFILE
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
    echo "done" | tee -a $LOGFILE
  fi
fi

# XAUTH_BIN should be set
if [[ ! -n "${XAUTH_BIN}" ]]; then
  echo "xauth binary could not be located." | tee -a $LOGFILE
  cleanup 1
fi

print_header_message "Checking for X11 authentication keys... "
OUTPUT=$(get_xauth_keys)
if [[ -z $OUTPUT ]]; then
  echo "no valid keys" | tee -a $LOGFILE
  NEW_XAUTH_KEYS=1
  if [[ "$OS" =~ "mac" ]]; then
    # might be able to fix by restarting xquartz
    echo "XQuartz authentication keys need to be updated" | tee -a $LOGFILE
    restart_xquartz

    # run xauth again
    print_header_message "(retry) Checking for X11 authentication keys... "
    OUTPUT=$(get_xauth_keys)
    if [[ -z $OUTPUT ]]; then
      echo "failed. Error with xauth: no valid keys" | tee -a $LOGFILE
      cleanup 2
    else
      echo "done" | tee -a $LOGFILE
    fi
  else
    generate_xauth_keys
    fail_on_bad_exit $?
    print_header_message "(retry) Checking for X11 authentication keys... "
    OUTPUT=$(get_xauth_keys)
    if [[ -z $OUTPUT ]]; then
      echo "warning: couldn't validate xauth keys" | tee -a $LOGFILE
    else
      echo "done" | tee -a $LOGFILE
    fi
  fi
else
  echo "done" | tee -a $LOGFILE
fi

# ignore hostname in Xauthority by setting FamilyWild mask
# https://stackoverflow.com/questions/16296753/can-you-run-gui-applications-in-a-docker-container/25280523#25280523

KEYS_TO_CONVERT=$(echo $OUTPUT | grep -v '^ffff')
if [[ -n $KEYS_TO_CONVERT ]]; then
  print_header_message "Updating xauth keys for use with docker... "
  echo -e "\n  ** Command: \"${XAUTH_BIN}\" nlist $DISPLAY | sed -e 's/^..../ffff/' | \"${XAUTH_BIN}\" -f \"$XAUTHORITY\" -b -i nmerge -" >> $LOGFILE
  echo -n "  ** Output: " >> $LOGFILE
  "${XAUTH_BIN}" nlist $DISPLAY | sed -e 's/^..../ffff/' | "${XAUTH_BIN}" -f "$XAUTHORITY" -b -i nmerge - >> $LOGFILE 2>&1
  if [[ "$?" -ne "0" ]] || [[ -f "${XAUTHORITY}-n" ]]; then
    echo "*failed*" | tee -a $LOGFILE
    rm -f "${XAUTHORITY}-n"
    cleanup 2
  fi
  echo "done" | tee -a $LOGFILE
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

echo $CWD | tee -a $LOGFILE

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
    echo -e "\n  ** Command: echo -e \"\n\" | ssh-keygen -f $SSH_PRIVKEY -t rsa -N ''" >> $LOGFILE
    echo -n "  ** Output: " >> $LOGFILE
    echo -e "\n" | ssh-keygen -f $SSH_PRIVKEY -t rsa -N '' >> $LOGFILE 2>&1
    if [[ $? -ne "0" ]]; then
      echo "Error: failed running ssh-keygen." | tee -a $LOGFILE
      cleanup 2
    fi

    echo -n "command=\"/home/hnn_user/start_hnn.sh\" " > "$SSH_AUTHKEYS"
    cat "$SSH_PUBKEY" >> "$SSH_AUTHKEYS"
    echo "done" | tee -a $LOGFILE
  fi
fi

echo | tee -a $LOGFILE
echo "Starting HNN" | tee -a $LOGFILE
echo "--------------------------------------" | tee -a $LOGFILE

# check if container exists
output_existing_container_command > /dev/null
if [[ $? -eq "0" ]]; then
  # container does exist, so check if it is running
  print_header_message "Checking for running HNN container... "
  check_for_running_container_command
  if [[ $? -eq "0" ]]; then
    echo "found" | tee -a $LOGFILE
    ALREADY_RUNNING=1
  else
    ALREADY_RUNNING=0
    echo "not found" | tee -a $LOGFILE
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

check_x_port_container
# could open port

setup_xauthority_in_container
# xauth is good

check_hnn_out_perms
# can read/write to hnn_out directory

if [[ $USE_SSH -eq 0 ]]; then
  # start the GUI without SSH

  # start the GUI
  start_hnn
  if [[ $? -ne 0 ]]; then
    cleanup 2
  fi
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
    copy_ssh_files_to_running_container

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
  echo "Testing mode: exited succesfully" | tee -a $LOGFILE
fi

## DONE! all successful cases reach here
cleanup 0
