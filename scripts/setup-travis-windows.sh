#!/bin/bash
set -e

echo "Installing Microsoft MPI"
powershell -command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/microsoft/Microsoft-MPI/releases/download/v10.1.1/msmpisetup.exe', 'msmpisetup.exe')" && \
    ./msmpisetup.exe -unattend && \
    rm -f msmpisetup.exe

echo "Running HNN Windows install script..."
powershell.exe -ExecutionPolicy Bypass -File ./installer/windows/hnn-windows.ps1

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
