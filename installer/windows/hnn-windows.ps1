<#

This powershell script will install HNN and all of its prerequisites. It will attempt
to use an already installed python3.x, but if a suitable one cannot be found it will
install Miniconda:
 - Miniconda3-latest-Windows-x86_64.exe

Additionally the following will be installed if they are not found:
 - nrn-7.7.w64-mingwsetup.exe

Other requirements:
 - Only 64-bit installs are supported due to NEURON compatibility
 - Windows 7 or greater is required for multi-processing support

There may be several permission prompts for installing Microsoft MPI. Additionally, a
terminal Windows may open up for building nrnmech.dll

Expect that installation will pause for several minutes while waiting for the Miniconda
installation to finish

#>

$script:NEURON_PATH = "C:\nrn"
$script:NEURON_ESC_PATH = "C:/nrn"

function Test-64-bit () {
  if ([IntPtr]::Size -eq 8) {
    return $true;
  }
  else {
    return $false;
  }
}

if (!(Test-64-Bit)) {
  Write-Warn "A 64-bit environment was not detected. Install script does not support x86 (32-bit) mode"
  return
}

function Test-Installed($program) {
  if ($PSVersionTable.PSVersion.Major -ge 5) {
    (Get-Package -Name *$program* ).Length -gt 0 2> $null
  }
  else {
    # This method is not reliable for non-MSI installers (NEURON, Miniconda/Anaconda)
    # So for older versions, the packages will likely be installed again. If a python3 exe 
    # can be found, it will still be used instead of installing Miniconda
    if (((Get-ChildItem "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall") |
          Where-Object { $null -ne $_.GetValue( "DisplayName" ) -like "*$program*" } )) {
      return $true
    }
    elseif (((Get-ChildItem "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall") |
          Where-Object { $null -ne $_.GetValue( "DisplayName" ) -like "*$program*" } )) {
      return $true
    }

    return $false
  }
}

function Download-Program($program, $file, $url) {
  $dst = "$HOME\Downloads\$file"
  if (!(Test-Path $dst)) {
    Write-Host "Downloading $program..."
    (New-Object System.Net.WebClient).DownloadFile($url, $dst)
  }
}

function Update-User-Paths ($pathToAdd) {
  $oldpath = [environment]::GetEnvironmentVariable("PATH", "User")
  $envPaths = $oldpath -split ';'
  if ($envPaths -notcontains $pathToAdd) {
    $newpath = "$oldpath;$pathToAdd"
    [Environment]::SetEnvironmentVariable("PATH", "$newpath", "User")
  }
  else {
    Write-Host "PATH already contains $pathToAdd"
  }
  # temporary
  $Env:path += ";$pathToAdd"
}

function Test-Numeric ($Value) {
    return $Value -match "^[\d\.]+$"
}

function Test-Python-3 ($python_exe) {
  # redirect stderr into stdout
  $v = (& "$python_exe" "-V" 2>&1)
  # check if an ErrorRecord was returned
  $z,$version = $v.tostring().split(' ')


  if ((Test-Numeric $version) -and ($version -ge 3.0)) {
    return $true
  }
  else {
    return $false
  }
}

function Get-Python-Dll ($python_exe) {
  $python_dir = Split-Path -Path $python_exe -parent
  Get-Item -Path "$python_dir\python3*.dll" | foreach-object {
    $dll = $_.FullName
  }
  # $dll will have the last match (e.g. python37.dll instead of python3.dll)
  if (($null -ne $dll) -and (Test-Path $dll -PathType Leaf)) {
    return $dll
  }
  else {
    # For some Python 3.4 versions
    Get-Item -Path "$python_dir\DLLs\python3*.dll" | foreach-object {
      $dll = $_.FullName
    }
    if (($null -ne $dll) -and (Test-Path $dll -PathType Leaf)) {
      return $dll
    }
    else {
      return $null
    }
  }
}

function Get-Python-VirtualEnv ($python_exe) {
  $python_dir = Split-Path -Path $python_exe -parent
  $virtualenv = "$python_dir\Scripts\virtualenv.exe"
  if (Test-Path $virtualenv -PathType Leaf) {
    return $virtualenv
  }
  else {
    return $null
  }
}

