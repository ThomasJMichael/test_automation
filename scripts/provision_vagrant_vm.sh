#!/bin/bash

# Function to update package list and upgrade all packages
update_packages() {
    echo "Updating package list and upgrading all packages..."
    sudo apt-get update
    sudo apt-get upgrade -y
}

# Function to install basic dependencies
install_basic_dependencies() {
    echo "Installing basic dependencies..."
    sudo apt-get install -y software-properties-common
}

# Function to install Ansible
install_ansible() {
    echo "Installing Ansible..."
    sudo apt-add-repository --yes --update ppa:ansible/ansible
    sudo apt-get install -y ansible
}

# Function to install Docker
install_docker() {
    echo "Installing Docker..."
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    sudo apt-get update
    sudo apt-get install -y docker-ce
}

# Function to install Squid
install_squid() {
    echo "Installing Squid..."
    sudo apt-get install -y squid
}

# Function to configure Firewall and SELinux
configure_security() {
    echo "Configuring Firewall..."

    # Allow SSH, HTTP, HTTPS, and Squid ports
    sudo ufw allow 22/tcp    # SSH
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
    install_ansible
    install_docker
    install_squid
    configure_security  # Replacing disable_security with configure_security
}

# Run the main function
main
