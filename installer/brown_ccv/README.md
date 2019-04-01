# Running HNN on Brown's Oscar supercomputer

**(Brown students, staff, faculty only)**

Brown's Oscar supercomputer operated by the CCV group is able to run HNN as a Docker container using [Singularity](https://www.sylabs.io/guides/3.0/user-guide/). This method greatly simplifies installing HNN and its prerequisites. Instead, HNN is pre-installed in a vetted environment inside a Docker container that is pulled from Docker Hub before starting on Oscar.

## Getting an account on Oscar

Please see  [Create an Account](https://web1.ccv.brown.edu/start/account) on Brown's CCV (Center for Computation and Visualization) site and fill out a new user account form. If you are a member of a lab that has priority or condo access on Oscar, make sure to list the PI and request those accesses. Otherwise choose an exploratory account for access to 16 cores, which is adequate for most HNN simulations.

## Choose a method for displaying GUI

In order to display the HNN GUI on your computer (while HNN is running on Oscar), you can use X11 forwarding or the Java VNC client. X11 forwarding is typically easier once you have installed an X client on your system (XQuartz for Mac and VcXsrv for Windows)

* [X11 Forwarding (recommended)](./x11-forwarding.md)
* [VNC Client](./vnc-client.md)

## Installing HNN in a user directory (Advanced users)

Alternatively, advanced users may wish to install HNN and run it from their home directory rather than a Docker container