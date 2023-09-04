#!/bin/bash

# Define the image and container names
IMAGE_NAME="cobbler_image"
CONTAINER_NAME="cobbler_container"
BUILD_PATH="../docker"

# Check if the container already exists
if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}\$"; then
    echo "Container ${CONTAINER_NAME} already exists."

    # Check if the container is running
    if ! docker ps --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}\$"; then
        echo "Starting existing container ${CONTAINER_NAME}..."
        docker start ${CONTAINER_NAME}
        if [ $? -eq 0 ]; then
            echo "Container ${CONTAINER_NAME} started successfully!"
            exit 0
        else
            echo "Error starting container ${CONTAINER_NAME}."
            exit 1
        fi
    else
        echo "Container ${CONTAINER_NAME} is already running."
        exit 0
    fi
else
    # Build the Docker image
    echo "Building Docker image: $IMAGE_NAME..."
    docker build -t $IMAGE_NAME $BUILD_PATH

    # Check if the build was successful
    if [ $? -ne 0 ]; then
        echo "Error building Docker image. Exiting."
        exit 1
    fi

    # Run the Docker container
    echo "Starting container from image: $IMAGE_NAME..."
    docker run -d \
        --name ${CONTAINER_NAME} \
        --privileged \
        --tmpfs /run \
        --tmpfs /run/lock \
        -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
        -p 67:67 \
        -p 69:69 \
        -p 873:873 \
        -p 80:80 \
        -p 25151:25151 \
        $IMAGE_NAME

    # Check if the container started successfully
    if [ $? -eq 0 ]; then
        echo "Container started successfully!"
    else
        echo "Error starting container."
        exit 1
    fi
fi
