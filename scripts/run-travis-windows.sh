#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
export TRAVIS_TESTING=1

source "$DIR/docker_functions.sh"
source "$DIR/utils.sh"
export LOGFILE="hnn-docker.log"
set_globals

function cleanup {
    check_var LOGFILE

    local __failed

    __failed=$1

    echo -e "\n=====================" >> "$LOGFILE"
    echo "cleanup() called from: ${FUNCNAME[1]} (L:${BASH_LINENO[0]})" >> "$LOGFILE"

    if [[ $__failed -ne "0" ]]; then
    echo -e "\n======================================"
    echo "Error: Please see log output for more details"
    cat "$LOGFILE"
    return $__failed
    fi
}

export -f cleanup

cd "$DIR/../"
export PATH=$PATH:/C/tools/msys64/mingw64/bin
tar -xf hnn-install.tar.gz
USE_SSH=0 ./hnn-install/hnn-docker.sh start || script_fail
