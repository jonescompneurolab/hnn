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
sudo pip install matplotlib pyqt5 scipy numpy nlopt NEURON

echo '# these lines define global session variables for HNN' >> ~/.bashrc
echo 'export OMPI_MCA_btl_base_warn_component_unused=0' >> ~/.bashrc

export OMPI_MCA_btl_base_warn_component_unused=0

cd $HOME && \
  git clone https://github.com/jonescompneurolab/hnn && \
  cd hnn && \
  make

echo '#!/bin/bash' | sudo tee /usr/local/bin/hnn
echo 'cd $HOME/hnn' | sudo tee -a /usr/local/bin/hnn
echo 'python3 hnn.py' | sudo tee -a /usr/local/bin/hnn
sudo chmod 755 /usr/local/bin/hnn

# prepare image - only use if creating an AMI
# sudo apt-get install -y ec2-ami-tools
# echo "PermitRootLogin without-password" | sudo tee -a /etc/ssh/sshd_config  
# sudo passwd -l root
# sudo rm -rf /tmp/*
# sudo shred -u $HOME/.*history
# rm -f ~/.sudo_as_admin_successful
# rm -f ~/.viminfo
# rm -f ~/.Xauthority
# sudo rm -rf $HOME/.cache/
# rm -rf ~/.gnupg/
# rm -rf ~/.config/
# rm -rf ~/.ssh/