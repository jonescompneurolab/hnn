#!/bin/bash

# make sure the package lists are current
sudo apt-get update

# packages neded for NEURON and graphics
sudo apt install -y zlib1g-dev bison flex automake libtool libncurses-dev \
                    python3-dev libopenmpi-dev python3-psutil python3-pip \
                    git

sudo pip3 install pip --upgrade
sudo pip install PyOpenGL matplotlib pyqt5 pyqtgraph scipy numpy nlopt

# save dir installing hnn to
startdir=$(pwd)
echo $startdir

# Install NEURON
cd $startdir && \
    mkdir nrn && \
    cd nrn && \
    git clone https://github.com/neuronsimulator/nrn src && \
    cd $startdir/nrn/src && \
    ./build.sh && \
    ./configure --with-nrnpython=python3 --with-paranrn --disable-rx3d \
      --without-iv --without-nrnoc-x11 --with-mpi \
      --prefix=$startdir/nrn/build && \
    make -j4 && \
    make install -j4 && \
    cd src/nrnpython && \
    python3 setup.py install --user && \
    cd $startdir/nrn/ && \
    rm -rf src && \
    sudo apt-get -y remove --purge bison flex python3-dev zlib1g-dev python && \
    sudo apt-get autoremove -y --purge && \
    sudo apt-get clean

# create the global session variables
echo '# these lines define global session variables for HNN' >> ~/.bashrc
echo 'export CPU=$(uname -m)' >> ~/.bashrc
echo "export PATH=\$PATH:$startdir/nrn/build/\$CPU/bin:$startdir/hnn_source_code" >> ~/.bashrc
echo "export PYTHONPATH=$startdir/nrn/build/lib/python" >> ~/.bashrc

export CPU=$(uname -m)
export PATH=${PATH}:$startdir/nrn/build/$CPU/bin:$startdir/hnn_source_code
export PYTHONPATH=$startdir/nrn/build/lib/python

# setup HNN itself
cd $startdir && \
    git clone https://github.com/jonescompneurolab/hnn.git hnn_source_code && \
    cd hnn_source_code && \
    make

if [[ -d "$HOME/Desktop" ]]; then
    mkdir -p $HOME/.local/share/icons && \
    cp -f hnn.png $HOME/.local/share/icons/ && \
    cp -f hnn.desktop $HOME/Desktop && \
    sed -i "s~/home/hnn_user~$startdir~g" $HOME/Desktop/hnn.desktop && \
    chmod +x $HOME/Desktop/hnn.desktop
fi
