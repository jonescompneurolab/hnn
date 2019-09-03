# HNN Docker Container

This directory contains files for building the HNN container and using docker-compose to start the container on any platform. The container itself is running the Ubuntu 18.04 Linux distribution, but can run on any operating system assuming that [Docker](https://www.docker.com/) is installed. For more specific instructions on installing Docker and starting the HNN container, see one of the following pages that matches your operating system:

* [Windows](../windows)
* [Mac](../mac)
* [Ubuntu](../ubuntu)
* [CentOS](../centos)

## Pulling the prebuilt Docker container from Docker Hub

The newest version of HNN is available as a prebuilt container posted on Docker Hub, which can be used instead of building the container and all of its prerequisites (NEURON) from scratch.

```bash
docker pull jonescompneurolab/hnn
```

## Building HNN container from this directory

The CACHEBUST argument reuses the docker cache up to the point where new HNN source code is included (container will always include latest source code).

```bash
cd hnn/installer/docker
docker build --tag jonescompneurolab/hnn --build-arg CACHEBUST=$(date +%s) .
```

## Running HNN container without docker-compose

Using docker-compose is the preferred way to run HNN containers, because it sets needed environment variables and defines volumes automatically. However, if docker-compose is not available or the user wants to modify docker run arguments, the following command Replicates behavior by docker-compose:

```bash
# Set DISPLAY for Mac and Windows
export DOCKER_DISPLAY=host.docker.internal:0
# For docker toolbox only
export DOCKER_DISPLAY=192.168.99.1:0
# For Linux
export DOCKER_DISPLAY=:0

# Start container
docker run -d -e XAUTHORITY="/.Xauthority" -e DISPLAY=$DOCKER_DISPLAY -v "./hnn:/home/hnn_user/hnn" -v ~/.Xauthority:/.Xauthority -v /tmp/.X11-unix:/tmp/.X11-unix jonescompneurolab/hnn /home/hnn_user/start_hnn.sh
```
