#!/bin/bash

[[ $TRAVIS_TESTING ]] || TRAVIS_TESTING=0
[[ $VERBOSE ]] || VERBOSE=0
[[ $DEBUG ]] || DEBUG=0

[[ $UID ]] || {
  echo -e "\n=====================" >> "$LOGFILE"
  echo "Error: ${BASH_SOURCE[0]} (L:$BASH_LINENO) expects UID to be set" >> "$LOGFILE"
  cleanup 1
}

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
[[ $LOGFILE ]] || export LOGFILE="$DIR/hnn-docker.log"
source "$DIR/docker_functions.sh"

set_globals
if [[ $? -ne 0 ]]; then
  echo "*failed*" | tee -a "$LOGFILE"
  cleanup 2
fi

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
  echo "No valid action provided. Available actions are start, stop, upgrade, and uninstall" | tee -a "$LOGFILE"
  cleanup 1
fi

echo >> "$LOGFILE"
echo "Performing pre-checks before starting HNN" | tee -a "$LOGFILE"
echo "--------------------------------------" | tee -a "$LOGFILE"

print_header_message "Checking OS version... "
echo "$OS" | tee -a "$LOGFILE"

# defaults
if [[ "$OS" == "linux" ]] || [[ "$OS" == "wsl" ]]; then
  [[ $USE_SSH ]] || USE_SSH=0
else
  [[ $USE_SSH ]] || USE_SSH=1
fi

# check for DOCKER_MACHINE_NAME environment variable
if  [[ ! -z "${DOCKER_MACHINE_NAME}" ]]; then
  DOCKER_TOOLBOX=1
else
  DOCKER_TOOLBOX=0
fi

find_program_print docker || cleanup 1
# ${docker_cmd} is set

check_docker_working_print
if [[ $? -ne "0" ]]; then
  # try loading docker machine env variables
  find_program_print docker-machine
  if [[ $? -eq 0 ]]; then
    # ${docker_machine_cmd} is set
    start_docker_machine_fail
    echo "Relading docker machine environment variables" >> "$LOGFILE"
    eval $("${docker_machine}" env -u 2> /dev/null)
    eval $("${docker_machine}" env 2> /dev/null)
    RETRY=1
    check_docker_working_print
    if [[ $? -ne 0 ]]; then
      cleanup 1
    fi
  else
    cleanup 1
  fi
fi

get_docker_container_type
if [[ $? -ne "0" ]]; then
  exit $?
fi
# CONTAINER_TYPE is set

if [[ $UPGRADE -eq 1 ]]; then
  retry_docker_pull
  if [[ $? -ne 0 ]]; then
    cleanup 2
  fi

  if [[ $START -eq 0 ]]; then
    # just doing upgrade
    cleanup 0
  fi
fi

if [[ $STOP -eq 1 ]]; then
  stop_container_fail
  if [[ "${DOCKER_TOOLBOX}" -eq "1" ]]; then
    stop_docker_machine_fail
  fi
  cleanup 0
fi

if [[ "$UNINSTALL" -eq "1" ]]; then
  find_existing_container_print
  if [[ $? -eq "0" ]]; then
    prompt_remove_container_fail
  fi

  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    remove_hnn_image_fail
    cleanup 0
  fi

  while true; do
    echo
    read -p "Are you sure that you want to remove the HNN image? (y/n)" yn
    case $yn in
      [Yy]* ) remove_hnn_image_fail
              break;;
      [Nn]* ) cleanup 1
              break;;
      * ) echo "Please answer yes or no.";;
    esac
  done
  cleanup 0
fi

# ******************* Starting **********************

set_xauthority
# can use global XAUTHORITY

