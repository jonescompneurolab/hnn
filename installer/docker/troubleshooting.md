# Docker Troubleshooting

Common problems that one might encounter running the HNN docker container are listed below. Some of the links below go to an external site (e.g. MetaCell). If you encounter an issue not listed below, please [open an issue](https://github.com/jonescompneurolab/hnn/issues) on GitHub, including the output with the failed command and any other error messages.

* [Could not connect to any X display](#xdisplay)
* [Could not create /home//hnn_user/hnn_out/data](#dir)
* [This computer doesn't have VT-x/AMD-v enabled](#vtx)
* [Image operating system linux cannot be used on this platform](#image)

<a name="xdisplay"/>

## Failed to start HNN on any X port

Output from `docker-compose run`:

```none
...
hnn_container | Trying to start HNN with DISPLAY=host.docker.internal:4
hnn_container | HNN failed to start GUI using DISPLAY=host.docker.internal:4
hnn_container | Failed to start HNN on any X port
```

The docker container is trying to reach an IP address and port defined in the $DISPLAY environment variable, but is failing. The start script first tries port 5000 for the IP address in $DISPLAY, then 5001 through 5004 before giving up. Troubleshooting steps diverge for each operating system.

* Mac/Windows

    1. Check that the X server is started (VcXsrv for Windows and XQuartz for Mac).
    2. Check for connectivity from within the container to the address given. This may be because of firewalls or an incorrect IP address.
    3. Try setting DISPLAY in the docker-compose.yml file for your operating system (e.g. installer/mac/docker-compose.yml) to these different IP addresses and try `docker-compose restart` to rerun the start script.
        * `192.168.99.1:0`
        * `192.168.65.2:0`
    4. As a last step try changing DISPLAY to the IP address of the external interface (e.g. wireless) followed by a ":0". The drawback of this approach is that loosing your WiFi connection will cause HNN to close.

* Linux

    1. Try explicitly giving the docker container authentication for display on the X server

        ```bash
        xhost +local:docker
        cd hnn/installer/docker
        docker-compose restart
        ```

If HNN still fails to start, sometimes more verbose error messages can be seen by open another shell by starting HNN manually.

```bash
docker exec -ti hnn_container bash
```

Try starting HNN manually:

```bash
python3 hnn.py
```

If issues persist, please include output from the above commands in a new [GitHub issue](https://github.com/jonescompneurolab/hnn/issues)

<a name="dir"/>

## Could not create /home//hnn_user/hnn_out/data

```bash
hnn_container | Trying to start HNN with DISPLAY=host.docker.internal:4
hnn_container | ERR: could not create /home//hnn_user/hnn_out/data
hnn_container | HNN failed to start GUI using DISPLAY=host.docker.internal:4
hnn_container | Failed to start HNN on any X port
```

This can be the result of the shared directory (docker_hnn_out on the host, hnn_out in the container) being owned by root rather than hnn_user. From the host, run the following:

```none
$ docker-compose up -d
$ docker exec -ti hnn_container bash
hnn_user@hnn-container:/home/hnn_user/hnn_source_code$ sudo chown -R hnn_user:hnn_group /home/hnn_user/hnn_out
hnn_user@hnn-container:/home/hnn_user/hnn_source_code$ exit
$ docker-compose restart
```

<a name="vtx"/>

## This computer doesn't have VT-x/AMD-v enabled

[MetaCell documentation link](https://github.com/MetaCell/NetPyNE-UI/wiki/Docker-installation#problem-this-computer-doesnt-have-vt-xamd-v-enabled)

<a name="image"/>

## Image operating system linux cannot be used on this platform

[MetaCell documentation link](https://github.com/MetaCell/NetPyNE-UI/wiki/Docker-installation#problem-image-operating-system-linux-cannot-be-used-on-this-platform)
