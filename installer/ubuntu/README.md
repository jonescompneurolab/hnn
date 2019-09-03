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

1. Check that Docker is running properly by typing the following in a new terminal window.
    ```bash
    $ docker info
    ```

2. Clone or download the [HNN repo](https://github.com/jonescompneurolab/hnn). If you already have a previous version of the repository, bring it up to date with the command `git pull origin master` instead of the `git clone` command below.

    ```bash
    $ git clone https://github.com/jonescompneurolab/hnn.git
    $ cd hnn/installer/docker
    ```

3. Create the shared directory for HNN output between your host system and the Docker container

    ```bash
    $ mkdir docker_hnn_out
    ```

4. Start the Docker container. Note: the jonescompneurolab/hnn Docker image will be downloaded from Docker Hub (about 2 GB). The docker-compose command can be used to manage Docker containers described in the specification file docker-compose.yml.

    ```bash
    $ docker-compose up
    Pulling hnn (jonescompneurolab/hnn:)...
    latest: Pulling from jonescompneurolab/hnn
    34dce65423d3: Pull complete
    796769e96d24: Pull complete
    2a0eada9611d: Pull complete
    d6830a7cd972: Pull complete
    ddf2bf28e180: Pull complete
    3cc50322f9e6: Pull complete
    413f53de8db6: Pull complete
    17dc3d1b2db0: Pull complete
    630b5e60ea64: Pull complete
    78e9a198ddb9: Pull complete
    45d8623e986c: Pull complete
    e32873c7bf4d: Pull complete
    Creating hnn_container ... done
    Attaching to hnn_container
    ```

5. The HNN GUI should show up. Make sure that you can run simulations by clicking the 'Run Simulation' button. This will run a simulation with the default configuration. After it completes, graphs should be displayed in the main window.
6. You can now proceed to running the tutorials at [https://hnn.brown.edu/index.php/tutorials/](https://hnn.brown.edu/index.php/tutorials/) . Some things to note:
   - A directory called "hnn_out" exists both inside the container (at /home/hnn_user/hnn_out) and outside (in the directory set by step 2) that can be used to share files between the container and your host OS.
   - The HNN repository with sample data and parameter files exists at /home/hnn_user/hnn_source_code.
   - If you run into problems starting the Docker container or the GUI is not displaying, please see the [Docker troubleshooting section](../docker/README.md#Troubleshooting)

## Updgrading to a new version of HNN

You can download the latest version of the hnn container with `docker-compose pull`:

```bash
$ cd hnn/installer/mac
$ docker-compose pull
Pulling hnn ... done
$ docker-compose up
Recreating hnn_container ... done
Attaching to hnn_container
```

## Editing files within HNN container

You may want run commands or edit files within the container. To access a command shell in the container, start the container using `docker-compose up -d` to start hnn in the background and use [`docker exec`](https://docs.docker.com/engine/reference/commandline/exec/) as shown below:

```bash
$ docker exec -ti hnn_container bash
hnn_user@hnn-container:/home/hnn_user/hnn_source_code$
```

If you'd like to be able to copy files from the host OS without using the shared directory, you do so directly with [`docker cp`](https://docs.docker.com/engine/reference/commandline/cp/).

## Uninstalling HNN

1. If you want to just remove the container and 2 GB HNN image, run these commands from a terminal window:

    ```bash
    $ docker rm -f hnn_container
    $ docker rmi jonescompneurolab/hnn
    ```

2. To continue and remove Docker, follow these instructions from [Uninstall Docker CE](https://docs.docker.com/install/linux/docker-ce/ubuntu/#uninstall-docker-ce)

    ```bash
    sudo apt-get purge docker-ce
    sudo rm -rf /var/lib/docker
    ```

# Troubleshooting

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.

For other HNN software issues, please visit the [HNN bulletin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)