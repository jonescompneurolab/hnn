#!/bin/bash
set -xe

export TRAVIS_TESTING=1

source scripts/utils.sh
export -f sha256sum

export DOCKER_IMAGE_NAME="jonescompneurolab/hnn:master"
export BASE_QEMU_OPTS="--disable-cocoa --disable-curses --disable-vnc --disable-vde \
                        --disable-pie --disable-libusb --disable-hax --disable-kvm \
                        --disable-debug-info --disable-docs --disable-nettle \
                        --disable-sparse --disable-guest-agent --disable-qom-cast-debug \
                        --disable-lzo --disable-bzip2 --disable-fdt \
                        --disable-tpm --disable-replication --disable-modules --disable-blobs \
                        --disable-gnutls --disable-vhost-crypto --disable-live-block-migration \
                        --disable-user --disable-vhost-net"


# install miniconda, XQuartz, NEURON, docker, qemu

export HOMEBREW_NO_INSTALL_CLEANUP=1
if [[ $BREW_UNTAP -eq 1 ]]; then
brew untap homebrew/versions
fi

if [[ $HOMEBREW_NO_AUTO_UPDATE -eq 0 ]]; then
echo "Updating Homebrew... (will take a while)"
brew update > /dev/null 2>&1 &
elif [[ $TRAVIS_OSX_IMAGE =~ "xcode11.3" ]]; then
# for mojave
brew install pixman jq go &
BREW_PID=$!
fi

echo "Cloning https://github.com/qemu/qemu"
if [[ $HOMEBREW_QEMU -eq 1 ]]; then
git clone --branch stable-3.0 https://github.com/qemu/qemu.git &
elif [[ $BUILD_QEMU -eq 1 ]]; then
git clone --branch stable-4.1 https://github.com/qemu/qemu.git &
fi
GIT_CLONE_PID=$!

URL="https://download.docker.com/mac/stable/Docker.dmg"
FILENAME="$HOME/Docker.dmg"
start_download "$FILENAME" "$URL" &
DOCKER_PID=$!

if [[ -n $BREW_PID ]]; then
echo "Waiting for homebrew to complete..."
NAME="homebrew command"
wait_for_pid ${BREW_PID} "$NAME"
unset BREW_PID
fi

echo "Installing prerequisites for qemu with homebrew..."
if [[ $HOMEBREW_QEMU -eq 1 ]]; then
brew uninstall --ignore-dependencies python
if [[ $TRAVIS_OSX_IMAGE =~ "xcode9.2" ]]; then
    :
    # softwareupdate --install "Command Line Tools (macOS Sierra version 10.12) for Xcode-9.2"
elif [[ $TRAVIS_OSX_IMAGE =~ "xcode8" ]]; then
    brew cask reinstall xquartz
    # DISPLAY updated with current xquartz port number
    # softwareupdate --install "Command Line Tools (macOS El Capitan version 10.11) for Xcode-8.2"
    brew install --ignore-dependencies openssl libffi
fi
sudo chmod -R u+rw /Users/travis/Library/Caches/Homebrew # for el capitan
brew install --ignore-dependencies xz python3 pixman
brew install ninja jq &
BREW_PID=$!
elif [[ $BUILD_QEMU -eq 1 ]]; then
# for high sierra
brew unlink python@2
brew uninstall --ignore-dependencies glib
brew uninstall --ignore-dependencies xz readline
brew install --ignore-dependencies xz readline oniguruma jq &
BREW_PID=$!
fi

URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
FILENAME="$HOME/miniconda.sh"
start_download "$FILENAME" "$URL" &
CONDA_PID=$!

# install miniconda
echo "Waiting for miniconda download to finish"
NAME="downloading Miniconda3-latest-MacOSX-x86_64.sh"
wait_for_pid "${CONDA_PID}" "$NAME"

echo "Installing miniconda..."
chmod +x "$HOME/miniconda.sh"
"$HOME/miniconda.sh" -b -p "${HOME}/miniconda"
export PATH=${HOME}/miniconda/bin:$PATH

# create conda environment
conda create -n hnn --yes python=${PYTHON_VERSION}
source activate hnn && echo "activated conda HNN environment"
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/miniconda/envs/hnn/lib

if [[ $HOMEBREW_QEMU -eq 1 ]] || [[ $BUILD_QEMU -eq 1 ]]; then
echo "Waiting for homebrew to complete..."
NAME="homebrew command"
wait_for_pid "${BREW_PID}" "$NAME"
fi

if [[ $HOMEBREW_QEMU -eq 1 ]]; then
brew install meson --ignore-dependencies
if [[ $TRAVIS_OSX_IMAGE =~ "xcode8" ]]; then
    brew install gettext
fi
brew install --ignore-dependencies glib

# export CFLAGS="-D_POSIX_C_SOURCE=199309L"
export CFLAGS="-D_DARWIN_C_SOURCE -D_POSIX_C_SOURCE=200809L"
elif [[ $BUILD_QEMU -eq 1 ]]; then
QEMU_OPTS="$BASE_QEMU_OPTS --disable-sheepdog --disable-parallels \
            --disable-qed --disable-cloop --disable-bochs --disable-dmg --disable-qcow1 --disable-vdi \
            --disable-vvfat"
