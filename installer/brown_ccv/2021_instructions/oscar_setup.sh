#!/bin/bash

# Setting things up
module load mpi/openmpi_3.1.3_gcc python/3.6.6
mkdir -p $HOME/HNN

# Clone the source code for HNN and prerequisites
cd $HOME/HNN
git clone https://github.com/jonescompneurolab/hnn

# Install python modules. Ignore the errors
pip3 install --user psutil nlopt hnn-core >/dev/null 2>&1

# Build HNN
cd $HOME/HNN/hnn && \
   make

# Set commands to run at login for future logins

cat <<EOF | tee -a $HOME/.bash_profile > /dev/null
export PYTHONPATH="/gpfs/runtime/opt/hnn/1.0/pyqt:"
export OMPI_MCA_btl_openib_allow_ib=1
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

# Kill VNC Session. Click `EXIT` button in upper left corner and choose `Kill VNC Session` (`Disconnect from VNC Session` is not enough!).
# Log back in to a new VNC session.

# Start HNN
module load mpi/openmpi_4.0.0_gcc python/3.6.6
cd $HOME/HNN/hnn
python3 hnn.py