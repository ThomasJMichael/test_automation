#!/bin/bash
set -e
dnf install -y /cobbler-3.3.3-1.el8.noarch.rpm

./configure_docker_container.sh

(
    sleep 5
    systemctl enable --now cobblerd
    sleep 5
    cobbler sync
    cobbler mkloaders
    cobbler signature update
    systemctl restart tftp.service

    tail -n +1 -f /var/log/cobbler/cobbler.log
) &
exec /usr/sbin/init 