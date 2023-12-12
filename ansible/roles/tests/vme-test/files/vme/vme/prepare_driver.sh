#!/bin/bash
cd `dirname $(readlink -f "$0")`

if [ "$(lsmod | grep -c gefvme)" -eq "1" ]; then
    rmmod gefvme
fi

if [ "$(lsmod | grep -c capivme)" -eq "0" ]; then
    ./install.sh
else
    echo "Forcing driver restart"
    /etc/init.d/DLIN-X86_64-VME stop
    /etc/init.d/DLIN-X86_64-VME start
fi
