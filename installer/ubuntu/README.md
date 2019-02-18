# Installing HNN on Ubuntu

This guide describes two methods for installing HNN and its prerequisistes Ubuntu (tested on Ubuntu 18.04 LTS):

Method 1: A Docker container running a Linux install of HNN (recommended)
   - The Docker installation fully isolates HNN's python environment and the NEURON installation from the rest of your system, reducing the possibility of version incompatibilities. Additionally, the same Docker container is used for all platforms (Windows/Linux/Mac) meaning it has likely been tested more recently.
   - See [OS requirements](https://docs.docker.com/install/linux/docker-ce/ubuntu/#os-requirements)

Method 2: Natively running HNN on Ubuntu (advanced users)
   - HNN runs directly on the OS and uses a script to download and install prerequisites. It is more difficult to control the native environment than in Method 1 (with Docker), so it's possible that the script will need user intervention. Thus, Method 2 is best suited for advanced users.

## Method 1: Docker install

### Prerequisite: install Docker
* Follow [Docker's Ubuntu install instructions](https://docs.docker.com/install/linux/docker-ce/ubuntu/) to install the docker-ce packages from Docker's official repository
* Add your user to the docker group to avoid having to run docker commands with "sudo"
    ```
    sudo usermod -a -G docker [username]
    ```
* Log out and back in (may need to reboot) for the group change to take effect

### Prerequisite: install Docker Compose
* From https://docs.docker.com/compose/install/:
    ```
    sudo curl -L "https://github.com/docker/compose/releases/download/1.23.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    docker-compose --version
    ```

### Start HNN
1. Check that Docker is running properly by typing the following in a new terminal window.
    ```
    docker info
    ```
2. Clone or download the [HNN repo](https://github.com/jonescompneurolab/hnn). If you already have a previous version of the repository, bring it up to date with the command `git pull origin master` instead of the `git clone` command below.
    ```
    git clone https://github.com/jonescompneurolab/hnn.git
    cd hnn/installer/docker
    ```
3. Start the Docker container. Note: the jonescompneurolab/hnn docker image will be downloaded from Docker Hub (about 1.5 GB). Docker-compose starts a docker container based on the specification file docker-compose.yml and "up" starts the containers in that file and "-d" starts the docker containers in the background.
    ```
    docker-compose up -d
    ```    
4. The HNN GUI should show up and you should now be able to run the tutorials at: https://hnn.brown.edu/index.php/tutorials/
   * A directory called "hnn" exists both inside the container (at /home/hnn_user/hnn) and outside (in the directory where step 3 was run) that can be used to share files between the container and your host OS.
   * If you run into problems starting the Docker container or the GUI is not displaying, please see the [Docker troubleshooting section](../docker/README.md#Troubleshooting)
   * If you closed the HNN GUI, and would like to restart it, run the following:
      ```
      docker-compose restart
      ```
5. **NOTE:** You may want run commands or edit files within the container. To access a command prompt in the container, use [`docker exec`](https://docs.docker.com/engine/reference/commandline/exec/):
    ```
    C:\Users\myuser>docker exec -ti docker_hnn_1 bash
    hnn_user@054ba0c64625:/home/hnn_user$
    ```

    If you'd like to be able to copy files from the host OS without using the shared directory, you do so directly with [`docker cp`](https://docs.docker.com/engine/reference/commandline/cp/).

## Method 2: native install
See the scripts in this directory:
* [installer.sh](installer.sh)
  ```
  chmod +x ./installer.sh
  ./installer.sh
  ```
* [uninstaller.sh](uninstaller.sh)
  ```
  chmod +x ./uninstaller.sh
  ./uninstaller.sh
  ```
* [updater.sh](updater.sh)
  ```
  chmod +x ./updater.sh
  ./updater.sh
  ```