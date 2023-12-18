#!/bin/bash -e
SDIR=`dirname $(readlink -f "$0")`

PROFILES=($(cobbler profile list))
for p in ${PROFILES[@]}; do
    echo "Replacing '/var/lib/cobbler/kickstarts/${p}.ks'"
    cp "${SDIR}/default.ks" "/var/lib/cobbler/kickstarts/${p}.ks"
done

