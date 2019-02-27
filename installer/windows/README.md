# Installing HNN on Windows (Docker install)

This guide describes installing HNN on Windows 10 using Docker. This method will automatically download the HNN Docker container image when HNN is started for the first time. If you would prefer to install HNN without Docker, please see the instructions below.
  - Alternative: [Native install instructions (advanced users)](native_install.md)

## Prerequisite: Hyper-V support
The Hyper-V feature must be enabled on your computer to use the Docker-based installation. Not all systems support this feature, and it may require making changes to your computer's BIOS settings. If you run into problems enabling Hyper-V, we recommend that you follow the [native install instructions](native_install.md) instead. You can check whether it is enabled with the following procedure.

1. Open the Control Panel "Turn Windows features on or off" (search bar next to start menu).
2. Make sure that Hyper-V is turned on as in the image below

    <img src="install_pngs/hyper-V.png" height="200" />

3. If you enabled Hyper-V, please reboot your computer before continuing below to install docker.

## Prerequisite: VcXsrv
1. Download the installer (version 64.1.20.1.4 tested): https://sourceforge.net/projects/vcxsrv/files/latest/download
   * [Alternative direct download link](https://downloads.sourceforge.net/project/vcxsrv/vcxsrv/1.20.1.4/vcxsrv-64.1.20.1.4.installer.exe?r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Fvcxsrv%2Ffiles%2Fvcxsrv%2F1.20.1.4%2Fvcxsrv-64.1.20.1.4.installer.exe%2Fdownload%3Fuse_mirror%3Dversaweb%26r%3Dhttps%253A%252F%252Fsourceforge.net%252Fprojects%252Fvcxsrv%252Ffiles%252Flatest%252Fdownload&ts=1550243133)
2. Run the installer, choosing any installation folder.
3. Start the XLaunch desktop app from the VcXsrv folder in the start menu.
4. Choose "Multiple windows" and set "Display number" to '0'. Click 'Next'.
5. Select "Start no client" and click 'Next'.
6. Under "Extra settings" make sure that "Disable access control" is checked.
7. Click "Finish" and an "X" icon will appear in the lower-right dock signaling that VcXsrv is waiting for connections.
8. A message from Windows firewall to allow connections may pop up. If it does, choose options allowing connections to the VcXsrv when connected to both public and private networks.

## Prerequisite: Docker

Click on your version of Windows to expand instructions:
<details><summary>Windows 10 (Pro/Enterprise only): Docker Desktop</summary>
<p>

1. In order to download Docker Desktop, you'll need to sign up for a Docker Hub account. It only requires an email address to confirm the account. Sign up here: [Docker Hub Sign-up](https://hub.docker.com/signup)
2. Download the installer (requires logging in to your Docker Hub account):
https://hub.docker.com/editions/community/docker-ce-desktop-windows
3. Run the installer. **DO NOT check** "Use Windows containers instead of Linux containers".
4. Start the Docker Desktop app from the start menu (requires logging in to your Docker Hub account).
5. The installer may prompt you to turn on Hyper-V, which will not allow you to also run virtual machines through applications such as VirtualBox. If you get an error saying that Hyper-V needs to be enabled, you can do it manually by "Control Panel" -> Programs -> "Turn Windows features on or off" and select all Hyper-V options (a reboot is required).
   * If you get a message similar to the screen below, click 'Ok' and restart your computer.
     <img src="install_pngs/enable_hyperv.png" height="150" />

6. Docker Desktop will start automatically and the Docker icon will show up in the lower-right dock
   * If you get the error message shown below, there was a problem turning on virtualization, which is required for Docker on Windows. This may be fixable by changing settings in your motherboard's BIOS menu (see [step-by-step guide](https://blogs.technet.microsoft.com/canitpro/2015/09/08/step-by-step-enabling-hyper-v-for-use-on-windows-10/)), however, at this point, the easiest option for installing HNN would be to switch to using the PowerShell script (method 2). Please uninstall Docker, and then proceed with the instructions below for method 2.

     <img src="install_pngs/hyperv_error.png" height="150" />

</p>
</details>

<details><summary>Windows 10 Home: Docker Toolbox</summary>
<p>

1. Download the installer:
https://docs.docker.com/toolbox/toolbox_install_windows/
2. Run the installer. In "Select Components" check the component "Docker Compose for Windows". Click 'Next'.
3. In "Select Additional Tasks", **check "Add docker binaries to PATH"**. Click 'Next'.
4. Choose the default for the other options and click 'Install'.
5. Launch "Docker Quickstart Terminal" from the Desktop or start menu.
6. Run the commands below from a new cmd.exe window.

</p>
</details>

## Start HNN
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
5. The HNN GUI should show up and you should now be able to run the tutorials at https://hnn.brown.edu/index.php/tutorials/
   * A directory called "hnn" exists both inside the container (at /home/hnn_user/hnn) and outside (in the directory where step 3 was run) that can be used to share files between the container and your host OS.
   * If you run into problems starting the Docker container or the GUI is not displaying, please see the [Docker troubleshooting section](../docker/README.md#Troubleshooting)
   * If you closed the HNN GUI, and would like to restart it, run the following:
      ```
      docker-compose restart
      ```

6. **NOTE:** You may want run commands or edit files within the container. To access a command prompt in the container, use [`docker exec`](https://docs.docker.com/engine/reference/commandline/exec/):
    ```
    C:\Users\myuser>docker exec -ti windows_hnn_1 bash
    hnn_user@054ba0c64625:/home/hnn_user$
    ```

    If you'd like to be able to copy files from the host OS without using the shared directory, you do so directly with [`docker cp`](https://docs.docker.com/engine/reference/commandline/cp/).

## Uninstalling HNN

If you want to remove the container and 1.5 GB HNN image, run the following commands from a cmd.exe window. You can then remove Docker Desktop using "Add/Remove Programs"
```
docker rm -f windows_hnn_1
docker rmi jonescompneurolab/hnn
```


# Troubleshooting

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.

For other HNN software issues, please visit the [HNN bullentin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)