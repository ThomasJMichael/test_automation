#!/bin/bash

PROVISIONER_DIR="/vagrant_shared/provisioner-v3"
HOST_JSON="/vagrant_shared/config/host.json"

if [ ! -f $HOST_JSON ]; then
    echo "host.json file not found at $HOST_JSON. Exiting."
    exit 1
fi

RANGE=$(jq -r ".dhcp_range" $HOST_JSON)
SERVER=$(jq -r ".dhcp_server" $HOST_JSON)
SUBNET=$(jq -r ".dhcp_subnet" $HOST_JSON)
NETMASK=$(jq -r ".dhcp_netmask" $HOST_JSON)

# Check if jq commands were successful
if [ $? -ne 0 ]; then
    echo "Error reading from JSON file."
    exit 1
fi

install_provisioner(){
    cd $PROVISIONER_DIR
    sudo python3 setup.py install
    
    if [ $? -ne 0 ]; then
        echo "Error installing provisioner tools. Exiting." 
        exit 1
    fi

    cd -
}

install_tftp_dhcp(){
    sudo apt install -y isc-dhcp-server apache2 tftpd-hpa grub-efi-amd64-bin
}

setup_tftp_for_pxe(){
    mkdir -p /srv/tftp
    chmod -R 777 /srv/tftp
    chown -R nobody /srv/tftp

    mkdir -p /srv/tftp/boot/grub
    mkdir -p /srv/tftp/boot/fonts

    cd /srv/tftp && ln -s boot/grub grub

    sudo grub-mknetdir --net-directory /srv/tftp/
    curl -O http://archive.ubuntu.com/ubuntu/dists/jammy/main/uefi/grub2-amd64/current/grubnetx64.efi.signed
    cp grubnetx64.efi.signed /srv/tftp/boot/bootx64.efi
}

copy_and_config_tftp_dhcp(){
    cp $PROVISIONER_DIR/ubuntupxe/grub.cfg.template /srv/tftp/boot/grub/
    cp $PROVISIONER_DIR/misc/grub.cfg.uattemplate /srv/tftp/boot/grub/
    cp $PROVISIONER_DIR/ubuntupxe/grub.cfg /srv/tftp/boot/grub/
    sudo cp $PROVISIONER_DIR/ubuntupxe/dhcpd.conf.template /etc/dhcp/dhcpd.conf

    # Add host.json values into tftp/dhcp config
    sudo sed -i "s/SERVER/$SERVER/g" /srv/tftp/boot/grub/grub.cfg.template
    sudo sed -i "s/SERVER/$SERVER/g" /etc/dhcp/dhcpd.conf
    sudo sed -i "s/RANGE/$RANGE/g" /etc/dhcp/dhcpd.conf
    sudo sed -i "s/SUBNET/$SUBNET/g" /etc/dhcp/dhcpd.conf
    sudo sed -i "s/NETMASK/$NETMASK/g" /etc/dhcp/dhcpd.conf
}

setup_provisioner_scripts(){
    # Currently copying scripts from provisiner but I want to
    # redo the implementaton of the scripts in the future
    # and move the scripts to a /scripts/provisoner/ directory
    sudo cp $PROVISIONER_DIR/ubuntupxe/*.sh /vagrant_shared/scripts
    sudo cp $PROVISIONER_DIR/misc/*.sh /vagrant_shared/scripts

    # Make all the scripts executable
    sudo chmod +x /vagrant_shared/scripts/*.sh
}

stop_tftp_dhcp_service(){
    /vagrant_shared/scripts/ubuntu_pxe_stop.sh
}

main(){
    install_provisioner
    install_tftp_dhcp
    setup_tftp_for_pxe
    copy_and_config_tftp_dhcp
    setup_provisioner_scripts
    stop_tftp_dhcp_service
}

main