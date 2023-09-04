
# Test Automation

This project is designed for setting up, provisioning, and eventually testing SBCs (Single Board Computers).

## Directory Structure

```
.
├── ansible/          # Reserved for future Ansible configurations and playbooks.
├── docker/           # Docker-related files and configurations.
│   └── cobbler/
│       └── volumes/  # Cobbler volume configurations.
├── scripts/          # Utility scripts used throughout the project.
├── squid/            # Configuration files for the Squid proxy server.
└── vagrant/          # Vagrant configurations and related files.
    └── shared/       # Shared directory for Vagrant.
```

## Components Description

- **ansible/**: This directory is reserved for future use with Ansible. It will contain configurations and playbooks to automate tasks across multiple hosts.
  
- **docker/**: Contains Docker configurations and related files. The `cobbler/volumes/` sub-directory holds configurations specific to Cobbler volumes.

- **scripts/**: This directory houses utility scripts that assist in various tasks throughout the project. These scripts are meant to simplify repetitive tasks and ensure consistency.

- **squid/**: Holds the configuration files for the Squid proxy server. Squid is used in this project to cache and forward web page requests, improving the performance and security of web traffic. This also will allow the SBC's to make web requests and download packages without being connected to the network.

- **vagrant/**: Contains Vagrant configurations and related files. Vagrant is utilized to create and manage virtualized development environments. The `shared/` sub-directory is a shared folder accessible from both the host and the Vagrant VM.
