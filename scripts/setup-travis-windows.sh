#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# we use wait_for_pid and start_download from utils.sh
source "$DIR/utils.sh"

[[ $LOGFILE ]] || LOGFILE="hnn_travis.log"

echo "Installing Ubuntu WSL..."
powershell.exe -ExecutionPolicy Bypass -File ./scripts/setup-travis-wsl.ps1 &
WSL_PID=$!

# prepare for installing msys2
[[ ! -f C:/tools/msys64/msys2_shell.cmd ]] && rm -rf C:/tools/msys64
choco uninstall -y mingw

# enable windows remoting service to log in as a different user to run tests
powershell -Command 'Start-Service -Name WinRM' > /dev/null
powershell -Command 'Start-Service -Name seclogon' > /dev/null

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
  cp -r "$(pwd)" "$TEST_USER_DIR/"
else
  echo "No user home directory created at $TEST_USER_DIR"
  exit 2
fi

echo "Installing Microsoft MPI"
powershell -command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/microsoft/Microsoft-MPI/releases/download/v10.1.1/msmpisetup.exe', 'msmpisetup.exe')" && \
    ./msmpisetup.exe -unattend && \
    rm -f msmpisetup.exe

echo "Running HNN Windows install script..."
powershell.exe -ExecutionPolicy Bypass -File ./installer/windows/hnn-windows.ps1
# add miniconda python to the path
export PATH=$PATH:$HOME/Miniconda3/Scripts
export PATH=$HOME/Miniconda3/envs/hnn/:$PATH
export PATH=$HOME/Miniconda3/envs/hnn/Scripts:$PATH
export PATH=$HOME/Miniconda3/envs/hnn/Library/bin:$PATH

echo "Installing msys2 with choco..."
choco upgrade --no-progress -y msys2 &> /dev/null

echo "Downloading VcXsrv..."
URL="https://downloads.sourceforge.net/project/vcxsrv/vcxsrv/1.20.8.1/vcxsrv-64.1.20.8.1.installer.exe"
FILENAME="$HOME/vcxsrv-64.1.20.8.1.installer.exe"
start_download "$FILENAME" "$URL" > /dev/null

echo "Installing VcXsrv..."
cmd //c "$HOME/vcxsrv-64.1.20.8.1.installer.exe /S"

# get opengl32.dll from mesa
# this is needed to be able to start vcxsrv
export msys2='cmd //C RefreshEnv.cmd '
export msys2+='& set MSYS=winsymlinks:nativestrict '
export msys2+='& C:\\tools\\msys64\\msys2_shell.cmd -defterm -no-start'
export mingw64="$msys2 -mingw64 -full-path -here -c "\"\$@"\" --"
export msys2+=" -msys2 -c "\"\$@"\" --"
$msys2 pacman --sync --noconfirm --needed mingw-w64-x86_64-mesa

echo "Downloading python test packages..."
pip download flake8 pytest pytest-cov coverage coveralls mne

echo "Waiting for WSL install to finish..."
NAME="installing WSL"
wait_for_pid "${WSL_PID}" "$NAME" || script_fail
