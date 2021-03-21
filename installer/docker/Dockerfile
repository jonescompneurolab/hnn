FROM ubuntu:18.04

# avoid questions from debconf
ENV DEBIAN_FRONTEND noninteractive

# create the group hnn_group and user hnn_user
# add hnn_user to the sudo group
RUN groupadd hnn_group && useradd -m -b /home/ -g hnn_group hnn_user && \
    adduser hnn_user sudo && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers && \
    chsh -s /bin/bash hnn_user

# Qt prerequisites packages
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        libfontconfig libxext6 libx11-xcb1 libxcb-glx0 \
        libxcb-icccm4 libxcb-util1 libxcb-image0 libxcb-keysyms1 \
        libxcb-render0 libxcb-shape0 libxcb-randr0 libxcb-render-util0 \
        libxcb-xinerama0 \
        libegl1 && \
    apt-get clean

# base prerequisites packages
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        python3-pip python3-setuptools openssh-server openmpi-bin lsof netcat xauth && \
    apt-get clean

# get HNN python dependencies
# python3-dev and gcc needed for building psutil
RUN sudo pip3 install --no-cache-dir --upgrade pip && \
    sudo apt-get update && \
    sudo apt-get install --no-install-recommends -y \
        gcc python3-dev && \
    sudo pip install --no-cache-dir matplotlib \
        pyqt5 scipy numpy nlopt psutil && \
    sudo apt-get -y remove --purge \
        gcc python3-dev && \
    sudo apt-get autoremove -y --purge && \
    sudo apt-get clean

COPY date_base_install.sh /usr/local/bin
RUN chmod +x /usr/local/bin/date_base_install.sh && \
    /usr/local/bin/date_base_install.sh

RUN mkdir /var/run/sshd

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
RUN sed 's/AcceptEnv.*/AcceptEnv LANG LC_* DISPLAY XAUTHORITY SYSTEM_USER_DIR TRAVIS_TESTING/' -i /etc/ssh/sshd_config

# if users open up a shell, they should go to the hnn repo checkout
ENV HOME /home/hnn_user
WORKDIR $HOME/hnn_source_code
RUN chown -R hnn_user:hnn_group $HOME

CMD sleep infinity

USER hnn_user

RUN mkdir $HOME/.ssh

# get rid of warning about XDG_RUNTIME_DIR
ENV XDG_RUNTIME_DIR=/tmp/runtime-hnn_user
RUN mkdir /tmp/runtime-hnn_user && \
    chmod 700 /tmp/runtime-hnn_user

# use environment variables from hnn_envs
RUN echo "source $HOME/hnn_envs" >> ~/.bashrc

# run sudo to get rid of message on first login about using sudo
RUN sudo -l

# use args to avoid caching
ARG BUILD_DATE
ARG VCS_REF
ARG VCS_TAG
ARG SOURCE_REPO="https://github.com/jonescompneurolab/hnn.git"
ARG SOURCE_BRANCH="master"

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url=$SOURCE_REPO \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.schema-version=$VCS_TAG

# install hnn-core
RUN sudo pip install hnn-core

# install HNN
RUN sudo apt-get update && \
    sudo apt-get install --no-install-recommends -y \
        make gcc libc6-dev libtinfo-dev libncurses-dev \
        libx11-dev libreadline-dev g++ && \
    git clone --single-branch --branch maint/pre-hnn-core \
    ${SOURCE_REPO} \
      --depth 1 --single-branch --branch $SOURCE_BRANCH \
      $HOME/hnn_source_code && \
    cd $HOME/hnn_source_code && \
    make && \
    sudo apt-get -y remove --purge \
        make gcc libc6-dev libtinfo-dev libncurses-dev \
        libx11-dev libreadline-dev g++ && \
    sudo apt-get autoremove -y --purge && \
    sudo apt-get clean

# NEURON runtime prerequisites
RUN sudo apt-get update && \
    sudo apt-get install --no-install-recommends -y \
        libncurses5 libreadline5 libdbus-1-3 libopenmpi-dev && \
    sudo apt-get clean

COPY QtProject.conf $HOME/.config/
COPY check_hnn_out_perms.sh $HOME/
COPY start_hnn.sh $HOME/
COPY hnn_envs $HOME
COPY start_ssh.sh /
COPY check_sshd_port.sh /
COPY check_x_port.sh /

RUN sudo chown -R hnn_user:hnn_group $HOME && \
    sudo chmod +x $HOME/start_hnn.sh $HOME/check_hnn_out_perms.sh && \
    sudo chmod +x /check_sshd_port.sh /start_ssh.sh /check_x_port.sh && \
    sudo chown root:root /check_sshd_port.sh /start_ssh.sh /check_x_port.sh && \
    sudo chmod 666 $HOME/.config/QtProject.conf
