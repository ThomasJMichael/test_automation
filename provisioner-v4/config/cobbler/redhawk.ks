# This kickstart file should only be used with EL > 5 and/or Fedora > 7.
# For older versions please use the sample.ks kickstart file.

#platform=x86, AMD64, or Intel EM64T
# System authorization information
#auth  --useshadow  --enablemd5
%addon com_redhat_kdump --disable

%end
# System bootloader configuration
bootloader --location=mbr
# Choose disk
ignoredisk --only-use=nvme0n1
# Partition clearing information
clearpart --all --initlabel

# Partitions for Redhawk
part /boot --fstype="xfs" --ondisk=nvme0n1 --size=4096
part /boot/efi --fstype="efi" --ondisk=nvme0n1 --size=1024 --fsoptions="umask=0077,shortname=winnt"
part swap --fstype="swap" --size=16384 --ondisk=nvme0n1
part / --fstype="xfs" --size=65536 --ondisk=nvme0n1
part /home --fstype="xfs" --size=65536 --ondisk=nvme0n1

# Use text mode install
text
# Firewall configuration
#firewall --enabled
# Run the Setup Agent on first boot
firstboot --disable
# System keyboard
keyboard us
# System language
lang en_US

%packages
@^workstation-product-environment
@backup-client
@console-internet
@container-management
@development
@dotnet
@gnome-apps
@graphical-admin-tools
@headless-management
@internet-applications
@legacy-unix
@network-server
@office-suite
@remote-desktop-clients
@rpm-development-tools
@scientific
@security-tools
@smart-card
@system-tools

%end

# Use network installation
url --url=$tree
# If any cobbler repo definitions were referenced in the kickstart profile, include them here.
$yum_repo_stanza
# Reboot after installation
reboot

#Root password
rootpw --iscrypted $default_password_crypted
# User Credentials set by ksmeta params
user --name=$dev_username --groups=wheel --plaintext --password=$dev_password
# SELinux configuration
selinux --disabled
# System timezone
timezone  America/New_York
# Clear the Master Boot Record
zerombr

%pre
$SNIPPET('log_ks_pre')
$SNIPPET('autoinstall_start')
$SNIPPET('pre_install_network_config')
# Enable installation monitoring
$SNIPPET('pre_anamon')
%end

# Network information
$SNIPPET('network_config')

%post --nochroot
$SNIPPET('log_ks_post_nochroot')
%end

%post
$SNIPPET('log_ks_post')
# Start yum configuration
$yum_config_stanza
# End yum configuration
$SNIPPET('post_install_kernel_options')
$SNIPPET('post_install_network_config')
$SNIPPET('func_register_if_enabled')
$SNIPPET('download_config_files')
$SNIPPET('koan_environment')
$SNIPPET('cobbler_register')
# Enable post-install boot notification
$SNIPPET('post_anamon')
# Start final steps
$SNIPPET('autoinstall_done')
# End final steps
%end

%post
rm -f /etc/sysconfig/network-scripts/ifcfg-default
# give him the sudo
sed -i 's/ requiretty/ !requiretty/' /etc/sudoers
echo "$dev_username ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/$dev_username
# add /usr/local/bin to the sudo secure path
sed -i '/secure_path/ s/$/:\/usr\/local\/bin/' /etc/sudoers
# Mod the UseDNS setting
echo "@reboot root sed -i 's/.*UseDNS.*/UseDNS no/' /etc/ssh/sshd_config" >> /etc/crontab
%end
