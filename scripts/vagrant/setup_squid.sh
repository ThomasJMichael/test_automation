#!/bin/bash

SQUID_CONF="/etc/squid/squid.conf"

check_squid_conf(){
    if [ ! -f $SQUID_CONF ]; then
        echo "Squid configuration file not found at $SQUID_CONF. Exiting."
        exit 1
    fi
}

configure_squid(){
    echo "Configurin Squid..."

    # Comment out the default localnet ACL
    sudo sed -i 's/^acl localnet/\#acl localnet/g' $SQUID_CONF

    # Add custom ACLs for SSL ports, Safe ports, and localnet
    sudo sed -i '/^acl SSL_ports.*/a acl SSL_ports port 22\nacl Safe_ports port 22\nacl localnet src 192.168.75.0\/24' $SQUID_CONF

    # Allow traffic from localnet and then deny all other traffic
    sudo sed -i 's/^http_access deny all/http_access allow localnet\nhttp_access deny all/g' $SQUID_CONF

    # Configure cache directory
    sudo sed -i 's/#cache_dir.*/cache_dir ufs \/var\/spool\/squid 15000 16 256/' $SQUID_CONF

    echo "Squid configuration updated."
}

restart_squid(){
    echo "Restarting Squid..."

    sudo systemctl restart squid

    if sudo systemctl is-active --quiet squid; then
        echo "Squid restarted successfully."
    else
        echo "Error restarting Squid. Exiting."
        exit 1
    fi
}

main(){
    echo "Running setup_squid.sh...."
    check_squid_conf
    configure_squid
    restart_squid
    echo "setup_squid.sh finished."
}

main