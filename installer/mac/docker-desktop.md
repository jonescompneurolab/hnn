# Installing HNN on Mac OS (Docker Desktop)

## Prerequisite: XQuartz
1. Download the installer image (version 2.7.11 tested): https://www.xquartz.org/
2. Run the XQuartz.pkg installer within the image, granting privileges when requested.
3. Start the XQuartz application. An "X" icon will appear in the taskbar along with a terminal, signaling that XQuartz is waiting for connections. You can minimize the terminal, but do not close it.
4. **Important** - Open the XQuartz preferences and navigate to the "security" tab. Make sure "Authenticate connections" is unchecked and "Allow connections from network clients" is checked.

   <img src="install_pngs/xquartz_preferences.png" height="250" />
5. Quit X11 and the restart the application. This is needed for the setting above to take effect.

## Prerequisite: Docker Desktop

1. In order to download Docker Desktop, you'll need to sign up for a Docker Hub account. It only requires an email address to confirm the account. Sign up here: [Docker Hub Sign-up](https://hub.docker.com/signup)
2. Download the installer image (requires logging in to your Docker Hub account): [Docker Desktop](https://hub.docker.com/editions/community/docker-ce-desktop-mac)
3. Run the Docker Desktop installer, moving docker to the applications folder.
4. Start the Docker application, acknowledging that it was downloaded from the Internet and you still want to open it.
5. Log into your Docker Hub account if prompted by the Docker Desktop application.
6. The Docker Desktop icon will appear in the taskbar with the message "Docker Desktop is starting", Followed by "Docker Desktop is now up and running!".
7. Increase the number of cores that Docker can use (we recommend all cores) by clicking on the Docker Desktop icon in the taskbar and then clicking "Preferences". Choose the "Advanced" tab, and adjust with the slider.

   <img src="install_pngs/docker_cores.png" height="300" />

## Start HNN
1. Verify that XQuartz and Docker are running. These will not start automatically after a reboot. Check that Docker is running properly by typing the following in a new terminal window.
    ```
    $ docker info
    ```


2. Clone or download the [HNN repo](https://github.com/jonescompneurolab/hnn). **Chose one of the following methods:**

   * Option 1: Cloning (requires Xcode Command Line Tools)

     1. Check that you have Git installed from a terminal window
        ```
        $ git version
        git version 2.17.2 (Apple Git-113)
        ```
     2. Type the following to clone the repo. If you already have a previous version of the repository, bring it up to date with the command `git pull origin master` instead of the `git clone` command below.

        ```
        $ git clone https://github.com/jonescompneurolab/hnn.git
        $ cd hnn/installer/mac
        ```
   
   * Option 2: Downloading a HNN release

     1. Download the source code (zip) for our latest HNN release from our [GitHub releases page](https://github.com/jonescompneurolab/hnn/releases)
     2. Open the .zip file and click "Extract all". Choose any destination folder on your machine.
     3. Open a cmd.exe window and change to the directory part of the extracted HNN release shown below:

        ```bash
        $ cd REPLACE-WITH-FOLDER-EXTRACTED-TO/hnn/installer/mac
        ```

3. Start the Docker container. Note: the jonescompneurolab/hnn Docker image will be downloaded from Docker Hub (about 2 GB). The `docker-compose` command can be used to manage Docker containers described in the specification file docker-compose.yml.

    ```bash
    $ docker-compose run hnn
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
    * If starting the GUI doesn't work, the first thing to check is XQuartz settings (see screnshot above). Then restart XQuartz and try starting the HNN container again.
5. You can now proceed to running the tutorials at https://hnn.brown.edu/index.php/tutorials/ . Some things to note:
   * A directory called "hnn_out" exists both inside the container (at /home/hnn_user/hnn_out) and outside (in the directory set by step 2) that can be used to share files between the container and your host OS.
   * The HNN repository with sample data and parameter files exists at /home/hnn_user/hnn_source_code.
   * If you run into problems starting the Docker container or the GUI is not displaying, please see the [Docker troubleshooting section](../docker/README.md#Troubleshooting)

## Updgrading to a new version of HNN

1. Verify that XQuartz and Docker are running. XQuartz will not start automatically after a reboot by default. To confirm that Docker is running properly, typing `docker info` should return a bunch of output, but no errors.

    ```bash
    $ docker info
    ```

2. Open a terminal window

    ```bash
    $ cd hnn/installer/mac
    $ docker-compose up --no-start
    Recreating mac_hnn_1 ... done
    $ docker-compose run hnn
    ```

## Editing files within HNN container

You may want run commands or edit files within the container. To access a command shell in the container, start the container using `docker-compose run hnn` in one terminal window and open another terminal to use [`docker exec`](https://docs.docker.com/engine/reference/commandline/exec/) as shown below:

```bash
$ docker exec -ti mac_hnn_1 bash
hnn_user@054ba0c64625:/home/hnn_user$
```

If you'd like to be able to copy files from the host OS without using the shared directory, you do so directly with [`docker cp`](https://docs.docker.com/engine/reference/commandline/cp/).

## Uninstalling HNN

If you want to remove the container and 1.5 GB HNN image, run the following commands from a terminal window. You can then remove Docker Desktop by removing it from your Applications folder.

```bash
$ docker rm -f mac_hnn_1
$ docker rmi jonescompneurolab/hnn
```

# Troubleshooting

For Mac OS specific issues: please see the [Mac OS troubleshooting page](troubleshooting.md)

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.

For other HNN software issues, please visit the [HNN bulletin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)
