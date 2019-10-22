# Running HNN in VirtualBox VM

We have created a VirtualBox VM image that allows users to run HNN using virtualization software. The virtualized machine runs Ubuntu Linux with HNN pre-installed.

You will need an additional ~20 GB of storage space on your machine to set up the VirtualBox image. Of note, any virtualization software can be used to the same effect.

## Installing VirtualBox

You will first need to download VirtualBox if you do not already have the application on your machine. You can download VirtualBox by clicking [here](https://www.virtualbox.org/wiki/Downloads).

## Downloading VirtualBox VM

You can download our Ubuntu image with HNN pre-installed by clicking [here](https://www.dropbox.com/s/h1carbyc4lcq74c/hnn_vb_osx_updated_10222019.ova?dl=0) (updated 10/22/19).

* **CRITICAL NOTES**:

  1. The image we provide requires a significant amount of storage space to download. You will also need an additional ~20 GB of storage space on your machine to set up the VirtualBox image.
  2. You will need to [adjust the system settings](https://lifehacker.com/the-power-users-guide-to-better-virtual-machines-in-vir-1569943402) of the virtual machine to match the specifications of your hardware. This entails adjusting the number of cores and the amount of RAM dedicated to running the virtual machine. The virtual machines we supply above are set to use 2 cores and 4 GB of RAM.
  3. To load our HNN image into VirtualBox, in the VirtualBox menu, select File -> Import Appliance. In the pop-up window, navigate to the location where the image is stored, then press continue to import the appliance.
  4. For advanced users: adjust the number of CPUs available on your HNN VirtualBox to match the number of cores available on your computer, so that HNN will run optimally. See here for more information: [http://smallbusiness.chron.com/make-cpu-available-virtualbox-30729.html](http://smallbusiness.chron.com/make-cpu-available-virtualbox-30729.html)

## Running HNN on VirtualBox

1. Start up the virtual machine by clicking on the green 'Start' arrow or from the "Machine" menu -> "Start" -> "Normal Start".
2. Start HNN by clicking on the desktop icon "Human Neocortical Neurosolver (HNN)".

Additional Notes:

1. After the HNN GUI shows up, make sure that you can run simulations by clicking the 'Run Simulation' button. This will run a simulation with the default configuration. After it completes, graphs should be displayed in the main window.
2. You can now proceed to run the tutorials at https://hnn.brown.edu/index.php/tutorials/
3. If you need the login information, use the following:

    * username: hnn_user
    * password: hnn

## Updating HNN

Improvements to HNN with updated releases can be found on [our GitHub page](https://github.com/jonescompneurolab/hnn/releases">https://github.com/jonescompneurolab/hnn/releases). These changes may need to be incorporated into to the VM by running the command `git pull origin master` from the `/home/hnn_user/hnn_source_code` directory in a terminal window.

## Troubleshooting

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will be able to suggest possible fixes.

For other HNN software issues, please visit the [HNN bulletin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)