# start X server and set DISPLAY
if [[ "$OS" == "windows" ]] || [[ "$OS" == "wsl" ]]; then
  check_vcxsrv_running_print
  if [[ $? -ne 0 ]]; then
    find_command_suggested_path "vcxsrv" "/c/Program Files/VcXsrv"
    if [[ $? -ne 0 ]]; then
      echo "Could not find vcxsrv command. Please run XLaunch manually" | tee -a "$LOGFILE"
      cleanup 1
    fi
    start_vcxsrv_print
  fi
  set_local_display_from_port 0
  # DISPLAY is set

  if [[ "$OS" == "windows" ]]; then
    find_command_suggested_path "xauth" "/c/Program Files/VcXsrv"
    if [[ $? -ne 0 ]]; then
      echo "Could not find xauth command. Please check VcXsrv installation" | tee -a "$LOGFILE"
      cleanup 1
    fi
  else
    find_program_print xauth
    if [[ $? -ne 0 ]]; then
      echo "Could not find xauth command." | tee -a "$LOGFILE"
      cleanup 1
    fi
  fi

  set_local_display_from_port 0
elif [[ "$OS" =~ "mac" ]]; then
  check_xquartz_listening
  if [[ $? -ne 0 ]]; then
    echo "Failed to start XQuartz for accepting TCP connections" | tee -a "$LOGFILE"
    cleanup 2
  fi
  # DISPLAY updated with current xquartz port number in check_xquartz_listening

  # macOS will sometimes have a system X11 (before high sierra), so try it first
  # However, it is unlikely to work, so fall back to the XQuartz version
  find_program_print "xauth" && check_xauth_cmd_print
  if [[ $? -ne "0" ]]; then
    if [[ "$OS" =~ "mac" ]]; then
      if [[ ! "${xauth_cmd}" =~ "/opt/X11/bin/xauth" ]] &&
        [[ -f "/opt/X11/bin/xauth" ]]; then
        export xauth_cmd=/opt/X11/bin/xauth
        check_xauth_cmd_print
        if [[ $? -ne "0" ]]; then
          cleanup 2
        fi
      else
        cleanup 2
      fi
    else
      cleanup 2
    fi
  fi
else  # linux and wsl
  find_program_print "xauth" && check_xauth_cmd_print
  if [[ $? -ne "0" ]]; then
    cleanup 2
  fi
fi

check_xauth_keys_print
if [[ $? -ne 0 ]]; then
  NEW_XAUTH_KEYS=1
  if [[ "$OS" =~ "mac" ]]; then
    # might be able to fix by restarting xquartz
    echo "XQuartz authentication keys need to be updated" | tee -a "$LOGFILE"
    restart_xquartz_fail

    check_xauth_keys_print
    if [[ $? -ne 0 ]]; then
      echo "Error with xauth" | tee -a "$LOGFILE"
      cleanup 2
    fi
  else
    # windows and linux can generate keys from cmdline
    generate_xauth_keys_fail

    check_xauth_keys_print
    if [[ $? -ne 0 ]]; then
      echo "Warning: couldn't validate xauth keys" | tee -a "$LOGFILE"
    fi
  fi
fi

# ignore hostname in Xauthority by setting FamilyWild mask
# https://stackoverflow.com/questions/16296753/can-you-run-gui-applications-in-a-docker-container/25280523#25280523

KEYS_TO_CONVERT=$(echo "$(get_host_xauth_keys)" | grep -v '^ffff')  # we know get_xauth_keys will succeed after above
if [[ -n $KEYS_TO_CONVERT ]]; then
  print_header_message "Updating xauth keys for use with docker... "
  # this command is too complicated to try to wrap in a function... quoting all variables
  echo -e "\n  ** Command: \"${xauth_cmd}\" nlist $DISPLAY | sed -e 's/^..../ffff/' | \"${xauth_cmd}\" -f \"$XAUTHORITY\" -b -i nmerge -" >> "$LOGFILE"
  echo -n "  ** Stderr: " >> "$LOGFILE"
  "${xauth_cmd}" nlist "$DISPLAY" 2>> "$LOGFILE" | sed -e 's/^..../ffff/' | "${xauth_cmd}" -f "$XAUTHORITY" -b -i nmerge - 2>> "$LOGFILE"
  if [[ "$?" -ne "0" ]] || [[ -f "${XAUTHORITY}-n" ]]; then
    echo "*failed*" | tee -a "$LOGFILE"
    rm -f "${XAUTHORITY}-n"
    cleanup 2
  fi
  echo "done" | tee -a "$LOGFILE"
