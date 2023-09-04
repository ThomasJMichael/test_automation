#!/bin/bash

# Define the image name
IMAGE_NAME="cobbler_image"
BUILD_PATH="../docker"

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
    --name cobbler_container \
    --privileged \
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
fi
