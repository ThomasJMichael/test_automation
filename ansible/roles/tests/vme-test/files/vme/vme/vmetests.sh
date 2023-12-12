#!/bin/bash
cd `dirname $(readlink -f "$0")`

echo "Do '$0 -h' to see available options."

systemctl stop capivme
systemctl start capivme

/test/pcd/pythonenv/bin/python3 ./examples.py $@
