sudo apt install -y git

# HNN repo from bitbucket
git clone https://bitbucket.org/samnemo/hnn.git

# packages neded for NEURON and graphics
sudo apt install -y python3-pyqt5 python3-pip python3-pyqtgraph zlib1g-dev zlib1g zlibc libx11-dev mercurial bison flex automake libtool libxext-dev libncurses-dev python3-dev xfonts-100dpi cython libopenmpi-dev python3-scipy 

# use pip for matplotlib to get latest version (2.x) since apt-get was using older
# version (1.5) which does not have set_facecolor
sudo pip3 install matplotlib

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
#git checkout be2997e
./build.sh
./configure --with-nrnpython=python3 --with-paranrn --disable-rx3d
make -j4
sudo make install -j4
cd src/nrnpython
sudo python3 setup.py install

# move outside of nrn directories
cd $startdir

# setup HNN itself
cd hnn
# make compiles the mod files
export CPU=$(uname -m)
export PATH=$PATH:/usr/local/nrn/$CPU/bin
make
cd ..

echo 'export CPU=$(uname -m)' >> ~/.bashrc
echo 'export PATH=$PATH:/usr/local/nrn/$CPU/bin' >> ~/.bashrc
