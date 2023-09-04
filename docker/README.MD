# Docker Configuration

This directory contains the Docker-related files and configurations essential for setting up and provisioning the required services for our test automation system.

## Directory Structure

```
docker/
│
└── cobbler/
    ├── cobbler-3.3.3-1.el8.noarch.rpm  # Cobbler RPM package.
    ├── entrypoint.sh  # Script executed upon container start.
    └── volumes/  # Cobbler volume configurations.
```

## Components Description

- **cobbler/**: This directory contains Docker configurations specific to the Cobbler service. Cobbler is a Linux installation server that allows for rapid setup of network installation environments.

    - **cobbler-3.3.3-1.el8.noarch.rpm**: The RPM package for Cobbler.
    - **entrypoint.sh**: This script is executed when the Docker container starts. It contains commands to set up and start the Cobbler service inside the container.
    - **volumes/**: Holds configurations and data specific to Cobbler volumes. These volumes are essential for persistent storage and ensuring data consistency across container restarts.

## Usage

To build the Docker image for Cobbler, navigate to the `cobbler/` directory and use the Docker build command:

```bash
cd cobbler/
docker build -t cobbler_image .
```

When running the Docker container, the following volumes are mounted:

```
-v /vagrant_share/docker/cobbler/volumes/var/www/cobbler:/var/www/cobbler
-v /vagrant_share/docker/cobbler/volumes/var/lib/cobbler/config:/var/lib/cobbler
-v /vagrant_share/docker/cobbler/volumes/var/lib/tftpboot:/var/lib/tftpboot
-v /vagrant_share/docker/cobbler/volumes/var/config:/var/config
-v /vagrant_share/docker/cobbler/volumes/storage/baseimgs:/storage/baseimgs
```

For convenience, scripts for building, running, and accessing the Docker container are located in the `scripts/` directory at the project's root level. Specifically:

- **start_container.sh**: Script to build and/or start the Docker container.
- **access_container.sh**: Script to access the running Docker container.

For more detailed instructions on using Docker and the provided configurations, refer to the individual service directories.

---