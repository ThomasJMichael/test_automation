
# Vagrant Directory

This directory contains the configuration and resources required to set up and manage the Vagrant virtual environment for the test automation project.

## Directory Structure

```
vagrant/
│
├── Vagrantfile       # Primary configuration file for Vagrant.
└── shared/           # Directory for shared files between the host and the Vagrant VM.
```

## Description

- **Vagrantfile**: This is the main configuration file for Vagrant. It defines the type of machine and resources to use, the way the machine is provisioned, and more. This file is read by Vagrant to set up the environment.

- **shared/**: This directory acts as a shared folder between the host machine and the Vagrant VM. Files placed in this directory can be accessed from both the host and the VM, facilitating easy data transfer and configuration management.

## Usage

1. **Setting Up the Vagrant Environment**: Navigate to the `vagrant/` directory and run the following command to initialize and start the Vagrant environment:

    ```bash
    cd vagrant/
    vagrant up
    ```

2. **Accessing the Vagrant VM**: Once the VM is up and running, you can SSH into it using:

    ```bash
    vagrant ssh
    ```

3. **Halting and Destroying the VM**: If you wish to stop the VM, you can use:

    ```bash
    vagrant halt
    ```

    To completely remove the VM and free up resources, use:

    ```bash
    vagrant destroy
    ```

4. **Shared Directory**: Any files or directories you want to be accessible both from the host and the VM should be placed in the `shared/` directory.

For more detailed instructions and configurations, refer to the `Vagrantfile` and the main project's README.

---

Note: Always ensure you have the latest version of Vagrant and the necessary plugins installed for smooth operation.