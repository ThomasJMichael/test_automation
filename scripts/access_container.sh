#!/bin/bash

# Define the container name or ID
CONTAINER_NAME="cobbler_container"

# Check if the container is running
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Accessing the container: $CONTAINER_NAME"
    docker exec -it $CONTAINER_NAME /bin/bash
else
    echo "Error: Container $CONTAINER_NAME is not running."
    exit 1
fi
