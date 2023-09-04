#!/bin/bash

# Start cobblerd
systemctl start cobblerd

# Start other services as needed
systemctl start httpd
systemctl start dhcpd
systemctl start tftp
systemctl start rsyncd

# Keep the container running
exec /usr/sbin/init
