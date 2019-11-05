# Docker Troubleshooting

Common problems that one might encounter running the HNN docker container are listed below. Some of the links below go to an external site (e.g. MetaCell). If you encounter an issue not listed below, please [open an issue](https://github.com/jonescompneurolab/hnn/issues) on GitHub, including the output with the failed command and any other error messages.

* [Could not connect to any X display](#xdisplay)
* [Could not create /home//hnn_user/hnn_out/data](#dir)
* [This computer doesn't have VT-x/AMD-v enabled](#vtx)
* [Image operating system linux cannot be used on this platform](#image)

<a name="xdisplay"/>

## Failed to start HNN

Output from `./docker_hnn.sh start`:

```none
Starting HNN... failed to start HNN. Please see hnn_docker.log for more details
```

In `hnn_docker.log`:
```none
Starting HNN GUI...
No protocol specified
qt.qpa.xcb: could not connect to display localhost:0
qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.

Available platform plugins are: eglfs, linuxfb, minimal, minimalegl, offscreen, vnc, wayland-egl, wayland, wayland-xcomposite-egl, wayland-xcomposite-glx, webgl, xcb.

/home/hnn_user/start_hnn.sh: line 41:   147 Aborted                 python3 hnn.py

...[more output]...

Failed to start HNN on any X port
Connection to localhost closed.
```

macOS only: try forcing a restart of the container:

```bash
./hnn_docker.sh -r start
```

Then try to start HNN manually: 
```bash
docker exec -ti hnn_container bash
```

Try starting HNN manually:

```bash
python3 hnn.py
```

If that doesn't work, troubleshooting steps diverge for each operating system.

* Mac/Windows

    1. Check that the X server is started (VcXsrv for Windows and XQuartz for Mac).

* Linux

    1. Try explicitly giving the docker container authentication for display on the X server

        ```bash
        xhost +local:docker
        cd hnn/installer/docker
        docker-compose restart
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
