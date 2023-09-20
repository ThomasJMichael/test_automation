#!/bin/bash

# This script instructs the dhcp client to use MAC address as client identifier
# when requesting an ip address and makes outbound traffic prioritize
# a ceratin ethernet interface

NETPLAN_CONF="/etc/netplan/50-vagrant.yaml"
ETH_INTERFACE="eth2" # Cobbler Network Interface

# Check if the Netplan configuration file exists
if [ ! -f "$NETPLAN_CONF" ]; then
    echo "Netplan configuration file not found at $NETPLAN_CONF"
    exit 1
fi

# Modify the Netplan configuration to use MAC as the DHCP identifier
sudo sed -i "s/$ETH_INTERFACE:/$ETH_INTERFACE:\n      dhcp-identifier: mac\n      dhcp4-overrides:\n        route-metric: 90/g" "$NETPLAN_CONF"

sudo netplan apply

# Wait for a few seconds to ensure network changes are applied
sleep 10

# Verify the changes
if ip a | grep -q "$ETH_INTERFACE"; then
    echo "Interface $ETH_INTERFACE is active."
else
    echo "Interface $ETH_INTERFACE is not active. Something went wrong."
    exit 1
fi

# Check the route metric
ROUTE_METRIC=$(ip route | grep "$ETH_INTERFACE" | awk '{print $9}')
if [ "$ROUTE_METRIC" == "90" ]; then
    echo "Route metric for $ETH_INTERFACE is set to 90 as expected."
else
    echo "Route metric for $ETH_INTERFACE is not set to 90. Current metric: $ROUTE_METRIC"
    exit 1
fi

echo "All checks passed!"
