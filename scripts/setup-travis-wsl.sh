#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# we use wait_for_pid and start_download from utils.sh
source "$DIR/utils.sh"

echo "Installing Ubuntu WSL..."
powershell.exe -ExecutionPolicy Bypass -File ./scripts/setup-travis-wsl.ps1 &
WSL_PID=$!

# Note: unable to get VcXServe to start, always missing some dll. First libcrypto, then
# api-ms-win-core-delayload-l1-1-0.dll

echo "Downloading VcXsrv..."
URL="https://downloads.sourceforge.net/project/vcxsrv/vcxsrv/1.20.8.1/vcxsrv-64.1.20.8.1.installer.exe"
FILENAME="$HOME/vcxsrv-64.1.20.8.1.installer.exe"
start_download "$FILENAME" "$URL" > /dev/null

echo "Installing VcXsrv..."
cmd //c "$HOME/vcxsrv-64.1.20.8.1.installer.exe /S"

echo "Starting VcXsrv..."
# note: do not try messing with quotes and escape characters here. you will
# regret it and the time wasted cannot be regained
cmd //c "C:\\PROGRA~1\\VcXsrv\vcxsrv.exe -wgl -multiwindow"

echo "Waiting for WSL install to finish..."
NAME="installing WSL"
wait_for_pid "${WSL_PID}" "$NAME" || script_fail