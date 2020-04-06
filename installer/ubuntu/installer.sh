#!/bin/bash
[[ ${NEURON_VERSION} ]] || NEURON_VERSION=7.7
DISTRIB=$(grep DISTRIB_CODENAME /etc/lsb-release | cut -d'=' -f2)
if [[ "$DISTRIB" =~ "xenial" ]]; then
  PYTHON_VERSION=3.5
elif [[ "$DISTRIB" =~ "bionic" ]]; then
  PYTHON_VERSION=3.6
elif [[ "$DISTRIB" =~ "disco" ]]; then
  PYTHON_VERSION=3.7
else
  echo "ubuntu distribtion $DISTRIB not supported"
  exit 1
fi

# avoid questions from debconf
export DEBIAN_FRONTEND=noninteractive

sudo apt-get update
if [[ "${PYTHON_VERSION}" =~ "3.7" ]] && [[ "$DISTRIB" =~ "bionic" ]]; then
  sudo apt-get install --no-install-recommends -y python3.7 python3-pip python3.7-tk python3.7-dev && \
    sudo python3.7 -m pip install --upgrade pip setuptools
else
  sudo apt-get install --no-install-recommends -y python3 python3-pip python3-tk python3-setuptools && \
    sudo pip3 install --upgrade pip
fi

# get prerequisites from pip. requires gcc to build psutil
sudo apt-get install --no-install-recommends -y \
        make gcc g++ python3-dev

which python > /dev/null 2>&1
if [[ $? -eq 0 ]]; then
  # there is another python executable that might be version 2.7
  export PYTHON=$(which python3)
  PIP=pip3
else
  PIP=pip
fi
$PIP install --no-cache-dir --user matplotlib PyOpenGL \
        pyqt5 pyqtgraph scipy numpy nlopt psutil

# base prerequisites packages
sudo apt-get install --no-install-recommends -y \
        openmpi-bin lsof

# Qt prerequisites packages
sudo apt-get install --no-install-recommends -y \
        libfontconfig libxext6 libx11-xcb1 libxcb-glx0 \
        libxkbcommon-x11-0



# Install NEURON
wget -q https://neuron.yale.edu/ftp/neuron/versions/v${NEURON_VERSION}/nrn-${NEURON_VERSION}.$(uname -p)-linux.deb -O /tmp/nrn.deb && \
    sudo dpkg -i /tmp/nrn.deb && \
    rm -f /tmp/nrn.deb

# HNN build prerequisites
sudo apt-get install --no-install-recommends -y \
        libc6-dev libtinfo-dev libncurses-dev \
        libx11-dev libreadline-dev

# save dir installing hnn to
startdir=$(pwd)

# setup HNN itself
if [ -d $startdir/hnn_source_code ]; then
  cd hnn_source_code
  if [ -d $startdir/hnn_source_code/.git ]; then
    git pull origin master
  fi
  make
else
  git clone https://github.com/jonescompneurolab/hnn.git hnn_source_code && \
    cd hnn_source_code &&
    make
fi
cd $startdir

# NEURON runtime prerequisites
sudo apt-get install --no-install-recommends -y \
        libncurses5 libreadline5 libdbus-1-3 libopenmpi-dev

# Clean up a little
sudo apt-get clean

# create the global session variables
echo '# these lines define global session variables for HNN' >> ~/.bashrc
echo "export PATH=\$PATH:$startdir/hnn_source_code" >> ~/.bashrc

if [[ -d "$HOME/Desktop" ]]; then
    mkdir -p $HOME/.local/share/icons && \
    cp -f hnn.png $HOME/.local/share/icons/ && \
    cp -f hnn.desktop $HOME/Desktop && \
    sed -i "s~/home/hnn_user~$startdir~g" $HOME/Desktop/hnn.desktop && \
    chmod +x $HOME/Desktop/hnn.desktop
fi
