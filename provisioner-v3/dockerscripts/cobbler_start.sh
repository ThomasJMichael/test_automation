#!/bin/bash
sudo docker system prune -f
sudo docker run -d --privileged --net host \
	-v /sys/fs/cgroup:/sys/fs/cgroup \
	-v /home/vagrant/provisioner-v3/var/www/cobbler:/var/www/cobbler \
	-v /home/vagrant/provisioner-v3/var/lib/cobbler:/var/lib/cobbler \
	-v /home/vagrant/provisioner-v3/var/lib/tftpboot:/var/lib/tftpboot \
	-v /home/vagrant/provisioner-v3/config/cobbler:/tmp/config/cobbler \
	-v /storage/baseimgs:/storage/baseimgs \
	-e SERVER_IP_V4=VAR_SERVER -e ROOT_PASSWORD=Passw0rd \
	-e NETMASK=VAR_NETMASK \
	-e SUBNET=VAR_SUBNET \
	-e RANGE="VAR_RANGE" \
	--name cobbler VAR_DOCKERNAME
sleep 60
sudo docker ps
