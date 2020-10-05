#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# we use wait_for_pid and start_download from utils.sh
source "$DIR/utils.sh"

echo "Installing Ubuntu WSL..."
powershell.exe -ExecutionPolicy Bypass -File ./scripts/setup-travis-wsl.ps1 &
WSL_PID=$!

echo "Downloading VcXsrv..."
URL="https://downloads.sourceforge.net/project/vcxsrv/vcxsrv/1.20.8.1/vcxsrv-64.1.20.8.1.installer.exe"
FILENAME="$HOME/vcxsrv-64.1.20.8.1.installer.exe"
start_download "$FILENAME" "$URL" > /dev/null

echo "Installing VcXsrv..."
cmd //c "$HOME/vcxsrv-64.1.20.8.1.installer.exe /S"

[[ ! -f C:/tools/msys64/msys2_shell.cmd ]] && rm -rf C:/tools/msys64
choco uninstall -y mingw
echo "Downloading msys2..."
URL="https://github.com/msys2/msys2-installer/releases/download/2020-09-03/msys2-base-x86_64-20200903.sfx.exe"
FILENAME="$HOME/msys2-base-x86_64-20200903.sfx.exe"
start_download "$FILENAME" "$URL" > /dev/null

echo "Installing VcXsrv..."
cmd //c "$HOME/msys2-base-x86_64-20200903.sfx.exe -y -oC:\\"

# choco upgrade --no-progress -y msys2
export msys2='cmd //C RefreshEnv.cmd '
export msys2+='& set MSYS=winsymlinks:nativestrict '
export msys2+='& C:\\msys64\\msys2_shell.cmd -defterm -no-start'
export mingw64="$msys2 -mingw64 -full-path -here -c "\"\$@"\" --"
export msys2+=" -msys2 -c "\"\$@"\" --"
$msys2 pacman --sync --noconfirm --needed base-devel mingw-w64-x86_64-toolchain python
$msys2 pacman --sync --noconfirm --needed mingw-w64-x86_64-glib2 mingw-w64-cross-binutils mingw-w64-x86_64-pixman

echo "Waiting for WSL install to finish..."
NAME="installing WSL"
wait_for_pid "${WSL_PID}" "$NAME" || script_fail