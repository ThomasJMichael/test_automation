#!/bin/bash

DHCP_TEMPLATE="/vagrant_shared/docker/cobbler/volumes/var/lib/cobbler/config/dhcp.template"
SETTINGS_YAML="/vagrant_shared/docker/cobbler/volumes/var/lib/cobbler/config/settings.yaml"
JSON_FILE="/vagrant_share/docker/cobbler/cobbler_config.json"

if [ ! -f $DHCP_TEMPLATE ] || [ ! -f $SETTINGS_YAML ] || [ ! -f $JSON_FILE ]; then
    echo "Configuration files not found!"
    exit 1
fi

# Extract values from the JSON file
DHCP_SERVER=$(jq -r '.dhcp_server' $JSON_FILE)
DHCP_RANGE=$(jq -r '.dhcp_range' $JSON_FILE)
DHCP_SUBNET=$(jq -r '.dhcp_subnet' $JSON_FILE)
DHCP_NETMASK=$(jq -r '.dhcp_netmask' $JSON_FILE)

# Check if jq commands were successful
if [ $? -ne 0 ]; then
    echo "Error reading from JSON file."
    exit 1
fi

# Modify the configuration files
sed -i "s/192.168.1.100 192.168.1.254/$DHCP_RANGE/g" $DHCP_TEMPLATE
sed -i "s/192.168.1.5;/$DHCP_SERVER;/g" $DHCP_TEMPLATE
sed -i "s/192.168.1.1;/$DHCP_SERVER;/g" $DHCP_TEMPLATE
sed -i "s/192.168.1.0/$DHCP_SUBNET/g" $DHCP_TEMPLATE
sed -i "s/255.255.255.0/$DHCP_NETMASK/g" $DHCP_TEMPLATE
sed -i 's/grubx86/grubx64/g' $SETTINGS_YAML
sed -i 's/manage_dhcp: false/manage_dhcp: true/g' $SETTINGS_YAML
sed -i 's/manage_dhcp_v4: false/manage_dhcp_v4: true/g' $SETTINGS_YAML

echo "Configuration files updated successfully!"
