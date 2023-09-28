# Ubuntu Server Quick Install
# by Dustin Kirkland <kirkland@ubuntu.com>
#  * Documentation: http://bit.ly/uquick-doc
d-i     live-installer/net-image string http://$http_server/cobbler/links/$distro_name/install/filesystem.squashfs
d-i     debian-installer/locale string en_US.UTF-8
d-i     debian-installer/splash boolean false
d-i     console-setup/ask_detect        boolean false
d-i     console-setup/layoutcode        string us
d-i     console-setup/variantcode       string
d-i     netcfg/dhcp_failed note
d-i     netcfg/dhcp_options select Configure network manually
d-i     netcfg/disable_autoconfig boolean true
d-i     netcfg/get_nameservers  string $http_server
d-i     netcfg/get_ipaddress    string $ip_address_enp_cobbler
d-i     netcfg/get_netmask      string 255.255.255.0
d-i     netcfg/get_gateway      string $http_server
d-i     netcfg/confirm_static   boolean true
d-i     mirror/country string manual
d-i     mirror/http/hostname string http://archive.ubuntu.com
d-i     mirror/http/directory string /ubuntu
d-i     mirror/http/proxy string http://$http_server:3128
#d-i     apt-setup/use_mirror boolean false
#d-i     apt-setup/local0/repository string http://192.168.75.1/cblr/links/ubuntu1804-x86_64/ubuntu bionic main
d-i     debian-installer/allow_unauthenticated boolean true
d-i     clock-setup/utc boolean true
d-i     partman-auto/method string regular
d-i     partman-lvm/device_remove_lvm boolean true
d-i     partman-lvm/confirm boolean true
d-i     partman/confirm_write_new_label boolean true
d-i     partman/choose_partition        select Finish partitioning and write changes to disk
d-i     partman/confirm boolean true
d-i     partman/confirm_nooverwrite boolean true
d-i     partman/default_filesystem string ext3
d-i     clock-setup/utc boolean true
d-i     clock-setup/ntp boolean true
d-i     clock-setup/ntp-server  string ntp.ubuntu.com
d-i     base-installer/kernel/image     string linux-server
d-i     passwd/root-login       boolean false
d-i     passwd/make-user        boolean true
d-i     passwd/user-fullname    string $dev_username
d-i     passwd/username         string $dev_username
d-i     passwd/user-password password $dev_password
d-i     passwd/user-password-again password $dev_password
d-i     passwd/user-uid string
d-i     user-setup/allow-password-weak  boolean false
d-i     user-setup/encrypt-home boolean false
d-i     passwd/user-default-groups      string adm cdrom dialout lpadmin plugdev sambashare
d-i     apt-setup/services-select       multiselect security
d-i     apt-setup/security_host string security.ubuntu.com
d-i     apt-setup/security_path string /ubuntu
d-i     debian-installer/allow_unauthenticated  string false
d-i     pkgsel/upgrade  select safe-upgrade
d-i     pkgsel/language-packs   multiselect
d-i     pkgsel/update-policy    select none
d-i     pkgsel/updatedb boolean true
d-i     grub-installer/skip     boolean false
d-i     lilo-installer/skip     boolean false
d-i     grub-installer/only_debian      boolean true
d-i     grub-installer/with_other_os    boolean true

#d-i     preseed/early_command string wget -O- http://$http_server/cblr/svc/op/script/$what/$name/?script=preseed_early_default | /bin/sh -s
d-i     preseed/early_command string wget "http://$http_server/cblr/svc/op/nopxe/system/$system_name" -O /dev/null ; \
        echo "$dev_username ALL=(ALL) NOPASSWD:ALL" > sudo_$dev_username ; \
        echo "#Testing netplan shenanigans" > etc/netplan/01-netcfg.yaml ; \
        echo "network:" >> etc/netplan/01-netcfg.yaml ; \
        echo "  version: 2" >> etc/netplan/01-netcfg.yaml ; \
        echo "  renderer: networkd" >> etc/netplan/01-netcfg.yaml ; \
        echo "  ethernets:" >> etc/netplan/01-netcfg.yaml ; \
        echo "    $dev_interface:" >> etc/netplan/01-netcfg.yaml ; \
        echo "      dhcp4: no" >> etc/netplan/01-netcfg.yaml ; \
        echo "      addresses: [$ip_address_enp_cobbler/24]" >> etc/netplan/01-netcfg.yaml ; \
        echo "      gateway4: $http_server" >> etc/netplan/01-netcfg.yaml ; \
        echo "      nameservers:" >> etc/netplan/01-netcfg.yaml ; \
        echo "        addresses: [$http_server]" >> etc/netplan/01-netcfg.yaml

d-i     preseed/late_command string true ; \
        cp etc/netplan/01-netcfg.yaml /target/etc/netplan/01-netcfg.yaml ; \
        cp sudo_$dev_username /target/etc/sudoers.d/.

d-i     finish-install/keep-consoles    boolean false
d-i     finish-install/reboot_in_progress       note
d-i     cdrom-detect/eject      boolean true
d-i     debian-installer/exit/halt      boolean false
d-i     debian-installer/exit/poweroff  boolean false
d-i     pkgsel/include string byobu vim openssh-server
byobu   byobu/launch-by-default boolean true
