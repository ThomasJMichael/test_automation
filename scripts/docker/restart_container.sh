#!/bin/bash

CONTAINER_NAME="cobbler_container"

# Check if the container exists
if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}\$"; then
    echo "Restarting container ${CONTAINER_NAME}..."
    docker restart ${CONTAINER_NAME}
    if [ $? -eq 0 ]; then
        echo "Container ${CONTAINER_NAME} restarted successfully!"
    else
        echo "Error restarting container ${CONTAINER_NAME}."
        exit 1
    fi
else
    echo "Container ${CONTAINER_NAME} does not exist."
    exit 1
fi
