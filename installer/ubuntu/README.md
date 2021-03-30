# HNN install (Ubuntu)

## Prerequisite: Miniconda

- Run the commands below from a terminal window (as a regular user). This will create a python environment isolated from other installations on the system.

    ```bash
    cd /tmp/
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    sh ./Miniconda3-latest-Linux-x86_64.sh -b
    rm /tmp/Miniconda3-latest-Linux-x86_64.sh
    ```

## Prepare the Python environment

1. Create a conda environment with the Python prerequisites for HNN.

    ```bash
    conda env create -f environment.yml
    ```

2. Activate the HNN conda environment and python prerequisite packages

    ```bash
    conda activate hnn
    pip install https://api.github.com/repos/jonescompneurolab/hnn-core/zipball/master
    pip install nlopt
    pip install mpi4py
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

3. You can now proceed to running the tutorials at [https://hnn.brown.edu/index.php/tutorials/](https://hnn.brown.edu/index.php/tutorials/) . Some things to note:

    - A directory called "hnn_out" exists in your home directory where the results from your simulations (data and param files) will be stored.

## Upgrading to a new version of HNN

HNN Releases can be found on the [GitHub releases page](https://github.com/jonescompneurolab/hnn/releases/). You can also be notified of new releases by watching the hnn [repository on GitHub](https://github.com/jonescompneurolab/hnn/).

To download the latest HNN release:

```bash
curl --remote-name https://github.com/jonescompneurolab/hnn/releases/latest/download/hnn.tar.gz
mkdir hnn_source_code
tar -x --strip-components 1 -f hnn.tar.gz -C hnn_source_code
cd hnn_source_code
conda activate hnn
python3 hnn.py
```

If you are using `git`, then run `git pull origin master` from the source code directory.

## Troubleshooting

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will investigate possible fixes.

Another option for users that are running into problems with the above methods, we provide a VirtualBox VM pre-installed with HNN.

- [Virtualbox install instructions](../virtualbox/README.md)
