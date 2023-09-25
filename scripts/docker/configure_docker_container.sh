#!/bin/bash

DHCP_TEMPLATE="/etc/cobbler/dhcp.template"
SETTINGS_YAML="/etc/cobbler/settings.yaml"
JSON_FILE="host.json"

if [ ! -f $DHCP_TEMPLATE ]; then
    echo "DHCP template file not found!"
    exit 1
fi

if [ ! -f $SETTINGS_YAML ]; then
    echo "Settings YAML file not found!"
    exit 1
fi

if [ ! -f $JSON_FILE ]; then
    echo "JSON file not found!"
    exit 1
fi


dnf install -y jq

# Extract values from the JSON file
DHCP_SERVER=$(jq -r '.dhcp_server' $JSON_FILE)
DHCP_RANGE=$(jq -r '.dhcp_range' $JSON_FILE)
DHCP_SUBNET=$(jq -r '.dhcp_subnet' $JSON_FILE)
DHCP_NETMASK=$(jq -r '.dhcp_netmask' $JSON_FILE)
PASSWORD=$(jq -r '.container_password' $JSON_FILE)

# Check if jq last command was successful
if [ $? -ne 0 ]; then
    echo "Error reading from JSON file."
    exit 1
fi

CRYPTED_PASSWORD=$(openssl passwd -1 "$PASSWORD")
sed -i "s#^default_password.*#default_password_crypted: \"$CRYPTED_PASSWORD\"#g" $SETTINGS_YAML

# Modify the configuration files
sed -i "s/127.0.0.1/$DHCP_SERVER/g" $SETTINGS_YAML
sed -i "s/192.168.1.100 192.168.1.254/$DHCP_RANGE/g" $DHCP_TEMPLATE
sed -i "s/192.168.1.5;/$DHCP_SERVER;/g" $DHCP_TEMPLATE
sed -i "s/192.168.1.1;/$DHCP_SERVER;/g" $DHCP_TEMPLATE
sed -i "s/192.168.1.0/$DHCP_SUBNET/g" $DHCP_TEMPLATE
sed -i "s/255.255.255.0/$DHCP_NETMASK/g" $DHCP_TEMPLATE
sed -i 's/grubx86/grubx64/g' $SETTINGS_YAML
sed -i 's/manage_dhcp: false/manage_dhcp: true/g' $SETTINGS_YAML
sed -i 's/manage_dhcp_v4: false/manage_dhcp_v4: true/g' $SETTINGS_YAML

echo "Configuration files updated successfully!"
