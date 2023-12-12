# Test Automation (`test_automation`)

The `test_automation` project is designed to facilitate the setup, provisioning, and testing of SBCs (Single Board Computers). This repository provides a structured approach to automate various tasks related to SBC testing using tools like Ansible, Docker, and Vagrant.

## Project Structure

```
test_automation
│
├───ansible                # Ansible playbooks and roles for configuration management.
│
├───config                 # Configuration files for various components.
│   └───squid              # Configuration files for squid
│
├───docker                 # Docker-related files.
│   └───cobbler            # Docker setup for Cobbler.
│       ├───storage        # Storage directory for Cobbler.
│       └───volumes        # Mounted volumes for the Docker container.
│           └───var        # Var directory containing various configurations.
│               ├───baseimgs
│               ├───config
│               ├───lib
│               │   ├───cobbler
│               │   └───tftpboot
│               └───www
│                   └───cobbler
│
├───provisioner-v3         # External git project (may be refactored in the future).
│   ├───...                # Various directories related to the provisioner.
│
├───scripts                # Utility scripts for the project.
│   ├───docker             # Scripts related to Docker operations.
│   └───vagrant            # Scripts related to Vagrant operations.
│
├───squid                  # Configuration and related files for the Squid proxy.
│
└───vagrant                # Vagrant setup and related files.
    └───shared             # Shared directory for Vagrant.
```

## Overview

- **Ansible**: Contains Ansible playbooks and roles that are used for configuration management and orchestration of tasks.
  
- **Docker**: Houses the Docker setup for Cobbler, which is a Linux installation and update server. The `volumes` directory is crucial as it contains directories that are mounted to the Docker container, ensuring persistence of data.

- **Provisioner-v3**: An external project that is currently included in the repository. This might undergo refactoring or replacement in the future.

- **Scripts**: This directory contains utility scripts that assist in various operations, categorized into Docker and Vagrant.

- **Squid**: Configuration files and related setup for the Squid proxy server.

- **Vagrant**: Contains the Vagrant setup, which is used to create and manage virtualized development environments.

## Getting Started

1. Ensure you have all the necessary tools installed, such as Vagrant, a hypervisor, and rsync.
2. Clone the repository.
3. Navigate to the desired directory (e.g., `docker`, `vagrant`) and follow the specific README or instructions available.
4. Use the scripts provided in the `scripts` directory to automate various tasks.

---
