#!/bin/bash

# set permissions for these files in case they were copied in by the
# start script since last start
if [ -e "/home/hnn_user/.ssh/authorized_keys" ]; then
    chown hnn_user /home/hnn_user/.ssh/authorized_keys
    chmod 600 /home/hnn_user/.ssh/authorized_keys
fi
if [ -e "/home/hnn_user/.ssh/known_hosts" ]; then
    chown hnn_user:hnn_group /home/hnn_user/.ssh/known_hosts
fi

echo "HNN container has started. To start the HNN GUI run the following command:"
echo "docker exec hnn_container /home/hnn_user/start_hnn.sh"

/usr/sbin/sshd -D
