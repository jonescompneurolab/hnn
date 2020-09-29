#!/bin/bash

set -e

[[ "$LOGFILE" ]] || LOGFILE="ubuntu_install.log"

function start_download {
  echo "Downloading $2"
  let __retries=5
  while [[ $__retries -gt 0 ]]; do
    curl -Lo "$1" --retry 5 --retry-delay 30 "$2" && break
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
  echo -ne "\n******* install script failed. output from log below  *******\n"
  cat "$LOGFILE"
  exit 2
}

trap script_fail EXIT

DISTRIB=$(grep DISTRIB_CODENAME /etc/lsb-release | cut -d'=' -f2)
echo "Starting installation of HNN on dectected Ubuntu OS: $DISTRIB" | tee -a "$LOGFILE"
echo "Output in log file: $LOGFILE"

[[ $PYTHON_VERSION ]] || {
  if [[ "$DISTRIB" =~ "xenial" ]]; then
    PYTHON_VERSION=3.5
  elif [[ "$DISTRIB" =~ "bionic" ]]; then
    PYTHON_VERSION=3.6
  elif [[ "$DISTRIB" =~ "disco" ]]; then
    PYTHON_VERSION=3.7
  else
    echo "Error: Ubuntu distribtion $DISTRIB not supported" | tee -a "$LOGFILE"
    exit 1
  fi
}
echo "Using python version $PYTHON_VERSION" | tee -a "$LOGFILE"

# avoid questions from debconf
export DEBIAN_FRONTEND=noninteractive

echo "Updating package repository..." | tee -a "$LOGFILE"
sudo -E apt-get update &> "$LOGFILE"

echo "Downloading Python packages..." | tee -a "$LOGFILE"
apt-get download \
  make gcc g++ python3 python3-pip python3-dev python3-tk python3-setuptools \
  libncurses5 libreadline5 libdbus-1-3 libopenmpi-dev &> "$LOGFILE" &
APT_DOWNLOAD=$!

echo "Waiting for package download to finish..."
NAME="downloading python packages"
wait_for_pid "${APT_DOWNLOAD}" "$NAME"

echo "Updating OS python packages..." | tee -a "$LOGFILE"
if [[ "${PYTHON_VERSION}" =~ "3.7" ]] && [[ "$DISTRIB" =~ "bionic" ]]; then
  sudo -E apt-get install --no-install-recommends -y python3.7 python3-pip python3.7-tk python3.7-dev &> "$LOGFILE" && \
    sudo python3.7 -m pip install --upgrade pip setuptools &> "$LOGFILE"
  sudo ln -s /usr/lib/python3/dist-packages/apt_pkg.cpython-36m-x86_64-linux-gnu.so \
    /usr/lib/python3/dist-packages/apt_pkg.so
else
  sudo -E apt-get install --no-install-recommends -y python3 python3-pip python3-tk python3-setuptools &> "$LOGFILE" && \
    sudo pip3 install --upgrade pip &> "$LOGFILE"
fi

if which python3 &> /dev/null; then
  export PYTHON=$(which python3)
  if pip3 -V &> /dev/null; then
    PIP=pip3
  else
    PIP=pip
  fi
elif which python &> /dev/null; then
  export PYTHON=$(which python)
  PIP=pip
fi
echo "Using python: $PYTHON" | tee -a "$LOGFILE"

echo "Downloading python packages for HNN with pip..." | tee -a "$LOGFILE"
$PIP download NEURON matplotlib PyOpenGL \
        pyqt5 pyqtgraph scipy numpy nlopt psutil &> "$LOGFILE" &
PIP_PID=$!

echo "Installing OS compilation toolchain..." | tee -a "$LOGFILE"
# get prerequisites from pip. requires gcc to build psutil
sudo -E apt-get install --no-install-recommends -y \
        make gcc g++ python3-dev &> "$LOGFILE"

echo "Waiting for python packages for HNN downloads to finish..."
NAME="downloading python packages for HNN "
wait_for_pid "${PIP_PID}" "$NAME"

echo "Installing python packages for HNN with pip..." | tee -a "$LOGFILE"
$PIP install --no-cache-dir --user NEURON matplotlib PyOpenGL \
        pyqt5 pyqtgraph scipy numpy nlopt psutil &> "$LOGFILE"

