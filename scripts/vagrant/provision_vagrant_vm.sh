#!/bin/bash

update_packages() {
    echo "Updating package list and upgrading all packages..."
    sudo apt-get update
    sudo apt-get upgrade -y
}

install_basic_dependencies() {
    echo "Installing basic dependencies..."
    sudo apt-get install -y software-properties-common
}

install_dev_tools() {
    echo "Installing development tools..."
    sudo apt-get install -y make tar git wget bzip2 zip gcc build-essential python3-dev libffi-dev
}

install_network_tools() {
    echo "Installing network utilities..."
    sudo apt-get install -y net-tools dmidecode jq
}

install_auth_tools() {
    echo "Installing authentication tools..."
    sudo apt-get install -y sssd-ldap sssd-krb5 realmd ldap-utils libnl-genl-3-200
}

install_misc_tools() {
    echo "Installing miscellaneous tools..."
    sudo apt-get install -y perl
}

install_ansible() {
    echo "Installing Ansible..."
    sudo apt-add-repository --yes --update ppa:ansible/ansible
    sudo apt-get install -y ansible
}

install_docker() {
    echo "Installing Docker..."
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    sudo apt-get update
    sudo apt-get install -y docker-ce
}

install_squid() {
    echo "Installing Squid..."
    sudo apt-get install -y squid
    
    echo "Enabling Squid..."
    sudo systemctl enable --now squid
}

# Function to configure Firewall and Apparmor
configure_security() {
    echo "Disabling apprmor..."

    sudo systemctl stop apparmor
    sudo systemctl disable apparmor

    echo "Configuring Firewall..."

    # Allow SSH, HTTP, HTTPS, and Squid ports
    sudo ufw allow 22/tcp    # SSH
    sudo ufw allow 67/udp    # DHCP
    sudo ufw allow 68/udp    # DHCP
    sudo ufw allow 69/udp    # TFTP
    sudo ufw allow 80/tcp    # HTTP
    sudo ufw allow 443/tcp   # HTTPS
    sudo ufw allow 3128/tcp  # Squid default port

    # Enable the firewall
    sudo ufw enable

    echo "Firewall configured."
}

# Main execution
main() {
    update_packages
    install_basic_dependencies
    install_dev_tools
    install_network_tools
    install_auth_tools
    install_ansible
    install_docker
    install_squid
    configure_security 
}

main
