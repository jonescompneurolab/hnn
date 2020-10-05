# Installing HNN on Windows

This guide describes installing HNN on Windows 10. There are two methods to choose from

1. [Windows Subsystem for Linux (WSL) installation (recommended)](wsl.md)
2. [Powershell script for Windows-native installation (advanced users)](native_install.md)

We recommend the Microsoft Windows Subsystem for Linux (with WSL) because:

1. The simulation code is compiled into a Linux system compatible format, which actually runs faster than when compiled to run directly on Windows.
2. With WSL installed, the installation process becomes nearly identical to that on a Linux system, which helps ensure that the installation process remains reliable with common troubleshooting steps.

The major drawbacks to the recommend option are:

1. Using WSL requires running a X server on the Windows OS to display graphics from the WSL environment. The steps to install VcXsrv (a free X server for Windows) are part of the HNN installation instructions above.
2. The data and parameter files from HNN simulations are stored in a filesystem specific for the Ubuntu application. You can read Windows files from Ubuntu in the Ubuntu command-line (e.g. via `/mnt/c/users/`). However, you cannot access simulation results from Windows applications without copying the file to the mount directory first. See [WSL FAQ](https://docs.microsoft.com/en-us/windows/wsl/faq#how-do-i-use-a-windows-file-with-a-linux-app). If this is a limitation for your workflow, please try the Windows-native install instructions.

## Other installation options

Another option for users that are running into problems with the above methods, we provide a VirtualBox VM pre-installed with HNN.

- [Virtualbox install instructions](../virtualbox/README.md)

Lastly installation using Docker is possible, but we are in the process of deprecating the instructions below.

- [Windows 10 (Pro/Enterprise only): Docker Desktop](./docker-desktop.md)
- [Windows 10 Home: Docker Toolbox](./docker-toolbox.md)
