FROM ubuntu:18.04

# avoid questions from debconf
ENV DEBIAN_FRONTEND noninteractive

# packages neded for NEURON and graphics
# - Includes fixes the issue where importing OpenGL in python throws an error
#    (I assume that this works by installing the OpenGL for qt4 and then updating? it's not clear...)
#    I think that this is an error in the repos, not our fault.
# - These packages are needed for X display libxaw7 libxmu6 libxpm4
RUN apt-get update && \
    apt-get install -y git python3-pyqt5 python3-pip python3-pyqtgraph \
                       python3-opengl zlib1g-dev zlib1g zlibc libx11-dev mercurial \
                       bison flex automake libtool libxext-dev libncurses-dev \
                       python3-dev xfonts-100dpi cython libopenmpi-dev python3-scipy \
                       python3-pyqt4.qtopengl libxaw7 libxmu6 libxpm4 \
                       git vim iputils-ping net-tools iproute2 nano sudo \
                       telnet && \
    apt-get remove -y python3-matplotlib

# use pip for matplotlib to get latest version (2.x) since apt-get was using older
# version (1.5) which does not have set_facecolor
# make sure matplotlib version 2 is used -- is this strictly needed?
RUN pip3 install PyOpenGL matplotlib && \
    pip3 install --upgrade PyOpenGL matplotlib

# create the group hnn_group and user hnn_user
RUN groupadd hnn_group && useradd -m -b /home/ -g hnn_group hnn_user

# add hnn_user to the sudo group
RUN adduser hnn_user sudo && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# copy the start script into the container
COPY start_hnn.sh /home/hnn_user/
RUN sudo chown hnn_user:hnn_group /home/hnn_user/start_hnn.sh && \
    sudo chmod +x /home/hnn_user/start_hnn.sh

USER hnn_user
# install NEURON dependencies
RUN cd /home/hnn_user && \
    git clone https://github.com/neuronsimulator/nrn && \
    git clone https://github.com/neuronsimulator/iv

RUN cd /home/hnn_user/iv && \
    git checkout d4bb059 && \
    ./build.sh && \
    ./configure --prefix=/home/hnn_user/iv/build && \
    make -j4 && \
    make install -j4
RUN cd /home/hnn_user/nrn && \
    ./build.sh && \
    ./configure --with-nrnpython=python3 --with-paranrn --disable-rx3d \
      --with-iv=/home/hnn_user/iv/build --prefix=/home/hnn_user/nrn/build && \
    make -j4 && \
    make install -j4 && \
    cd src/nrnpython && \
    python3 setup.py install --user

# create the global session variables
RUN echo '# these lines define global session variables for HNN' >> ~/.bashrc && \
    echo 'export CPU=$(uname -m)' >> ~/.bashrc && \
    echo 'export PATH=$PATH:/home/hnn_user/nrn/build/$CPU/bin' >> ~/.bashrc

# allow user to specify architecture if different than x86_64
ARG CPU=x86_64
# supply the path NEURON binaries for building hnn
ENV PATH=${PATH}:/home/hnn_user/nrn/build/$CPU/bin

# setup HNN itself
# HNN repo from github - moved to github on April 8, 2018
RUN cd /home/hnn_user && \
    git clone https://github.com/jonescompneurolab/hnn.git hnn_repo
# make compiles the mod files
RUN cd /home/hnn_user/hnn_repo && \
    make

# cleanup these folders
RUN cd /home/hnn_user/iv && \
    make clean && \
    cd /home/hnn_user/nrn && \
    make clean

# run sudo to get rid of message on first login about using sudo
RUN sudo -l

# create the hnn shared folder (don't rely on docker daemon
# to create it)
RUN mkdir /home/hnn_user/hnn

# if users open up a shell, they should go to the hnn repo checkout
WORKDIR /home/hnn_user

CMD /home/hnn_user/start_hnn.sh
