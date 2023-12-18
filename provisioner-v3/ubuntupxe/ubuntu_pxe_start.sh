#!/bin/bash
sudo systemctl start apache2
sudo systemctl start isc-dhcp-server
sudo systemctl start tftpd-hpa

