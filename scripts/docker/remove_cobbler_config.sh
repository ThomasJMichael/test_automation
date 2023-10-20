#!/bin/bash

# Declare an associative array with host paths as keys and container paths as values
declare -A VOLUME_MAP=(
    ["/vagrant_shared/docker/cobbler/volumes/var/www/cobbler"]="/var/www/cobbler"
    ["/vagrant_shared/docker/cobbler/volumes/var/lib/cobbler/config"]="/var/lib/cobbler"
    ["/vagrant_shared/docker/cobbler/volumes/var/lib/tftpboot"]="/var/lib/tftpboot"
    ["/vagrant_shared/docker/cobbler/volumes/var/config"]="/var/config"
    ["/vagrant_shared/docker/cobbler/volumes/etc/cobbler"]="/etc/cobbler"
)

# Clear contents of each directory on both host and container
for host_path in "${!VOLUME_MAP[@]}"; do
    container_path="${VOLUME_MAP[$host_path]}"

    # Clear host side
    if [ -d "$host_path" ]; then
        echo "Clearing contents of host directory: $host_path..."
        rm -rf "$host_path"/*
    else
        echo "Host directory $host_path does not exist."
    fi

    # Clear container side (assuming the container is running)
    # Note: You might need to adjust this if you have a specific container name or ID
    echo "Clearing contents of container directory: $container_path..."
    docker exec -it cobbler_container rm -rf "$container_path"/*
done

echo "Directories cleared on both host and container."
