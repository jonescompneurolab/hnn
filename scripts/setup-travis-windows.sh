#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# we use wait_for_pid and start_download from utils.sh
source "$DIR/utils.sh"

# we use find_program_print and retry_docker_pull from docker_functions.sh
source "$DIR/docker_functions.sh"
export LOGFILE="docker_setup.log"
# docker_functions.sh expects some globals to be set
set_globals

# override the cleanup function in docker_functions.sh to not quit
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

# start the docker pull in the background
find_program_print docker
(retry_docker_pull && touch $HOME/docker_image_loaded) &

# enable windows remoting service to log in as a different user to run tests
powershell -Command 'Start-Service -Name WinRM' > /dev/null

# change settings to allow a blank password for TEST_USER
reg add HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Lsa //t REG_DWORD //v LimitBlankPasswordUse //d 0 //f 2>&1 > /dev/null
net accounts /minpwlen:0 > /dev/null

# create the test user with a space in the username
echo "Creating user: \"test user\"..."
TEST_USER="test user"
echo > "$HOME/test_user_creds"
net user "$TEST_USER" //ADD "//homedir:\\\\%computername%\\users\\$TEST_USER" > /dev/null < "$HOME/test_user_creds"

# add to administrators group
net localgroup administrators "$TEST_USER" //add > /dev/null

# run a command as new user to create home directory
runas //user:"$TEST_USER" "cmd /C whoami" > /dev/null < "$HOME/test_user_creds"

# copy hnn source to test user's home directory
TEST_USER_DIR="/c/Users/$TEST_USER"
if [ -d "$TEST_USER_DIR" ]; then
  mkdir "$TEST_USER_DIR/hnn"
  cp -r "$(pwd)" "$TEST_USER_DIR/"
else
  echo "No user home directory created at $TEST_USER_DIR"
  exit 2
fi

echo "Starting Windows install script..."
powershell.exe -ExecutionPolicy Bypass -File ./installer/windows/hnn.ps1 &
POWERSHELL_PID=$!

echo "Waiting for Windows install script to finish..."
NAME="installing HNN on host system"
wait_for_pid "${POWERSHELL_PID}" "$NAME"

URL="https://downloads.sourceforge.net/project/vcxsrv/vcxsrv/1.20.8.1/vcxsrv-64.1.20.8.1.installer.exe"
FILENAME="$HOME/vcxsrv-64.1.20.8.1.installer.exe"
start_download "$FILENAME" "$URL" > /dev/null &
VCXSRV_PID=$!

# install msys2 to get opengl32.dll from mesa
# this is needed to be able to start vcxsrv for docker tests
[[ ! -f C:/tools/msys64/msys2_shell.cmd ]] && rm -rf C:/tools/msys64
choco uninstall -y mingw

# install vcxsrv for docker tests
echo "Waiting for VcXsrv download to finish..."
NAME="downloading VcXsrv"
wait_for_pid "${VCXSRV_PID}" "$NAME"

echo "Installing msys2 with choco..."
choco upgrade --no-progress -y msys2 &
MSYS2_PID=$!

echo "Installing VcXsrv..."
cmd //c "$HOME/vcxsrv-64.1.20.8.1.installer.exe /S"

echo "Waiting for msys2 installation to finish..."
NAME="isntalling msys2"
wait_for_pid "${MSYS2_PID}" "$NAME"

export msys2='cmd //C RefreshEnv.cmd '
export msys2+='& set MSYS=winsymlinks:nativestrict '
export msys2+='& C:\\tools\\msys64\\msys2_shell.cmd -defterm -no-start'
export mingw64="$msys2 -mingw64 -full-path -here -c "\"\$@"\" --"
export msys2+=" -msys2 -c "\"\$@"\" --"
$msys2 pacman --sync --noconfirm --needed mingw-w64-x86_64-mesa &
# the command above will complete before the docker test begins
