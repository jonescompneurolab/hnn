# Installing HNN on Windows systems

This guide describes two methods for installing HNN and its prerequisistes on a Windows 10 system:

1. A docker container running a Linux install of HNN (recommended)
2. Natively running HNN on Windows (better performance)

The docker installation is recommended because the python environment and the NEURON installation are fully isolated, reducing the possibility of version conflicts, or the wrong version being used. The same Docker container is used for all platforms (Windows/Linux/Mac) meaning it has likely been tested more recently.

Method 1 (using Docker) displays the GUI through an X windows server which may lead to slower responsiveness as compared to using method 2, which displays the GUI running natively on Windows.

## Docker Install

[Docker Desktop](https://www.docker.com/products/docker-desktop) for Windows 10 (Pro/Enterprise only) is capable of running both Linux containers and Windows containers. For HNN's GUI to display properly, only Linux containers work. Docker Desktop is installed with this configuration by default.  For Windows 10 Home or other versions of windows, use the legacy version of [Docker Toolbox](https://docs.docker.com/toolbox/toolbox_install_windows/).

The only other component to install is an X server. Both [VcXsrv](https://sourceforge.net/projects/vcxsrv/) and [Xming](https://sourceforge.net/projects/xming/) are recommended free options. These install instructions will cover VcXsrv.

### Install VcXsrv
1. Download the installer (version 64.1.20.1.4 tested): https://sourceforge.net/projects/vcxsrv/files/latest/download
2. Run the installer, choosing any installation folder.
3. Start the XLaunch desktop app from the VcXsrv folder in the start menu.
4. Choose "Multiple windows" and set "Display number" to '0'. Click 'Next'.
5. Select "Start no client" and click 'Next'.
6. Under "Extra settings" make sure that "Disable access control" is checked.
7. Click "Finish" and an "X" icon will appear in the lower-right dock signaling that VcXsrv is waiting for connections.

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
1. Open a cmd.exe window and run `ipconfig` to get your external IPv4 address e.g. "Wireless LAN adapter Wi-Fi 2" 
    ```
    C:\Users\myuser>ipconfig

    Windows IP Configuration
    ...
    Wireless LAN adapter Wi-Fi 2:

       Connection-specific DNS Suffix  . :
       ...
       IPv4 Address. . . . . . . . . . . : 192.168.0.16
       Subnet Mask . . . . . . . . . . . : 255.255.255.0
       ...
    ```
2. Set an environment variable DISPLAY containing "[IP address]:0" (e.g. `192.168.0.16:0`)
    ```
    set DISPLAY=[external IPv4 address]:0
    ```
3. Clone or download the [HNN repo](https://github.com/jonescompneurolab/hnn). Assuming [Git for Windows](https://gitforwindows.org/) is installed, type the following in a cmd.exe window:
    ```
    git clone https://github.com/jonescompneurolab/hnn.git
    cd hnn\installer\docker
    ```
4. Build start the Docker container. Note: build may take more than 10 minutes
    ```
    docker-compose build
    docker-compose up -d
    ```
5. A prompt from the dock will ask you to share the drive. Click 'Share'
6. The HNN GUI should show up and you should now be able to run the tutorials at: https://hnn.brown.edu/index.php/tutorials/
7. **NOTE:** To access a command prompt in the container, use `docker exec`:
    ```
    docker exec -ti docker_hnn_1 bash
    ```






[](https://docs.docker.com/docker-for-windows/install/)
## Native Install

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

