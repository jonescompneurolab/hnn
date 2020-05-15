# Docker Troubleshooting

Common problems that one might encounter running the HNN docker container are listed below. Some of the links below go to an external site (e.g. MetaCell). If you encounter an issue not listed below, please [open an issue](https://github.com/jonescompneurolab/hnn/issues) on GitHub, including the output with the failed command and any other error messages.

Make sure to check the log hnn-docker.log for more verbose error messages that will hint at which of the sections to go to below.

* [Failed to start HNN (No GUI)](#xdisplay)
* [Starting HNN fails with 'Drive has not been shared'](#shared)
* [This computer doesn't have VT-x/AMD-v enabled](#vtx)
* [Image operating system linux cannot be used on this platform](#image)

## Failed to start HNN (No GUI)

Output from `./docker_hnn.sh start`:

```none
Starting HNN... failed
Please see hnn-docker.log for more details
```

Check the contents of `hnn-docker.log`. Most likely, they will be something similar to below:

```none
Creating hnn_container ... done
Attaching to hnn_container
hnn_container | Starting HNN GUI...
hnn_container | No protocol specified
hnn_container | qt.qpa.xcb: could not connect to display :0
hnn_container | qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
hnn_container | This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.
hnn_container |
hnn_container | Available platform plugins are: eglfs, linuxfb, minimal, minimalegl, offscreen, vnc, wayland-egl, wayland, wayland-xcomposite-egl, wayland-xcomposite-glx, webgl, xcb.
hnn_container |
```

The important line for troubleshooting is the next line and will look something like this:

```none
hnn_container | /home/hnn_user/start_hnn.sh: line 41:   147 Aborted                 python3 hnn.py
```

OR

```none
hnn_container | /home/hnn_user/start_hnn.sh: line 45:    12 Aborted                 (core dumped) python3 hnn.py
```

Troubleshooting steps diverge for each operating system.

* Mac/Windows

    1. Check that the X server is started (VcXsrv for Windows and XQuartz for Mac) and verify that it works with other applications, such as with ssh X-forwarding, if possible.

* Linux

    1. Try explicitly giving the docker container authentication for display on the X server

        ```bash
        xhost +local:docker
        ```

If issues persist, we'd greatly appreciate it if you would report the issue on our [GitHub Issues](https://github.com/jonescompneurolab/hnn/issues). Please include output from hnn-docker.log and the above commands

<a name="shared"/>

## Starting HNN fails with 'Drive has not been shared' in hnn-docker.log

In `hnn-docker.log`:

```node
Creating hnn_container ... error

ERROR: for hnn_container  Cannot create container for service hnn: b'Drive has not been shared'

ERROR: for hnn  Cannot create container for service hnn: b'Drive has not been shared'
```

This will happen when starting the HNN container for the first time on Windows. When it is starting, there will be a prompt in the lower-right asking you to share the drive C:. Rerun the script to see the prompt again

<a name="vtx"/>

## This computer doesn't have VT-x/AMD-v enabled

[MetaCell documentation link](https://github.com/MetaCell/NetPyNE-UI/wiki/Docker-installation#problem-this-computer-doesnt-have-vt-xamd-v-enabled)

<a name="image"/>

## Image operating system linux cannot be used on this platform

[MetaCell documentation link](https://github.com/MetaCell/NetPyNE-UI/wiki/Docker-installation#problem-image-operating-system-linux-cannot-be-used-on-this-platform)
