#!/bin/bash

echo "HNN container has started. To start the HNN GUI run the following command:"
echo "docker exec hnn_container /home/hnn_user/start_hnn.sh"

/usr/sbin/sshd -D
