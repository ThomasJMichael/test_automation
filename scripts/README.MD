
# Scripts Directory

This directory contains various utility scripts that facilitate the setup, provisioning, and management of the test automation environment.

## Directory Structure

```
scripts/
│
├── start_container.sh  # Script to build and/or start the Docker container.
├── access_container.sh  # Script to access the running Docker container.
├── provision_vagrant.sh  # Script to provision the Vagrant environment.
└── setup_squid.sh  # Script to set up and configure the Squid proxy server.
```

## Scripts Description

- **start_container.sh**: This script is responsible for building the Docker image for Cobbler and starting the container. If the container already exists, it ensures the container is running.

- **access_container.sh**: Use this script to access the running Docker container. It provides an interactive shell inside the container, allowing for manual configurations or debugging.

- **provision_vagrant.sh**: This script provisions the Vagrant environment. It sets up the necessary configurations and services inside the Vagrant VM, ensuring a consistent environment for test automation.

- **setup_squid.sh**: This script sets up the Squid proxy server. Squid is a caching proxy for the Web supporting HTTP, HTTPS, FTP, and more. It reduces bandwidth and improves response times by caching and reusing frequently-requested web pages.

## Usage

To use any of the scripts, navigate to the `scripts/` directory and execute the desired script:

```bash
cd scripts/
./<script_name>.sh
```

Ensure you have the necessary permissions to execute the scripts. If not, you might need to use `chmod` to make them executable:

```bash
chmod +x <script_name>.sh
```

For more detailed instructions on using each script, refer to the comments inside the individual scripts or the main project's README.

---