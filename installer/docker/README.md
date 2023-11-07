### Windows Installation Process
**Part 1**
1. Open command Prompt
2. Run the following command to install Windows Subsystem for Linux (WSL)
```
wsl --install
``` 
![image](https://github.com/jonescompneurolab/hnn/assets/34087669/f94c9ea6-1459-4082-8a01-af69d115368c)

3. Once the installation is done, you will see that an `Ubuntu` application is also downloaded. This can be found in Settings > Apps > Installed apps or simply by searching `Ubuntu` in the Windows search bar.
   ![image](https://github.com/jonescompneurolab/hnn/assets/34087669/aa1635db-ccd7-4989-bdbd-7f89f5493225)

4. Once WSL is installed, navigate to the Windows Start Menu and in the search bar, look up `Turn Windows Features on or off` and click on it
5. Go down the list until you see Windows Subsystem for Linux, and check the box so that it is enabled. Click ok so the changes can be applied.
   ![image](https://github.com/jonescompneurolab/hnn/assets/34087669/d9c9580f-2082-4ac8-bdee-ca599e9b2da1)

6. Then open up the Ubuntu application that was installed alongside WSL.
7. The very first time you open this application up, you will see instructions prompting you to create a new UNIX username and password. Afterwards, it will show you an installation successful message.
   ![image](https://github.com/jonescompneurolab/hnn/assets/34087669/d6e26399-804d-4780-a451-492c1ccdf81f)



**Part 2**
1. Please install Docker Desktop https://docs.docker.com/desktop/wsl/#download
2. Once installed, open up the Docker Desktop application.
3. Navigate to Settings, and click on general. Make sure that `Use the WSL 2 Based Engine` is checked.
   ![image](https://github.com/jonescompneurolab/hnn/assets/34087669/84d0078a-ba4f-478c-8af1-e7771ba896b3)

4. Next, click on Resources > WSL Integration
5. Inside here, make sure that all Ubuntu options are toggled. Then press apply & restart.
   ![image](https://github.com/jonescompneurolab/hnn/assets/34087669/d01a0c14-37b2-456a-b7d8-3ed3bdd5283c)

6. To check if Docker is correctly installed, you can open up the Ubuntu terminal (application) and type `docker --version` this should display the version and build number of the software installed.


**Part 3**
1. Please install Vcxsrv https://sourceforge.net/projects/vcxsrv/
2. Run the installer, choosing "C:\Program Files\VcXsrv" as the destination folder.
3. Start the XLaunch desktop app from the VcXsrv folder in the start menu.
4. Choose "Multiple windows". Choose '0' for the "Display number". Click 'Next'.
5. Select "Start no client" and click 'Next'.
6. Important: under "Extra settings" make sure that "Disable access control" is checked.

7. For the following step, you will need the IP address of your local machine. To find it, open up Settings > Network & internet > Wi-Fi > Hardware properties and look for `IPv4 address:`
   ![image](https://github.com/jonescompneurolab/hnn/assets/34087669/45f51c4b-c2c5-48f4-9f7f-490ee423ebd3)

8. Now open up the ubuntu application terminal and run the following commands. Comments above each command help to provide additional details. Original source of instructions comes from https://sourceforge.net/p/vcxsrv/wiki/VcXsrv%20%26%20Win10/.
```
# in the following command, replace the NN.NN.NN.NN with the IPv4 addess that you've obtained in the previous step. 
export DISPLAY=NN.NN.NN.NN:0

# you can ignore any errors that arise from running the following command.
sudo apt install -y xauth coreutils gawk gnome-terminal 

# running the following command should display nothing, to show you that you do not have credentials set up yet. 
xauth list 

# run the following command, with {some-pass-phrase} replaced by any phrase. Ex. hnn-app
magiccookie=$(echo '{some-pass-phrase}'|tr -d '\n\r'|md5sum|gawk '{print $1}')

# run the following
xauth add "$DISPLAY" . "$magiccookie"

# running this command again, you will see that something shows up, displaying the new credentials you have set up. 
xauth list

# run the following commands
userprofile=$(wslpath $(/mnt/c/Windows/System32/cmd.exe /C "echo %USERPROFILE%" | tr -d '\r\n'))
cp ~/.Xauthority "$userprofile
```


**Part 4**
1. Open up a new Ubuntu terminal application.
2. We will now download the code that will run the program to start up the GUI.
3. Run this command to create a copy of the source code in your computer.
```
Git clone https://github.com/jonescompneurolab/hnn.git
```
4. Run the following command to navigate to inside the repository in your Ubuntu terminal.
```
cd hnn
```
5. Run the following command to start up the hnn GUI.
```
./hnn_docker.sh start
``` 

Your terminal should show the following logs if it successfully starts up the hnn GUI.
![image](https://github.com/jonescompneurolab/hnn/assets/34087669/2e5942cb-100f-44cf-9c6f-fdee72576844)

The resulting hnn GUI on initial startup.
![image](https://github.com/jonescompneurolab/hnn/assets/34087669/cb6f404c-d6df-45ef-ab80-cf85e293bf8b)


**Part 4 Troubleshooting**
If you run into the following error while running `./hnn_docker.sh start`

`
docker-machine could not be found.
`
- Please make sure you have gone over the previous steps for installing the docker desktop.
- If this error persists, please try closing and restarting the docker desktop application.

If you run into the following error while running `./hnn_docker.sh start`

`
xuath: (argv):1: couldn't query Security extension on display “:0”
`
- Please double check that you have gone through the steps in Part 3 to configure the magic cookie credentials required for the VcXsrv server to accept connections. 


