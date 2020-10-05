# HNN "Python" install (Mac OS)

## Opening a terminal window

1. Open up macOS's terminal.app by searching for terminal in Spotlight (upper right search icon). We will use this terminal for running the commands below.

## Prerequisite 1: Xcode Command Line Tools

The Xcode Command Line Tools package includes utilities for compiling code from the terminal (gcc, make, etc.). This is needed for compiling mod files in NEURON.

1. To install the package, type the following from a terminal.app window:

    ```bash
    xcode-select --install
    ```

     - If you get the following error, you can skip this step.
      `xcode-select: error: command line tools are already installed, use "Software Update" to install updates`

2. Then press `Install` in the pop-up dialog

  <img src="install_pngs/xcode_tools.png" width="400" />

## Prerequisite 2: Miniconda (Python 3)

1. Run the commands below from a terminal window (as a regular user). This will create a python environment isolated from other installations on the system. You could use homebrew `brew install python3` if you wish (has been tested with HNN), but this guide will cover the miniconda version.

    ```bash
    cd /tmp/
    curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
    sh ./Miniconda3-latest-MacOSX-x86_64.sh -b
    rm /tmp/Miniconda3-latest-MacOSX-x86_64.sh
    ```

## Prepare the Python environment

1. Create a conda environment with the Python prerequisites for HNN.

    ```bash
    conda create -y -n hnn python=3.7 openmpi pyqtgraph pyopengl matplotlib scipy psutil
    ```

2. Activate the HNN conda environment and install nlopt and NEURON

    ```bash
    source activate hnn
    pip install nlopt NEURON
    ```

3. Set the LD_LIBRARY_PATH for openmpi on conda activation. This environnement variable must be set before HNN can run simulations with openmpi. The variable is only useful inside the 'hnn' conda environment, so we will set the variable when conda is activated with `source activate hnn`. Run the following commands to make this automatic.

    ```bash
    cd ${CONDA_PREFIX}
    mkdir -p etc/conda/activate.d etc/conda/deactivate.d
    echo "export OLD_LD_LIBRARY_PATH=\$LD_LIBRARY_PATH" >> etc/conda/activate.d/env_vars.sh
    echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:\${CONDA_PREFIX}/lib" >> etc/conda/activate.d/env_vars.sh
    echo "export LD_LIBRARY_PATH=\$OLD_LD_LIBRARY_PATH" >> etc/conda/deactivate.d/env_vars.sh
    echo "unset OLD_LD_LIBRARY_PATH" >> etc/conda/deactivate.d/env_vars.sh
    ```

4. Open a new terminal window for the settings in the previous step to take effect and activate the HNN conda environment

    ```bash
    source activate hnn
    ```

## Download HNN source code

1. The following commands will download the hnn source code and compile HNN's mod files for NEURON. This is where Xcode Command Line Tools are needed.

    ```bash
    curl --remote-name https://github.com/jonescompneurolab/hnn/releases/latest/download/hnn.tar.gz
    tar -x --strip-components 1 -f hnn.tar.gz -C hnn_source_code
    cd hnn_source_code
    make
    ```

## Run the HNN model

1. Start the HNN GUI from a terminal window:

    ```bash
    source activate hnn
    python hnn.py
    ```

2. The HNN GUI should show up. Make sure that you can run simulations by clicking the 'Run Simulation' button. This will run a simulation with the default configuration. After it completes, graphs should be displayed in the main window.

3. When you run simulations for the first time, the following dialog boxes may pop-up and ask you for permission to allow connections through the firewall. Saying 'Deny' is fine since simulations will just run locally on your Mac.

    <img src="install_pngs/nrniv_firewall.png" width="400" />

    <img src="install_pngs/orterun_firewall.png" width="400" />

4. You can now proceed to running the tutorials at https://hnn.brown.edu/index.php/tutorials/ . Some things to note:
    - A directory called "hnn_out" exists in your home directory where the results from your simulations (data and param files) will be stored.

## Upgrading to a new version of HNN

HNN Releases can be seen on the [GitHub releases page](https://github.com/jonescompneurolab/hnn/releases/). You can also be notified of new releases by watching the hnn [repository on GitHub](https://github.com/jonescompneurolab/hnn/).

To download the latest release, use the following commands within an Ubuntu terminal:

```bash
curl --remote-name https://github.com/jonescompneurolab/hnn/releases/latest/download/hnn.tar.gz
tar -x --strip-components 1 -f hnn.tar.gz -C hnn_source_code
cd hnn_source_code
make
python3 hnn.py
```

## Troubleshooting

For Mac OS specific issues: please see the [Mac OS troubleshooting page](troubleshooting.md)

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will investigate possible fixes.

Another option for users that are running into problems with the above methods, we provide a VirtualBox VM pre-installed with HNN.

- [Virtualbox install instructions](../virtualbox/README.md)
