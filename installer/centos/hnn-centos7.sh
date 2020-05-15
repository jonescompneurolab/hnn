#!/bin/bash

# get epel release for python3
sudo yum -y install epel-release

sudo yum -y install automake gcc gcc-c++ flex bison libtool git \
                    ncurses-devel readline-devel openmpi-devel \
                    python36-devel python36-psutil \

# the system version of pip installs nlopt in the wrong directory
sudo pip3 install --upgrade pip
sudo /usr/local/bin/pip3 install PyOpenGL matplotlib pyqt5 pyqtgraph scipy numpy nlopt

export PATH=$PATH:/usr/lib64/openmpi/bin

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
    sudo yum clean all

# create the global session variables
echo '# these lines define global session variables for HNN' >> ~/.bashrc
echo 'export CPU=$(uname -m)' >> ~/.bashrc
echo "export PATH=\$PATH:$startdir/nrn/build/\$CPU/bin:/usr/lib64/openmpi/bin" >> ~/.bashrc
echo "export PYTHONPATH=$startdir/nrn/build/lib/python" >> ~/.bashrc

export CPU=$(uname -m)
export PATH=${PATH}:$startdir/nrn/build/$CPU/bin
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