brew install --ignore-dependencies glib
fi

# Install qemu, which allows virtual machines to be started without virtualbox.
# This means a Linux VM running docker containers can be started on a mac.
# Running the native docker command on the mac connects to the docker daemon
# running inside the virtual machine to start, stop, run containers.

if [[ $HOMEBREW_QEMU -eq 1 ]] || [[ $BUILD_QEMU -eq 1 ]]; then
echo "Waiting for qemu clone to finish"
NAME="https://github.com/qemu/qemu"
wait_for_pid "${GIT_CLONE_PID}" "$NAME"

echo "Building qemu from source"
command cd qemu && mkdir build && command cd build
../configure --target-list=x86_64-softmmu ${QEMU_OPTS}
make -j2 &
MAKE_PID=$!
fi

mkdir -p "$HOME/.docker/machine/cache"
FILENAME="$HOME/.docker/machine/cache/boot2docker.iso"
URL="https://github.com/boot2docker/boot2docker/releases/latest/download/boot2docker.iso"
start_download "$FILENAME" "$URL" &
boot2docker_PID=$!

URL="https://www.dropbox.com/s/zuo6s1uy89a7tp0/docker-machine-driver-qemu-4.2.tar.gz?dl=1"
FILENAME="$HOME/docker-machine-driver-qemu-4.2.tar.gz"
start_download "$FILENAME" "$URL" &
DOCKER_MACHINE_PID=$!

echo "Waiting for Docker.dmg download to finish"
NAME="downloading Docker.dmg"
wait_for_pid "${DOCKER_PID}" "$NAME"

echo "Started conda in the background to download packages."
conda create -n warm_cache --yes --download-only python=${PYTHON_VERSION} pip openmpi scipy numpy matplotlib pyqtgraph pyopengl psutil > /dev/null 2>&1 &

echo "Installing docker..."
hdiutil attach "$HOME/Docker.dmg"
sudo rsync -a /Volumes/Docker/Docker.app /Applications
export PATH=$PATH:/Applications/Docker.app/Contents/Resources/bin

echo "Waiting for docker-machine-driver-qemu download to finish"
NAME="downloading docker-machine-driver-qemu-4.2.tar.gz"
wait_for_pid "${DOCKER_MACHINE_PID}" "$NAME"
sudo tar -xPf "$HOME/docker-machine-driver-qemu-4.2.tar.gz"

echo "Waiting for boot2docker download to finish"
NAME="downloading boot2docker"
wait_for_pid "${boot2docker_PID}" "$NAME"

URL="https://neuron.yale.edu/ftp/neuron/versions/v${NEURON_VERSION}/nrn-${NEURON_VERSION}.x86_64-osx.pkg"
FILENAME="$HOME/nrn.pkg"
start_download "$FILENAME" "$URL" &
NRN_PID=$!

if [[ $HOMEBREW_QEMU -eq 1 ]] || [[ $BUILD_QEMU -eq 1 ]]; then
echo "Waiting for qemu build to finish"
NAME="building qemu"
wait_for_pid "${MAKE_PID}" "$NAME"

make install
command cd ${TRAVIS_BUILD_DIR}
fi

# create default VM with docker-machine
echo "Starting qemu VM..."
docker-machine -D create --driver qemu --qemu-cache-mode unsafe --qemu-cpu-count 2 default &
export MACHINE_PID=$!

curl -Lo "$HOME/download-frozen-image-v2.sh" https://raw.githubusercontent.com/moby/moby/master/contrib/download-frozen-image-v2.sh
chmod +x "$HOME/download-frozen-image-v2.sh"

download_docker_image "$DOCKER_IMAGE_NAME" &
IMAGE_PID=$!

# install NEURON
echo "Waiting for neuron download to finish"
NAME="downloading NEURON"
wait_for_pid "${NRN_PID}" "$NAME"

echo "Starting NEURON installer..."
sudo installer -pkg "$HOME/nrn.pkg" -target > /dev/null / 2>&1 &
NRN_INSTALL_PID=$!

# create conda environment
conda install -y -n hnn pip openmpi scipy numpy matplotlib pyqtgraph pyopengl psutil
# conda is faster to install nlopt
conda install -y -n hnn -c conda-forge nlopt

pip download flake8 pytest pytest-cov coverage coveralls mne

echo "Waiting for VM to start..."
wait $MACHINE_PID
echo "VM running docker is up"

# set up environment variables to use docker within VM
docker-machine env default >> "$HOME/.bash_profile"
eval "$(docker-machine env default)"

echo "Waiting for HNN docker image download to finish"
NAME="downloading HNN docker image"
wait_for_pid "${IMAGE_PID}" "$NAME"
echo "Loading downloaded image into docker"
(tar -cC "$HOME/docker_image" . | docker load && \
docker tag jonescompneurolab/hnn:master jonescompneurolab/hnn:latest && \
touch $HOME/docker_image_loaded) &

# hack so that NEURON install doesn't take forever
sudo kill -9 $NRN_INSTALL_PID && wait $NRN_INSTALL_PID || {
if [[ $? -eq 137 ]]; then
    echo "NEURON installer successful"
else
    echo "NEURON installer unknown"
fi
}

echo "Install finished"