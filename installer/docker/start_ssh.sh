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

debug=
if [[ "$DEBUG" = "1" ]]; then
  debug="-d"
fi
/usr/sbin/sshd ${debug} -E /tmp/sshd.log