function Test-Good-Python-3 ($python_exe) {
  # does it exist?
  if (!(Test-Path($python_exe) -PathType Leaf)) {
    return $false
  }
  # check that it's the correct version
  elseif (!(Test-Python-3($python_exe))) {
    return $false
  }
  # check that it has a DLL file
  elseif ($null -eq (Get-Python-Dll($python_exe))) {
    return $false
  }
  else {
    # pyth
    return $true
  }
}

function Test-Good-Virtualenv ($python_exe) {
  # check for virtualenv
  $python_dir = Split-Path -Path $python_exe -parent
  if ($null -eq (Get-Python-VirtualEnv($python_exe))) {
    # install virtualenv
    Start-Process "$python_dir\scripts\pip.exe" "install virtualenv" -Wait
  }
  if ($null -ne (Get-Python-VirtualEnv($python_exe))) {
    # success
    return $true
  }
  else {
    return $false
  }
}


function Get-Python-From-Path {
  $cmdOutput = (cmd.exe "/C where python" 2>&1)
  $cmdOutput | ForEach-Object {
    $python_exe = "$_\python.exe"
    if ((Test-Good-Python-3($python_exe)) -and
        (Test-Good-Virtualenv($python_exe))) {
          return $python_exe
          break
    }
  }
  return $null
}

# for checking distributions without virtualenv (e.g. 'conda)
function Get-Python-From ($python_dir) {
  $python_exe = "$python_dir\python.exe"
  if (Test-Good-Python-3($python_exe)) {
    return $python_exe
  }
  return $null
}

function Get-Python-From-Base ($base_dir) {
  $good_python_found = $false

  $cmdOutput = (get-childitem "$base_dir\Python*" 2>&1)
  $cmdOutput | ForEach-Object {
    $python_exe = "$_\python.exe"
    if (!($good_python_found) -and
        (Test-Good-Python-3($python_exe)) -and
        (Test-Good-Virtualenv($python_exe))) {
          $good_python_found = $true
          return $python_exe
    }
  }

  if (!($good_python_found)) {
    return $null
  }
}


# Find an existing python.exe from:
#   1. Miniconda3
#   2. Anaconda3
#   3. $PATH
#   4. User's AppData directory (default dir for python.org installations)

# Note: Test-Installed only finds *conda or NERUON with in powershell 5+
#       with Windows 10. Assume not installed because little harm is done
#       by reinstalling Miniconda if an existing python.exe cannot be found
#       In other words, if python.exe cannot be found, *conda is probably
#       not installed

# Assumptions:
$script:installMiniconda = $true
$script:PYTHON = $null
$script:PYTHON_DLL = $null
$script:CONDA_PATH = $null
$script:VIRTUALENV = $null

# For Anaconda and Miniconda
function Use-Python-Program($program) {
  $PYTHON = $null

  # try to find python.exe
  $PYTHON = Get-Python-From ("$HOME\$program")
  if ($null -ne $PYTHON) {
    # success
    $script:PYTHON = $PYTHON
    $script:PYTHON_DLL = Get-Python-Dll($PYTHON)
    $script:CONDA_PATH = "$HOME\$program"
    Write-Host "Using $program $script:PYTHON"
    return $true
  }
  else {
    return $false
  }
}

# For python in $PATH
function Use-Python-From-Path {
  $PYTHON = $null

  $PYTHON = Get-Python-From-Path
  if ($null -ne $PYTHON) {
    # success
    $script:PYTHON = $PYTHON
    $script:PYTHON_DLL = Get-Python-Dll($PYTHON)
    $script:VIRTUALENV = Get-Python-VirtualEnv($PYTHON)
    Write-Host "Using $script:PYTHON"
    return $true
  }
  else {
    return $false
  }
}


