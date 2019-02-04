# Installing HNN on Windows systems

This guide describes two methods for installing HNN and its prerequisistes on a Windows 10 system:

1. A Docker container running a Linux install of HNN (recommended)
2. Natively running HNN on Windows (better performance)

The Docker installation is recommended because the python environment and the NEURON installation are fully isolated, reducing the possibility of version conflicts, or the wrong version being used. The same Docker container is used for all platforms (Windows/Linux/Mac) meaning it has likely been tested more recently.

Method 1 (using Docker) displays the GUI through an X server which may lead to slower responsiveness as compared to using method 2, which displays the GUI running natively on Windows.

## Docker install

[Docker Desktop](https://www.docker.com/products/docker-desktop) for Windows 10 (Pro/Enterprise only) is capable of running both Linux containers and Windows containers. For HNN's GUI to display properly, only Linux containers work. Docker Desktop is installed with this configuration by default.  For Windows 10 Home or other versions of windows, use the legacy version of [Docker Toolbox](https://docs.docker.com/toolbox/overview/).

The only other component to install is an X server. Both [VcXsrv](https://sourceforge.net/projects/vcxsrv/) and [Xming](https://sourceforge.net/projects/xming/) are recommended free options. These install instructions will cover VcXsrv.

### Install VcXsrv
1. Download the installer (version 64.1.20.1.4 tested): https://sourceforge.net/projects/vcxsrv/files/latest/download
2. Run the installer, choosing any installation folder.
3. Start the XLaunch desktop app from the VcXsrv folder in the start menu.
4. Choose "Multiple windows" and set "Display number" to '0'. Click 'Next'.
5. Select "Start no client" and click 'Next'.
6. Under "Extra settings" make sure that "Disable access control" is checked.
7. Click "Finish" and an "X" icon will appear in the lower-right dock signaling that VcXsrv is waiting for connections.
8. A message from Windows firewall to allow connections may pop up. If it does, choose options allowing connections to the VcXsrv when connected to both public and private networks.


### Install Docker Desktop (Windows 10 Pro/Enterprise)
1. Download the installer (requires a free Docker Hub account):
https://hub.docker.com/editions/community/docker-ce-desktop-windows
2. Run the installer. **DO NOT check** "Use Windows containers instead of Linux containers".
3. Start the Docker Desktop app from the start menu.
4. The installer may prompt you to turn on Hyper-V, which will not allow you to also run virtual machines through applications such as VirtualBox. If you get an error saying that Hyper-V needs to be enabled, you can do it manually by: Go to "Control Panel" → Programs → "Turn Windows features on or off" and select all Hyper-V options (a reboot is required).
5. Docker Desktop will start automatically and the Docker icon will show up in the lower-right dock

### Install Docker Toolbox (Windows 10 Home)
1. Download the installer:
https://docs.docker.com/toolbox/toolbox_install_windows/
2. Run the installer. In "Select Components" check the component "Docker Compose for Windows". Click 'Next'.
3. In "Select Additional Tasks", **check "Add docker binaries to PATH"**. Click 'Next'.
4. Choose the default for the other options and click 'Install'.
5. Launch "Docker Quickstart Terminal" from the Desktop or start menu and make sure that Docker has started with
    ```
    docker info
    ```
6. Run the commands below from a new cmd.exe window.

### Start the HNN Docker container
1. Verify that the docker interface on your system has an IP address of 10.0.75.1. If you see a different IP address from the output of ipconfig, use that instead. Open a cmd.exe window and run `ipconfig`. The output should be similar to below. If the IP address differs from 10.0.75.1, you need to correct it in [docker-compose.yml](../docker/docker-compose.yml).
    ```
    C:\Users\[USER]>ipconfig

    Windows IP Configuration


    Ethernet adapter vEthernet (DockerNAT):

       Connection-specific DNS Suffix  . :
       IPv4 Address. . . . . . . . . . . : 10.0.75.1
       Subnet Mask . . . . . . . . . . . : 255.255.255.0
       Default Gateway . . . . . . . . . :

    ```
2. Clone or download the [HNN repo](https://github.com/jonescompneurolab/hnn). Assuming [Git for Windows](https://gitforwindows.org/) is installed, type the following in a cmd.exe window:
    ```
    git clone https://github.com/jonescompneurolab/hnn.git
    cd hnn\installer\windows
    ```
3. Start the Docker container. Note: the jonescompneurolab/hnn docker image will be downloaded from Docker Hub (about 1.5 GB)
    ```
    docker-compose up -d
    ```
4. A prompt from the dock will ask you to share the drive. Click 'Share'
5. The HNN GUI should show up and you should now be able to run the tutorials at: https://hnn.brown.edu/index.php/tutorials/

   * If you run into problems starting the Docker container or the GUI is not displaying, please see the [Docker troubleshooting section](../docker/README.md#Troubleshooting)
   * If you closed the HNN GUI, and would like to restart it, run the following:
      ```
      docker-compose restart
      ```

6. **NOTE:** You may want to edit files within the container. To access a command prompt in the container, use `docker exec`:
    ```
    docker exec -ti docker_hnn_1 bash
    ```
    If you'd like to be able to access files from the host Windows system within the container, you can either copy files with [docker cp](https://docs.docker.com/engine/reference/commandline/cp/) or start the container with host directory that is visible as a "volume" within the container (instead of step 3):
    ```
    mkdir %HOME%\dir_on_host
    docker-compose run -d -v %HOME%\dir_on_host:/home/hnn_user/dir_from_host hnn
    ```
    * Note the different container name after running docker-compose

## Native install script

The [HNN install powershell script](hnn.ps1) will manage downloading all prerequisites except Microsoft MPI which requires a web browser to download. If the script finds msmpisetup.exe in the Downloads folder, it will take care of installing it.

Requirements:
 - A 64-bit OS
 - Windows 7 or later. Windows Vista is not supported for lack of multiprocessing support.
 - Powershell version 1.0 or later. If Powershell is not installed, please follow the link below for downloading and running the Powershell installer:
 https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell

Install procedure:
1. Download Microsoft MPI (msmpisetup.exe) from the link below and save it to the user's Downloads  folder (C:\Users\\[MY_USERNAME]\Downloads): https://msdn.microsoft.com/en-us/library/bb524831.aspx

2. Run the script from a cmd prompt:
    ```
    @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/jonescompneurolab/hnn/master/installer/windows/hnn.ps1'))"
    ```
    OR from a powershell prompt:
    ```
    Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/jonescompneurolab/hnn/master/installer/windows/hnn.ps1'))
    ```
    OR from a local copy:
    ```
    powershell.exe -ExecutionPolicy Bypass -File .\hnn\installer\windows\hnn.ps1
    ```
   * There will be a permission prompt to install Microsoft MPI and a couple of terminal windows will
open up. There will be a prompt for pressing ENTER after nrnmech.dll has been built
   * If an existing Python 3.X installation isn't found, expect that installation will pause for ~5min while installing Miniconda

3. After the script has completed, instructions will be displayed for using the environment either with virtualenv or Miniconda. Open up a new cmd.exe window (not Powershell) for the environment variables to get set in the session.
4. Run:
    ```
    activate hnn
    cd hnn
    python hnn.py hnn.cfg
    ```
5. That will launch the HNN GUI. You should now be able to run the tutorials at: https://hnn.brown.edu/index.php/tutorials/

