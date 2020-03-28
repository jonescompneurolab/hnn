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
RUN apt-get install --no-install-recommends -y \
        python3-pip python3-setuptools openssh-server openmpi-bin lsof && \
    apt-get clean

COPY date_base_install.sh /usr/local/bin
RUN chmod +x /usr/local/bin/date_base_install.sh && \
    /usr/local/bin/date_base_install.sh

RUN mkdir /var/run/sshd

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
RUN sed 's/AcceptEnv.*/AcceptEnv LANG LC_* DISPLAY/' -i /etc/ssh/sshd_config

# if users open up a shell, they should go to the hnn repo checkout
WORKDIR /home/hnn_user/hnn_source_code
RUN chown -R hnn_user:hnn_group /home/hnn_user

USER hnn_user

# get HNN python dependencies
# python3-dev and gcc needed for building psutil
RUN sudo pip3 install --no-cache-dir --upgrade pip && \
    sudo apt-get install --no-install-recommends -y \
        gcc python3-dev && \
    pip install --no-cache-dir --user matplotlib PyOpenGL \
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

CMD /home/hnn_user/start_hnn.sh

# use args to avoid caching
ARG BUILD_DATE
ARG VCS_REF
ARG VCS_TAG
ARG SOURCE_BRANCH

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/jonescompneurolab/hnn.git" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.schema-version=$VCS_TAG

# install NEURON
RUN wget -q https://neuron.yale.edu/ftp/neuron/versions/v7.7/nrn-7.7.x86_64-linux.deb -O /tmp/nrn.deb && \
    sudo dpkg -i /tmp/nrn.deb && \
    rm -f /tmp/nrn.deb

# install HNN
RUN sudo apt-get install --no-install-recommends -y \
        make gcc libc6-dev libtinfo-dev libncurses-dev \
        libx11-dev libreadline-dev && \
    cd /home/hnn_user && \
    git clone https://github.com/jonescompneurolab/hnn.git \
        --depth 1 --single-branch --branch $SOURCE_BRANCH hnn_source_code && \
    cd hnn_source_code && \
    make && \
    sudo apt-get -y remove --purge \
        make gcc libc6-dev libtinfo-dev libncurses-dev \
        libx11-dev libreadline-dev && \
    sudo apt-get autoremove -y --purge && \
    sudo apt-get clean

# NEURON runtime prerequisites
RUN sudo apt-get install --no-install-recommends -y \
        libncurses5 libreadline5 libdbus-1-3 libopenmpi-dev && \
    sudo apt-get clean

# copy the start script into the container
COPY start_hnn.sh /home/hnn_user/
COPY hnn_envs /home/hnn_user/
COPY start_ssh.sh /
RUN sudo chown hnn_user:hnn_group /home/hnn_user/start_hnn.sh && \
    sudo chmod +x /home/hnn_user/start_hnn.sh && \
    sudo chown root:root /start_ssh.sh && \
    sudo chmod +x /start_ssh.sh && \
    sudo chown hnn_user:hnn_group /home/hnn_user/hnn_envs