# For all other pythons
function Use-Python-From-Base($base_dir) {
  $PYTHON = $null

  $PYTHON = Get-Python-From-Base($base_dir)
  if ($null -ne $PYTHON) {
    # success
    $script:PYTHON = $PYTHON
    $script:PYTHON_DLL = Get-Python-Dll($PYTHON)
    $script:VIRTUALENV = Get-Python-VirtualEnv($PYTHON)
    Write-Host "Using $script:PYTHON with virtualenv"
    return $true
  }
  else {
    return $false
  }
}

if ((Use-Python-Program("Miniconda3")) -or
    (Use-Python-Program("Anaconda3")) -or
    (Use-Python-From-Path) -or
    (Use-Python-From-Base("$HOME\AppData\Local\Programs\Python")) -or
    (Use-Python-From-Base("$env:ProgramFiles")) -or
    (Use-Python-From-Base("$env:HOMEDRIVE")) -or
    (Use-Python-From-Base("$env:SYSTEMDRIVE"))) {
  $script:installMiniconda = $false
}

if ($script:installMiniconda) {
  $program = "Miniconda3"
  $file = "Miniconda3-latest-Windows-x86_64.exe"
  $url = "https://repo.anaconda.com/miniconda/$file"
  Download-Program $program $file $url
  $script:CONDA_PATH = "$HOME\Miniconda3"
  $dirpath = $script:CONDA_PATH
  Write-Host "Installing $program to $dirpath..."
  $dst = "$HOME\Downloads\$file"
  $proc1 = Start-Process $dst "/S /D=$dirpath" -PassThru
}

$program = "NEURON"
if (!(Test-Installed($program))) {
  $file = "nrn-7.7.w64-mingwsetup.exe"
  $url = "https://neuron.yale.edu/ftp/neuron/versions/v7.7/$file"
  Download-Program $program $file $url
  $dirpath = $script:NEURON_PATH
  Write-Host "Installing $program to $dirpath..."
  $dst = "$HOME\Downloads\$file"
  $proc2 = Start-Process $dst "/S /D=$dirpath" -PassThru
}
else {
  Write-Host "$program already installed"
}

$program = "Microsoft MPI"
if (!(Test-Installed($program))) {
  $file = "msmpisetup.exe"
  $url = "https://github.com/microsoft/Microsoft-MPI/releases/download/v10.1.1/$file"
  Download-Program $program $file $url
  Write-Host "Installing Microsoft MPI..."
  $dst = "$HOME\Downloads\$file"
  & "$dst" "-unattend"
}
else {
  Write-Host "$program already installed"
}

# Script might have been run installers/windows from hnn repo
$hnn_cloned = $false
$cur_dir = Split-Path -Path $MyInvocation.MyCommand.Definition -parent
$test_dir = Resolve-Path -Path "$cur_dir\..\..\..\hnn" 2> $null
if ("$Env:TRAVIS_TESTING" -eq "1") {
  Write-Host "Running in Travis CI. Not pulling from repo"
  $hnn_cloned = $true
  $HNN_PATH = (Get-Item -Path "$test_dir").FullName
}
elseif (($null -ne $test_dir) -and
   (Test-Path -Path "$test_dir\.git")) {
    Write-Host "TRAVIS = $Env:TRAVIS_TESTING"
  # use the already existing repo.
  # hnn will not be cloned
  $HNN_PATH = (Get-Item -Path "$test_dir").FullName
}
else {
  $file = "hnn.zip"
  $url = "https://github.com/jonescompneurolab/hnn/releases/latest/download/hnn.zip"
  Download-Program $program $file $url
  $test_dir = Resolve-Path -Path ".\hnn" 2> $null
  if (($null -ne $test_dir) -and
    (Test-Path -Path "$test_dir")) {
      Write-Host "dir $test_dir already exists"
  }
  else{
    unzip $HOME\Downloads\hnn.zip
    Rename-Item .\hnn-1.3.1 .\hnn
    $hnn_cloned = $true
  }
  $HNN_PATH = (Get-Item -Path "$HOME\hnn").FullName
}

if (!($hnn_cloned)) {
  Write-Host "HNN source code already exists at $HNN_PATH."
}


if ($proc1) {
  Write-Host "Waiting for Miniconda install to finish..."
  $proc1.WaitForExit() 2>$null
  Write-Host "Miniconda is finished"
}

