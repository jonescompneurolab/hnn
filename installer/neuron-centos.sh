wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
sudo rpm -i epel-release-latest-7.noarch.rpm
sudo yum -y install python34-devel.x86_64
sudo yum -y install libX11-devel
sudo yum -y group install "Development Tools"
sudo yum -y install xorg-x11-fonts-100dpi 
sudo yum -y install Cython
sudo yum -y install python34-pip python-tools
sudo pip3 install matplotlib
sudo pip3 install scipy
sudo yum -y install ncurses-devel
sudo yum -y install openmpi openmpi-devel
sudo yum -y install libXext libXext-devel
export PATH=$PATH:/usr/lib64/openmpi/bin
sudo PATH=$PATH:/usr/lib64/openmpi/bin pip3 install mpi4py

# save dir installing hnn to
startdir=$(pwd)
echo $startdir

git clone https://github.com/nrnhines/nrn
git clone https://github.com/nrnhines/iv
cd iv
git checkout d4bb059
./build.sh
./configure
make -j4
sudo make install -j4
cd ../nrn
git checkout cc66ee1
./build.sh
./configure --with-nrnpython=python3 --with-paranrn --disable-rx3d
make -j4
sudo PATH=$PATH:/usr/lib64/openmpi/bin make install -j4
cd src/nrnpython
sudo python3 setup.py install

# move outside of nrn directories
cd $startdir

# need hg for now
sudo yum -y install mercurial
# pip3 install Mercurial # <<-- alternative for other platform - doesn't work on centos

# HNN repo from bitbucket - can adjust to git later
hg clone https://bitbucket.org/samnemo/hnn
cd hnn
# make compiles the mod files
make

# need sip for pyqt5 - https://www.riverbankcomputing.com/software/sip/download
# pip3 install SIP # problems with bison (used by NEURON) and sip
cd ..
wget https://sourceforge.net/projects/pyqt/files/sip/sip-4.19.2/sip-4.19.2.tar.gz
tar -zxf sip-4.19.2.tar.gz
cd sip-4.19.2
sudo python3 configure.py
make
sudo make install

# qt, pyqt, and supporting packages - needed for GUI
wget https://sourceforge.net/projects/pyqt/files/sip/sip-4.19.2/sip-4.19.2.tar.gz
tar -zxf sip-4.19.2.tar.gz
cd sip-4.19.2
sudo python3 configure.py
make
sudo make install
cp ..

sudo yum -y install qt-devel
sudo yum -y install qt5-qtbase
sudo yum -y install qt5-qtbase-devel

wget https://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.8.2/PyQt5_gpl-5.8.2.tar.gz
tar -xvf PyQt5_gpl-5.8.2.tar.gz
cd PyQt5_gpl-5.8.2
python3 configure.py --qmake=/usr/lib64/qt5/bin/qmake --confirm-license
make
sudo make install
cd ..
# pyqtgraph - only used for visualization
cd hnn
git clone https://github.com/pyqtgraph/pyqtgraph.git
cd pyqtgraph
git checkout pyqt5
git pull
sudo python3 setup.py install

