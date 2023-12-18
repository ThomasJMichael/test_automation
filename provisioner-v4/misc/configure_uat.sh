#!/bin/bash
# $1 json file
set -x
system_name=$(jq -r ".uat_name" $1)
ipaddr=$(jq -r ".uat_ip_address" $1)
mac_address=$(jq -r ".uat_address" $1)
netdev=$(jq -r ".uat_netdev" $1)
proxy=$(jq -r ".gateway" $1)

mac=$(echo "$mac_address" | sed 's/.*/\L&/')

sudo docker inspect -f '{{.State.Running}}' cobbler
if [ $? -eq 0 ];
then
    echo "Cobbler running"
    sudo docker exec -it cobbler cobbler system remove --name=${system_name}_uat_system
    sudo docker exec -it cobbler cobbler profile remove --name=${system_name}_profile
    sudo docker exec -it cobbler cobbler distro remove --name=${system_name}_distro
    sudo docker exec -it cobbler cobbler distro add --name=${system_name}_distro --kernel=/storage/baseimgs/vmlinuz_${system_name} --initrd=/storage/baseimgs/initrd_${system_name}.cgz
    sudo docker exec -it cobbler cobbler profile add --name=${system_name}_profile --distro=${system_name}_distro
    sudo docker exec -it cobbler cobbler system add --name=${system_name}_uat_system --profile=${system_name}_profile
    sudo docker exec -it cobbler cobbler system edit --name=${system_name}_uat_system --mac=${mac} --filename="grub/grubx64.efi" --ip-address=${ipaddr} --netmask="255.255.255.0" --static=1 --netboot-enabled=true --interface=$netdev --gateway=$proxy --kernel-options="console=tty0 console=ttyS0,115200,8,n,1" --host=${system_name}_uat_system
fi
echo "Ubuntu DHCP?"
sudo systemctl show -p SubState --value isc-dhcp-server
# Copy new grub config file
sudo cp /storage/baseimgs/vmlinuz_${system_name} /srv/tftp/boot/
sudo cp /storage/baseimgs/initrd_${system_name}.cgz /srv/tftp/boot/
sudo cp /srv/tftp/grub/grub.cfg.uattemplate /srv/tftp/grub/${mac}
sudo sed -i "s/VMLINUZ/vmlinuz_${system_name}/g" /srv/tftp/grub/${mac}
sudo sed -i "s/INITRD/initrd_${system_name}.cgz/g" /srv/tftp/grub/${mac}
sudo sed -i "s/IPADDR/${ipaddr}/g" /srv/tftp/grub/${mac}
sudo sed -i "s/GATEWAY/${proxy}/g" /srv/tftp/grub/${mac}
sudo sed -i "s/NETDEV/${netdev}/g" /srv/tftp/grub/${mac}
