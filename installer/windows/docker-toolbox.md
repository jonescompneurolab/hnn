# Installing HNN on Windows 10 (Home)

## Prerequisite: hardware virtualization features

Nearly all PC's have this feature, but it may not be enabled by default. If not already enabled, it may be necessary to manually set these through your PC manufacturer's BIOS settings. However, if Docker cannot turn this feature on from its installer, you may need to reboot your computer and change your PC manufacturer's BIOS settings. You can check whether it is enabled from the Task Manger. The picture below shows that hardware virtualization is disabled and will need to be manually enabled in the BIOS.

  <img src="install_pngs/virtualization_disabled.png" width="600" />

See [https://www.trishtech.com/2017/08/check-if-virtualization-is-enabled-in-windows-10](https://www.trishtech.com/2017/08/check-if-virtualization-is-enabled-in-windows-10) for more details.

If you run into problems enabling hardware virtualization support, we recommend that you follow the [native install instructions](native_install.md) instead. Also running our [VirtualBox VM with HNN pre-installed](https://hnn.brown.edu/index.php/installation-instructions/) is possible without hardware virtualization support.

## Prerequisite: disable Hyper-V

It is necessary to turn off Hyper-V for using HNN with Docker Toolbox. You may find that this feature is already turned off, but use the following steps to confirm.

1. Start typing "Turn Windows features on or off" in the search bar next to start menu and click on it to launch the control panel dialog window shown below.
2. Make sure that the "Hyper-V" component is unchecked as shown in the image below and click "Ok".

    <img src="install_pngs/disable-hyperv.png" width="400" />

3. **If you disabled Hyper-V, please reboot your computer before continuing below to install docker.**

## Prerequisite: VcXsrv (XLaunch)

1. Download the installer from [https://sourceforge.net/projects/vcxsrv/files/latest/download](https://sourceforge.net/projects/vcxsrv/files/latest/download)
   * Here's the link to the [direct download of version 64.1.20.1.4](https://downloads.sourceforge.net/project/vcxsrv/vcxsrv/1.20.1.4/vcxsrv-64.1.20.1.4.installer.exe?r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Fvcxsrv%2Ffiles%2Fvcxsrv%2F1.20.1.4%2Fvcxsrv-64.1.20.1.4.installer.exe%2Fdownload%3Fuse_mirror%3Dversaweb%26r%3Dhttps%253A%252F%252Fsourceforge.net%252Fprojects%252Fvcxsrv%252Ffiles%252Flatest%252Fdownload&ts=1550243133)
2. Run the installer, choosing any installation folder.
3. Start the XLaunch desktop app from the VcXsrv folder in the start menu.
4. Choose "Multiple windows" and change "Display number" at '0'. Click 'Next'.
5. Select "Start no client" and click 'Next'.
6. Under "Extra settings" make sure that "Disable access control" is checked.
7. Click "Save configuration" to create a shortcut with the settings we just chose. Click "Finish" and an "X" icon will appear in the lower-right dock signaling that XLaunch has started.
8. A message from Windows firewall to allow connections may pop up. If it does, choose options allowing connections to VcXsrv (XLaunch) when connected to both public and private networks.

## Prerequisite: Docker Toolbox

1. Download the latest installer image (.pkg): [https://github.com/docker/toolbox/releases/](https://github.com/docker/toolbox/releases/)
2. Run the installer. Click 'Yes' if there's a Windows security prompt requesting to make changes to your device.
3. Choose any install location.
4. In "Select Components" check the components "Docker Compose for Windows" and "VirtualBox". "Kitematic" is not needed. Click 'Next'.
5. In "Select Additional Tasks", make sure to **check "Add docker binaries to PATH"**. Click 'Next'.
6. Choose the default for the other options and click 'Install'.
7. When the installer has finished, select the option to "Open program shortcuts in File Explorer". Click "Finish".
8. Click on the "Docker Quickstart Terminal" shortcut. After opening the window, docker will run "pre-create checks" and then install VirtualBox (if needed). The output should be similar to below. Keep this window opening for running commands in later steps

    ```none
    Running pre-create checks...
    (default) Unable to get the latest Boot2Docker ISO release version:  Get https://api.github.com/repos/boot2docker/boot2docker/releases/latest: dial tcp: lookup api.github.com: no such host
    Creating machine...
    (default) Unable to get the latest Boot2Docker ISO release version:  Get https://api.github.com/repos/boot2docker/boot2docker/releases/latest: dial tcp: lookup api.github.com: no such host
    (default) Copying C:\Users\user\.docker\machine\cache\boot2docker.iso to C:\Users\user\.docker\machine\machines\default\boot2docker.iso...
    (default) Creating VirtualBox VM...
    (default) Creating SSH key...
    (default) Starting the VM...
    (default) Check network to re-create if needed...
    (default) Windows might ask for the permission to create a network adapter. Sometimes, such confirmation window is minimized in the taskbar.
    (default) Found a new host-only adapter: "VirtualBox Host-Only Ethernet Adapter #12"
    (default) Windows might ask for the permission to configure a network adapter. Sometimes, such confirmation window is minimized in the taskbar.
    (default) Windows might ask for the permission to configure a dhcp server. Sometimes, such confirmation window is minimized in the taskbar.
    (default) Waiting for an IP...
    Waiting for machine to be running, this may take a few minutes...
    Detecting operating system of created instance...
    Waiting for SSH to be available...
    Detecting the provisioner...
    Provisioning with boot2docker...
    Copying certs to the local machine directory...
    Copying certs to the remote machine...
    Setting Docker configuration on the remote daemon...
    Checking connection to Docker...
    Docker is up and running!
    To see how to connect your Docker Client to the Docker Engine running on this virtual machine, run: C:\Program Files\Docker Toolbox\docker-machine.exe env default



                            ##         .
                    ## ## ##        ==
                ## ## ## ## ##    ===
            /"""""""""""""""""\___/ ===
        ~~~ {~~ ~~~~ ~~~ ~~~~ ~~~ ~ /  ===- ~~~
            \______ o           __/
                \    \         __/
                \____\_______/

    docker is configured to use the default machine with IP 192.168.99.100
    For help getting started, check out the docs at https://docs.docker.com


    Start interactive shell
    user@DESKTOP-LHCRPOM /c/Program Files/Docker Toolbox$
    ```

   * If you get the error message shown below in the "Docker Quickstart Terminal", hardware support for virtualization isn't turned on, which is required for Docker on Windows. This may be fixable by changing settings in your PC manufacturer's BIOS. See the note on "Hardware virtualization features" under the "Prerequisite: Virtualization support" heading at the top of this page.

      <img src="install_pngs/vtx_disabled.png" width="500"/>

   * If you get the error message shown below, the Hyper-V feature needs to be turned off. Please see the "Prerequisite: disable Hyper-V" heading at the top of this page. After rebooting, launch "Docker Quickstart Terminal" from the Start Menu.

      <img src="install_pngs/docker-toolbox-error-hyperv-on.png" width="500" />

9. We want HNN to use all of the CPU cores available on your system when it runs a simulation, and Docker only uses half by default. To change this setting we need to first stop the Docker VM that was started above in step 5. Run the command below in a "Docker Quickstart Terminal" window.

    ```bash
    $ docker-machine stop
    ```

10. Type 'VirtualBox' into the start menu search bar and launch "Oracle VM VirtualBox"
11. Click on the VM "default" in the left pane and then click "Settings"
12. Navigate to "System", then the "Processor" tab and move the slider all the way to the right.

    <img src="install_pngs/virtualbox_cores.png" width="400"/>

13. Click 'Ok', then reopen "Docker Quickstart Terminal". When you get the prompt after "Start interactive shell", you can continue on.

If you run into problems, check the official Docker Toolbox documentation: [Docker Toolbox for Windows](https://docs.docker.com/toolbox/toolbox_install_windows/)

## Start HNN

1. Verify that VcXsrv (XLaunch application) and Docker are running. Both will not start automatically after a reboot. VcXsrv (XLaunch application) will show an "X" icon in the Windows dock when running. The Docker Desktop icon should be present in the lower-right dock. To confirm that Docker is running properly, run the `docker ps` command, which return output similar to below and not return an error message.

    ```bash
    $ docker ps
    CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
    ```

2. Clone or download the [HNN repo](https://github.com/jonescompneurolab/hnn). **Chose one of the following methods:**

   * Option 1: Downloading a HNN release

     1. Download the source code (zip) for our latest HNN release from our [GitHub releases page](https://github.com/jonescompneurolab/hnn/releases)
     2. Open the .zip file and click "Extract all". Choose any destination folder on your machine.
     3. In the terminal, change to the directory part of the extracted HNN release shown below:

        ```bash
        $ cd REPLACE-WITH-FOLDER-EXTRACTED-TO\hnn\installer\windows
        ```

   * Option 2: Cloning (requires Git for Windows)

     1. If you didn't install Git for Windows above (not required), download the installer at [Git for Windows](https://gitforwindows.org/)
     2. If you already have a previous version of the repository, bring it up to date with the command `git pull origin master` instead of the `git clone` command below.

        ```bash
        $ cd ~
        $ git clone https://github.com/jonescompneurolab/hnn.git
        $ cd hnn/installer/windows
        ```

3. Start the Docker container. Note: the jonescompneurolab/hnn Docker image will be downloaded from Docker Hub (about 2 GB). The docker-compose command can be used to manage Docker containers described in the specification file docker-compose.yml.

    ```bash
    $ docker-compose run -e "DISPLAY=192.168.99.1:0" --name hnn_container hnn
    Creating network "windows_default" with the default driver
    Pulling hnn (jonescompneurolab/hnn:)...
    latest: Pulling from jonescompneurolab/hnn
    34dce65423d3: Already exists
    796769e96d24: Already exists
    2a0eada9611d: Already exists
    d6830a7cd972: Already exists
    ddf2bf28e180: Already exists
    77bf1279b29f: Pull complete
    6c8ddf82616f: Pull complete
    a991616934ba: Pull complete
    2cece6240c19: Pull complete
    df826e7d26b9: Pull complete
    824d51cbc89d: Pull complete
    0d16f27c744b: Pull complete
    Digest: sha256:0c27e2027828d2510a8867773562bbc966c509f45c9921cc2d1973c575d327b3
    Status: Downloaded newer image for jonescompneurolab/hnn:latest
    ```

4. A window will pop up stating "Docker needs to access your computer's filesystem". This is necessary to share data and parameter files that HNN creates with your Windows OS. Enter your Windows login password.

    <img src="install_pngs/access_filesystem.png" width="300" />

5. The HNN GUI should show up. Make sure that you can run simulations by clicking the 'Run Simulation' button. This will run a simulation with the default configuration. After it completes, graphs should be displayed in the main window.
    * If starting the GUI doesn't work the first time, the first thing to check is VcXsrv settings have "Disable access control" (see above). Then restart VcXsrv and try starting the HNN container again.
6. You can now proceed to running the tutorials at [https://hnn.brown.edu/index.php/tutorials/](https://hnn.brown.edu/index.php/tutorials/) . Some things to note:
   * A directory called "hnn_out" exists both inside the container (at /home/hnn_user/hnn_out) and outside (in the directory set by step 2) that can be used to share files between the container and your host OS.
   * The HNN repository with sample data and parameter files exists at /home/hnn_user/hnn_source_code

## Stopping Docker Toolbox VM

The Docker Toolbox VM will remain running the background using some resources. If you are not using HNN, you can shut down the VM by the following command:

```bash
$ docker-machine stop
```

## Upgrading to a new version of HNN

1. Verify that XLaunch and Docker are running. Both will not start automatically after a reboot by default.

2. You will then need to remove the existing hnn container

    ```bash
    $ cd hnn/installer/mac
    $ docker rm -f hnn_container
    hnn_container
    ```

3. Then download the latest version of the hnn container image with `docker-compose pull`:

    ```bash
    $ docker-compose pull
    Pulling hnn ... done
    ```

4. Start the hnn container:

    ```bash
    $ docker-compose up
    Recreating hnn_container ... done
    Attaching to hnn_container
    ```

## Editing files within HNN container

You may want run commands or edit files within the container. To access a command shell in the container, start the container with `docker-compose run -e "DISPLAY=192.168.99.1:0" --name hnn_container hnn` in one terminal window and open another terminal to use [`docker exec`](https://docs.docker.com/engine/reference/commandline/exec/) as shown below:

```none
$ docker exec -ti hnn_container bash
hnn_user@hnn-container:/home/hnn_user/hnn_source_code$
```

If you'd like to be able to copy files from the host OS without using the shared directory, you do so directly with [`docker cp`](https://docs.docker.com/engine/reference/commandline/cp/).

## Uninstalling HNN

If you want to remove the container and 1.6 GB HNN image, run the following commands from a quickstart terminal window. You can then remove Docker Desktop using "Add/Remove Programs"

```bash
$ docker rm -f windows_hnn_1
$ docker rmi jonescompneurolab/hnn
```

## Troubleshooting

For errors related to Docker, please see the [Docker troubleshooting section](../docker/troubleshooting.md)

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.

For other HNN software issues, please visit the [HNN bulletin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)
