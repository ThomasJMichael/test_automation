# This kickstart file should only be used with EL > 5 and/or Fedora > 7.
# For older versions please use the sample.ks kickstart file.

#platform=x86, AMD64, or Intel EM64T
# System authorization information
auth  --useshadow  --enablemd5
# System bootloader configuration
bootloader --location=mbr
# Partition clearing information
clearpart --all --initlabel
# Always use SDA 
ignoredisk --only-use=sda
# Use text mode install
text
# Firewall configuration
firewall --enabled
# Run the Setup Agent on first boot
firstboot --disable
# System keyboard
keyboard us
# System language
lang en_US
# Use network installation
url --url=$tree
# Reboot after installation
reboot

#Root password
rootpw --iscrypted $default_password_crypted
# User Credentials set by ksmeta params
user --name=$dev_username --groups=wheel --plaintext --password=$dev_password
# SELinux configuration
selinux --disabled
# Do not configure the X Window System
skipx
# System timezone
timezone  America/New_York
# Install OS instead of upgrade
install
# Clear the Master Boot Record
zerombr
# Allow anaconda to partition the system as needed
autopart

%pre
$SNIPPET('log_ks_pre')
$SNIPPET('autoinstall_start')
$SNIPPET('pre_install_network_config')
# Enable installation monitoring
$SNIPPET('pre_anamon')
%end

# Network information
$SNIPPET('network_config')

%packages
$SNIPPET('func_install_if_enabled')
%end

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
#$SNIPPET('redhat_register')
$SNIPPET('cobbler_register')
# Enable post-install boot notification
$SNIPPET('post_anamon')
# Start final steps
$SNIPPET('autoinstall_done')
# End final steps
%end

%post
# obliterate the firewall 
rm -f /etc/systemd/system/dbus-org.fedoraproject.FirewallD1.service 
find /etc/systemd/system/ -name firewalld.service -type f -exec rm -f {} \;
find /usr/lib/systemd/system/ -name firewalld.service -type f -exec rm -f {} \;

find /etc/sysconfig/network-scripts -name "ifcfg-*" \
    -exec sed -i 's/ONBOOT=.*/ONBOOT=yes/' {} \;
# fix routes on fedora 20 because we have to
find /etc/sysconfig/network-scripts -name "ifcfg-*" \
    -exec grep $mac_address_enp_cobbler {} \; \
    -exec sed -i '/IPADDR/d' {} \; \
    -exec sed -i 's/BOOTPROTO=.*/BOOTPROTO=none/' {} \; \
    -exec sh -c "echo \"IPADDR=$ip_address_enp_cobbler\" >> {}" \; 

# give him the sudo
sed -i 's/ requiretty/ !requiretty/' /etc/sudoers
echo "$dev_username ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
%end
