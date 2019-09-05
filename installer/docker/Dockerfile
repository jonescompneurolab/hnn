FROM caldweba/opengl-docker

# avoid questions from debconf
ENV DEBIAN_FRONTEND noninteractive

# create the group hnn_group and user hnn_user
# add hnn_user to the sudo group
RUN groupadd hnn_group && useradd -m -b /home/ -g hnn_group hnn_user && \
    adduser hnn_user sudo && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers && \
    chown -R hnn_user:hnn_group /home/hnn_user

COPY date_base_install.sh /usr/local/bin
RUN chmod +x /usr/local/bin/date_base_install.sh && \
    /usr/local/bin/date_base_install.sh

USER hnn_user

# allow user to specify architecture if different than x86_64
ARG CPU=x86_64
# supply the path NEURON binaries for building hnn
ENV PATH=${PATH}:/home/hnn_user/nrn/build/$CPU/bin

# create the global session variables
RUN echo '# these lines define global session variables for HNN' >> ~/.bashrc && \
    echo 'export CPU=$(uname -m)' >> ~/.bashrc && \
    echo 'export PATH=$PATH:/home/hnn_user/nrn/build/$CPU/bin' >> ~/.bashrc && \
    echo 'export PYTHONPATH=/home/hnn_user/nrn/build/lib/python' >> ~/.bashrc && \
    echo 'export OMPI_MCA_mpi_warn_on_fork=0' >> ~/.bashrc && \
    echo 'export OMPI_MCA_btl_openib_allow_ib=1' >> ~/.bashrc

# run sudo to get rid of message on first login about using sudo
RUN sudo -l

CMD /home/hnn_user/start_hnn.sh

# compile NEURON, only temporarily installing packages for building
RUN sudo apt-get update && \
    sudo apt-get install -y git python3-dev python3-pip python3-psutil \
                       bison flex automake libtool libncurses-dev zlib1g-dev \
                       libopenmpi-dev openmpi-bin libqt5core5a libllvm6.0 \
                       libxaw7 libxmu6 libxpm4 libxcb-glx0 \
                       libxkbcommon-x11-0 libfontconfig libx11-xcb1 libxrender1 \
                       git vim iputils-ping net-tools iproute2 nano sudo \
                       telnet language-pack-en-base && \
    sudo pip3 install pip --upgrade && \
    sudo pip install PyOpenGL matplotlib pyqt5 pyqtgraph scipy numpy nlopt && \
    sudo rm -rf /home/hnn_user/.cache && \
    cd /home/hnn_user/ && \
    mkdir nrn && \
    cd nrn && \
    git clone https://github.com/neuronsimulator/nrn src && \
    cd /home/hnn_user/nrn/src && \
    ./build.sh && \
    ./configure --with-nrnpython=python3 --with-paranrn --disable-rx3d \
      --without-iv --without-nrnoc-x11 --with-mpi \
      --prefix=/home/hnn_user/nrn/build && \
    make -j4 && \
    make install -j4 && \
    cd src/nrnpython && \
    python3 setup.py install --user && \
    cd /home/hnn_user/nrn/ && \
    rm -rf src && \
    sudo apt-get -y remove --purge bison flex python3-dev zlib1g-dev && \
    sudo apt-get autoremove -y --purge && \
    sudo apt-get clean

# copy the start script into the container
COPY start_hnn.sh /home/hnn_user/
RUN sudo chown hnn_user:hnn_group /home/hnn_user/start_hnn.sh && \
    sudo chmod +x /home/hnn_user/start_hnn.sh

RUN mkdir /home/hnn_user/hnn_out

ARG BUILD_DATE
ARG VCS_REF
ARG VCS_TAG

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/jonescompneurolab/hnn.git" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.schema-version=$VCS_TAG

RUN cd /home/hnn_user && \
    git clone https://github.com/jonescompneurolab/hnn.git \
      --single-branch --branch $SOURCE_BRANCH hnn_source_code && \
    cd hnn_source_code && \
    make

# if users open up a shell, they should go to the hnn repo checkout
WORKDIR /home/hnn_user/hnn_source_code
