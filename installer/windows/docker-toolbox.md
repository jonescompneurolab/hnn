# Installing HNN on Windows 10 (Home)

## Prerequisite: hardware virtualization features (manual setting)

Nearly all PC's have this feature, but it may not be enabled by default. If not already enabled, it may be necessary to manually set these through your PC manufacturer's BIOS settings. However, if Docker cannot turn this feature on from its installer, you may need to reboot your computer and change your PC manufacturer's BIOS settings. You can check whether it is enabled from the Task Manger. The picture below shows that hardware virtualization is disabled and will need to be manually enabled in the BIOS.

      <img src="install_pngs/virtualization_disabled.png" height="250" />
    
    See [https://www.trishtech.com/2017/08/check-if-virtualization-is-enabled-in-windows-10](https://www.trishtech.com/2017/08/check-if-virtualization-is-enabled-in-windows-10) for more details.

    If you run into problems enabling hardware virtualization support, we recommend that you follow the [native install instructions](native_install.md) instead. Also running our [VirtualBox VM with HNN pre-installed](https://hnn.brown.edu/index.php/installation-instructions/) is possible without hardware virtualization support.

## Prerequisite: VcXsrv
1. Download the installer from [https://sourceforge.net/projects/vcxsrv/files/latest/download](https://sourceforge.net/projects/vcxsrv/files/latest/download)
   * Here's the link to the [direct download of version 64.1.20.1.4](https://downloads.sourceforge.net/project/vcxsrv/vcxsrv/1.20.1.4/vcxsrv-64.1.20.1.4.installer.exe?r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Fvcxsrv%2Ffiles%2Fvcxsrv%2F1.20.1.4%2Fvcxsrv-64.1.20.1.4.installer.exe%2Fdownload%3Fuse_mirror%3Dversaweb%26r%3Dhttps%253A%252F%252Fsourceforge.net%252Fprojects%252Fvcxsrv%252Ffiles%252Flatest%252Fdownload&ts=1550243133)
2. Run the installer, choosing any installation folder.
3. Start the XLaunch desktop app from the VcXsrv folder in the start menu.
4. Choose "Multiple windows" and click 'Next'. Leave "Display number" at '-1'.
5. Select "Start no client" and click 'Next'.
6. Under "Extra settings" make sure that "Disable access control" is checked.
7. Click "Save configuration" to create a shortcut with the settings we just chose. Click "Finish" and an "X" icon will appear in the lower-right dock signaling that VcXsrv has started.
8. A message from Windows firewall to allow connections may pop up. If it does, choose options allowing connections to the VcXsrv when connected to both public and private networks.

## Prerequisite: Docker Toolbox

1. Download the installer: [Docker Toolbox for Windows](https://docs.docker.com/toolbox/toolbox_install_windows/)
2. Run the installer. In "Select Components" check the component "Docker Compose for Windows". Click 'Next'.
3. In "Select Additional Tasks", **check "Add docker binaries to PATH"**. Click 'Next'.
4. Choose the default for the other options and click 'Install'.
5. Launch "Docker Quickstart Terminal" from the Desktop or start menu.
   * If you get the error message shown below, hardware support for virtualization isn't turned on, which is required for Docker on Windows. This may be fixable by changing settings in your PC manufacturer's BIOS. See the note on "Hardware virtualization features" under the "Prerequisite: Virtualization support" heading at the top of this page.

     <img src="install_pngs/vtx_disabled.png" height="150" />

6. Run the commands below from a new cmd.exe window.

## Start HNN
1. Verify that VcXsrv (XLaunch application) and Docker are running. VcXsrv will not start automatically after a reboot. The Docker Desktop icon should be present in the lower-right dock. To confirm that Docker is running properly, typing the following in a new cmd.exe window.
    ```
    docker info
    ```
2. Clone or download the [HNN repo](https://github.com/jonescompneurolab/hnn). **Chose one of the following methods:**

   * Option 1: Cloning (requires Git for Windows)

     1. First install [Git for Windows](https://gitforwindows.org/)
     2. Type the following in a cmd.exe window. If you already have a previous version of the repository, bring it up to date with the command `git pull origin master` instead of the `git clone` command below.

        ```
        C:\Users\myuser> git clone https://github.com/jonescompneurolab/hnn.git
        C:\Users\myuser\hnn\installer\windows> cd hnn\installer\windows
        ```
   
   * Option 2: Downloading a HNN release

     1. Download the source code (zip) for our latest HNN release from our [GitHub releases page](https://github.com/jonescompneurolab/hnn/releases)
     2. Open the .zip file and click "Extract all". Choose any destination folder on your machine.
     3. Open a cmd.exe window and change to the directory part of the extracted HNN release shown below:
        ```
        C:\Users\myuser> cd REPLACE-WITH-FOLDER-EXTRACTED-TO\hnn\installer\windows
        ```

3. Start the Docker container. Note: the jonescompneurolab/hnn Docker image will be downloaded from Docker Hub (about 1.5 GB). The docker-compose command can be used to manage Docker containers described in the specification file docker-compose.yml. The parameter "up" starts the containers (just one in our case) in that file and "-d" starts the docker container in the background.
    ```
    C:\Users\myuser\hnn\installer\windows> docker-compose run -d --name windows_hnn_1 -e "DISPLAY=192.168.99.1:0" hnn
    mac_hnn_1
    ```
    * You can see that the HNN container is running
      ```
      C:\Users\myuser> docker ps -a
      CONTAINER ID  IMAGE                 COMMAND                 CREATED        STATUS       PORTS  NAMES
      1fa235c2f831  jonescompneurolab/hnn "/home/hnn_user/star…"  6 seconds ago  Up 5 seconds        windows_hnn_1
      ```

    * If starting the GUI doesn't work the first time, the first thing to check is VcXsrv settings have "Disable access control" (see above). Then restart VcXsrv and try starting the HNN container again with
      ```
      C:\Users\myuser\hnn\installer\windows> docker-compose restart
      ```
4. A window will pop up stating "Docker needs to access your computer's filesystem". This is necessary to share data and parameter files that HNN creates with your Windows OS. Enter your Windows login password.

   <img src="install_pngs/access_filesystem.png" height="200" />

5. The HNN GUI should show up. Make sure that you can run simulations by cliking the 'Run Simulation' button. This will run a simulation with the default configuration. After it completes, graphs should be displayed in the main window.
6. You can now proceed to running the tutorials at https://hnn.brown.edu/index.php/tutorials/ . Some things to note:
   * A directory called "hnn" exists both inside the container (at /home/hnn_user/hnn) and outside (in the directory set by step 2) that can be used to share files between the container and your host OS.
   * The HNN repository with sample data and parameter files exists at /home/hnn_user/hnn_repo. You will probably want to browse to this directory when using "Set Parameters from File" in the GUI
   * If you run into problems starting the Docker container or the GUI is not displaying, please see the [Docker troubleshooting section](../docker/README.md#Troubleshooting)


## Launching HNN again
1. Verify that VcXsrv and Docker are running. Both will not start automatically after a reboot by default.
2. Open a Command Prompt (cmd.exe)
    ```
    C:\Users\myuser> cd hnn\installer\windows
    C:\Users\myuser> docker-compose restart
    ```

## Editing files within HNN container
You may want run commands or edit files within the container. To access a command shell in the container, use [`docker exec`](https://docs.docker.com/engine/reference/commandline/exec/) as shown below:
```
C:\Users\myuser> docker exec -ti windows_hnn_1 bash
hnn_user@054ba0c64625:/home/hnn_user$
```

If you'd like to be able to copy files from the host OS without using the shared directory, you do so directly with [`docker cp`](https://docs.docker.com/engine/reference/commandline/cp/).

## Uninstalling HNN

If you want to remove the container and 1.5 GB HNN image, run the following commands from a cmd.exe window. You can then remove Docker Desktop using "Add/Remove Programs"
```
C:\Users\myuser> docker rm -f windows_hnn_1
C:\Users\myuser> docker rmi jonescompneurolab/hnn
```


# Troubleshooting

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.

For other HNN software issues, please visit the [HNN bullentin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)
