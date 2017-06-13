#!/bin/bash
export CPU = $(uname -m)
export PATH=$PATH:/usr/lib64/openmpi/bin:/usr/local/nrn/$CPU/bin
python3 hnn.py hnn.cfg
