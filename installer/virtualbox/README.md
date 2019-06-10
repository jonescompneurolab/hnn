# Running HNN in VirtualBox VM

We have created a VirtualBox VM image that allows users to run HNN using virtualization software. The virtualized machine runs Ubuntu Linux with HNN pre-installed.

You will need an additional ~20 GB of storage space on your machine to set up the VirtualBox image. Of note, any virtualization software can be used to the same effect.

Improvements to HNN with updated releases can be found on [our GitHub page](https://github.com/jonescompneurolab/hnn/releases">https://github.com/jonescompneurolab/hnn/releases). These changes may need to be incorporated into to the VM by running `git pull` from the HNN directory.

## Installing VirtualBox

You will first need to download VirtualBox if you do not already have the application on your machine. You can download VirtualBox by clicking [here](https://www.virtualbox.org/wiki/Downloads).

## Downloading VirtualBox VM

Windows Notes:

* Due to the greater diversity of hardware on Windows machines, we recommend that Windows users start by creating a new virtual machine in VirtualBox, loading a clean version of [Ubuntu 16.04](https://www.ubuntu.com/download/desktop/thank-you?country=US&amp;version=16.04.4&amp;architecture=amd64) into their virtualization software, and then installing HNN using the Ubuntu install scripts found above. If you are using a Windows machine, be sure that virtualization is enabled in the BIOS.

You can download our Ubuntu image with HNN pre-installed by clicking [here](https://www.dropbox.com/s/md2zeazrc8v7vut/hnn_vb_osx_updated_11222018.ova?dl=0) (updated 11/22/18) for OSX users and [here](https://www.dropbox.com/s/1njlc74q32drvvo/hnn_vb_windows_updated_12112018.ova?dl=0) (updated 12/11/18) for Windows users.

* **CRITICAL NOTES**:

  1. The image we provide requires a significant amount of storage space to download. You will also need an additional ~20 GB of storage space on your machine to set up the VirtualBox image.
  2. You will need to [adjust the system settings](https://lifehacker.com/the-power-users-guide-to-better-virtual-machines-in-vir-1569943402) of the virtual machine to match the specifications of your hardware. This entails adjusting the number of cores and the amount of RAM dedicated to running the virtual machine. The virtual machines we supply above are set to use two cores and four GB of RAM.
  3. To load our HNN image into VirtualBox, in the VirtualBox menu, select File -> Import Appliance. In the pop-up window, navigate to the location where the image is stored, then press continue to import the appliance.
  4. For advanced users: adjust the number of CPUs available on your HNN VirtualBox to match the number of cores available on your computer, so that HNN will run optimally. See here for more information: http://smallbusiness.chron.com/make-cpu-available-virtualbox-30729.html 

## Running HNN on VirtualBox

The username for our Ubuntu image is HNN User. The password is hnn. Once you have logged in, you may begin using HNN. To launch HNN, open the terminal and type hnn. Then press enter.

Additional Notes:

1. In the latest version of the software, you cannot currently launch a functional version of HNN by searching for HNN in the inspector and then clicking the HNN icon. If you launch HNN this way, you will be unable to run simulations. The HNN icon functionality is still in development.
2. If HNN does not launch from the terminal, it may not be in the appropriate path. In this case, to launch HNN, follow these instructions: type cd /usr/local/hnn and press enter. Then type hnn and press enter again.
3. After the HNN GUI shows up, make sure that you can run simulations by clicking the 'Run Simulation' button. This will run a simulation with the default configuration. After it completes, graphs should be displayed in the main window.
4. You can now proceed to run the tutorials at https://hnn.brown.edu/index.php/tutorials/

## Troubleshooting

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.

For other HNN software issues, please visit the [HNN bulletin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)