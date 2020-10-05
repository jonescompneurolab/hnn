$ErrorActionPreference = "Stop"

Set-Location C:\Users\travis
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
Write-Host "Downloading Ubuntu image..."
Invoke-WebRequest -Uri https://aka.ms/wsl-ubuntu-1804 -OutFile Ubuntu.appx -UseBasicParsing

Write-Host "Finished downloading Ubuntu image. Extracting..."
Move-Item .\Ubuntu.appx .\Ubuntu.zip
Expand-Archive .\Ubuntu.zip .\Ubuntu
$userenv = [System.Environment]::GetEnvironmentVariable("Path", "User"); [System.Environment]::SetEnvironmentVariable("PATH", $userenv + ";C:\Users\travis\Ubuntu", "User")

Write-Host "Configuring Ubuntu WSL..."
& .\Ubuntu\Ubuntu1804.exe install --root

# This creates "hnn_user" which will be the default user in WSL
& wsl -- bash -ec "groupadd hnn_group && useradd -m -b /home/ -g hnn_group hnn_user && adduser hnn_user sudo && echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers && chsh -s /bin/bash hnn_user"

# Copy hnn source (from Travis clone) to hnn_user homedir and change permissions
& wsl -- bash -ec "cp -r build/jonescompneurolab/hnn /home/hnn_user/ && chown -R hnn_user: /home/hnn_user && apt-get update && apt-get install -y dos2unix"

# Now all future commands can be run as hnn_user
& .\Ubuntu\Ubuntu1804.exe config --default-user hnn_user

# remove windows newlines
& wsl -- bash -ec "dos2unix /home/hnn_user/hnn/scripts/* /home/hnn_user/hnn/installer/ubuntu/hnn-ubuntu.sh /home/hnn_user/hnn/installer/docker/hnn_envs"

Write-Host "Installing HNN in Ubuntu WSL..."
& wsl -- bash -ec "cd /home/hnn_user/hnn && source scripts/utils.sh && export LOGFILE=ubuntu_install.log && installer/ubuntu/hnn-ubuntu.sh || script_fail"

if (!$?) {
    exit 1
}
else {
    exit 0
}
