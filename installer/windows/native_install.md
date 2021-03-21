# Windows-native HNN install script

With this method, a [PowerShell install script](hnn-windows.ps1) will manage downloading all prerequisites, including Python (Anaconda), NEURON, and Git for Windows.

## Requirements

- A 64-bit OS
- Windows 7 or later. Windows Vista is not supported for lack of multiprocessing support.
- PowerShell version 1.0 or later. If PowerShell is not installed, please follow [this link](https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell) for downloading and running the PowerShell installer.

## Run install script

The PowerShell script used below will create a new directory called "hnn" in the place where the command is run from. If you have already cloned a copy of the HNN source code, you can avoid creating this new directory by running the script within the existing source code directory (using the third option below).

1. Run the script from a cmd prompt:

    From a local copy (already checked out with git):

    ```powershell
    cd hnn
    powershell.exe -ExecutionPolicy Bypass -File .\installer\windows\hnn-windows.ps1
    ```

    OR to download and run the script from a url:

    ```powershell
    @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/blakecaldwell/hnn/integration_docs/installer/windows/hnn-windows.ps1'))"
    ```

    OR from a powershell prompt:

    ```powershell
    Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/blakecaldwell/hnn/integration_docs/installer/windows/hnn-windows.ps1'))
    ```

   - There will be a permission prompt to install Microsoft MPI and a couple of terminal windows will
open up. There will be a prompt for pressing ENTER after nrnmech.dll has been built
   - If an existing Python 3.X installation isn't found, you should expect that installation will pause for ~5min while installing Miniconda

2. After the script has completed, instructions will be displayed for using the environment either with virtualenv or Miniconda. **Open up a new cmd.exe window (not PowerShell)**.
3. Run:

    ```powershell
    activate hnn
    cd hnn
    python hnn.py
    ```

4. That will launch the HNN GUI. You should now be able to run the tutorials at https://hnn.brown.edu/index.php/tutorials/

## Troubleshooting

### Running hnn fails with "Permission denied" for python3

When trying to run simulations in HNN, you might see messages similar to below:

```powershell
Starting simulation (2 cores). . .
Simulation exited with return code 4294967293. Stderr from console:
NEURON -- VERSION 7.6.5 master (f3dad62b) 2019-01-11
Duke, Yale, and the BlueBrain Project -- Copyright 1984-2018
See http://neuron.yale.edu/neuron/credits

C:/nrn/bin/nrnpyenv.sh: line 141: /cygdrive/c/Users/[USERNAME]/AppData/Local/Microsoft/WindowsApps/python3: Permission denied
Python not available
```

This issue occurs after a particular Windows update is applied that inserts a non-functional alias for Python into the PATH environment variable before the functional version we installed. Since these are non-functional aliases, it is fine to remove them. HNN will then be able to locate the correct Python executable.

```powershell
rm $HOME\AppData\Local\Microsoft\WindowsApps\python.exe
rm $HOME\AppData\Local\Microsoft\WindowsApps\python3.exe
```

### Other issues

If you run into other issues with the installation, please [open an issue on our GitHub](https://github.com/jonescompneurolab/hnn/issues). Our team monitors these issues and will investigate possible fixes.
