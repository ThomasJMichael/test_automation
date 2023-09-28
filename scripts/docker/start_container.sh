#!/bin/bash

# Define the image and container names
IMAGE_NAME="cobbler_image"
CONTAINER_NAME="cobbler_container"
BUILD_PATH="/vagrant_shared/docker"

# cleanup docker resources
docker system prune -f

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
    HOST_JSON_SRC="/vagrant_shared/config/host.json"
    CONFIGURE_SCRIPT_SRC="/vagrant_shared/scripts/docker/configure_docker_container.sh"

    HOST_JSON_DEST="$BUILD_PATH/host.json"
    CONFIGURE_SCRIPT_DEST="$BUILD_PATH/configure_docker_container.sh"
    
    if [ ! -f "$HOST_JSON_DEST" ]; then
        echo "Copying host.json to Docker build directory..."
        cp "$HOST_JSON_SRC" "$HOST_JSON_DEST"
    fi

    if [ ! -f "$CONFIGURE_SCRIPT_DEST" ]; then
        echo "Copying configure_docker_container.sh to Docker build directory..."
        cp "$CONFIGURE_SCRIPT_SRC" "$CONFIGURE_SCRIPT_DEST"
    fi

    # Build the Docker image
    echo "Building Docker image: $IMAGE_NAME..."
    MAX_RETRIES=10
    RETRY_DELAY=1
    RETRY_COUNT=0
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        docker build -t $IMAGE_NAME $BUILD_PATH && break
        RETRY_COUNT=$((RETRY_COUNT+1))
        echo "Build failed, retrying in $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
    done

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
        --net host \
        -v /sys/fs/cgroup:/sys/fs/cgroup \
        -v /vagrant_shared/docker/cobbler/volumes/var/www/cobbler:/var/www/cobbler \
        -v /vagrant_shared/docker/cobbler/volumes/var/lib/cobbler/config:/var/lib/cobbler \
        -v /vagrant_shared/docker/cobbler/volumes/var/lib/tftpboot:/var/lib/tftpboot \
        -v /vagrant_shared/docker/cobbler/volumes/var/config:/var/config \
        -v /vagrant_shared/docker/cobbler/volumes/storage/baseimgs:/storage/baseimgs \
        -v /vagrant_shared/config/kickstarts/:/tmp/config/cobbler \
        $IMAGE_NAME

    # Check if the container started successfully
    if [ $? -eq 0 ]; then
        echo "Container started successfully!"
    else
        echo "Error starting container."
        exit 1
    fi
fi
