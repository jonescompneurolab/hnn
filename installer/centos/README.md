# Installing HNN on CentOS (Docker install)

This guide describes installing HNN on CentOS using Docker. This method will automatically download the HNN Docker container image when HNN is started for the first time. If you would prefer to install HNN without Docker, please see the instructions below.

- Alternative: [Native install instructions (advanced users)](native_install.md)

## Verify that your OS supports Docker CE

    - CentOS 7 and later versions are supported
    - See [OS requirements](https://docs.docker.com/install/linux/docker-ce/centos/#os-requirements)
    - It may be possible to install older versions of docker meant for earlier CentOS versions. We recommend following the currently supported procedure from Docker, but you may find a version of Docker in the [EPEL repositories](https://fedoraproject.org/wiki/EPEL) for CentOS 6, which would would work for your OS.

## Prerequisite: install Docker

1. To install docker, type the following commands in a terminal (x86_64 only). They are from [Docker's CentOS install instructions](https://docs.docker.com/install/linux/docker-ce/centos/) for installing docker-ce from Docker's official repository.

    ```bash
    # get prerequisites for docker
    sudo yum install -y yum-utils device-mapper-persistent-data lvm2
    # add the repository
    sudo yum-config-manager --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo
    # install docker-ce
    sudo yum install -y docker-ce docker-ce-cli containerd.io
    # start docker
    sudo systemctl start docker
    # verify that docker runs
    sudo docker run hello-world
    ```

2. Add your user to the docker group to avoid having to run docker commands with "sudo"

    ```bash
    $ sudo usermod -a -G docker [username]
    ```

3. Log out and back in (may need to reboot) for the group change to take effect

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
    $ docker-compose run hnn
    Creating network "docker_default" with the default driver
    Pulling hnn (jonescompneurolab/hnn:)...
    latest: Pulling from jonescompneurolab/hnn
    34dce65423d3: Pull complete
    796769e96d24: Pull complete
    2a0eada9611d: Pull complete
    d6830a7cd972: Pull complete
    ddf2bf28e180: Pull complete
    1b92ede96ea9: Pull complete
    d40cff005cd9: Pull complete
    8c2b6fabd4cd: Pull complete
    739b6844c557: Pull complete
    93e57038c24c: Pull complete
    8a0c9da0fc98: Pull complete
    87b245fb518f: Pull complete
    Digest: sha256:c561d0880aa8c69995dfc84e2c456b7dea688f829bfbadedfed94425c1f2044c
    Status: Downloaded newer image for jonescompneurolab/hnn:latest
    ```

5. The HNN GUI should show up. Make sure that you can run simulations by clicking the 'Run Simulation' button. This will run a simulation with the default configuration. After it completes, graphs should be displayed in the main window.
6. You can now proceed to running the tutorials at https://hnn.brown.edu/index.php/tutorials/ . Some things to note:
   - A directory called "hnn_out" exists both inside the container (at /home/hnn_user/hnn_out) and outside (in the directory set by step 2) that can be used to share files between the container and your host OS.
   - The HNN repository with sample data and parameter files exists at /home/hnn_user/hnn_source_code.
   - If you run into problems starting the Docker container or the GUI is not displaying, please see the [Docker troubleshooting section](../docker/README.md#Troubleshooting)

## Updgrading to a new version of HNN

1. Verify Docker is still running. To confirm that Docker is running properly, typing `docker info` should return a bunch of output, but no errors.

    ```bash
    $ docker info
    ```

2. Open a terminal window

    ```bash
    $ cd hnn/installer/docker
    $ docker-compose up --no-start
    Recreating docker_hnn_1 ... done
    $ docker-compose run hnn
    ```

## Editing files within HNN container

You may want run commands or edit files within the container. To access a command shell in the container, start the container using `docker-compose run hnn` in one terminal window and open another terminal to use [`docker exec`](https://docs.docker.com/engine/reference/commandline/exec/) as shown below:

    ```bash
    $ docker exec -ti docker_hnn_1 bash
    hnn_user@054ba0c64625:/home/hnn_user$
    ```

    If you'd like to be able to copy files from the host OS without using the shared directory, you do so directly with [`docker cp`](https://docs.docker.com/engine/reference/commandline/cp/).

## Uninstalling HNN

1. If you want to just remove the container and 2 GB HNN image, run these commands from a terminal window:

    ```bash
    $ docker rm -f docker_hnn_1
    $ docker rmi jonescompneurolab/hnn
    ```

2. To continue and remove Docker, follow these instructions from [Uninstall Docker CE](https://docs.docker.com/install/linux/docker-ce/centos/#uninstall-docker-ce)

    ```bash
    $ sudo yum remove docker-ce
    $ sudo rm -rf /var/lib/docker
    ```

# Troubleshooting

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.

For other HNN software issues, please visit the [HNN bulletin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)
