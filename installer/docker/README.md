# HNN Docker Container

### ** UPDATED Instructions: 11/29/2023 **

### Windows Installation Process

## Part 1 Install WSL
1. Open the Command Prompt application. Can be found by searching `Command Prompt` in the Windows search bar.
2. Paste the following command to install Windows Subsystem for Linux (WSL)
```
wsl --install
``` 
![image](https://github.com/jonescompneurolab/hnn/assets/34087669/f94c9ea6-1459-4082-8a01-af69d115368c)

3. Once the installation is completed, you will see that an `Ubuntu` application is also downloaded. This can be found in `Settings > Apps > Installed apps` or by searching `Ubuntu` in the Windows search bar. Please take note of this as it will be important later on in this installation.

![image](https://github.com/jonescompneurolab/hnn/assets/34087669/aa1635db-ccd7-4989-bdbd-7f89f5493225)

5. Once WSL is installed, navigate to the Windows Start Menu and in the search bar, look up `Turn Windows Features on or off` and click on it

6. Go down the list until you see Windows Subsystem for Linux, and check the box so that it is enabled. Click OK so the changes can be applied.
   
![image](https://github.com/jonescompneurolab/hnn/assets/34087669/d9c9580f-2082-4ac8-bdee-ca599e9b2da1)

8. Then open up the Ubuntu application that was mentioned in Step 3.
9. The very first time you open up this application, you will be instructed to create a new UNIX username and password. If done correctly, it will show an `installation successful!` message.
   
![image](https://github.com/jonescompneurolab/hnn/assets/34087669/d6e26399-804d-4780-a451-492c1ccdf81f)



## Part 2 Install Docker
1. Please install Docker Desktop from this link https://docs.docker.com/desktop/install/windows-install/
2. Once installed, click on the newly added Docker Desktop icon on your computer to open up the application.
3. Press on the Settings Icon in the navigation bar to navigate to the Settings. Once there, click on the General tab. Make sure that `Use the WSL 2 Based Engine` is checked as shown in the screenshot below.
   
![image](https://github.com/jonescompneurolab/hnn/assets/34087669/84d0078a-ba4f-478c-8af1-e7771ba896b3)

5. Next, click on the Resources tab on the left and navigate to `WSL Integration`
6. Inside here, make sure that all Ubuntu options are toggled. Then press apply & restart.
   
![image](https://github.com/jonescompneurolab/hnn/assets/34087669/d01a0c14-37b2-456a-b7d8-3ed3bdd5283c)

8. To check if Docker is correctly installed, you can open up the Ubuntu terminal (application) and type `docker --version`, If done correctly, a version and build number of the software installed should be fed back.


## Part 3 Install Vcxsrv
1. Please install Vcxsrv https://sourceforge.net/projects/vcxsrv/
2. Run the installer, choosing `C:\Program Files\VcXsrv` as the destination folder.
3. A new icon named `XLaunch` should now appear on your computer. Click on the icon to open up the application and continue with the installation steps.
4. Choose "Multiple windows" for `Select display settings`. Choose '0' for the `Display number`. Click 'Next'.

![Screenshot 2023-11-29 163402](https://github.com/jonescompneurolab/hnn/assets/34087669/89bcad1a-56fd-4026-a718-ea3c81b8554d)

5. Select "Start no client" and click 'Next'.

![Screenshot 2023-11-29 164111](https://github.com/jonescompneurolab/hnn/assets/34087669/57ba748c-6a05-424d-aa7b-8afcc7f9b917)

7. Please make sure "Disable access control" is checked and click 'Next'. This will take you to the final page where you can press 'Finish' to complete the installation.

![Screenshot 2023-11-29 163550](https://github.com/jonescompneurolab/hnn/assets/34087669/d4c7341b-1b00-4721-b49d-79b5dd081047)


## Part 4 Configure and Run HNN Application
1. Open up a new Ubuntu terminal application, referenced in Step 3 of Part 1.
2. We will now download the source code that starts up the GUI. Paste this command to create a copy of the source code on your computer.
```
git clone https://github.com/jonescompneurolab/hnn.git
```
3. Paste the following command to navigate to inside the project in your Ubuntu terminal.
```
cd hnn
```
4. Before we can start up the application, an additional step is required. We have to set up the right configurations for Vcxsrv (downloaded in Part 3) before we can start up the HNN interface. To do so, please paste the following command in the terminal to run the `configure_vcxsrv.sh` script which will automatically handle the configurations for you.
```
./scripts/configure_vcxsrv.sh
``` 
A successful run of the `configure_vcxsrv.sh` script should output the following logs.
![Screenshot 2023-11-29 165651](https://github.com/jonescompneurolab/hnn/assets/34087669/5c41c8f5-2e4e-48c6-b32a-1de2cebdd7b9)

5. Now run the following command to start up the HNN GUI.
```
./hnn_docker.sh start
``` 

Your terminal should display the following messages if it successfully started up the HNN GUI.

![image](https://github.com/jonescompneurolab/hnn/assets/34087669/2e5942cb-100f-44cf-9c6f-fdee72576844)

The resulting HNN GUI on initial startup.

![image](https://github.com/jonescompneurolab/hnn/assets/34087669/cb6f404c-d6df-45ef-ab80-cf85e293bf8b)


## Troubleshooting
If you run into the following error while running `./hnn_docker.sh start`

`
docker-machine could not be found.
`
- Please make sure you have gone over the previous steps for installing the docker desktop.
- If this error persists, please try closing and restarting the docker desktop application.

If you run into the following error while running `./hnn_docker.sh start`

`
xauth: (argv):1: couldn't query Security extension on display “:0”
`
- Please double check that you have gone through the steps in Part 3 to correctly set up the Vcxsrv server. Also check that you have successfully ran the `configure_vcxsrv.sh` script from the previous Step 4 of this Part 4 of the installation.

