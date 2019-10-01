# Installing HNN on Mac OS (Docker Toolbox)

## Prerequisite: XQuartz

1. Download the installer image (version 2.7.11 tested): https://www.xquartz.org/
2. Run the XQuartz.pkg installer within the image, granting privileges when requested.
3. Start the XQuartz application. An "X" icon will appear in the taskbar along with a terminal, signaling that XQuartz is waiting for connections. You can minimize the terminal, but do not close it.
4. **Important** - Open the XQuartz preferences and navigate to the "security" tab. Make sure "Authenticate connections" is unchecked and "Allow connections from network clients" is checked.

   <img src="install_pngs/xquartz_preferences.png" height="250" />
5. Quit X11 and the restart the application. This is needed for the setting above to take effect.

## Prerequisite: Docker Toolbox

1. Download the installer image: [Docker Toolbox for Mac](https://docs.docker.com/toolbox/toolbox_install_mac/)
2. Run the installer, selecting any directory for installation.
3. Choose "Docker Quickstart Terminal" tool
4. You may get an error such as the one below. You need to grant Docker Quickstart Terminal permission to control you computer in System Preferences -> Security -> Privacy -> Privacy -> Accessibility. If it's already checked, uncheck it and check it again.
5. After a couple of minutes the "Waiting for an IP" task should complete.
6. Run the commands below in the same terminal window or by relaunching "Docker Quickstart Terminal".

## Start HNN

1. Verify that XQuartz and Docker are running. These will not start automatically after a reboot. To confirm that Docker is running properly, typing `docker info` should return a bunch of output, but no errors.

    ```bash
    $ docker info
    ```

2. Clone or download the [HNN repo](https://github.com/jonescompneurolab/hnn). **Chose one of the following methods:**
   * Option 1: Downloading a HNN release

     1. Download the source code (zip) for our latest HNN release from our [GitHub releases page](https://github.com/jonescompneurolab/hnn/releases)
     2. Open the .zip file and click "Extract all". Choose any destination folder on your machine.
     3. Open a cmd.exe window and change to the directory part of the extracted HNN release shown below:

        ```bash
        $ cd REPLACE-WITH-FOLDER-EXTRACTED-TO/hnn/installer/mac
        ```

   * Option 2: Cloning (requires Xcode Command Line Tools)

     1. Check that you have Git installed from a terminal window

        ```bash
        $ git version
        git version 2.17.2 (Apple Git-113)
        ```

     2. Type the following to clone the repo. If you already have a previous version of the repository, bring it up to date with the command `git pull origin master` instead of the `git clone` command below.

        ```bash
        $ git clone https://github.com/jonescompneurolab/hnn.git
        $ cd hnn/installer/mac
        ```

3. Start the Docker container. Note: the jonescompneurolab/hnn Docker image will be downloaded from Docker Hub (about 2 GB). The `docker-compose` command can be used to manage Docker containers described in the specification file docker-compose.yml.

    ```bash
    $ docker-compose run -e "DISPLAY=192.168.99.1:0" --name hnn_container hnn
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

4. The HNN GUI should show up. Make sure that you can run simulations by clicking the 'Run Simulation' button. This will run a simulation with the default configuration. After it completes, graphs should be displayed in the main window.
    * If starting the GUI doesn't work the first time, the first thing to check is XQuartz settings (see screnshot above). Then restart XQuartz and try starting the HNN container again.
5. You can now proceed to running the tutorials at https://hnn.brown.edu/index.php/tutorials/](https://hnn.brown.edu/index.php/tutorials/) . Some things to note:
   * A directory called "hnn_out" exists both inside the container (at /home/hnn_user/hnn_out) and outside (in the directory set by step 2) that can be used to share files between the container and your host OS.
   * The HNN repository with sample data and parameter files exists at /home/hnn_user/hnn_source_code.

## Stopping Docker Toolbox VM

The Docker Toolbox VM will remain running the background using some resources. If you are not using HNN, you can shut down the VM by the following command:

   ```bash
   $ docker-machine stop
   ```

## Upgrading to a new version of HNN

1. Verify that XQuartz and Docker are running. XQuartz will not start automatically after a reboot by default.
2. Open a terminal window

    ```bash
    $ cd hnn/installer/mac
    $ docker-compose pull
    Pulling hnn ... done
    $ docker-compose run -e "DISPLAY=192.168.99.1:0" --name hnn_container hnn
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

If you want to remove the container and 1.5 GB HNN image, run the following commands from a terminal window. You can then remove Docker Desktop by removing it from your Applications folder.

```bash
$ docker rm -f hnn_container
$ docker rmi jonescompneurolab/hnn
```

## Troubleshooting

For errors related to Docker, please see the [Docker troubleshooting section](../docker/troubleshooting.md)

For Mac OS specific issues: please see the [Mac OS troubleshooting page](troubleshooting.md)

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.

For other HNN software issues, please visit the [HNN bulletin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)