# setup python with virtualenv or 'conda
if ($null -ne $script:VIRTUALENV) {
  Write-Host "Creating Python virtualenv at $HOME\venv\hnn..."
  Start-Process $script:VIRTUALENV "-p $script:PYTHON $HOME\venv\hnn" -Wait
  Write-Host "Now setting up virtualenv for HNN..."
  Start-Process "$HOME\venv\hnn\Scripts\activate" -Wait

  # update $script:PYTHON and sanity check the environment
  $script:PYTHON = "$HOME\venv\hnn\Scripts\python.exe"
  if (Test-Python-3($script:PYTHON)) {
    # use pip3 for good measure
    Start-Process "$HOME\venv\hnn\Scripts\pip3" "install matplotlib scipy PyQt5 psutil nlopt" -Wait
  }
  else {
    Write-Warning "Virtualenv failed to create a valid python3 environment"
  }
}
elseif ($null -ne $script:CONDA_PATH)  {
  Write-Host "Setting environment variables..."
  Update-User-Paths("$script:CONDA_PATH")
  Update-User-Paths("$script:CONDA_PATH\Library\bin")
  Update-User-Paths("$script:CONDA_PATH\Scripts")

  # if the python version is a 'conda, set up the environment
  $CONDA_ENV = "$script:CONDA_PATH\envs\hnn"
  $script:env_exists = $false
  $cmdOutput = (conda list -n hnn) 2>$null
  $cmdOutput | ForEach-Object {
    If (!($script:env_exists) -and
        ($_ -match "# packages in environment*")) {
      $script:env_exists = $true
    }
  }

  if (!$script:env_exists) {
    Write-Host "Setting up anaconda hnn environment..."
    conda create -y -f environment.yml
    conda install -y -n hnn -c conda-forge nlopt

    pip install --upgrade https://api.github.com/repos/jonescompneurolab/hnn-core/zipball/master
    Set-Location $CONDA_ENV
    mkdir .\etc\conda\activate.d 2>&1>$null
    mkdir .\etc\conda\deactivate.d 2>&1>$null

    #"set NRN_PYLIB=$script:PYTHON_DLL" | Set-Content "$CONDA_ENV\etc\conda\activate.d\env_vars.bat"
    "set PYTHONHOME=$CONDA_ENV" | Add-Content "$CONDA_ENV\etc\conda\activate.d\env_vars.bat"
  }
  else {
    Write-Host "Miniconda hnn environment already exists"
  }
}
else {
  # setup virtualenv

}


if ($proc2) {
  Write-Host "Waiting for NEURON install to finish..."
  $proc2.WaitForExit() 2>$null
  Update-User-Paths("$script:NEURON_PATH\bin")
  Write-Host "NEURON is finished"
}

if (!(Test-Path "$HNN_PATH\nrnmech.dll" -PathType Leaf)) {
  Write-Host "Creating nrnmech.dll"
  Set-Location $HNN_PATH\mod
  Start-Process "$script:NEURON_PATH\mingw\usr\bin\sh.exe" "$script:NEURON_ESC_PATH/lib/mknrndll.sh C:\nrn\"
  $obj = New-Object -com Wscript.Shell
  sleep -s 10
  $obj.SendKeys("{ENTER}")
  Copy-Item $HNN_PATH\mod\nrnmech.dll -Destination $HNN_PATH
}
else {
  Write-Host "nrnmech.dll already exists $HNN_PATH\nrnmech.dll"
}

Write-Host ""
Write-Host "Finished installing HNN and prerequisites."
Write-Host "Activate the environment from cmd.exe (not Powershell):"
Write-Host ""

if ($null -ne $script:CONDA_PATH)  {
  if ($script:installMiniconda) {
    Write-Host "# *** run the commands below from a new command prompt or 'conda' will not be found ****"
  }
  Write-Host "conda activate hnn"
}
elseif ($null -ne $script:VIRTUALENV) {
  Write-Host "$HOME\venv\hnn\Scripts\activate"
}
Write-Host "cd $HNN_PATH"
Write-Host "python hnn.py"
Write-Host ""

return
