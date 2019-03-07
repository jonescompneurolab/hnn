# Installing HNN on Ubuntu (Docker install)

This guide describes installing HNN on Ubuntu using Docker. This method will automatically download the HNN Docker container image when HNN is started for the first time. If you would prefer to install HNN without Docker, please see the instructions below.
  - Alternative: [Native install instructions (advanced users)](native_install.md)

**Note: please verify that your OS supports Docker CE**
   - Ubuntu 16.04 and later versions are supported
   - See [OS requirements](https://docs.docker.com/install/linux/docker-ce/ubuntu/#os-requirements)
   - It may be possible to install older versions of docker meant for earlier Ubuntu OSs. We recommend following the currently supported procedure from Docker, but Ubuntu provides docker in its own repositories, which would be specific for your OS. If a Docker CE package is not available, search for docker.io and docker packages in that order.


## Prerequisite: install Docker
1. To install docker, type the following commands in a terminal (x86_64 only). They are from [Docker's Ubuntu install instructions](https://docs.docker.com/install/linux/docker-ce/ubuntu/) for installing docker-ce from Docker's official repository.
    ```
    # get prerequisites for adding the docker repository and verifying with the GPG key
    sudo apt-get update
    sudo apt-get -y install apt-transport-https ca-certificates curl gnupg-agent software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo apt-key fingerprint 0EBFCD88
    # add the docker repository to apt sources list
    bash -c 'sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"'
    sudo apt-get update
    # install docker packages
    sudo apt-get -y install docker-ce docker-ce-cli containerd.io
    # verify that docker runs
    sudo docker run hello-world
    ```
2. Add your user to the docker group to avoid having to run docker commands with "sudo"
    ```
    sudo usermod -a -G docker [username]
    ```
3. Log out and back in (may need to reboot) for the group change to take effect

## Prerequisite: install Docker Compose
Open a bash terminal and run these commands (from [Docker Compose installation](https://docs.docker.com/compose/install/)):
  ```
  bash -c 'sudo curl -L "https://github.com/docker/compose/releases/download/1.23.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose'
  sudo chmod +x /usr/local/bin/docker-compose
  docker-compose --version
  ```

## Start HNN
1. Check that Docker is running properly by typing the following in a new terminal window.
    ```
    docker info
    ```
2. Clone or download the [HNN repo](https://github.com/jonescompneurolab/hnn). If you already have a previous version of the repository, bring it up to date with the command `git pull origin master` instead of the `git clone` command below.
    ```
    git clone https://github.com/jonescompneurolab/hnn.git
    cd hnn/installer/docker
    ```
3. Start the Docker container. Note: the jonescompneurolab/hnn Docker image will be downloaded from Docker Hub (about 1.5 GB). The docker-compose command can be used to manage Docker containers described in the specification file docker-compose.yml. The parameter "up" starts the containers (just one in our case) in that file and "-d" starts the docker container in the background.
    ```
    docker-compose up -d
    ```    
4. The HNN GUI should show up and you should now be able to run the tutorials at https://hnn.brown.edu/index.php/tutorials/ . Some things to note:
   * A directory called "hnn" exists both inside the container (at /home/hnn_user/hnn) and outside (in the directory set by step 2) that can be used to share files between the container and your host OS.
   * If you run into problems starting the Docker container or the GUI is not displaying, please see the [Docker troubleshooting section](../docker/README.md#Troubleshooting)
   * If you closed the HNN GUI or it is no longer running, and you would like to restart it, run the following command from the same directory set in step 2:
      ```
      docker-compose restart
      ```
5. **NOTE:** You may want run commands or edit files within the container. To access a command prompt in the container, use [`docker exec`](https://docs.docker.com/engine/reference/commandline/exec/) as shown below:
    ```
    C:\Users\myuser>docker exec -ti docker_hnn_1 bash
    hnn_user@054ba0c64625:/home/hnn_user$
    ```

    If you'd like to be able to copy files from the host OS without using the shared directory, you do so directly with [`docker cp`](https://docs.docker.com/engine/reference/commandline/cp/).

## Uninstalling HNN

1. If you want to just remove the container and 1.5 GB HNN image, run these commands from a terminal window:
    ```
    docker rm -f docker_hnn_1
    docker rmi jonescompneurolab/hnn
    ```
2. To continue and remove Docker, follow these instructions from [Uninstall Docker CE](https://docs.docker.com/install/linux/docker-ce/ubuntu/#uninstall-docker-ce)
    ```
    sudo apt-get purge docker-ce
    sudo rm -rf /var/lib/docker
    ```

# Troubleshooting

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.

For other HNN software issues, please visit the [HNN bullentin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)