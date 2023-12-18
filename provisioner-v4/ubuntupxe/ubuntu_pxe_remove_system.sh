#!/bin/bash
# $1 json
mac_address=$(jq -r ".mac_address" $1)
mac=$(echo "$mac_address" | sed 's/.*/\L&/')
echo "Removing /srv/tftp/grub/${mac}"
sudo rm /srv/tftp/grub/${mac}