fi

if [[ $USE_SSH -eq 1 ]]; then
  # set up ssh keys
  check_local_ssh_keys_print
  if [[ $? -ne "0" ]]; then
    generate_ssh_auth_keys_fail
  fi
fi

check_hnn_out_perms_host
if [[ $? -ne "0" ]]; then
  fix_hnn_out_perms_host_fail
fi

echo | tee -a "$LOGFILE"
echo "Starting HNN" | tee -a "$LOGFILE"
echo "--------------------------------------" | tee -a "$LOGFILE"

# check if container exists
output_existing_container_command &> /dev/null
if [[ $? -eq "0" ]]; then
  # container does exist, so check if it is running
  print_header_message "Checking for running HNN container... "
  check_for_running_container_command
  if [[ $? -eq "0" ]]; then
    echo "found" | tee -a "$LOGFILE"
    ALREADY_RUNNING=1
  else
    ALREADY_RUNNING=0
    echo "not found" | tee -a "$LOGFILE"
    print_header_message "Starting existing HNN container... "
    start_container_silent
    if [[ $? -eq 0 ]]; then
      echo "done" | tee -a "$LOGFILE"
    else
      echo "*failed*" | tee -a "$LOGFILE"
      if [[ $TRAVIS_TESTING -eq 1 ]]; then
        find_existing_container_print
        if [[ $? -eq "0" ]]; then
          print_header_message "Removing old container... "
          remove_container_fail
        fi
      else
        echo "Removing old container might resolve failure. Verification required." | tee -a "$LOGFILE"
        prompt_remove_container_fail
      fi
    fi
  fi
else
  ALREADY_RUNNING=0
fi

if [[ $ALREADY_RUNNING -eq 0 ]]; then
  # start the container
  docker_run_fail
  # container is up

  if [[ $USE_SSH -eq 1 ]]; then
    copy_ssh_files_to_container_fail
  fi

  if [[ $TRAVIS_TESTING -eq 1 ]]; then
    # Use Travis's checkout of the code inside the container
    copy_hnn_source_fail
    copy_hnn_out_fail
  fi
fi

if [[ $TRAVIS_TESTING -eq 1 ]]; then
  # we may not have write access if the user changed (i.e. now USE_SSH=1)
  change_hnn_source_perms_fail
fi

fix_hnn_out_perms_container_print
if [[ $? -ne 0 ]]; then
  fix_hnn_out_perms_host_fail
fi

if [[ "$CONTAINER_TYPE" == "linux" ]]; then
  check_x_port_container_fail
  # could open port
fi

setup_xauthority_in_container_fail
# xauth is good

if [[ $USE_SSH -eq 0 ]]; then
  # start the GUI without SSH

  # start the GUI
  start_hnn_print
  if [[ $? -ne 0 ]]; then
    cleanup 2
  fi
else
  if [[ "$CONTAINER_TYPE" == "windows" ]]; then
    echo "SSH mode not supported with windows containers"
    cleanup 1
  fi
  if [[ $ALREADY_RUNNING -eq 0 ]]; then
    # need to start sshd
    start_check_container_sshd_fail
  else
    # container is still running. check that sshd is running too
    check_sshd_port_print
    if [[ $? -ne 0 ]]; then
      start_check_container_sshd_fail
    fi
  fi
  # sshd is working with container

  # start the GUI with SSH (will confirm that X server port is open)
  # a failure wi
  ssh_start_hnn_print
  if [[ $? -ne 0 ]]; then
    # failure could be caused by bad ssh keys
    copy_ssh_files_to_container_fail

    RETRY=1
    DEBUG=1
    # start the GUI
    ssh_start_hnn_print
    if [[ $? -ne 0 ]]; then
      cleanup 2
    fi
  fi
fi

if [[ $TRAVIS_TESTING -eq 1 ]]; then
  echo "Testing mode: $LOGFILE" | tee -a "$LOGFILE"
fi

## DONE! all successful cases reach here
cleanup 0
