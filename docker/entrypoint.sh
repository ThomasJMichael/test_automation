#!/bin/bash
set -e
dnf install -y /cobbler-3.3.3-1.el8.noarch.rpm
(
sleep 10
# Start cobblerd
systemctl enable --now cobblerd
sleep 5
cobbler sync
cobbler mkloaders

systemctl restart tftp.service

tail -n +1 -f /var/log/cobbler/cobbler.log

) & 
exec /usr/sbin/init