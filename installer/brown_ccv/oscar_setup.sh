module load mpi/openmpi_3.1.3_gcc python/3.6.6 hnn/1.0
BASE=$HOME/HNN

mkdir -p $BASE
cd $BASE
git clone https://github.com/neuronsimulator/nrn
git clone https://github.com/neuronsimulator/iv
git clone https://github.com/jonescompneurolab/hnn

# build interviews (required for NEURON)
cd $BASE/iv && \
    git checkout d4bb059 && \
    ./build.sh && \
    ./configure --prefix=$(pwd)/build && \
    make -j2 && \
    make install -j2

# build NEURON
cd $BASE/nrn && \
    ./build.sh && \
    ./configure --with-nrnpython=python3 --with-paranrn --disable-rx3d \
      --with-iv=$(pwd)/../iv/build --prefix=$(pwd)/build && \
    make -j2 && \
    make install -j2 && \
    cd src/nrnpython && \
    python3 setup.py install --home=$BASE/nrn/build/x86_64/python

# setup HNN itself
cd $BASE/hnn && \
    make

# cleanup compiled prerequisites
cd $BASE/iv && \
    make clean
cd $BASE/nrn && \
    make clean

# set command to run at login
cat <<EOF | tee $HOME/.bash_profile > /dev/null
export PATH=\$PATH:\$BASE/nrn/build/x86_64/bin
# HNN settings
if [[ ! "\$(ulimit -l)" =~ "unlimited" ]]; then
  ulimit -l unlimited
  if [[ "\$?" -eq "0" ]]; then
    echo "** Successfully increased max locked memory (for HNN) **"
  else
    echo "** Failed to increase max locked memory (for HNN) **"
  fi
fi
EOF


export PATH=$PATH:$BASE/nrn/build/x86_64/bin
if [[ ! "$(ulimit -l)" =~ "unlimited" ]]; then
  ulimit -l unlimited
  if [[ "$?" -eq "0" ]]; then
    echo "** Successfully increased max locked memory (for HNN) **"
  else
    echo "** Failed to increase max locked memory (for HNN) **"
  fi
fi
cd $BASE/hnn
python3 hnn.py hnn.cfg
