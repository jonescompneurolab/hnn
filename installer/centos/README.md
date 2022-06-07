# HNN "Python" install (CentOS)

The script below assumes that it can update OS packages for python and prerequisites for HNN.

* CentOS 7: [hnn-centos7.sh](hnn-centos7.sh)

    ```bash
    curl --remote-name https://raw.githubusercontent.com/jonescompneurolab/hnn/master/installer/centos/hnn-centos7.sh
    bash hnn-centos7.sh
    ```

* CentOS 6 (no longer maintained): [hnn-centos6.sh](hnn-centos6.sh)

    ```bash
    curl --remote-name https://raw.githubusercontent.com/jonescompneurolab/hnn/master/installer/centos/hnn-centos6.sh
    bash hnn-centos6.sh
    ```

## Start HNN

1. From the command-line, type following commands

    ```bash
    cd hnn_source_code
    python3 hnn.py
    ```

2. The HNN GUI should show up. Make sure that you can run simulations by clicking the 'Run Simulation' button. This will run a simulation with the default configuration. After it completes, graphs should be displayed in the main window.

3. You can now proceed to running the tutorials at [https://hnn.brown.edu/index.php/tutorials/](https://hnn.brown.edu/index.php/tutorials/) . Some things to note:

    * A directory called "hnn_out" exists in your home directory in Ubuntu where the results from your simulations (data and param files) will be stored.

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

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will investigate possible fixes.

Another option for users that are running into problems with the above methods, we provide a VirtualBox VM pre-installed with HNN.

* [Virtualbox install instructions](../virtualbox/README.md)
