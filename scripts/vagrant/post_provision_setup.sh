#!/bin/bash

json_file="/home/vagrant/cobbler.json"
json_host="/home/vagrant/host.json"
provisioned="/home/vagrant/post-provisioned"

range=$(jq -r ".dhcp_range" $json_host)
server=$(jq -r ".dhcp_server" $json_host)
subnet=$(jq -r ".dhcp_subnet" $json_host)
netmask=$(jq -r ".dhcp_netmask" $json_host)
dockername=$(jq -r ".docker" $json_file)

download_file() {
    local url="$1"
    local dest="$2"
    echo "Downloading $url to $dest"
    sudo curl --retry 10 -ubuild:${ATLAS_TOKEN} -o "$dest" "$url"
}

compare_md5() {
    local url="$1"
    local file="$2"
    local md5url=$(curl -ubuild:${ATLAS_TOKEN} -Is "$url" | grep Md5 | cut -f2 -d' ' | tr '\r' ' ')
    local md5file=$(cat "$file" | cut -f1 -d' ')
    [ "$md5url" == "$md5file" ]
}

setup_environment() {
    if [[ ! -f $provisioned ]]; then

        # Clone provisioner tool
        git_url=$(jq -r ".provisioner_url" $json_file)
        git_branch=$(jq -r ".provisioner_branch" $json_file)
        git clone $git_url
        cd provisioner-v3
        git checkout $git_branch
        # Setup provisioner tool
        sudo python3 setup.py install
        
        # Install necessary packages
        sudo apt install -y isc-dhcp-server apache2 tftpd-hpa grub-efi-amd64-bin
        
        # Setup TFTP for pxe booting
        mkdir -p /srv/tftp
        chmod -R 777 /srv/tftp
        chown -R nobody /srv/tftp
        mkdir -p /srv/tftp/boot/grub
        mkdir -p /srv/tftp/boot/fonts
        cd /srv/tftp && ln -s boot/grub grub
        sudo grub-mknetdir --net-directory /srv/tftp/
        curl -O http://archive.ubuntu.com/ubuntu/dists/jammy/main/uefi/grub2-amd64/current/grubnetx64.efi.signed
        cp grubnetx64.efi.signed /srv/tftp/boot/bootx64.efi

        # Copy DHCP/TFTP files for provisioner library to appropriate location
        cp /home/vagrant/provisioner-v3/ubuntupxe/unicode.pf2 /srv/tftp/boot/fonts/
        cp /home/vagrant/provisioner-v3/ubuntupxe/grub.cfg.template /srv/tftp/boot/grub/
        cp /home/vagrant/provisioner-v3/misc/grub.cfg.uattemplate /srv/tftp/boot/grub/
        cp /home/vagrant/provisioner-v3/ubuntupxe/grub.cfg /srv/tftp/boot/grub/	
        sudo cp /home/vagrant/provisioner-v3/ubuntupxe/dhcpd.conf.template /etc/dhcp/dhcpd.conf

        # Add host.json values into tftp/dhcp config
        sudo sed -i "s/SERVER/$server/g" /srv/tftp/boot/grub/grub.cfg.template
        sudo sed -i "s/SERVER/$server/g" /etc/dhcp/dhcpd.conf
        sudo sed -i "s/RANGE/$range/g" /etc/dhcp/dhcpd.conf
        sudo sed -i "s/SUBNET/$subnet/g" /etc/dhcp/dhcpd.conf
        sudo sed -i "s/NETMASK/$netmask/g" /etc/dhcp/dhcpd.conf

        # Copy scripts from provisioner library to bin
        sudo cp /home/vagrant/provisioner-v3/dockerscripts/*.sh /usr/local/bin
        sudo cp /home/vagrant/provisioner-v3/ubuntupxe/*.sh /usr/local/bin
        sudo cp /home/vagrant/provisioner-v3/misc/*.sh /usr/local/bin

        # Make all the scripts executable
        sudo chmod +x /usr/local/bin/*.sh

        # Change all of the values in the scripts to reflect host.json
        sudo sed -i "s/VAR_SERVER/$server/g" /usr/local/bin/cobbler_start.sh
        sudo sed -i "s/VAR_RANGE/$range/g" /usr/local/bin/cobbler_start.sh
        sudo sed -i "s/VAR_SUBNET/$subnet/g" /usr/local/bin/cobbler_start.sh
        sudo sed -i "s/VAR_NETMASK/$netmask/g" /usr/local/bin/cobbler_start.sh
        sudo sed -i "s/VAR_DOCKERNAME/$dockername/g" /usr/local/bin/cobbler_start.sh
        
        # Stop TFTP/DHCP services
        /usr/local/bin/ubuntu_pxe_stop.sh

        touch $provisioned
    fi
}

download_distros() {
    for k in $(jq '.distros | keys | .[]' $json_file); do
        local name=$(jq -r ".distros[$k].name" $json_file)
        local url=$(jq -r ".distros[$k].url" $json_file)
        local dest="/storage/baseimgs/${name}.iso"
        local md5dest="/storage/baseimgs/${name}.md5"

        echo "Processing $name / $url"

        if [ -f "$dest" ] && compare_md5 "$url" "$md5dest"; then
            echo "$name is up to date."
        else
            download_file "$url" "$dest"
            md5sum "$dest" | sudo tee "$md5dest"
        fi
    done
}

download_uat() {
    for k in $(jq -r ".uat_url[]" $json_file); do
        local base_name=$(basename ${k})
        local dest="/storage/baseimgs/$base_name"

        if [ ! -f "$dest" ]; then
            download_file "$k" "$dest"
        else
            echo "$dest exists"
        fi
    done
}

main() {
    setup_environment
    # download_distros
    #download_uat
}

main
