FROM mcr.microsoft.com/windows/servercore:ltsc2019

# SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]
SHELL ["cmd", "/S", "/C"]
ADD https://downloads.sourceforge.net/project/vcxsrv/vcxsrv/1.20.8.1/vcxsrv-64.1.20.8.1.installer.exe /vcxsrv-installer.exe
RUN vcxsrv-installer.exe /S && \
    erase vcxsrv-installer.exe

ENV DISPLAY "host.docker.internal:0"

RUN reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList" /t REG_EXPAND_SZ /v ProfilesDirectory /d %SystemDrive%\home /f

RUN echo > "/test_user_creds"
RUN net user /add hnn_user /homedir:C:\home\hnn_user /profilepath:C:\home\hnn_user < "/test_user_creds"
RUN net localgroup Administrators hnn_user /add

USER hnn_user

# run a command to create user dir
RUN erase "C:\test_user_creds"

ADD hnn.ps1 /home/hnn_user/Downloads/

RUN powershell -executionpolicy bypass -File "C:\home\hnn_user\Downloads\hnn.ps1" && \
    "C:\home\hnn_user\Miniconda3\Scripts\conda" clean -y -a && \
    del home\hnn_user\Downloads\*.* /Q

ADD "http://repo.msys2.org/distrib/x86_64/msys2-base-x86_64-20161025.tar.xz" msys2.tar.xy

RUN powershell -Command "Install-Package -Scope CurrentUser -Force 7Zip4Powershell" \
    && powershell -Command "Expand-7zip msys2.tar.xy ." \
    && powershell -Command "Expand-7zip msys2.tar C:\\" \
    && erase "C:\msys2.tar"

COPY QtProject.conf /home/hnn_user/.config/
COPY QtProject.conf /.config/
COPY start_hnn.sh /home/hnn_user
COPY hnn_envs /home/hnn_user

RUN powershell -Command "$env:PATH = 'C:\msys64\usr\bin;"C:\Program Files\VcXsrv";' + $env:PATH; \
[Environment]::SetEnvironmentVariable('PATH', $env:PATH, [EnvironmentVariableTarget]::Machine)"

WORKDIR /home/hnn_user/
ENV HOME /c/home/hnn_user

SHELL ["bash", "--login"]
CMD ["bash", "-c", "sleep infinity"]
