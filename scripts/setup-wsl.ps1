$ErrorActionPreference = "Stop"

Set-Location C:\Users\travis
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
Write-Host "Downloading Ubuntu image..."
Invoke-WebRequest -Uri https://aka.ms/wsl-ubuntu-1804 -OutFile Ubuntu.appx -UseBasicParsing

Write-Host "Finished downloading Ubuntu image. Extracting..."
Move-Item .\Ubuntu.appx .\Ubuntu.zip
Expand-Archive .\Ubuntu.zip .\Ubuntu
$userenv = [System.Environment]::GetEnvironmentVariable("Path", "User"); [System.Environment]::SetEnvironmentVariable("PATH", $userenv + ";C:\Users\travis\Ubuntu", "User")

Write-Host "Configuring Ubuntu WSL for $env:UserName..."
& .\Ubuntu\Ubuntu1804.exe install --root

& wsl -- dos2unix.exe -n build/jonescompneurolab/hnn/installer/ubuntu/installer.sh ./installer-unix.sh
Write-Host "Installing HNN in Ubuntu WSL..."
Set-Location C:\Users\travis\build\jonescompneurolab\hnn
& wsl -- bash -c "export LOGFILE=/mnt/c/users/travis/build/jonescompneurolab/hnn/hnn_travis.log && TRAVIS_TESTING=1 /mnt/c/users/travis/installer-unix.sh"

if (!$?) {
    exit 1
}
else {
    exit 0
}
