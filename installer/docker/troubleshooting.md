# Docker Troubleshooting

Common problems that one might encounter running the HNN docker container are listed below. Some of the links below go to an external site (e.g. MetaCell). If you encounter an issue not listed below, please [open an issue](https://github.com/jonescompneurolab/hnn/issues) on GitHub, including the output with the failed command and any other error messages.

Make sure to check the log hnn_docker.log for more verbose error messages that will hint at which of the sections to go to below.

* [Failed to start HNN on any X port](#xdisplay)
* [Starting HNN fails with 'Drive has not been shared'](#shared)
* [This computer doesn't have VT-x/AMD-v enabled](#vtx)
* [Image operating system linux cannot be used on this platform](#image)

# Failed to start HNN

Output from `./docker_hnn.sh start`:

```none
Starting HNN... failed to start HNN. Please see hnn_docker.log for more details
```

Check the contents of `hnn_docker.log` to determine which of the following issue applies

<a name="xdisplay"/>

## Failed to start HNN on any X port

`hnn_docker.log` contents:
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

<a name="shared"/>

## Starting HNN fails with 'Drive has not been shared' in hnn_docker.log

In `hnn_docker.log`:

```node
Creating hnn_container ... error

ERROR: for hnn_container  Cannot create container for service hnn: b'Drive has not been shared'

ERROR: for hnn  Cannot create container for service hnn: b'Drive has not been shared'
```
This will happen when starting the HNN container for the first time on Windows. When it is starting, there will be a prompt in the lower-right asking you to share the drive C:. Rerun the script to see the prompt again

<a name="vtx"/>

# This computer doesn't have VT-x/AMD-v enabled

[MetaCell documentation link](https://github.com/MetaCell/NetPyNE-UI/wiki/Docker-installation#problem-this-computer-doesnt-have-vt-xamd-v-enabled)

<a name="image"/>

# Image operating system linux cannot be used on this platform

[MetaCell documentation link](https://github.com/MetaCell/NetPyNE-UI/wiki/Docker-installation#problem-image-operating-system-linux-cannot-be-used-on-this-platform)
