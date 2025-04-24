# Installing HNN via Docker on Windows (WSL)

**Note**: these are instructions for installing the *original* version of HNN, which is **no longer actively-developed**, and only made available for scientific reproducibility. If you are reading this, you probably want to be using the actively-developed version, called *HNN-Core*, which is [available here](https://github.com/jonescompneurolab/hnn-core).

## 1) Install Docker Desktop

Simply scroll down and follow the instructions on the website to download and install Docker Desktop: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/).

You do NOT need to create an account.

## 2) Install Windows Subsystem for Linux (WSL)

Open the "PowerShell" or "Windows Command Prompt" programs in administrator mode by right-clicking either and selecting "Run as administrator". Then, in the window, run the following command:

```
wsl --install
```

Follow the default options for your install. For more information, see https://learn.microsoft.com/en-us/windows/wsl/install .

## 3) Install VcXsrv

Download "VcXsrv Windows X Server" from either https://sourceforge.net/projects/vcxsrv/ (older) or https://github.com/marchaesen/vcxsrv/releases (newer). Either should work.

## 4) Restart your computer

Make sure to restart your computer.

## 5) Start Docker Desktop

After restart, start Docker so that it is running. Make sure to accept any license agreements if it prompts you to.

## 6) Configure VcXsrv for WSL

Open the new program called "Ubuntu" to access your WSL install, then follow the instructions at https://sourceforge.net/p/vcxsrv/wiki/VcXsrv%20%26%20Win10/ . The "Alternate Setup" after the main text is another method that works, and is somewhat easier to follow.

## 7) Download the HNN repository

Download the repository from https://github.com/jonescompneurolab/hnn . You can do this by either installing git then running `git clone https://github.com/jonescompneurolab/hnn`, or clicking the green `Code` button and selecting `Download ZIP`. If you downloaded the ZIP file, extract it into a folder.

## 8) Run the HNN Docker script

In **the Ubuntu app, which is the same as your WSL installation**, navigate to inside the `hnn` or `hnn-master` folder that you just downloaded. Then, run `./hnn_docker.sh start` to start the script, which should take a minute to download the Docker image, and then it will start up the GUI. Note that you must do this through your Ubuntu/WSL install, *not* via Windows Powershell or Command-Prompt. Then get simulating!

## Troubleshooting

If you receive an error, try running `./hnn_docker.sh uninstall` first, before running `./hnn_docker.sh start` again. This could happen if you're trying to run an old version of HNN. Note that these instructions were based off of the instructions provided in this pull request: https://github.com/jonescompneurolab/hnn/pull/337 . See the following comment in particular:  https://github.com/jonescompneurolab/hnn/pull/337#issuecomment-1799006204 . If you run into issues, follow the instructions in that comment.

If you have further issues with the above installation method, you can view older but different install methods at [this link here](2021_instructions).

