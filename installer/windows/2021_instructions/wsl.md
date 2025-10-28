# Installing HNN on Windows Subsystem for Linux (WSL)

## Prerequisite: WSL

Below is Microsoft's guide for installing WSL. Note that both WSL 1 and WSL 2 will work with, but **WSL1 is recommended** because the DISPLAY variable will need to be adjusted with WSL 2.

https://docs.microsoft.com/en-us/windows/wsl/install-win10

Some notes:

* We strongly recommend that you download the **Ubuntu 18.04 LTS** distribution. Other distributions may work, but the steps could be slightly different for each.
* There is no need to install "Windows Terminal"
* The username/password you create has no relation to any existing credentials on your system. Make it whatever you please.

## Prerequisite: VcXsrv

1. Download the installer from [https://sourceforge.net/projects/vcxsrv/files/latest/download](https://sourceforge.net/projects/vcxsrv/files/latest/download)
2. Run the installer, choosing "C:\Program Files\VcXsrv" as the destination folder.
3. Start the XLaunch desktop app from the VcXsrv folder in the start menu.
4. Choose "Multiple windows". Choose '0' for the "Display number". Click 'Next'.
5. Select "Start no client" and click 'Next'.
6. **Important**: under "Extra settings" make sure that "Disable access control" is checked.
7. Click "Save configuration" to create a shortcut with the settings we just chose. Click "Finish" and an "X" icon will appear in the lower-right dock signaling that VcXsrv has started. Use this shortcut whenever you are starting HNN.
8. A message from Windows firewall to allow connections may pop up. If it does, you do not need to allow any access to VcXsrv.

## Install HNN

Launch the Ubuntu application to open a command line and run the commands below to download and run a script that will install HNN and its prerequisites.

```bash
curl --remote-name https://raw.githubusercontent.com/jonescompneurolab/hnn/master/installer/ubuntu/hnn-ubuntu.sh
bash hnn-ubuntu.sh
```

Some notes:

* You'll be asked for the password you created in WSL (above)
* While it gets tested frequently as part of our automated builds, please let us know if you run into a failure by creating a GitHub issue](https://github.com/jonescompneurolab/hnn/issues).

You will need to **restart Ubuntu** after this. Until you do so, simulations will fail to run from HNN.

## Start HNN

1. From the Ubuntu application, type the following commands in the terminal.

    ```bash
    export DISPLAY=:0  # WSL 1
    cd hnn_source_code
    python3 hnn.py
    ```

2. The HNN GUI should show up. Make sure that you can run simulations by clicking the 'Run Simulation' button. This will run a simulation with the default configuration. After it completes, graphs should be displayed in the main window.

3. You can now proceed to running the tutorials at [https://hnn.brown.edu/index.php/tutorials/](https://hnn.brown.edu/index.php/tutorials/) . Some things to note:
    * A message from Windows firewall about connection to `nrniv` may pop up. If it does, you can press 'Cancel'. The program does not need any network access to run a simulation.
    * A directory called "hnn_out" exists in your home directory in Ubuntu where the results from your simulations (data and param files) will be stored. This is part of a filesystem specific for the Ubuntu application. You can read Windows files (e.g. your own ".param" files) from Ubuntu in the Ubuntu command-line (e.g. via `/mnt/c/Users/userA/Downloads`). However, you cannot access simulation results from Windows applications without copying the file to the mount directory first (see [WSL FAQ](https://docs.microsoft.com/en-us/windows/wsl/faq#how-do-i-use-a-windows-file-with-a-linux-app)). For example to copy the entire output directory (param files and data files) to Windows (replace "userA"):

        ```bash
        cp -r ~/hnn_out /mnt/c/Users/userA/Downloads
        ```

    * If you are using WSL 2, use the following command to set the DISPLAY variable before starting HNN. The IP address comes from the "WSL" interface on Windows that gets created when Ubuntu starts.

        ```bash
        export DISPLAY=192.168.57.17:0  # WSL 2
        ```

## Upgrading to a new version of HNN

HNN Releases can be seen on the [GitHub releases page](https://github.com/jonescompneurolab/hnn/releases/). You can also be notified of new releases by watching the hnn [repository on GitHub](https://github.com/jonescompneurolab/hnn/).

To download the latest release, use the following commands within an Ubuntu terminal:

```bash
wget -O hnn.tar.gz https://github.com/jonescompneurolab/hnn/releases/latest/download/hnn.tar.gz
tar -x --strip-components 1 -f hnn.tar.gz -C hnn_source_code
cd hnn_source_code
make
python3 hnn.py
```

## Uninstalling HNN

If you still want to use WSL, you can just remove the hnn source code directory with Ubuntu. Or you can remove the entire distribution by finding Ubuntu in "Add or remove programs" and clicking Uninstall. VcXsrv can also be uninstall from "Add or remove programs".

## Troubleshooting

### VcXsrv

Make sure VcXsrv has been updated to at least 1.20.60. Earlier versions can cause the errors below:

`hnn_docker.sh` would fail:

```bash
Starting VcXsrv... done
Checking for xauth... found
Checking for X11 authentication keys... *failed*
```

`hnn_docker.log` contains:

```bash
Retrieving host xauth keys...

  ** Command: /c/Program Files/VcXsrv/xauth.exe -f /c/Users/user/.Xauthority -ni nlist localhost:0
  ** Stderr: C:\Program Files\VcXsrv\xauth.exe: (argv):1:  bad display name "localhost:0" in "nlist" command
*failed*
```

### Other

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.
