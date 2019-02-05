# Installing HNN on CentOS

This guide describes two methods for installing HNN and its prerequisistes CentOS (tested on CentOS 7):

1. A Docker container running a Linux install of HNN (recommended, CentOS 7 only) 
2. Natively running HNN on CentOS 6 or 7 (advanced users)

The Docker installation (Method 1) is recommended because the python environment and the NEURON installation are fully isolated, reducing the possibility of version incompatibilities. The same Docker container is used for all platforms (Windows/Linux/Mac) meaning it has likely been tested more recently.

Method 2 runs HNN directly on the OS and uses a script to download and install prerequisites. It is more difficult to control the native environment than in Method 1 (with Docker), so it's possible that the script will need user intervention. Thus, Method 2 is best suited for advanced users.


## Install Docker
* Follow [Docker's CentOS install instructions](https://docs.docker.com/install/linux/docker-ce/centos/) to install the docker-ce RPM packages from Docker's official repository
* Add your user to the docker group to avoid having to run docker commands with "sudo"
    ```
    sudo usermod -a -G docker [username]
    ```
* Log out and back in for the group change to take effect

## Install Docker Compose
* From https://docs.docker.com/compose/install/:
    ```
    sudo curl -L "https://github.com/docker/compose/releases/download/1.23.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    docker-compose --version
    ```

### Start the HNN Docker container
1. Clone or download the [HNN repo](https://github.com/jonescompneurolab/hnn):
    ```
    git clone https://github.com/jonescompneurolab/hnn.git
    cd hnn/installer/docker
    ```
2. Start the Docker container. Note: the jonescompneurolab/hnn docker image will be downloaded from Docker Hub (about 1.5 GB)
    ```
    docker-compose up -d
    ```    
3. The HNN GUI should show up and you should now be able to run the tutorials at: https://hnn.brown.edu/index.php/tutorials/
   * If you run into problems starting the Docker container or the GUI is not displaying, please see the [Docker troubleshooting section](../docker/README.md#Troubleshooting)
   * If you closed the HNN GUI, and would like to restart it, run the following:
      ```
      docker-compose restart
      ```
4. **NOTE:** You may want to edit files within the container. To access a command prompt in the container, use `docker exec`:
    ```
    docker exec -ti docker_hnn_1 bash
    ```
    If you'd like to be able to access files from the host system within the container, you can either copy files with [docker cp](https://docs.docker.com/engine/reference/commandline/cp/) or start the container with host directory that is visible as a "volume" within the container (instead of step 4):
    ```
    mkdir $HOME/dir_on_host
    docker-compose run -d -v $HOME/dir_on_host:/home/hnn_user/dir_from_host hnn
    ```
    * Note the different container name after running docker-compose

## Native install scripts

See the scripts in this directory:
* CentOS 6: [centos6-installer.sh](centos6-installer.sh)
* CentOS 7: [centos7-installer.sh](centos7-installer.sh)

```
chmod +x ./centos7-installer.sh
./centos7-installer.sh
```
