# HNN native install (Windows)

This method will run HNN without using virtualization, meaning the GUI may feel more responsive and simulations may run slightly faster. However, the procedure is a set of steps that the user must follow, and there is a possibility that differences in the base environment may require additional troubleshooting. Thus, it is best suited for advanced users. For the recommended Docker-based installation please see the instructions below.
  - Alternative: [Docker install instructions](README.md)

A [PowerShell install script](hnn.ps1) will manage downloading all prerequisites except Microsoft MPI which requires a web browser to download. If the script finds msmpisetup.exe in the Downloads folder, it will take care of installing it.

## Requirements
 - A 64-bit OS
 - Windows 7 or later. Windows Vista is not supported for lack of multiprocessing support.
 - PowerShell version 1.0 or later. If PowerShell is not installed, please follow the link below for downloading and running the PowerShell installer:
 https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell

## Prerequisite: Microsoft MPI

1. Download Microsoft MPI (msmpisetup.exe) from the link below and save it to the user's Downloads  folder (C:\Users\\[MY_USERNAME]\Downloads): https://msdn.microsoft.com/en-us/library/bb524831.aspx

## Run install script

1. Run the script from a cmd prompt:
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

2. After the script has completed, instructions will be displayed for using the environment either with virtualenv or Miniconda. Open up a new cmd.exe window (not PowerShell) for the environment variables to get set in the session.
3. Run:
    ```
    activate hnn
    cd hnn
    python hnn.py hnn.cfg
    ```
4. That will launch the HNN GUI. You should now be able to run the tutorials at https://hnn.brown.edu/index.php/tutorials/

# Troubleshooting

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will investigate possible fixes.

For other HNN software issues, please visit the [HNN bullentin board](https://www.neuron.yale.edu/phpBB/viewforum.php?f=46)