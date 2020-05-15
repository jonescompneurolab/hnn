# Installing HNN on Mac OS (Docker Desktop)

## Prerequisite: XQuartz

1. Download the installer image (version 2.7.11 tested): https://www.xquartz.org/
2. Run the XQuartz.pkg installer within the image, granting privileges when requested.

## Prerequisite: Docker Desktop

1. In order to download Docker Desktop, you'll need to sign up for a Docker Hub account. It only requires an email address to confirm the account. Sign up here: [Docker Hub Sign-up](https://hub.docker.com/signup)
2. Download the installer image (requires logging in to your Docker Hub account): [Docker Desktop](https://hub.docker.com/editions/community/docker-ce-desktop-mac)
3. Run the Docker Desktop installer, moving docker to the applications folder.
4. Start the Docker application, acknowledging that it was downloaded from the Internet and you still want to open it.
5. Log into your Docker Hub account if prompted by the Docker Desktop application.
6. The Docker Desktop icon will appear in the taskbar with the message "Docker Desktop is starting", Followed by "Docker Desktop is now up and running!".
7. Increase the number of cores that Docker can use (we recommend all cores) by clicking on the Docker Desktop icon in the taskbar and then clicking "Preferences". Choose the "Advanced" tab, and adjust with the slider. Then restart Docker Desktop to apply the setting.

   <img src="install_pngs/docker_cores.png" height="300" />

## Start HNN

1. Clone or download the [HNN repo](https://github.com/jonescompneurolab/hnn). **Choose one of the following methods:**

   * Option 1: Cloning (requires <a href="native_install#prerequisite-2-xcode-command-line-tools">Xcode Command Line Tools</a>)

     1. Check that you have Git installed from a terminal window

        ```bash
        $ git version
        git version 2.21.0 (Apple Git-122)
        ```

     2. Type the following to clone the repo. If you already have a previous version of the repository, bring it up to date with the command `git pull origin master` instead of the `git clone` command below.

        ```bash
        $ git clone https://github.com/jonescompneurolab/hnn.git
        $ cd hnn
        ```

   * Option 2: Downloading a HNN release

     1. Download the source code (zip) for our latest HNN release from our [GitHub releases page](https://github.com/jonescompneurolab/hnn/releases)
     2. Open the .zip file and click "Extract all". Choose any destination folder on your machine.
     3. Open a cmd.exe window and change to the directory part of the extracted HNN release shown below:

        ```bash
        $ cd REPLACE-WITH-FOLDER-EXTRACTED-TO/hnn
        ```

2. Start the Docker container using the `hnn-docker.sh` script. For the first time, we will pass the `-u` option in case there were any previous versions of the docker image on your computer. You can omit the `-u` option later

    ```bash
    ./scripts/hnn-docker.sh -u start
    ```

3. The HNN GUI should show up. Make sure that you can run simulations by clicking the 'Run Simulation' button. This will run a simulation with the default configuration. After it completes, graphs should be displayed in the main window.
    * If the GUI doesn't show up, check the [Docker troubleshooting section](../docker/troubleshooting.md) (also links the bottom of this page)
4. You can now proceed to running the tutorials at [https://hnn.brown.edu/index.php/tutorials/](https://hnn.brown.edu/index.php/tutorials/) . Some things to note:
    * A subdirectory called "hnn_out" is created in your home directory and is where simulation results and parameter files will be saved.
5. To quit HNN and shut down container, first press 'Quit' within the GUI. Then run `./scripts/hnn-docker.sh stop`.

    ```bash
    $ ./scripts/hnn-docker.sh stop
    Stopping HNN container requested

    Performing pre-checks before starting HNN
    --------------------------------------
    Checking if Docker is working... ok
    hnn_container
    Successfully stopped HNN container
    ```

## Upgrading to a new version of HNN

To just pull the latest docker image from Docker Hub:

```bash
./scripts/hnn-docker.sh upgrade
```

Instead to upgrade and start the newest GUI:

```bash
./scripts/hnn-docker.sh -u start
```

## Editing files within HNN container

You may want run commands or edit files within the container. To access a command shell in the container, start the container using `./scripts/hnn-docker.sh  start` in one terminal window to start hnn in the background and then run [`docker exec`](https://docs.docker.com/engine/reference/commandline/exec/) in another terminal window:

```none
$ docker exec -ti hnn_container bash
hnn_user@hnn-container:/home/hnn_user/hnn_source_code$
```

If you'd like to be able to copy files from the host OS without using the shared directory, you can do so directly with [`docker cp`](https://docs.docker.com/engine/reference/commandline/cp/).

## Uninstalling HNN

If you want to remove the container and 1.6 GB HNN image, run the following commands from a terminal window.

```bash
./scripts/hnn-docker.sh uninstall
```

You can then remove Docker Desktop by removing it from your Applications folder.

## Troubleshooting

For errors related to Docker, please see the [Docker troubleshooting section](../docker/troubleshooting.md)

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.

For other HNN software issues, please visit the [HNN bulletin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)
