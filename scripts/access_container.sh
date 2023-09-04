#!/bin/bash

# Define the container name or ID
CONTAINER_NAME="cobbler_container"

# Check if the container is running
if docker ps | awk -v container="$CONTAINER_NAME" 'NR>1{print $NF}' | grep -q "^$container$"; then
    echo "Accessing the container: $CONTAINER_NAME"
    docker exec -it $CONTAINER_NAME /bin/bash
else
    echo "Error: Container $CONTAINER_NAME is not running."
    exit 1
fi
