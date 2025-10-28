# Running HNN in VirtualBox VM

**Note**: these are instructions for installing the *original* version of HNN, which is **no longer actively-developed**, and only made available for scientific reproducibility. If you are reading this, you probably want to be using the actively-developed version, called *HNN-Core*, which is [available here](https://github.com/jonescompneurolab/hnn-core).

We have created a VirtualBox VM image that allows users to run HNN using virtualization software. The virtualized machine runs Ubuntu Linux with HNN pre-installed.

You will need an additional ~20 GB of storage space on your machine to set up the VirtualBox image. Of note, any virtualization software can be used to the same effect.

## Windows-only prerequisite: disable Hyper-V

For Windows operating systems, it is necessary to turn off Hyper-V for running Virtualbox. You may find that this feature is already turned off, but use the following steps to confirm. This feature is required by Docker Desktop, so if you followed instructions for that method previously, you will now need to disable it.

1. Start typing "Turn Windows features on or off" in the search bar next to start menu and click on it to launch the control panel dialog window shown below.
2. Make sure that the "Hyper-V" component is unchecked as shown in the image below and click "Ok".

    <img src="../windows/install_pngs/disable-hyperv.png" width="400" />

3. **If you disabled Hyper-V, please reboot your computer before continuing below to install docker.**

## Installing VirtualBox

You will first need to download VirtualBox if you do not already have the application on your machine. You can download VirtualBox by clicking [here](https://www.virtualbox.org/wiki/Downloads).

## Downloading VirtualBox VM

You can download our Ubuntu image with HNN pre-installed by clicking [here](https://www.dropbox.com/s/vwlel40sbu7o41o/hnn_vb_osx_updated_11042019.ova?dl=0) (updated 11/04/19).

* **CRITICAL NOTES**:

  1. The image we provide requires a significant amount of storage space to download. You will also need an additional ~10 GB of storage space on your machine to set up the VirtualBox image.
  2. To load our HNN image into VirtualBox, in the VirtualBox menu, select File -> Import Appliance. In the pop-up window, navigate to the location where the image is stored, then press continue to import the appliance.
  3. Adjust the number of CPUs available on your HNN VirtualBox to match the number of cores available on your computer, so that HNN will run optimally. The virtual machine we supply above is set to use 1 core and 2 GB of RAM. See here for more information: [http://smallbusiness.chron.com/make-cpu-available-virtualbox-30729.html](http://smallbusiness.chron.com/make-cpu-available-virtualbox-30729.html)
  4. For advanced users: you may benefit from [adjusting the system settings](https://lifehacker.com/the-power-users-guide-to-better-virtual-machines-in-vir-1569943402) of the virtual machine to match the specifications of your hardware (hardware virtualization support and acceleration features).

## Running HNN on VirtualBox

1. Start up the virtual machine by clicking on the green 'Start' arrow or from the "Machine" menu -> "Start" -> "Normal Start".
2. Start HNN by clicking on the desktop icon "Human Neocortical Neurosolver (HNN)".

Additional Notes:

1. After the HNN GUI shows up, make sure that you can run simulations by clicking the 'Run Simulation' button. This will run a simulation with the default configuration. After it completes, graphs should be displayed in the main window.
2. You can now proceed to run the tutorials at [https://hnn.brown.edu/index.php/tutorials](https://hnn.brown.edu/index.php/tutorials)
3. If you need the login information, use the following:

    * username: hnn_user
    * password: hnn

## Updating HNN

Improvements to HNN with updated releases can be found on [our GitHub page](https://github.com/jonescompneurolab/hnn/releases). These changes may need to be incorporated into to the VM by running the command `git pull origin master` from the `/home/hnn_user/hnn_source_code` directory in a terminal window.
