# DEPRECATED: Installing HNN on Mac OS (Docker Toolbox)

- Supported alternative: [Python install instructions](README.md)

## Prerequisite: XQuartz

1. Download the installer image (version 2.7.11 tested): https://www.xquartz.org/
2. Run the XQuartz.pkg installer within the image, granting privileges when requested.

## Prerequisite: Docker Toolbox

1. Download the latest installer image (.pkg): [https://github.com/docker/toolbox/releases/](https://github.com/docker/toolbox/releases/)
2. Run the installer, selecting any directory for installation.
3. Choose "Docker Quickstart Terminal" tool
4. You may need to allow "Docker Quickstart Terminal" to use accessibility features. Do this in

    ```none
    System Preferences -> Security -> Privacy -> Privacy -> Accessibility.
    ```

    If it's already checked, uncheck it and check it again.
5. Click on "Docker Quickstart Terminal" again. The output will be similar to below:

    ```none
    Creating CA: /Users/user/.docker/machine/certs/ca.pem
    Creating client certificate: /Users/user/.docker/machine/certs/cert.pem
    Running pre-create checks...
    (default) Default Boot2Docker ISO is out-of-date, downloading the latest release...
    (default) Latest release for github.com/boot2docker/boot2docker is v19.03.4
    (default) Downloading /Users/user/.docker/machine/cache/boot2docker.iso from https://github.com/boot2docker/boot2docker/releases/download/v19.03.4/boot2docker.iso...
    (default) 0%....10%....20%....30%....40%....50%....60%....70%....80%....90%....100%
    Creating machine...
    (default) Copying /Users/user/.docker/machine/cache/boot2docker.iso to /Users/user/.docker/machine/machines/default/boot2docker.iso...
    (default) Creating VirtualBox VM...
    (default) Creating SSH key...
    (default) Starting the VM...
    (default) Check network to re-create if needed...
    (default) Found a new host-only adapter: "vboxnet0"
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
    To see how to connect your Docker Client to the Docker Engine running on this virtual machine, run: /usr/local/bin/docker-machine env default



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


    The default interactive shell is now zsh.
    To update your account to use zsh, please run `chsh -s /bin/zsh`.
    For more details, please visit https://support.apple.com/kb/HT208050.
    ```

6. We want HNN to use all of the CPU cores available on your system when it runs a simulation, and Docker only uses half by default. To change this setting we need to first stop the Docker VM that was started above in step 5. Run the command below in a "Docker Quickstart Terminal" window.

    ```bash
    docker-machine stop
    ```

7. Type 'VirtualBox' into the start menu search bar and launch "Oracle VM VirtualBox"
8. Click on the VM "default" in the left pane and then click "Settings"
9. Navigate to "System", then the "Processor" tab and move the slider all the way to the right.
10. Click 'Ok', then reopen "Docker Quickstart Terminal". When you get the prompt after "Start interactive shell", you can continue on. Run the commands below in the same terminal window or by relaunching "Docker Quickstart Terminal".

If you run into problems, check the official Docker Toolbox documentation: [Docker Toolbox for Mac](https://docs.docker.com/toolbox/toolbox_install_mac/)

## Start HNN

1. From a "Docker Quickstart Terminal", clone the [HNN repo](https://github.com/jonescompneurolab/hnn). If you already have a previous version of the repository, bring it up to date with the command `git pull origin master` instead of the `git clone` command below.

    ```bash
    cd ~
    git clone https://github.com/jonescompneurolab/hnn.git
    cd hnn
    ```

2. Start the Docker container using the `hnn_docker.sh` script. For the first time, we will pass the `-u` option in case there were any previous versions of the docker image on your computer. You can omit the `-u` option later

    ```bash
    ./hnn_docker.sh -u start
    ```

3. The HNN GUI should show up. Make sure that you can run simulations by clicking the 'Run Simulation' button. This will run a simulation with the default configuration. After it completes, graphs should be displayed in the main window.
    - If the GUI doesn't show up, check the [Docker troubleshooting section](../docker/troubleshooting.md) (also links the bottom of this page)

4. You can now proceed to running the tutorials at [https://hnn.brown.edu/index.php/tutorials/](https://hnn.brown.edu/index.php/tutorials/) . Some things to note:
    - A subdirectory called "hnn_out" is created in your home directory and is where simulation results and parameter files will be saved.

5. To quit HNN and shut down container, first press 'Quit' within the GUI. Then run `./hnn_docker.sh stop`.

    ```bash
    ./hnn_docker.sh stop
    ```

## Stopping Docker Toolbox VM

The Docker Toolbox VM will remain running the background using some resources. If you are not using HNN, you can shut down the VM by the following command:

```bash
docker-machine stop
```

## Upgrading to a new version of HNN

To just pull the latest docker image from Docker Hub:

```bash
./hnn_docker.sh upgrade
```

Instead to upgrade and start the newest GUI:

```bash
./hnn_docker.sh -u start
```

## Editing files within HNN container

You may want run commands or edit files within the container. To access a command shell in the container, start the container using `./hnn_docker.sh  start` in one terminal window to start hnn in the background and then run [`docker exec`](https://docs.docker.com/engine/reference/commandline/exec/) in another terminal window:

```none
$ docker exec -ti hnn_container bash
hnn_user@hnn-container:/home/hnn_user/hnn_source_code$
```

If you'd like to be able to copy files from the host OS without using the shared directory, you can do so directly with [`docker cp`](https://docs.docker.com/engine/reference/commandline/cp/).

## Uninstalling HNN

1. If you want to remove the container and 1.6 GB HNN image, run the following commands from a terminal window.

    ```bash
    ./hnn_docker.sh uninstall
    ```

2. You can then remove Docker Toolbox from Applications.

3. You can remove Virtualbox as well if you no longer need it to run virtual machines

## Troubleshooting

For errors related to Docker, please see the [Docker troubleshooting section](../docker/troubleshooting.md)

For Mac OS specific issues: please see the [Mac OS troubleshooting page](troubleshooting.md)

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.

For other HNN software issues, please visit the [HNN bulletin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)
