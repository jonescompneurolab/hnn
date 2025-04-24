FROM mcr.microsoft.com/windows/servercore:1909

# SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]
SHELL ["cmd", "/S", "/C"]
ADD https://downloads.sourceforge.net/project/vcxsrv/vcxsrv/1.20.8.1/vcxsrv-64.1.20.8.1.installer.exe /vcxsrv-installer.exe
RUN vcxsrv-installer.exe /S && \
    erase vcxsrv-installer.exe

RUN reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList" /t REG_EXPAND_SZ /v ProfilesDirectory /d %SystemDrive%\home /f && \
    reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /t REG_DWORD /v UseWUServer /d 0 /f && \
    echo > "C:\test_user_creds" && \
    net user /add hnn_user /homedir:C:\home\hnn_user /profilepath:C:\home\hnn_user < "C:\test_user_creds" && \
    erase C:\test_user_creds
    # powershell -Command "Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0" ; \
    # powershell -Command "Set-Service -Name sshd -StartupType 'Automatic'"

# MSMPI require Administrator privileges
RUN powershell -command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/microsoft/Microsoft-MPI/releases/download/v10.1.1/msmpisetup.exe', 'C:\msmpisetup.exe')" && \
    C:\msmpisetup.exe -unattend && \
    del C:\msmpisetup.exe /Q

USER hnn_user

RUN whoami

COPY installer/docker/QtProject.conf /home/hnn_user/.config/
COPY installer/docker/hnn_envs /home/hnn_user
COPY installer/docker/start_hnn.sh /home/hnn_user
COPY installer/docker/check_hnn_out_perms.sh /home/hnn_user

ADD installer/windows/hnn-windows.ps1 /home/hnn_user/Downloads/
RUN powershell -executionpolicy bypass -File "C:\home\hnn_user\Downloads\hnn-windows.ps1" && \
    powershell -Command "$env:PATH = 'C:\home\hnn_user\AppData\Local\Programs\Git\bin;' + $env:PATH + \
';"C:\Program Files\VcXsrv";C:\home\hnn_user\Miniconda3\Scripts;C:\home\hnn_user\Miniconda3\envs\hnn;' + \
'C:\home\hnn_user\Miniconda3\envs\hnn\Scripts;C:\home\hnn_user\Miniconda3\envs\hnn\Library\bin' ; \
[Environment]::SetEnvironmentVariable('PATH', $env:PATH, [EnvironmentVariableTarget]::User)" && \
    C:\home\hnn_user\Miniconda3\Scripts\conda clean -y -a && \
    del home\hnn_user\Downloads\*.* /Q

RUN cd home\hnn_user && \
    move /y hnn hnn_source_code && \
    mkdir .ssh

WORKDIR /home/hnn_user/hnn_source_code

SHELL ["bash", "--login"]
ENV HOME /c/home/hnn_user
CMD ["bash", "-c", "sleep infinity"]
