# HNN install (Mac OS)

## Opening a terminal window

- Open up macOS's terminal.app by searching for terminal in Spotlight (upper right search icon). We will use this terminal for running the commands below.

## Run pre-install checks

- The command below will run a script to check for existing installations of prerequisites. If a compatible version is installed, it will say which steps can be skipped below.

    ```bash
    curl -s "https://raw.githubusercontent.com/jonescompneurolab/hnn/master/installer/mac/check-pre.sh" | bash
    ```

## Prerequisite 1: Xcode Command Line Tools

The Xcode Command Line Tools package includes utilities for compiling code from the terminal. This is needed for compiling NEURON mod files during the hnn-core installation.

1. To install the package, type the following from a terminal.app window:

    ```bash
    xcode-select --install
    ```

     - If you get the following error, you can skip this step.
      `xcode-select: error: command line tools are already installed, use "Software Update" to install updates`

2. Then press `Install` in the pop-up dialog.

## Prerequisite 2: Miniconda (Python 3)

- Run the commands below from a terminal window (as a regular user). This will create a python environment isolated from other installations on the system. You could use homebrew `brew install python3` if you wish (has been tested with HNN), but this guide will cover the miniconda version.

    ```bash
    cd /tmp/
    curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
    sh ./Miniconda3-latest-MacOSX-x86_64.sh -b
    rm /tmp/Miniconda3-latest-MacOSX-x86_64.sh
    ```

## Prepare the Python environment

1. Create a conda environment with the Python prerequisites for HNN.

    ```bash
    conda env create -f environment.yml
    conda install -y -n hnn openmpi mpi4py
    ```

2. Activate the HNN conda environment and python prerequisite packages

    ```bash
    conda activate hnn
    pip install https://api.github.com/repos/jonescompneurolab/hnn-core/zipball/master
    pip install nlopt
    pip install mpi4py
    ```

## Run post-install checks

```bash
curl -s "https://raw.githubusercontent.com/jonescompneurolab/hnn/master/installer/mac/check-post.sh" | bash
```

## Download HNN source code

```bash
git clone https://github.com/jonescompneurolab/hnn.git
cd hnn
```

## Run the HNN model

1. Start the HNN GUI from a terminal window. Make sure the hnn environment has been activated each time a terminal window is opened:

    ```bash
    conda activate hnn
    python hnn.py
    ```

2. The HNN GUI should show up. Make sure that you can run simulations by clicking the 'Run Simulation' button. This will run a simulation with the default configuration. After it completes, graphs should be displayed in the main window.

3. When you run simulations for the first time, two dialog boxes may pop-up and ask you for permission to allow connections through the firewall. Saying 'Deny' is fine since simulations will just run locally on your Mac.

4. You can now proceed to running the tutorials at [https://hnn.brown.edu/index.php/tutorials/](https://hnn.brown.edu/index.php/tutorials/) . Some things to note:

    - A directory called "hnn_out" exists in your home directory where the results from your simulations (data and param files) will be stored.

## Upgrading to a new version of HNN

HNN Releases can be found on the [GitHub releases page](https://github.com/jonescompneurolab/hnn/releases/). You can also be notified of new releases by watching the hnn [repository on GitHub](https://github.com/jonescompneurolab/hnn/).

To download the latest HNN release:

```bash
curl -OL https://github.com/jonescompneurolab/hnn/releases/latest/download/hnn.tar.gz
mkdir hnn_source_code
tar -x --strip-components 1 -f hnn.tar.gz -C hnn_source_code
cd hnn_source_code
conda activate hnn
python3 hnn.py
```

If you are using `git`, then run `git pull origin master` from the source code directory.

## Troubleshooting

For Mac OS specific issues: please see the [Mac OS troubleshooting page](troubleshooting.md)

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will investigate possible fixes.

Another option for users that are running into problems with the above methods, we provide a VirtualBox VM pre-installed with HNN.

- [Virtualbox install instructions](../virtualbox/README.md)
