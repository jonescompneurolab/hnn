# Installing HNN on Windows systems

This guide describes two methods for installing HNN and its prerequisistes on a Windows 10 system:

Method 1: A Docker container running a Linux install of HNN (recommended)
   - The Docker installation fully isolates HNN's python environment and the NEURON installation from the rest of your system, reducing the possibility of version incompatibilities. Additionally, the same Docker container is used for all platforms (Windows/Linux/Mac) meaning it has likely been tested more recently.

Method 2: Running a script to install HNN natively on Windows (advanced users)
   - A script will download and install prerequisites without using virtualization, meaning the GUI may feel more responsive and simulations may run slightly faster. The script will detect installed Python environments, and install the HNN prerequisites in an isolated environment using conda or virtualenv. It is safe to run the script multiple times.

**Note (only for method 1):**  the Hyper-V feature must be enabled on your computer to use the Docker-based installation. Not all systems support this feature, and it may require making changes to your computer's BIOS settings. You can check whether it is enabled with the following procedure.

1. Open the Control Panel "Turn Windows features on or off" (search bar next to start menu).
2. Make sure that Hyper-V is turned on as in the image below

    <img src="install_pngs/hyper-V.png" height="200" />

3. If Hyper-V was disabled, please reboot your computer before continuing below to install docker.

## Method 1: Docker install

[Docker Desktop](https://www.docker.com/products/docker-desktop) for Windows 10 (Pro/Enterprise only) is capable of running both Linux containers and Windows containers. For HNN's GUI to display properly, only Linux containers work. Docker Desktop is installed with this configuration by default.  For Windows 10 Home or other versions of windows, use the legacy version of [Docker Toolbox](https://docs.docker.com/toolbox/overview/).

The only other component to install is an X server. Both [VcXsrv](https://sourceforge.net/projects/vcxsrv/) and [Xming](https://sourceforge.net/projects/xming/) are recommended free options. These install instructions will cover VcXsrv.

### Prerequisite: install VcXsrv
1. Download the installer (version 64.1.20.1.4 tested): https://sourceforge.net/projects/vcxsrv/files/latest/download
   * [Alternative direct download link](https://downloads.sourceforge.net/project/vcxsrv/vcxsrv/1.20.1.4/vcxsrv-64.1.20.1.4.installer.exe?r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Fvcxsrv%2Ffiles%2Fvcxsrv%2F1.20.1.4%2Fvcxsrv-64.1.20.1.4.installer.exe%2Fdownload%3Fuse_mirror%3Dversaweb%26r%3Dhttps%253A%252F%252Fsourceforge.net%252Fprojects%252Fvcxsrv%252Ffiles%252Flatest%252Fdownload&ts=1550243133)
2. Run the installer, choosing any installation folder.
3. Start the XLaunch desktop app from the VcXsrv folder in the start menu.
4. Choose "Multiple windows" and set "Display number" to '0'. Click 'Next'.
5. Select "Start no client" and click 'Next'.
6. Under "Extra settings" make sure that "Disable access control" is checked.
7. Click "Finish" and an "X" icon will appear in the lower-right dock signaling that VcXsrv is waiting for connections.
8. A message from Windows firewall to allow connections may pop up. If it does, choose options allowing connections to the VcXsrv when connected to both public and private networks.


### Prerequisite (Windows 10 Pro/Enterprise): install Docker Desktop
1. Download the installer (requires a free Docker Hub account):
https://hub.docker.com/editions/community/docker-ce-desktop-windows
2. Run the installer. **DO NOT check** "Use Windows containers instead of Linux containers".
3. Start the Docker Desktop app from the start menu.
4. The installer may prompt you to turn on Hyper-V, which will not allow you to also run virtual machines through applications such as VirtualBox. If you get an error saying that Hyper-V needs to be enabled, you can do it manually by: Go to "Control Panel" → Programs → "Turn Windows features on or off" and select all Hyper-V options (a reboot is required).
   * If you get a message similar to the screen below, click 'Ok' and restart your computer.
     <img src="install_pngs/enable_hyperv.png" height="150" />

6. Docker Desktop will start automatically and the Docker icon will show up in the lower-right dock
   * If you get the error message shown below, there was a problem turning on virtualization, which is required for Docker on Windows. This may be fixable by changing settings in your motherboard's BIOS menu (see [step-by-step guide](https://blogs.technet.microsoft.com/canitpro/2015/09/08/step-by-step-enabling-hyper-v-for-use-on-windows-10/)), however at this point, the easiest option for installing HNN would be to switch to using the powershell script (method 2). Please uninstall Docker, and then proceed with the instructions below for method 2.

     <img src="install_pngs/hyperv_error.png" height="150" />

### Prerequisite (Windows 10 Home only): install Docker Toolbox
1. Download the installer:
https://docs.docker.com/toolbox/toolbox_install_windows/
2. Run the installer. In "Select Components" check the component "Docker Compose for Windows". Click 'Next'.
3. In "Select Additional Tasks", **check "Add docker binaries to PATH"**. Click 'Next'.
4. Choose the default for the other options and click 'Install'.
5. Launch "Docker Quickstart Terminal" from the Desktop or start menu.
6. Run the commands below from a new cmd.exe window.

### Start HNN
1. Verify that VcXsrv (XLaunch application) and Docker are running. These will not start automatically after a reboot. Check that Docker is running properly by typing the following in a new cmd.exe window.
    ```
    docker info
    ```
2. Clone or download the [HNN repo](https://github.com/jonescompneurolab/hnn). Assuming [Git for Windows](https://gitforwindows.org/) is installed, type the following in a cmd.exe window. If you already have a previous version of the repository, bring it up to date with the command `git pull origin master` instead of the `git clone` command below.
    ```
    git clone https://github.com/jonescompneurolab/hnn.git
    cd hnn\installer\windows
    ```
3. Start the Docker container. Note: the jonescompneurolab/hnn docker image will be downloaded from Docker Hub (about 1.5 GB). Docker-compose starts a docker container based on the specification file docker-compose.yml and "up" starts the containers in that file and "-d" starts the docker containers in the background.
    ```
    docker-compose up -d
    ```
4. A prompt will ask you to share the drive. Click 'Share'
5. The HNN GUI should show up and you should now be able to run the tutorials at: https://hnn.brown.edu/index.php/tutorials/
   * A directory called "hnn" exists both inside the container (at /home/hnn_user/hnn) and outside (in the directory where step 3 was run) that can be used to share files between the container and your host OS.
   * If you run into problems starting the Docker container or the GUI is not displaying, please see the [Docker troubleshooting section](../docker/README.md#Troubleshooting)
   * If you closed the HNN GUI, and would like to restart it, run the following:
      ```
      docker-compose restart
      ```

6. **NOTE:** You may want run commands or edit files within the container. To access a command prompt in the container, use [`docker exec`](https://docs.docker.com/engine/reference/commandline/exec/):
    ```
    C:\Users\myuser>docker exec -ti mac_hnn_1 bash
    hnn_user@054ba0c64625:/home/hnn_user$
    ```

    If you'd like to be able to copy files from the host OS without using the shared directory, you do so directly with [`docker cp`](https://docs.docker.com/engine/reference/commandline/cp/).

## Method 2: native install script

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

