function sha256sum {
    shasum -a 256 "$@"
}

function cleanup {
    check_var LOGFILE

    local __failed

    __failed=$1

    echo -e "\n=====================" >> $LOGFILE
    echo "cleanup() called from: ${FUNCNAME[1]} (L:${BASH_LINENO[0]})" >> $LOGFILE

    if [[ $__failed -ne "0" ]]; then
    echo -e "\n======================================"
    echo "Error: Please see log output for more details"
    cat $LOGFILE
    return $__failed
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
    echo "*failed*"
    echo "Error: failed $2"
    exit 1
  }
}

function script_fail {
  check_var LOGFILE

  echo -ne "\n*******  hnn_docker.sh failed. output from hnn_docker.log below  *******\n"
  cat "$LOGFILE"
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

