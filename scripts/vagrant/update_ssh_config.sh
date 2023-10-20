#!/bin/bash

# Check if ~/.ssh exists, if not create it
if [ ! -d "$HOME/.ssh" ]; then
    mkdir "$HOME/.ssh"
    chmod 700 "$HOME/.ssh"
fi

# Check if the configuration already exists in ~/.ssh/config
if ! grep -q "Host 192.168.75.*" "$HOME/.ssh/config"; then
    # Append the configuration to ~/.ssh/config
    echo "Host 192.168.75.*" >> "$HOME/.ssh/config"
    echo "    StrictHostKeyChecking no" >> "$HOME/.ssh/config"
    echo "    UserKnownHostsFile /dev/null" >> "$HOME/.ssh/config"
    echo "Configuration added to $HOME/.ssh/config"
else
    echo "Configuration already exists in $HOME/.ssh/config"
fi

# Set the correct permissions for ~/.ssh/config
chmod 600 "$HOME/.ssh/config"
