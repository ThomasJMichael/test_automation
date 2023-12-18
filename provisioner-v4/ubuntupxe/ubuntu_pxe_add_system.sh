#!/bin/bash
# $1 json file
# $2 distro
system_name=$(jq -r ".system_name" $1)
ipaddr=$(jq -r ".ip_address" $1)
mac_address=$(jq -r ".mac_address" $1)
netdev=$(jq -r ".ub_netdev" $1)
proxy=$(jq -r ".gateway" $1)
user=$(jq -r ".dev_username" $1)
installdev=$(jq -r ".installdev" $1)
token=$(echo $ATLAS_TOKEN)

mac=$(echo "$mac_address" | sed 's/.*/\L&/')
# Check if ISO exists at apache base, if not copy
echo "Check ISO"
if [[ ! -f /var/www/html/${2}.iso ]]; then
        echo "Import ISO"
        sudo cp /storage/baseimgs/${2}.iso /var/www/html/
        sudo mkdir -p /var/www/html/${2}
        sudo touch /var/www/html/${2}/meta-data
fi

# Check if distro exists under tftp folder, if not copy
echo "Check kernel"
if [[ ! -d /srv/tftp/boot/${2} ]]; then
        echo "Import kernel"
        sudo mkdir -p /srv/tftp/boot/${2}
        sudo mount -o loop /storage/baseimgs/${2}.iso /mnt
        echo "Copy kernel and fs to TFTP server /srv/tftp/boot/${2}/"
        sudo cp /mnt/casper/vmlinuz /srv/tftp/boot/${2}/
        sudo cp /mnt/casper/initrd /srv/tftp/boot/${2}/
        sudo umount /mnt
fi

# Copy new grub config file
sudo cp /srv/tftp/grub/grub.cfg.template /srv/tftp/grub/${mac}
sudo sed -i "s/DISTRO/${2}/g" /srv/tftp/grub/${mac}

sudo cp /home/vagrant/provisioner-v3/ubuntupxe/user-data.template /var/www/html/${2}/user-data
sudo sed -i "s/HOSTNAME/$system_name/g" /var/www/html/${2}/user-data
sudo sed -i "s/ETHNAME/$netdev/g" /var/www/html/${2}/user-data
sudo sed -i "s/ETHADDR/$ipaddr/g" /var/www/html/${2}/user-data
sudo sed -i "s/NETMASK/24/g" /var/www/html/${2}/user-data
sudo sed -i "s/PROXY/$proxy/g" /var/www/html/${2}/user-data
sudo sed -i "s/USER/$user/g" /var/www/html/${2}/user-data
sudo sed -i "s/INSTALLDEV/$installdev/g" /var/www/html/${2}/user-data
sudo sed -i "s/TOKEN/$token/g" /var/www/html/${2}/user-data
cat /var/www/html/${2}/user-data

