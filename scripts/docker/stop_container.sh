#!/bin/bash

# Define the image and container names
IMAGE_NAME="cobbler_image"
CONTAINER_NAME="cobbler_container"
REMOVE_IMAGE=false

# Check for flags
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -r|--remove-image) REMOVE_IMAGE=true;;
        *) echo "Unknown parameter passed: $1"; exit 1;;
    esac
    shift
done

# Check if the container is running and stop it
if docker ps --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}\$"; then
    echo "Stopping container ${CONTAINER_NAME}..."
    docker stop ${CONTAINER_NAME}
    if [ $? -eq 0 ]; then
        echo "Container ${CONTAINER_NAME} stopped successfully!"
    else
        echo "Error stopping container ${CONTAINER_NAME}."
        exit 1
    fi
else
    echo "Container ${CONTAINER_NAME} is not running."
fi

# Remove the container
if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}\$"; then
    echo "Removing container ${CONTAINER_NAME}..."
    docker rm ${CONTAINER_NAME}
    if [ $? -eq 0 ]; then
        echo "Container ${CONTAINER_NAME} removed successfully!"
    else
        echo "Error removing container ${CONTAINER_NAME}."
        exit 1
    fi
else
    echo "Container ${CONTAINER_NAME} does not exist."
fi

# Remove the image if the flag is set
if $REMOVE_IMAGE; then
    if docker images --format '{{.Repository}}' | grep -Eq "^${IMAGE_NAME}\$"; then
        echo "Removing image ${IMAGE_NAME}..."
        docker rmi ${IMAGE_NAME}
        if [ $? -eq 0 ]; then
            echo "Image ${IMAGE_NAME} removed successfully!"
        else
            echo "Error removing image ${IMAGE_NAME}."
            exit 1
        fi
    else
        echo "Image ${IMAGE_NAME} does not exist."
    fi
fi

# Prune docker resources
echo "Pruning unused Docker resources..."
docker system prune -f

echo "Cleanup complete!"
