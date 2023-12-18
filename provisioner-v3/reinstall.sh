cd `dirname $(readlink -f "$0")`
PYTHON="/usr/local/bin/python3"
[ -n "`which python3 2>/dev/null`" ] && PYTHON="`which python3`"
sudo $PYTHON -m pip uninstall -y aslinuxtester
sudo $PYTHON setup.py install
