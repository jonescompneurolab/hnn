# Installing HNN via Docker on macOS

**Note**: these are instructions for installing the *original* version of HNN, which is **no longer actively-developed**, and only made available for scientific reproducibility. If you are reading this, you probably want to be using the actively-developed version, called *HNN-Core*, which is [available here](https://github.com/jonescompneurolab/hnn-core).

## 1) Install Docker Desktop

Simply scroll down and follow the instructions on the website to download and install Docker Desktop: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/).

You do NOT need to create an account.

## 2) Install Xquartz

Download the installer from [https://www.xquartz.org/](https://www.xquartz.org/).

## 3) Restart your computer

Make sure to restart your computer.

## 4) Start Docker Desktop

Start the Docker Desktop application. You can do this easily by pressing Command + space together, typing "docker", and then hit enter. If it asks you to accept any license agreements, select yes, but otherwise you don't need to change anything once it has started.

## 5) Start Xquartz

Start the Xquartz application. You can do this easily by pressing Command + space together, typing "xquartz", and then hit enter

After you've started it, in the top left, click the "XQuartz" dropdown menu, then "Settings" to open the Preferences window. Inside the Preferences window, click Security, then click the checkmark for "Allow connections from network clients". You should only have to do this once.

## 6) Obtaining the HNN code

Go to the HNN code repository at [https://github.com/jonescompneurolab/hnn](https://github.com/jonescompneurolab/hnn), then click the green "Code" button, then "Download ZIP". This will prompt you to download a file named `hnn-master.zip`. Download it. Open the Finder application, navigate to where you downloaded the file, then double-click it to create a new directory that contains the code. (If you are familiar with Git and Github, you can instead choose to clone the repository from the same repository URL.)

## 7) Start HNN-GUI

Once you have completed all of the above, you will only need execute the following steps everytime you want to start the HNN-GUI:

- Make sure Docker Desktop is running.
- Make sure Xquartz is running.
- Open the Terminal application.
- Navigate to the folder where you have cloned the HNN repository using `cd`. For example, if you downloaded and decompressed the code in your `Downloads` folder using the instructions in **6) Obtaining the HNN code**, you can run the following in the terminal: `cd ~/Downloads/hnn-master/`.
- Start the GUI by running the following:  `./hnn_docker.sh start`.
- You're done! Now it's time to get simulating!

## Troubleshooting

If you receive an error, try running `./hnn_docker.sh uninstall` first before running `./hnn_docker.sh start`.  This could happen if you're trying to run an old version of HNN. Note that these instructions were based off of the instructions provided in this pull request: https://github.com/jonescompneurolab/hnn/pull/337 .

If you have issues with the above installation method, you can view older but different install methods at [this link here](2021_instructions).
