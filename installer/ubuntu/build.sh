sudo apt install -y git

# HNN repo from bitbucket
git clone https://bitbucket.org/samnemo/hnn.git

# packages neded for NEURON and graphics
sudo apt install -y python3-pyqt5 python3-pip python3-pyqtgraph python3-opengl zlib1g-dev zlib1g zlibc libx11-dev mercurial bison flex automake libtool libxext-dev libncurses-dev python3-dev xfonts-100dpi cython libopenmpi-dev python3-scipy 

# use pip for matplotlib to get latest version (2.x) since apt-get was using older
# version (1.5) which does not have set_facecolor
sudo pip3 install matplotlib
# make sure matplotlib version 2 is used -- is this strictly needed?
sudo pip3 install --upgrade matplotlib

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

# setup the icon
sudo ln -s hnn/hnn.png /usr/share/pixmaps
sudo ln -s /usr/local/hnn/hnn.desktop /usr/share/applications/hnn.desktop

# move the hnn folder to the programs directory
sudo mv hnn /usr/local

# cleanup these folders (we've already installed them: they're in /usr/local)
rm -rf iv
rm -rf nrn

# make the program accessable via the terminal command 'hnn'
sudo ln -s /usr/local/hnn/hnn /usr/local/bin/hnn
sudo updatedb

echo 'export CPU=$(uname -m)' >> ~/.bashrc
echo 'export PATH=$PATH:/usr/local/nrn/$CPU/bin' >> ~/.bashrc
