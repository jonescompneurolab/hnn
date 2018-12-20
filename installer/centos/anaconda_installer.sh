#!/usr/bin/env bash

# get install prefrix from cmd line
if test "$#" -ne 1; then
    echo "please specify an install prefix"
fi

# expand provided path
if [[ ! "$1" =~ ^/ ]]
    then
        install_prefix="$PWD/$1"
    else
        install_prefix="$1"
fi
echo "Installing hnn, iv and nrn into $install_prefix"

# check system dependencies.
# TODO: What else should be checked for

# check that mpicc is on the path
if ! type -P mpicc &>/dev/null; then
    echo "mpicc is not in\$PATH"
    echo "Please install it and add to the PATH environment variable"
fi


# create conda environment
# TODO: Replace with enviroment.yml file?
conda create --name hnn python=3 cython scipy numpy matplotlib pyqt pyqtgraph pyopengl libtool=2.4.2
source activate hnn
#pip install PyOpenGL_accelerate
pip install mpi4py

# begin install
startdir=$(pwd)
echo $startdir

# download packages
git clone https://github.com/jonescompneurolab/hnn.git
git clone https://github.com/neuronsimulator/nrn
git clone https://github.com/neuronsimulator/iv

# build, configure and install iv
cd iv
git checkout d4bb059
./build.sh
./configure --prefix=${install_prefix}
make -j4
make install -j4

# build, configure and install nrn
cd ../nrn
#git checkout be2997e
./build.sh
./configure --with-nrnpython=python3 --with-paranrn --with-iv=${install_prefix} --prefix=${install_prefix}
make -j4
make install -j4
cd src/nrnpython
python3 setup.py install

# cleanup the nrn and iv folders, since NEURON Has been installed
cd $startdir
rm -rf iv
rm -rf nrn

# setup HNN itself
cd hnn
# make compiles the mod files
export CPU=$(uname -m)
export PATH=$PATH:${install_prefix}/$CPU/bin
make
cd ..

# delete the installed hnn folder in the event that it already exists
rm -rf ${install_prefix}/hnn
# move the hnn folder to the programs directory
cp -r hnn ${install_prefix}

# make the program accessable via the terminal command 'hnn'
ln -fs ${install_prefix}/hnn/hnn ${install_prefix}/${CPU}/bin/hnn

# useful environment variables
env_setup_fname=${install_prefix}/hnn_profile.sh
echo '# these lines define global session variables for HNN' | tee -a ${env_setup_fname}
echo 'export CPU=$(uname -m)' | tee -a ${env_setup_fname}
echo "install_prefix=${install_prefix}" | tee -a ${env_setup_fname}
echo 'source activate hnn' | tee -a ${env_setup_fname}
echo 'export PATH=$PATH:${install_prefix}/$CPU/bin' | tee -a ${env_setup_fname}
echo 'export HNN_ROOT=${install_prefix}/hnn' | tee -a ${env_setup_fname}
echo 'export PYTHONPATH=${HNN_ROOT}' | tee -a ${env_setup_fname}
