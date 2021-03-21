#!/bin/bash
set -e

export PATH=/usr/bin:/usr/local/bin:$PATH

echo "Starting fake Xserver"
Xvfb $DISPLAY -listen tcp -screen 0 1024x768x24 > /dev/null &

echo "Starting Ubuntu install script"
installer/ubuntu/hnn-ubuntu.sh

# test X server
xset -display $DISPLAY -q > /dev/null;
