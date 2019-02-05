# HNN Docker container

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
# Set DISPLAY on Mac 
export DISPLAY=$(ifconfig en0 | awk '/inet /{print $2 ":0"}')
# Set DISPLAY on Windows
set DISPLAY=10.0.75.1:0
# Start container
docker run -d -e XAUTHORITY="/.Xauthority" -e DISPLAY -v ~/.Xauthority:/.Xauthority -v /tmp/.X11-unix:/tmp/.X11-unix jonescompneurolab/hnn /home/hnn_user/start_hnn_in_docker.sh
```

## Troubleshooting

Common problems that one might encounter running the HNN docker container are listed below. Some of the links below go to an external site (e.g. MetaCell) because they provided an explanation of the problem and the appropriate fix.
 ### Problem: [This computer doesn't have VT-x/AMD-v enabled. (MetaCell documentation)](https://github.com/MetaCell/NetPyNE-UI/wiki/Docker-installation#problem-this-computer-doesnt-have-vt-xamd-v-enabled)
 ### Problem: [Image operating system linux cannot be used on this platform (MetaCell documentation)](https://github.com/MetaCell/NetPyNE-UI/wiki/Docker-installation#problem-image-operating-system-linux-cannot-be-used-on-this-platform)
 
 ### Problem: GUI is not displaying after starting the Docker container

The first thing is to check for any errors in starting the Docker container. Check the logs for the container using:
```
docker logs docker_hnn_1
```
If HNN fails to start, the startup script will fall back to running the command "sleep infinity" which allows you to open up a shell in the container and debug what went wrong. An example of not being able to connect to the X server:

    QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-hnn_user'
    qt.qpa.screen: QXcbConnection: Could not connect to display 10.0.75.1:0
    Could not connect to any X display.

* The first line is not indicative of any error, and is always present. In this case, the next two lines indicate that the X display for HNN GUI was not started. Check for connectivity from within the container to the address given. This may be because of firewalls or an incorrect IP address. When in doubt, an IP address of the external interface (e.g. wireless)will work in most cases.


If the error messages are different than above, open a shell in the container:
```
docker exec -ti docker_hnn_1 bash
```
Check which processes are running:
```
ps auxw
```
If HNN hasn't started, try starting it manually:
```
python3 hnn.py hnn.cfg
```


## Note on Linux X Windows for the GUI

The Linux HNN container uses the X11 protocol to display its GUI on the above platforms. This requires an X server to be installed on the host operating system. Since the container will be communicating via this protocol, it needs to know both the IP address of the X server and also be authorized to use the display. The IP address is passed into the container using the environment variable DISPLAY and the authorization issue is sidestepped by making the file ~/.Xauthority from the host available within the container. A more secure but slightly less user-friendly set up would be to use the xhost command on the host operating system to authorize the container's use of the display. This command may not be available on MS Windows systems, so the provided instructions use the .Xauthority file method instead.