echo "Downloading runtime prerequisite packages..." | tee -a "$LOGFILE"
apt-get download \
  openmpi-bin lsof libfontconfig1 libxext6 libx11-xcb1 libxcb-glx0 \
  libxkbcommon-x11-0 	libgl1-mesa-glx \
  libc6-dev libtinfo-dev libncurses5-dev \
  libx11-dev libreadline-dev \
  libxcb-icccm4 libxcb-util1 libxcb-image0 libxcb-keysyms1 \
  libxcb-render0 libxcb-shape0 libxcb-randr0 libxcb-render-util0 \
  libxcb-xinerama0 &> "$LOGFILE" &
APT_DOWNLOAD=$!

# save dir installing hnn to
startdir=$(pwd)

if [[ $TRAVIS_TESTING -ne 1 ]]; then
  # setup HNN itself
  source_code_dir="$startdir/hnn_source_code"
  if [ -d "$source_code_dir" ]; then
    echo "Updating HNN source code..." | tee -a "$LOGFILE"

    cd hnn_source_code
    if [ -d "$source_code_dir/.git" ]; then
      git pull origin master &> "$LOGFILE"
    fi
  else
    echo "Cloning HNN..." | tee -a "$LOGFILE"
    git clone https://github.com/jonescompneurolab/hnn.git hnn_source_code &> "$LOGFILE" && \
      cd hnn_source_code
  fi
else
  source_code_dir="$startdir"
  if [[ ! -f hnn.py ]]; then
    echo "Couldn't find HNN source code at $startdir" | tee -a "$LOGFILE"
    exit 1
  fi
fi


if [[ $TRAVIS_TESTING -ne 1 ]]; then
  echo "Building HNN..." | tee -a "$LOGFILE"
  make -j4 &> "$LOGFILE"
  MAKE_PID=$!
fi

# create the global session variables
echo '# these lines define global session variables for HNN' >> ~/.bashrc
echo "export PATH=\$PATH:\"$source_code_dir\"" >> ~/.bashrc
if [[ "${PYTHON_VERSION}" =~ "3.6" ]] && [[ "${PYTHON_VERSION}" =~ "3.7" ]]; then
  echo "export PYTHONPATH=/usr/local/nrn/lib/python" >> ~/.bashrc
fi

if [[ -d "$HOME/Desktop" ]]; then
  {
    mkdir -p "$HOME/.local/share/icons" && \
    cp -f hnn.png "$HOME/.local/share/icons/" && \
    cp -f hnn.desktop "$HOME/Desktop" && \
    sed -i "s~/home/hnn_user\(.*\)$~\"$startdir\"\1~g" "$HOME/Desktop/hnn.desktop" && \
    chmod +x "$HOME/Desktop/hnn.desktop"
  } &> "$LOGFILE"
fi

echo "Waiting for prerequisite package downloads to finish..."
NAME="downloading prerequisite packages"
wait_for_pid "${APT_DOWNLOAD}" "$NAME"

echo "Installing prerequisites..." | tee -a "$LOGFILE"
sudo -E apt-get install --no-install-recommends -y \
        openmpi-bin lsof \
        libfontconfig1 libxext6 libx11-xcb1 libxcb-glx0 \
        libxkbcommon-x11-0 	libgl1-mesa-glx \
        libncurses5 libreadline5 libdbus-1-3 libopenmpi-dev \
        libc6-dev libtinfo-dev libncurses5-dev \
        libx11-dev libreadline-dev \
        libxcb-icccm4 libxcb-util1 libxcb-image0 libxcb-keysyms1 \
        libxcb-render0 libxcb-shape0 libxcb-randr0 libxcb-render-util0 \
        libxcb-xinerama0 libxcb-xfixes0 &> "$LOGFILE"

# Clean up a little
echo "Cleaning up..." | tee -a "$LOGFILE"
sudo -E apt-get clean &> "$LOGFILE"

if [[ $TRAVIS_TESTING -ne 1 ]]; then
  echo "Waiting for HNN module build to finish..."
  NAME="building HNN modules"
  wait_for_pid "${MAKE_PID}" "$NAME"
fi

echo "HNN installation successful" | tee -a "$LOGFILE"
echo "Source code is at $source_code_dir" | tee -a "$LOGFILE"

trap EXIT
