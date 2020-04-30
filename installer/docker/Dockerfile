FROM caldweba/opengl-docker

EXPOSE 22

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
        libegl1 && \
    apt-get clean

# base prerequisites packages
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        python3-pip python3-setuptools openssh-server openmpi-bin lsof netcat xauth && \
    apt-get clean

COPY date_base_install.sh /usr/local/bin
RUN chmod +x /usr/local/bin/date_base_install.sh && \
    /usr/local/bin/date_base_install.sh

RUN mkdir /var/run/sshd

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
RUN sed 's/AcceptEnv.*/AcceptEnv LANG LC_* DISPLAY XAUTHORITY SYSTEM_USER_DIR TRAVIS_TESTING/' -i /etc/ssh/sshd_config

# if users open up a shell, they should go to the hnn repo checkout
WORKDIR /home/hnn_user/hnn_source_code
RUN chown -R hnn_user:hnn_group /home/hnn_user

CMD sleep infinity

USER hnn_user

# get HNN python dependencies
# python3-dev and gcc needed for building psutil
RUN sudo pip3 install --no-cache-dir --upgrade pip && \
    sudo apt-get update && \
    sudo apt-get install --no-install-recommends -y \
        gcc python3-dev && \
    sudo pip install --no-cache-dir matplotlib PyOpenGL \
        pyqt5 pyqtgraph scipy numpy nlopt psutil && \
    sudo apt-get -y remove --purge \
        gcc python3-dev && \
    sudo apt-get autoremove -y --purge && \
    sudo apt-get clean

RUN mkdir /home/hnn_user/hnn_out \
          /home/hnn_user/.ssh

# use environment variables from hnn_envs
RUN echo 'source /home/hnn_user/hnn_envs' >> ~/.bashrc

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

# install NEURON
ARG NEURON_VERSION="7.7"
ADD https://neuron.yale.edu/ftp/neuron/versions/v${NEURON_VERSION}/nrn-${NEURON_VERSION}.x86_64-linux.deb /tmp/nrn.deb
RUN sudo dpkg -i /tmp/nrn.deb && \
    sudo rm -f /tmp/nrn.deb

# install HNN
RUN sudo apt-get update && \
    sudo apt-get install --no-install-recommends -y \
        make gcc libc6-dev libtinfo-dev libncurses-dev \
        libx11-dev libreadline-dev && \
    git clone ${SOURCE_REPO} \
      --depth 1 --single-branch --branch $SOURCE_BRANCH \
      /home/hnn_user/hnn_source_code && \
    cd /home/hnn_user/hnn_source_code && \
    make && \
    sudo apt-get -y remove --purge \
        make gcc libc6-dev libtinfo-dev libncurses-dev \
        libx11-dev libreadline-dev && \
    sudo apt-get autoremove -y --purge && \
    sudo apt-get clean

# NEURON runtime prerequisites
RUN sudo apt-get update && \
    sudo apt-get install --no-install-recommends -y \
        libncurses5 libreadline5 libdbus-1-3 libopenmpi-dev && \
    sudo apt-get clean

COPY QtProject.conf /home/hnn_user/.config/
COPY QtProject.conf /.config/
COPY check_hnn_out_perms.sh /home/hnn_user/
COPY start_hnn.sh /home/hnn_user/
COPY hnn_envs /home/hnn_user/
COPY start_ssh.sh /
COPY check_sshd_port.sh /
COPY check_x_port.sh /

RUN sudo chown -R hnn_user:hnn_group /home/hnn_user/ && \
    sudo chmod +x /home/hnn_user/start_hnn.sh /home/hnn_user/check_hnn_out_perms.sh && \
    sudo chmod +x /check_sshd_port.sh /start_ssh.sh /check_x_port.sh && \
    sudo chown root:root /check_sshd_port.sh /start_ssh.sh /check_x_port.sh && \
    sudo chmod ugo+rw /.config/QtProject.conf && \
    sudo chmod ugo+rwx /.config/

USER root