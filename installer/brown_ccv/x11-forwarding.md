# Running HNN with X11 Forwarding on Oscar

## Installing the X11 client

### Mac (XQuartz)

1. Download the installer image (version 2.7.11 tested): https://www.xquartz.org/
2. Open the .dmg image and run XQuartz.pkg within the image, granting privileges when requested.
3. Start the XQuartz.app by searching for XQuartz in Spotlight (upper right search icon). An "X" icon will appear in the taskbar along with a terminal. We will not use this window because it is difficult to copy and paste into it, so you can close it by clicking on the red x in the upper left corner.

   * Alternatively steps 2 and 3 can be run from the terminal app (enter your user password when prompted after the `sudo` command):

     ```bash
     hdiutil attach ~/Downloads/XQuartz-2.7.11.dmg
     sudo installer -pkg /Volumes/XQuartz-2.7.11/XQuartz.pkg -target /
     hdiutil detach /Volumes/XQuartz-2.7.11
     rm ~/Downloads/XQuartz-2.7.11.dmg
     open /Applications/Utilities/XQuartz.app
     ```

### Windows (VcXsrv)

1. Download the installer from [https://sourceforge.net/projects/vcxsrv/files/latest/download](https://sourceforge.net/projects/vcxsrv/files/latest/download) (click [here](https://downloads.sourceforge.net/project/vcxsrv/vcxsrv/1.20.1.4/vcxsrv-64.1.20.1.4.installer.exe?r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Fvcxsrv%2Ffiles%2Fvcxsrv%2F1.20.1.4%2Fvcxsrv-64.1.20.1.4.installer.exe%2Fdownload%3Fuse_mirror%3Dversaweb%26r%3Dhttps%253A%252F%252Fsourceforge.net%252Fprojects%252Fvcxsrv%252Ffiles%252Flatest%252Fdownload&ts=1550243133) for the direct download link for version 64.1.20.1.4)
2. Run the installer, choosing any installation folder.
3. Start the XLaunch desktop app from the VcXsrv folder in the start menu.
4. Choose "Multiple windows" and Click 'Next'.
5. Select "Start no client" and click 'Next'.
6. Click "Save configuration" to create a shortcut with the settings we just chose. Click "Finish" and an "X" icon will appear in the lower-right dock signaling that VcXsrv has started.
7. A message from Windows firewall to allow connections may pop up. If it does, choose options allowing connections to the VcXsrv when connected to both public and private networks.

## Logging into Oscar with X11 forwarding

1. Start your X11 client and leave running in the background
2. Run the ssh command below from a terminal window. The `-X` is important to enable X11 forwarding for the GUI.

   ```bash
   ssh -X YOUR_USERNAME@ssh.ccv.brown.edu
   ```

3. Log in using your CCV account password

4. Start an interactive job with the `interact` command. Choose the number of cores for your allocations. If you have an exploratory account, you are limited to 16 cores. Anything larger will remain in the queue forever.

   ```bash
   interact -n 16
   ```

   * When the command above succeeds your command prompt will change from `[USER@login00XX ~]$` to `[USER@nodeXXXX ~]$`

5. Run the following commands to pull the HNN container and start the HNN GUI. If are logging in again, skip to "Running HNN a second time" below.

   ```bash
   singularity pull docker://jonescompneurolab/hnn
   singularity shell hnn.simg
   cd /home/hnn_user/hnn_repo/
   python3 hnn.py hnn.cfg
   ```

6. When the HNN GUI starts up, make sure to change limit the number of cores the amount when requesting the interactive session (e.g. 16 cores)
    * Click 'Set Parameters' -> 'Run' and change 'NumCores'
7. You can now proceed to the tutorials at https://hnn.brown.edu/index.php/tutorials/ . Some things to note:

   * The files within the container are visible at `/`. This allows you to access both the container filesystem and Oscar's filesystem seamlessly. If you are loading sample files for the tutorials, look in `/home/hnn_user/hnn_repo`
   * The "Model Visualization" feature will not work and you will receive an error in the terminal window: `ImportError: libreadline.so.6: cannot open shared object file: No such file or directory`.

## Running HNN a second time

Omit the `singularity pull` command from above. The large hnn.simg file was downloaded before and can be used directly this time.

## Troubleshooting

For HNN software issues, please visit the [HNN bulletin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46) and create a new post with your environment and any relevant error messages.