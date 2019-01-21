# Installing HNN on Windows systems

This guide describes two methods for installing HNN and its prerequisistes on a Windows 10 system:

1. A docker container running a Linux install of HNN (recommended)
2. Natively running HNN on Windows (better performance)

Both methods create python environments separate from the system environment, which may have existed before installing HNN. The docker installation is recommended because the python environment and the NEURON installation are fully isolated, reducing the possibility of version conflicts, or the wrong version being used.

Method 1 (using Docker) displays the GUI through an X windows server which may lead to slower responsiveness as compared to using method 2, which displays the GUI running natively on Windows with Python.

## Docker Install

Coming soon.

## Native Install

The [HNN install powershell script](hnn.ps1) will manage downloading all prerequisites except Microsoft MPI which requires a web browser to download. If the script finds msmpisetup.exe in the Downloads folder, it will take care of installing it.

Requirements:
 - A 64-bit OS
 - Windows 7 or later. Windows Vista is not supported for lack of multiprocessing support.
 - Powershell version 1.0 or later. If Powershell is not installed, please follow the link below for downloading and running the Powershell installer:
 https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell

Install procedure:
1. Download Microsoft MPI (msmpisetup.exe) from the link below and save it to the user's Downloads  folder (C:\Users\\[MY_USERNAME]\Downloads): https://msdn.microsoft.com/en-us/library/bb524831.aspx

2. Run the script from a cmd prompt:
    ```
    @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/jonescompneurolab/hnn/master/installer/windows/hnn.ps1'))"
    ```
    OR from a powershell prompt:
    ```
    Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/jonescompneurolab/hnn/master/installer/windows/hnn.ps1'))
    ```
    OR from a local copy:
    ```
    powershell.exe -ExecutionPolicy Bypass -File .\hnn\installer\windows\hnn.ps1
    ```
   * There will be a permission prompt to install Microsoft MPI and a couple of terminal windows will
open up. There will be a prompt for pressing ENTER after nrnmech.dll has been built
   * If an existing Python 3.X installation isn't found, expect that installation will pause for ~5min while installing Miniconda

3. After the script has completed, instructions will be displayed for using the environment either with virtualenv or Miniconda. Open up a new cmd.exe window (not Powershell) for the environment variables to get set in the session.
4. Run:
    ```
    activate hnn
    cd hnn
    python hnn.py hnn.cfg
    ```
5. That will launch the HNN GUI. You should nowbBe able to run the tutorials at: https://hnn.brown.edu/index.php/tutorials/

