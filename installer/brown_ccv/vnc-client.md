# Running HNN with the VNC client on Oscar

1. Download the CCV VNC Client (see [Oscar VNC Documentation](https://docs.ccv.brown.edu/oscar/connecting-to-oscar/vnc))
2. Move the file CCV_VNC_2.0.3.jar to somewhere where you can access later and double click on it.

   * On Mac systems:

      1. You may need to specifically allow this application to run despite warnings about being from an unknown developer.
      2. If you haven't already installed a Java JDK environment, you will be presented with the following dialog. Click "More Info..." to go to the site to download the Java SE Development Kit from Oracle. Proceed after installing the package. You should be able to re-launch CCV_VNC_2.0.3.jar.

      <img src="install_pngs/jdk.png" width="400" />

3. Log in using your CCV account credentials
4. Choose a machine size to run HNN on. Any size will work, but 4 cores should be enough. Click 'Create VNC Session'. You may have to wait why resources are being requested, but eventually, you should see a window pop-up displaying a desktop.
5. Launch "Terminal Emulator" from the bottom left. Run the following commands to pull the HNN container and start the HNN GUI. If are logging in again, skip to "Running HNN a second time" below.

   ```bash
   singularity pull docker://jonescompneurolab/hnn
   singularity run hnn.simg
   ```

6. You can now proceed to the tutorials at https://hnn.brown.edu/index.php/tutorials/ . Some things to note:

   * The files within the container are visible are integrated within Oscar's view of your director. For example, your user directory might be `/users/myuser` and the hnn_user within the container has a user directory `/home/hnn_user`. If you are loading sample files for the tutorials, look in `/home/hnn_user/hnn_source_code`. Your output from simulations will be stored in `/users/myuser/hnn_out`

## Running HNN a second time

Omit the `singularity pull` command from above. The large hnn.simg file was downloaded before and can be used directly this time.

## Troubleshooting

For HNN software issues, please visit the [HNN bulletin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46) and create a new post with your environment and any relevant error messages.
