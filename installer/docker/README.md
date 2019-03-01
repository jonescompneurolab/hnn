# HNN Docker Container

This directory contains files for building the HNN container and using docker-compose to start the container on any platform. The container itself is running the Ubuntu 18.04 Linux distribution, but can run on any operating system assuming that [Docker](https://www.docker.com/) is installed. For more specific instructions on installing Docker and starting the HNN container, see one of the following pages that matches your operating system:
 * [Windows](../windows)
 * [Mac](../mac)
 * [Ubuntu](../ubuntu)
 * [CentOS](../centos)

## Pulling the prebuilt Docker container from Docker Hub
The newest version of HNN is available as a prebuilt container posted on Docker Hub, which can be used instead of building the container and all of its prerequisites (NEURON) from scratch.
```
docker pull jonescompneurolab/hnn
```

## Building HNN container from this directory
```
cd hnn/installer/docker
docker build --tag jonescompneurolab/hnn .
```

## Running HNN container without docker-compose
Using docker-compose is the preferred way to run HNN containers, because it sets needed environment variables and defines volumes automatically. However, if docker-compose is not available or the user wants to modify docker run arguments, the following command Replicates behavior by docker-compose:
```
# Set DISPLAY for Mac and Windows
export DOCKER_DISPLAY=host.docker.internal:0
# For docker toolbox only 
export DOCKER_DISPLAY=192.168.99.1:0
# For Linux
export DOCKER_DISPLAY=:0

# Start container
docker run -d -e XAUTHORITY="/.Xauthority" -e DISPLAY=$DOCKER_DISPLAY -v "./hnn:/home/hnn_user/hnn" -v ~/.Xauthority:/.Xauthority -v /tmp/.X11-unix:/tmp/.X11-unix jonescompneurolab/hnn /home/hnn_user/start_hnn.sh
```

## Troubleshooting

Common problems that one might encounter running the HNN docker container are listed below. Some of the links below go to an external site (e.g. MetaCell).

### Problem: HNN GUI is not displaying after starting the Docker container

1. The first thing is to check for errors in starting the Docker container. Check the logs for the container using as command similar to below (note: `windows_hnn_1` for Windows and `mac_hnn_1` for Mac):

   ```
   docker logs docker_hnn_1
   ```
   An example of not being able to connect to the X server:

   ```
   QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-hnn_user'
   qt.qpa.screen: QXcbConnection: Could not connect to display :0
   Could not connect to any X display.
   ```

   The first line is not indicative of any error, and is always present. In this case, the next two lines indicate that the X display for HNN GUI was not started. Troubleshooting steps diverge for each operating system. Plase choose your OS below:
     <details><summary>Mac/Windows</summary>
     <p>

      1. Check that the X server is started (VcXsrv for Windows and XQuartz for Mac).
      2. Check for connectivity from within the container to the address given. This may be because of firewalls or an incorrect IP address. When in doubt, an IP address of the external interface (e.g. wireless) will work in most cases.
     </p>
     </details>
     <details><summary>Linux</summary>
     <p>

      1. Try explicitly giving the docker container authentication for display on the X server

         ```
         xhost +local:docker
         cd hnn/installer/docker
         docker-compose restart
         ```
     </p>
     </details>

2. If HNN fails to start, the startup script will fall back to running the command "sleep infinity" which allows you to open up a shell in the container and debug what went wrong. Open a shell by running
   ```
   docker exec -ti docker_hnn_1 bash
   ```

   and check which processes are running:
   ```
   ps auxw
   ```
   Try starting HNN manually:
   ```
   cd hnn_repo
   python3 hnn.py hnn.cfg
   ```
   If you see something other than messages similar to above, please [open an issue](https://github.com/jonescompneurolab/hnn/issues) on GitHub, including the output from the commands above.

 ### Problem: [This computer doesn't have VT-x/AMD-v enabled. (MetaCell documentation)](https://github.com/MetaCell/NetPyNE-UI/wiki/Docker-installation#problem-this-computer-doesnt-have-vt-xamd-v-enabled)
 ### Problem: [Image operating system linux cannot be used on this platform (MetaCell documentation)](https://github.com/MetaCell/NetPyNE-UI/wiki/Docker-installation#problem-image-operating-system-linux-cannot-be-used-on-this-platform)