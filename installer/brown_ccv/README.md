# Installing HNN on Brown's Oscar supercomputer
**(Brown students, staff, faculty only)**

## Getting an account on Oscar
Please see  [Create an Account](https://web1.ccv.brown.edu/start/account) on Brown's CCV (Center for Computation and Visualization) site and fill out a new user account form.
  * Choose an exploratory account
  * This may take a day or two

## Opening a VNC session

1. Download and run the CCV VNC Client (see [VNC Client](https://web1.ccv.brown.edu/technologies/vnc))

2. Log in using credentials created for you above

3. Choose a machine size to run HNN on. We recommend '4 Cores -- 15 GB Memory -- 4 days'. Click 'Create VNC Session'. You may have to wait why resources are being requested, but eventually you should see a window pop-up displaying a desktop.

4. Launch "Terminal Emulator" from the bottom left. Run the following commands to build HNN and its prerequisites in your home directory. If you've already built HNN and are logging in again, skip to "Running HNN a second time" below.


## Setting things up
```
module load mpi/openmpi_3.1.3_gcc python/3.6.6 hnn/1.0
BASE=$HOME/HNN
mkdir -p $BASE
```

## Clone the source code for HNN and prerequisites
```
cd $BASE
git clone https://github.com/neuronsimulator/nrn
git clone https://github.com/neuronsimulator/iv
git clone https://github.com/jonescompneurolab/hnn
```

## Build HNN prerequisites
```
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

# Cleanup compiled prerequisites
cd $BASE/iv && \
    make clean
cd $HOME/nrn && \
    make clean
```

## Build HNN

```
cd $BASE/hnn && \
    make
```

## Set commands to run at login

```
cat <<EOF | tee -a $HOME/.bash_profile > /dev/null
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

# actually run those commands for this session
export PATH=$PATH:$BASE/nrn/build/x86_64/bin
ulimit -l unlimited
```

## Start HNN

```
cd $BASE/hnn
python3 hnn.py hnn.cfg
```

# Running HNN a second time
1. If all of the commands above have been run once before, there are only a few commands to run HNN after logging back in
    ```
    module load mpi/openmpi_3.1.3_gcc python/3.6.6 hnn/1.0
    cd $HOME/HNN/hnn
    python3 hnn.py hnn.cfg
    ```

2. When the HNN GUI starts up, make sure to change limit the number of cores the amount when requesting the VNC session (e.g. 4 cores)
    * Click 'Set Parameters' -> 'Run' and change 'NumCores'
