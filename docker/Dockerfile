# Use an official Rocky Linux image as a parent image
FROM rockylinux/rockylinux:9

# Set environment variables to non-interactive (this prevents some prompts)
ENV container docker

# Install systemd and its libraries
RUN dnf -y install systemd systemd-libs && dnf clean all

# Remove unsafe paths and mask services that shouldn't run in the container
RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done) \
    && rm -f /lib/systemd/system/multi-user.target.wants/* \
    && rm -f /etc/systemd/system/*.wants/* \
    && rm -f /lib/systemd/system/local-fs.target.wants/* \
    && rm -f /lib/systemd/system/sockets.target.wants/*udev* \
    && rm -f /lib/systemd/system/sockets.target.wants/*initctl* \
    && rm -f /lib/systemd/system/basic.target.wants/* \
    && rm -f /lib/systemd/system/anaconda.target.wants/* \
    && rm -f /lib/systemd/system/systemd*udev* \
    && systemctl mask dev-hugepages.mount sys-fs-fuse-connections.mount

# Install EPEL repository for extra packages
RUN dnf install -y epel-release

# Install the additional packages
RUN dnf install -y dhcp-server pykickstart yum-utils debmirror git rsync-daemon \
    ipxe-bootimgs shim grub2-efi-x64-modules && \
    dnf clean all

# Copy the RPM from the cobbler directory into the container
COPY cobbler/cobbler-3.3.3-1.el9.noarch.rpm /tmp/

# Install Cobbler from the local RPM
RUN dnf install -y /tmp/cobbler-3.3.3-1.el9.noarch.rpm

# If you have other files or directories in the cobbler directory to add, use COPY or ADD commands
# For example:
# COPY cobbler/somefile /path/in/container/

# Expose necessary ports for Cobbler and its services

# DHCP server (if Cobbler is managing DHCP)
EXPOSE 67

# TFTP for serving boot files during PXE boot
EXPOSE 69

# rsync for file synchronization
EXPOSE 873

# HTTP for Cobbler's web interface and serving installation files
EXPOSE 80

# Cobbler's XML-RPC API
EXPOSE 25151

# Add any custom configuration files
ADD ./cobbler/settings /etc/cobbler/settings

# Copy the entrypoint script into the container
COPY entrypoint.sh /entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]
