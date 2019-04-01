#!/bin/bash

sudo apt-get update && \
     sudo apt-get upgrade -y
sudo apt-get install -y openmpi-bin openmpi-common openmpi-doc mpi-default-dev

# for IV
sudo apt-get install -y m4 automake g++ x11-common libx11-dev libxext-dev make

# for NEURON
sudo apt-get install -y python-minimal libpython-dev libpython-all-dev libzip-dev libncurses5-dev bison flex

# for python
sudo apt install -y python3-pyqt5 python3-pip python3-pyqtgraph python3-opengl zlib1g-dev zlib1g zlibc libx11-dev mercurial bison flex automake libtool libxext-dev libncurses-dev python3-dev xfonts-100dpi cython libopenmpi-dev python3-scipy 

cd $HOME && \
  git clone https://github.com/neuronsimulator/iv.git && \
  cd iv && \
  ./build.sh && \
  ./configure && \
  make && \
  sudo make install

cd $HOME && \
  git clone https://github.com/neuronsimulator/nrn.git && \
  cd nrn && \
  ./build.sh && \
  ./configure --with-nrnpython=python3 \
      --with-paranrn --disable-rx3d && \
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
echo 'python3 hnn.py hnn.cfg' | sudo tee -a /usr/local/bin/hnn
sudo chmod 755 /usr/local/bin/hnn

# prepare image
sudo apt-get install -y ec2-ami-tools
echo "PermitRootLogin without-password" | sudo tee -a /etc/ssh/sshd_config  
sudo passwd -l root
sudo rm -rf /tmp/*
shred -u ~/.*history
rm -f ~/.sudo_as_admin_successful
rm -f ~/.viminfo
rm -f ~/.Xauthority
rm -rf ~/.cache/
rm -rf ~/.gnupg/
rm -rf ~/.config/
#rm -rf ~/.ssh/