# Installing HNN on Mac OS

There are two methods for installing HNN and its prerequisistes on Mac OS (tested on High Sierra):

1. A Docker container running a Linux install of HNN (recommended)
2. Natively running HNN on Mac OS (better performance)

The Docker installation is recommended because the python environment and the NEURON installation are fully isolated, reducing the possibility of version conflicts, or the wrong version being used. The same Docker container is used for all platforms (Windows/Linux/Mac) meaning it has likely been tested more recently.

Both methods display the GUI through an X server. Differences in performance may be due to overhead from running and container (especially using Docker Toolbox in Which Docker Runs in a Virtual Machine)

## Docker Install

[Docker Desktop](https://www.docker.com/products/docker-desktop) requires Mac OS Sierra 10.12 or above. For earlier versions of Mac OS, use the legacy version of [Docker Toolbox](https://docs.docker.com/toolbox/overview/).

The only other component to install is an X server. [XQuartz](https://www.xquartz.org/) is a recommended free option.

### Install XQuartz
1. Download the installer image (version 2.7.11 tested): https://www.xquartz.org/
2. Run the XQuartz.pkg installer within the image, granting privileges when requested.
3. Start the XQuartz application. An "X" icon will appear in the taskbar along with a terminal, signaling that XQuartz is waiting for connections. You can minimize the terminal, but do not close it.

### Install Docker Desktop (Mac OS Sierra 10.12 or above)
1. Download the installer image (requires a free Docker Hub account):
https://hub.docker.com/editions/community/docker-ce-desktop-mac
2. Run the Docker Desktop installer, moving docker to the applications folder.
3. Start the Docker application, acknowledging that it was downloaded from the Internet and you still want to open it.
4. The Docker Desktop icon will appear in the taskbar with the message "Docker Desktop is starting", Followed by "Docker Desktop is running".

### Install Docker Toolbox (pre-10.12)
1. Download the installer image:
https://docs.docker.com/toolbox/toolbox_install_mac/
2. Run the installer, selecting any directory for installation.
3. Choose "Docker Quickstart Terminal" tool
4. Verify that Docker has started by running the following in the provided terminal window. 
    ```
    docker info
    docker-compose --version
    ```
5. Run the following commands in the same terminal window or by relaunching "Docker Quickstart Terminal".

### Start the HNN Docker container
1. Get the IP address of a local interface on the host(e.g. using ifconfig)
    * For Docker Toolbox you can use interface that will be named similar to vboxnet1 with an IP address such as 192.168.99.1
    * For Docker Desktop an additional interface is not created, so you'll have to use one that's in existence already. Ideally, find one that belongs to a local interface that will not go away when you connection disappears. If there are no other options besides your external network interface, you can get its IP address using:
    ```
    export IP=$(ifconfig en0 | awk '$1 == "inet" {print $2}')
2. Set an environment variable DISPLAY containing "[IP address]:0"
    ```
    export DISPLAY=$IP:0
    ```
3. Clone or download the [HNN repo](https://github.com/jonescompneurolab/hnn):
    ```
    git clone https://github.com/jonescompneurolab/hnn.git
    cd hnn/installer/docker
    ```
4. Start the Docker container. Note: the jonescompneurolab/hnn docker image will be downloaded from Docker Hub (about 1.5 GB)
    ```
    docker-compose up -d
    ```    
5. The HNN GUI should show up and you should now be able to run the tutorials at: https://hnn.brown.edu/index.php/tutorials/
   * If you run into problems starting the Docker container or the GUI is not displaying, please see the [Docker troubleshooting section](../docker/README.md#Troubleshooting)
   * If you closed the HNN GUI, and would like to restart it, run the following:
      ```
      docker-compose restart
      ```
6. **NOTE:** You may want to edit files within the container. To access a command prompt in the container, use `docker exec`:
    ```
    docker exec -ti docker_hnn_1 bash
    ```
    If you'd like to be able to access files from the host system within the container, you can either copy files with [docker cp](https://docs.docker.com/engine/reference/commandline/cp/) or start the container with host directory that is visible as a "volume" within the container (instead of step 4):
    ```
    mkdir $HOME/dir_on_host
    docker-compose run -d -v $HOME/dir_on_host:/home/hnn_user/dir_from_host hnn
    ```
    * Note the different container name after running docker-compose

## Native install

See the instructions in the file [mac-install-instructions.txt](mac-install-instructions.txt)