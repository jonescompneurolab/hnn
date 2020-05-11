#!/bin/bash

set -e

[[ ${NEURON_VERSION} ]] || NEURON_VERSION=7.7
[[ "$LOGFILE" ]] || LOGFILE="ubuntu_install.log"

DISTRIB=$(grep DISTRIB_CODENAME /etc/lsb-release | cut -d'=' -f2)
echo "Starting installation of HNN on dectected Ubuntu OS: $DISTRIB" | tee -a "$LOGFILE"
echo "Output in log file: $LOGFILE" | tee -a "$LOGFILE"

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
echo "Will install python version: $PYTHON_VERSION" | tee -a "$LOGFILE"


# avoid questions from debconf
export DEBIAN_FRONTEND=noninteractive

echo "Updating OS python packages..." | tee -a "$LOGFILE"
sudo apt-get update &> "$LOGFILE"
if [[ "${PYTHON_VERSION}" =~ "3.7" ]] && [[ "$DISTRIB" =~ "bionic" ]]; then
  sudo apt-get install --no-install-recommends -y python3.7 python3-pip python3.7-tk python3.7-dev &> "$LOGFILE" && \
    sudo python3.7 -m pip install --upgrade pip setuptools &> "$LOGFILE"
else
  sudo apt-get install --no-install-recommends -y python3 python3-pip python3-tk python3-setuptools &> "$LOGFILE" && \
    sudo pip3 install --upgrade pip &> "$LOGFILE"
fi

echo "Installing OS compilation toolchain..." | tee -a "$LOGFILE"
# get prerequisites from pip. requires gcc to build psutil
sudo apt-get install --no-install-recommends -y \
        make gcc g++ python3-dev &> "$LOGFILE"

which python > /dev/null 2>&1
if [[ $? -eq 0 ]]; then
  # there is another python executable that might be version 2.7
  export PYTHON=$(which python3)
  PIP=pip3
else
  PIP=pip
fi
echo "Using python: $PYTHON" | tee -a "$LOGFILE"

echo "Installing python pacakges for HNN with pip..." | tee -a "$LOGFILE"
$PIP install --no-cache-dir --user matplotlib PyOpenGL \
        pyqt5 pyqtgraph scipy numpy nlopt psutil &> "$LOGFILE"

# base prerequisites packages
echo "Installing OS openmpi..." | tee -a "$LOGFILE"
sudo apt-get install --no-install-recommends -y \
        openmpi-bin lsof &> "$LOGFILE"

# Qt prerequisites packages
echo "Installing Qt OS prerequisites..." | tee -a "$LOGFILE"
sudo apt-get install --no-install-recommends -y \
        libfontconfig libxext6 libx11-xcb1 libxcb-glx0 \
        libxkbcommon-x11-0 &> "$LOGFILE"

echo "Installing NEURON prerequisites..." | tee -a "$LOGFILE"
# NEURON runtime prerequisites
sudo apt-get install --no-install-recommends -y \
        libncurses5 libreadline5 libdbus-1-3 libopenmpi-dev &> "$LOGFILE"

# Install NEURON
echo "Installing NEURON $NEURON_VERSION precompiled package..." | tee -a "$LOGFILE"
wget -q https://neuron.yale.edu/ftp/neuron/versions/v${NEURON_VERSION}/nrn-${NEURON_VERSION}.$(uname -p)-linux.deb -O /tmp/nrn.deb &> "$LOGFILE" && \
    sudo dpkg -i /tmp/nrn.deb &> "$LOGFILE" && \
    rm -f /tmp/nrn.deb &> "$LOGFILE"

# HNN build prerequisites
echo "Installing HNN build prerequisites..." | tee -a "$LOGFILE"
sudo apt-get install --no-install-recommends -y \
        libc6-dev libtinfo-dev libncurses-dev \
        libx11-dev libreadline-dev &> "$LOGFILE"

# save dir installing hnn to
startdir=$(pwd)

if [[ $TRAVIS_TESTING -ne 1 ]]; then
  # setup HNN itself
  if [ -d "$startdir/hnn_source_code" ]; then
    echo "Updating HNN source code..." | tee -a "$LOGFILE"

    cd hnn_source_code
    if [ -d "$startdir/hnn_source_code/.git" ]; then
      git pull origin master &> "$LOGFILE"
    fi
  else
    echo "Cloning HNN..." | tee -a "$LOGFILE"
    git clone https://github.com/jonescompneurolab/hnn.git hnn_source_code &> "$LOGFILE" && \
      cd hnn_source_code
  fi

  echo "Building HNN..." | tee -a "$LOGFILE"
  make -j4 &> "$LOGFILE"

  cd "$startdir"
fi

# Clean up a little
echo "Cleaning up..." | tee -a "$LOGFILE"
sudo apt-get clean &> "$LOGFILE"

# create the global session variables
echo '# these lines define global session variables for HNN' >> ~/.bashrc
echo "export PATH=\$PATH:\"$startdir/hnn_source_code\"" >> ~/.bashrc

if [[ -d "$HOME/Desktop" ]]; then
  {
    mkdir -p "$HOME/.local/share/icons" && \
    cp -f hnn.png "$HOME/.local/share/icons/" && \
    cp -f hnn.desktop "$HOME/Desktop" && \
    sed -i "s~/home/hnn_user\(.*\)$~\"$startdir\"\1~g" "$HOME/Desktop/hnn.desktop" && \
    chmod +x "$HOME/Desktop/hnn.desktop"
  } &> "$LOGFILE"
fi

echo "HNN installation successful" | tee -a "$LOGFILE"
echo "Source code is at $startdir/hnn_source_code" | tee -a "$LOGFILE"
