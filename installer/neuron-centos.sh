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

# HNN repo from bitbucket - can adjust to git later
hg clone ssh://hg@bitbucket.org/samnemo/hnn
cd hnn
# make compiles the mod files
make

# pyqt - needed for GUI
sudo pip3 install pyqt5

# pyqtgraph - only used for visualization
git clone https://github.com/pyqtgraph/pyqtgraph.git
cd pyqtgraph
git checkout pyqt5
git pull
sudo python3 setup.py install

