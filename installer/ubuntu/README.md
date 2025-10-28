# Installing HNN via Python on Ubuntu Linux

**Note**: these are instructions for installing the *original* version of HNN, which is **no longer actively-developed**, and only made available for scientific reproducibility. If you are reading this, you probably want to be using the actively-developed version, called *HNN-Core*, which is [available here](https://github.com/jonescompneurolab/hnn-core).

These instructions were last successfully testing in September 2025, using Kubuntu 24.04 and Linux Mint 21.2 Cinnamon.

## 1) Install system packages

First, open a terminal program and update the following system packages using a command like the following:

```bash
sudo apt-get update
sudo apt-get install --no-install-recommends -y \
    make gcc g++ \
    openmpi-bin lsof \
    libfontconfig1 libxext6 libx11-xcb1 libxcb-glx0 \
    libxkbcommon-x11-0 libgl1-mesa-dev \
    libncurses6 libreadline8 libdbus-1-3 libopenmpi-dev \
    libc6-dev libtinfo-dev libncurses-dev \
    libx11-dev libreadline-dev \
    libxcb-icccm4 libxcb-util1 libxcb-image0 libxcb-keysyms1 \
    libxcb-render0 libxcb-shape0 libxcb-randr0 libxcb-render-util0 \
    libxcb-xinerama0 libxcb-xfixes0
```

## 2) Install Python and Python dependencies

We recommend installing Python via the [Anaconda Distribution](https://www.anaconda.com/download/success), but any virtual environment tool should work. Create a new virtual environment and enter it. (If you are new to Python virtual environments, see [https://www.anaconda.com/docs/getting-started/getting-started](https://www.anaconda.com/docs/getting-started/getting-started)).

We recommend you use Python 3.8. Python version 3.10 or later is unlikely to work.

Once you are inside your environment, install the following packages from pip using a command like the following:

```bash
pip install --no-cache-dir \
    NEURON matplotlib PyOpenGL \
    pyqt5 pyqtgraph scipy numpy nlopt psutil
```

## 3) Download HNN code and compile mechanisms

Next, you need to download and unpack the HNN release. Note that these files are NOT the same as cloning the `hnn` repository! Once you `cd` into the directory of your choosing, you can run the following command to download, extract, and compile the NEURON mechanisms of the HNN code:

```bash
curl -sOL https://github.com/jonescompneurolab/hnn/releases/latest/download/hnn.tar.gz
tar -x --strip-components 1 -f hnn.tar.gz --one-top-level=hnn_source_code
cd hnn_source_code
make
```

## 4) Run HNN

Finally, once you have done all of the above, you can start the HNN-GUI using the following command:

```bash
python hnn.py
```

## Troubleshooting

If you have issues with the above installation method, you can view older but different install methods at [this link here](2021_instructions). You can also try downloading [Docker Desktop](https://www.docker.com/products/docker-desktop/), downloading git (`sudo apt-get install git`), then using the HNN Docker image by following the instructions starting with "Part 4" from this comment: https://github.com/jonescompneurolab/hnn/pull/337#issuecomment-1799006204 .
