# HNN Docker Container

This directory contains files for building the HNN Docker container. The container itself is running the Ubuntu 18.04 Linux distribution, but can run on any operating system assuming that [Docker](https://www.docker.com/) is installed.

## Pulling the prebuilt Docker container from Docker Hub

The newest version of HNN is available as a prebuilt container posted on Docker Hub, which can be used instead of building the container and all of its prerequisites (NEURON) from scratch.

Linux container (built from release branches):

```bash
docker pull jonescompneurolab/hnn
```

Linux container (built from master):

```bash
docker pull jonescompneurolab/hnn:master
```

Windows container:

```bash
docker pull jonescompneurolab/hnn:win64
```

## Building HNN container

The BUILD_DATE argument is important to build the container with the latest HNN source code. Without it, the build will reuse the docker build cache, which may have been with an old code version.

Optional arguments are SOURCE_BRANCH and SOURCE_REPO. If they are not specified, the image will be build from source at 'https://github.com/jonescompneurolab/hnn' on branch 'master'

```bash
docker build --tag jonescompneurolab/hnn --build-arg SOURCE_BRANCH=master --build-arg SOURCE_REPO="https://github.com/jonescompneurolab/hnn" --build-arg BUILD_DATE=$(date +%s) installer/docker
```

The windows container container can be built with the following command:

```bash
docker build --tag jonescompneurolab/hnn:win64 -f installer/windows/Dockerfile installer/docker
```

## Starting HNN container

The container is designed to be run from the `hnn_docker.sh` script, but in general, the following scheme will work for Linux/mac:

```bash
docker run -d -v "$HOME/hnn_out":"$HOME/hnn_out" --env XAUTHORITY=/tmp/.Xauthority --env SYSTEM_USER_DIR="$HOME" --name hnn_container jonescompneurolab/hnn
```

This will start the container in the background. In order to start the HNN GUI, the start_hnn.sh script must be run inside the container:

## Running HNN with Docker

We recommend using the `hnn_docker.sh` script which includes checks for directory permissions, creating the necessary files, and adding the appropriate options for each host OS. The commands below give an outline of the process.

Using SSH can be controlled by the environment variable USE_SSH

### Without SSH (only recommended for Linux)

```bash
export USE_SSH=0
docker exec --env SYSTEM_USER_DIR="$HOME" --env DISPLAY=":0" -u "$(id -u)" hnn_container /home/hnn_user/start_hnn.sh
```

* In order to access the hnn_out volume, the command is run as the current user on the host OS. For Windows container, the user hnn_user should be used (-u option can be omitted).

### Using SSH (stable X server connection)

```bash
export USE_SSH=1
SSH_PRIVKEY="installer/docker/id_rsa_hnn"
ssh-keygen -f "$SSH_PRIVKEY" -t rsa -N ''

export DISPLAY=127.0.0.1:0
export XAUTHORITY=/tmp/.Xauthority
export SYSTEM_USER_DIR="$HOME"
ssh -o SendEnv=DISPLAY -o SendEnv=XAUTHORITY -o SendEnv=SYSTEM_USER_DIR -o SendEnv=TRAVIS_TESTING -o PasswordAuthentication=no -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -v -i "SSH_PRIVKEY" -R 6000:127.0.0.1:6000 hnn_user@localhost -p 32791
```

* Commands should be run from the HNN source code directory
