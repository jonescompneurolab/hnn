#!/bin/bash

# avoid questions from debconf
export DEBIAN_FRONTEND=noninteractive

sudo apt-get update && \
     sudo apt-get upgrade -y

# for NEURON
sudo apt-get install -y git python3-dev python3-pip python3-psutil \
                    bison flex automake libtool libncurses-dev zlib1g-dev \
                    libopenmpi-dev openmpi-bin libqt5core5a libllvm6.0 \
                    libxaw7 libxmu6 libxpm4 libxcb-glx0 \
                    libxkbcommon-x11-0 libfontconfig libx11-xcb1 libxrender1 \
                    git vim iputils-ping net-tools iproute2 nano sudo \
                    telnet language-pack-en-base
sudo pip3 install pip --upgrade
sudo pip install PyOpenGL matplotlib pyqt5 pyqtgraph scipy numpy nlopt

# build MESA from source (for software 3D rendering)
# this part is optional if the 'Model Visualization' feature is not needed
sudo apt-get update && \
    sudo apt-get upgrade -y && \
    sudo apt-get install --no-install-recommends -y \
    wget \
    bzip2 \
    curl \
    python \
    libllvm6.0 \
    llvm-6.0-dev \
    zlib1g-dev \
    xserver-xorg-dev \
    build-essential \
    libxcb-dri2-0-dev \
    libxcb-xfixes0-dev \
    libxext-dev \
    libx11-xcb-dev \
    pkg-config && \
    update-alternatives --install \
        /usr/bin/llvm-config       llvm-config      /usr/bin/llvm-config-6.0  200 \
--slave /usr/bin/llvm-ar           llvm-ar          /usr/bin/llvm-ar-6.0 \
--slave /usr/bin/llvm-as           llvm-as          /usr/bin/llvm-as-6.0 \
--slave /usr/bin/llvm-bcanalyzer   llvm-bcanalyzer  /usr/bin/llvm-bcanalyzer-6.0 \
--slave /usr/bin/llvm-cov          llvm-cov         /usr/bin/llvm-cov-6.0 \
--slave /usr/bin/llvm-diff         llvm-diff        /usr/bin/llvm-diff-6.0 \
--slave /usr/bin/llvm-dis          llvm-dis         /usr/bin/llvm-dis-6.0 \
--slave /usr/bin/llvm-dwarfdump    llvm-dwarfdump   /usr/bin/llvm-dwarfdump-6.0 \
--slave /usr/bin/llvm-extract      llvm-extract     /usr/bin/llvm-extract-6.0 \
--slave /usr/bin/llvm-link         llvm-link        /usr/bin/llvm-link-6.0 \
--slave /usr/bin/llvm-mc           llvm-mc          /usr/bin/llvm-mc-6.0 \
--slave /usr/bin/llvm-mcmarkup     llvm-mcmarkup    /usr/bin/llvm-mcmarkup-6.0 \
--slave /usr/bin/llvm-nm           llvm-nm          /usr/bin/llvm-nm-6.0 \
--slave /usr/bin/llvm-objdump      llvm-objdump     /usr/bin/llvm-objdump-6.0 \
--slave /usr/bin/llvm-ranlib       llvm-ranlib      /usr/bin/llvm-ranlib-6.0 \
--slave /usr/bin/llvm-readobj      llvm-readobj     /usr/bin/llvm-readobj-6.0 \
--slave /usr/bin/llvm-rtdyld       llvm-rtdyld      /usr/bin/llvm-rtdyld-6.0 \
--slave /usr/bin/llvm-size         llvm-size        /usr/bin/llvm-size-6.0 \
--slave /usr/bin/llvm-stress       llvm-stress      /usr/bin/llvm-stress-6.0 \
--slave /usr/bin/llvm-symbolizer   llvm-symbolizer  /usr/bin/llvm-symbolizer-6.0 \
--slave /usr/bin/llvm-tblgen       llvm-tblgen      /usr/bin/llvm-tblgen-6.0 && \
    set -xe; \
    mkdir -p /var/tmp/build; \
    cd /var/tmp/build; \
    wget -q --no-check-certificate "https://mesa.freedesktop.org/archive/mesa-18.0.1.tar.gz"; \
    tar xf mesa-18.0.1.tar.gz; \
    rm mesa-18.0.1.tar.gz; \
    cd mesa-18.0.1; \
    ./configure --enable-glx=gallium-xlib --with-gallium-drivers=swrast,swr --disable-dri --disable-gbm --disable-egl --enable-gallium-osmesa --enable-llvm --prefix=/usr/local; \
    make; \
    sudo make install; \
    cd .. ; \
    rm -rf mesa-18.0.1; \
    sudo apt-get -y remove --purge llvm-6.0-dev \
            zlib1g-dev \
            xserver-xorg-dev \
            python3-dev \
            python \
            pkg-config \
            libxext-dev \
            libx11-xcb-dev \
            libxcb-xfixes0-dev \
            libxcb-dri2-0-dev && \
    sudo apt autoremove -y --purge && \
    sudo apt clean

cd $HOME && \
  git clone https://github.com/neuronsimulator/nrn.git && \
  cd nrn && \
  git checkout 7.7 && \
  ./build.sh && \
  ./configure --with-nrnpython=python3 \
      --with-paranrn --without-iv --disable-rx3d && \
  make && \
  sudo make install

echo '# these lines define global session variables for HNN' >> ~/.bashrc
echo 'export CPU=$(uname -m)' >> ~/.bashrc
echo 'export PATH=$PATH:/usr/local/nrn/$CPU/bin' >> ~/.bashrc
echo 'export OMPI_MCA_btl_base_warn_component_unused=0' >> ~/.bashrc
echo 'export PYTHONPATH=/usr/local/nrn/lib/python:$PYTHONPATH' >> ~/.bashrc

export CPU=$(uname -m)
export PATH=$PATH:/usr/local/nrn/$CPU/bin
export OMPI_MCA_btl_base_warn_component_unused=0
export PYTHONPATH=/usr/local/nrn/lib/python:$PYTHONPATH

cd $HOME && \
  git clone https://github.com/jonescompneurolab/hnn && \
  cd hnn && \
  make

echo '#!/bin/bash' | sudo tee /usr/local/bin/hnn
echo 'cd $HOME/hnn' | sudo tee -a /usr/local/bin/hnn
echo 'python3 hnn.py' | sudo tee -a /usr/local/bin/hnn
sudo chmod 755 /usr/local/bin/hnn

# prepare image
sudo apt-get install -y ec2-ami-tools
echo "PermitRootLogin without-password" | sudo tee -a /etc/ssh/sshd_config  
sudo passwd -l root
sudo rm -rf /tmp/*
sudo shred -u $HOME/.*history
rm -f ~/.sudo_as_admin_successful
rm -f ~/.viminfo
rm -f ~/.Xauthority
sudo rm -rf $HOME/.cache/
rm -rf ~/.gnupg/
rm -rf ~/.config/
rm -rf ~/.ssh/