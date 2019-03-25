# Installing HNN on Brown's Oscar supercomputer
**(Brown students, staff, faculty only)**

## Getting an account on Oscar
Please see  [Create an Account](https://web1.ccv.brown.edu/start/account) on Brown's CCV (Center for Computation and Visualization) site and fill out a new user account form.
  * Choose an exploratory account
  * This may take some time

## Opening a VNC session

1. Download and run the CCV VNC Client (see [VNC Client](https://web1.ccv.brown.edu/technologies/vnc))

2. Log in using credentials created for you above

3. Choose a machine size to run HNN on. Any size will work, but 4 cores should be enough. Click 'Create VNC Session'. You may have to wait why resources are being requested, but eventually you should see a window pop-up displaying a desktop.

4. Launch "Terminal Emulator" from the bottom left. Run the following commands to build HNN and its prerequisites in your home directory. If you've already built HNN and are logging in again, skip to "Running HNN a second time" below.


## Installing from a terminal window within VNC

1. Setting things up
   ```
   module load mpi/openmpi_3.1.3_gcc python/3.6.6
   mkdir -p $HOME/HNN
   ```

2. Clone the source code for HNN and prerequisites
   ```
   cd $HOME/HNN
   git clone https://github.com/neuronsimulator/nrn
   git clone https://github.com/neuronsimulator/iv
   git clone https://github.com/jonescompneurolab/hnn
   ```

3. Build HNN prerequisites
   - Build interviews (required for NEURON)
     ```
     cd $HOME/HNN/iv && \
         git checkout d4bb059 && \
         ./build.sh && \
         ./configure --prefix=$(pwd)/build && \
         make -j2 && \
         make install -j2
     ```
   - Build NEURON
     ```
     cd $HOME/HNN/nrn && \
         ./build.sh && \
         ./configure --with-nrnpython=python3 --with-paranrn --disable-rx3d \
           --with-iv=$(pwd)/../iv/build --prefix=$(pwd)/build && \
         make -j2 && \
         make install -j2 && \
         cd src/nrnpython && \
         python3 setup.py install --home=$HOME/HNN/nrn/build/x86_64/python
     ```
   - Cleanup compiled prerequisites
     ```
     cd $HOME/HNN/iv && \
        make clean
     cd $HOME/HNN/nrn && \
        make clean
     ```
   - Install python modules. Ignore the errors
     ```
     pip3 install --user PyOpenGL pyqtgraph  >/dev/null 2>&1
     ```

4. Build HNN

   ```
   cd $HOME/HNN/hnn && \
       make
   ```

5. Set commands to run at login for future logins

   ```
   cat <<EOF | tee -a $HOME/.bash_profile > /dev/null
   export PATH="\$PATH:\$HOME/HNN/nrn/build/x86_64/bin"
   export PYTHONPATH="/gpfs/runtime/opt/hnn/1.0/pyqt:\$HOME/HNN/nrn/build/x86_64/python/lib/python"
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
   ```

6. Kill VNC Session. Click `EXIT` button in upper left corner and choose `Kill VNC Session` (`Disconnect from VNC Session` is not enough!).

7. Log back in to a new VNC session.

8. Start HNN

   ```
   module load mpi/openmpi_4.0.0_gcc python/3.6.6
   cd $HOME/HNN/hnn
   python3 hnn.py hnn.cfg
   ```

9. When the HNN GUI starts up, make sure to change the number of cores to match the VNC session (e.g. 4 cores, **NOT 16 cores**)
    * Click 'Set Parameters' -> 'Run' and change 'NumCores'

10. Note that there are some known issues that only produce warning messages. The following messages are safe to ignore for HNN.

    * In terminal window:
      ```
      QStandardPaths: XDG_RUNTIME_DIR points to non-existing path '/run/user/yyyy', please create it with 0700 permissions.
      qt.qpa.xcb: QXcbConnection: XCB error: 3 (BadWindow), sequence: 1697, resource id: 6294787, major code: 40 (TranslateCoords), minor code: 0
      ```

    * In simulation log:
      ```
      [1553532688.636610] [nodeyyy:27749:0]          mpool.c:38   UCX  WARN  object 0x7f5e460df860 was not returned to mpool mm_recv_desc
      ```


## Running HNN a second time
1. If all of the commands above have been run once before, these are the only commands to start HNN again.
   ```
   module load mpi/openmpi_4.0.0_gcc python/3.6.6
   cd $HOME/HNN/hnn
   python3 hnn.py hnn.cfg
   ```

2. When the HNN GUI starts up, make sure to change limit the number of cores the amount when requesting the VNC session (e.g. 4 cores)
    * Click 'Set Parameters' -> 'Run' and change 'NumCores'
