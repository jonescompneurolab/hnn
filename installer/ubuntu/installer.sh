# make sure the package lists are current
sudo apt-get update

sudo apt install -y git

# HNN repo from bitbucket
#git clone https://bitbucket.org/samnemo/hnn.git# old repo location

# HNN repo from github - moved to github on April 8, 2018
git clone https://github.com/jonescompneurolab/hnn.git

# packages neded for NEURON and graphics
sudo apt install -y python3-pyqt5 python3-pip python3-pyqtgraph python3-opengl zlib1g-dev zlib1g zlibc libx11-dev mercurial bison flex automake libtool libxext-dev libncurses-dev python3-dev xfonts-100dpi cython libopenmpi-dev python3-scipy python3-psutil

# fixes the issue where importing OpenGL in python throws an error
# (I assume that this works by installing the OpenGL for qt4 and then updating? it's not clear...)
# I think that this is an error in the repos, not our fault.
sudo apt install python3-pyqt4.qtopengl
sudo pip3 install PyOpenGL
sudo pip3 install --upgrade PyOpenGL

# first, we make sure that another older version isn't installed 
sudo apt remove python3-matplotlib
# use pip for matplotlib to get latest version (2.x) since apt-get was using older
# version (1.5) which does not have set_facecolor
sudo pip3 install matplotlib
# make sure matplotlib version 2 is used -- is this strictly needed?
sudo pip3 install --upgrade matplotlib nlopt

# save dir installing hnn to
startdir=$(pwd)
echo $startdir

git clone https://github.com/neuronsimulator/nrn
cd nrn
./build.sh
./configure --with-nrnpython=python3 --with-paranrn --disable-rx3d \
      --without-iv --without-nrnoc-x11 --with-mpi
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

# cleanup these folders (we've already installed them: they're in /usr/local)
sudo rm -rf nrn

# delete the installed hnn folder in the event that it already exists
sudo rm -rf /usr/local/hnn

# move the hnn folder to the programs directory
sudo mv hnn /usr/local

# setup the icon and register the program with the system
sudo ln -fs /usr/local/hnn/hnn.png /usr/share/pixmaps
sudo ln -fs /usr/local/hnn/hnn.desktop /usr/share/applications/hnn.desktop

# make the program accessable via the terminal command 'hnn'
sudo ln -fs /usr/local/hnn/hnn /usr/local/bin/hnn
sudo updatedb

# create the global session variables
echo '# these lines define global session variables for HNN'
echo 'export CPU=$(uname -m)' >> ~/.bashrc
echo 'export PATH=$PATH:/usr/local/nrn/$CPU/bin' >> ~/.bashrc
