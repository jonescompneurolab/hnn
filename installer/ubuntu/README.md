# Installing HNN on Ubuntu (Docker install)

This guide describes installing HNN on Ubuntu using Docker. This method will automatically download the HNN Docker container image when HNN is started for the first time. If you would prefer to install HNN without Docker, please see the instructions below.

- Alternative: [Native install instructions (advanced users)](native_install.md)

## Verify that your OS supports Docker CE

- Ubuntu 16.04 and later versions are supported
- See [OS requirements](https://docs.docker.com/install/linux/docker-ce/ubuntu/#os-requirements)
- It may be possible to install older versions of docker meant for earlier Ubuntu OSs. We recommend following the currently supported procedure from Docker, but Ubuntu provides docker in its own repositories, which would be specific for your OS. If a Docker CE package is not available, search for docker.io and docker packages in that order.

## Prerequisite: install Docker

1. To install docker, type the following commands in a terminal (x86_64 only). They are from [Docker's Ubuntu install instructions](https://docs.docker.com/install/linux/docker-ce/ubuntu/) for installing docker-ce from Docker's official repository.

    ```bash
    # get prerequisites for adding the docker repository and verifying with the GPG key
    sudo apt-get update
    sudo apt-get -y install apt-transport-https ca-certificates curl gnupg-agent software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo apt-key fingerprint 7EA0A9C3F273FCD8
    # add the docker repository to apt sources list
    bash -c 'sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"'
    sudo apt-get update
    # install docker packages
    sudo apt-get -y install docker-ce docker-ce-cli containerd.io
    # verify that docker runs
    sudo docker run hello-world
    ```

2. Add your user to the docker group to avoid having to run docker commands with "sudo"

    ```bash
    sudo usermod -a -G docker [username]
    ```

3. You will need to reboot for the group change to take effect

## Prerequisite: install Docker Compose

Open a bash terminal and run these commands (from [Docker Compose installation](https://docs.docker.com/compose/install/)):

  ```bash
  $ bash -c 'sudo curl -L "https://github.com/docker/compose/releases/download/1.23.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose'
  $ sudo chmod +x /usr/local/bin/docker-compose
  $ docker-compose --version
  ```

## Start HNN

1. Clone the [HNN repo](https://github.com/jonescompneurolab/hnn) using `git` from a terminal window. If you already have a previous version of the repository, bring it up to date with the command `git pull origin master` instead of the `git clone` command below.

    ```bash
    git clone https://github.com/jonescompneurolab/hnn.git
    cd hnn
    ```

2. Start the Docker container using the `hnn_docker.sh` script. For the first time, we will pass the `-u` option in case there were any previous versions of the docker image on your computer. You can omit the `-u` option later

    ```bash
    ./hnn_docker.sh -u start
    ```

3. The HNN GUI should show up. Make sure that you can run simulations by clicking the 'Run Simulation' button. This will run a simulation with the default configuration. After it completes, graphs should be displayed in the main window.
    * If the GUI doesn't show up, check the [Docker troubleshooting section](../docker/troubleshooting.md) (also links the bottom of this page). It may be necessary to run the `xhost +local:docker` command to open up permissions to display the GUI on your local machine.
4. You can now proceed to running the tutorials at [https://hnn.brown.edu/index.php/tutorials/](https://hnn.brown.edu/index.php/tutorials/) . Some things to note:
   * A directory called "hnn_out" exists both inside the container (at /home/hnn_user/hnn_out) and outside (in the directory set by step 2) that can be used to share files between the container and your host OS.
   * The HNN repository with sample data and parameter files exists at /home/hnn_user/hnn_source_code
5. To quit HNN and shut down container, first press 'Quit' within the GUI. Then run `./hnn_docker.sh stop`.

    ```bash
    ./hnn_docker.sh stop
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

If you want to remove the container and 1.6 GB HNN image, run the following commands from a terminal window.

```bash
./hnn_docker.sh uninstall
```

You can then remove Docker CE

```bash
sudo apt-get purge docker-ce
```

To remove all containers and images (should take minimal space after the uninstall command above):

```bash
sudo rm -rf /var/lib/docker
```

## Troubleshooting

For errors related to Docker, please see the [Docker troubleshooting section](../docker/troubleshooting.md)

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.

For other HNN software issues, please visit the [HNN bulletin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)