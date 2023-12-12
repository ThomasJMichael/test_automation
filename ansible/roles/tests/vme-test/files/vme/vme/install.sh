#!/bin/bash -e

cd "/home/npi/vme-test-repo/"

# once in archive directory, install and start
./uninstall 2>&1 >/dev/null ||:
./install

cat <<EOF | tee /etc/systemd/system/capivme.service 
[Unit]
Description=Abaco Linux CAPI VME Driver

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=${SCRIPT} start
ExecStop=${SCRIPT} stop

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable capivme
systemctl start capivme

${SCRIPT} start

echo "Done!"