sudo yum install -y epel-release
sudo yum install -y \
    gcc \
    libstdc++-devel.i686 \
    glibc-devel \
    glibc-devel.i686 \
    genisoimage \
    tar \
    nfs-utils \
    net-tools \
    make \
    git \
    subversion \
    sqlite \
    openssl-devel \
    libffi-devel \
    bzip2-devel \
    zip \
    readline-devel \
    dmidecode \
    jq \
    cobbler \
    cobbler-web

PYVER='3.7.3'
FORCE=false

if [ -n "${1}" ] && [ "${1}" = '--force' ]; then
    echo "Forcing reinstall"
    FORCE=true
fi

if ! $FORCE; then
    if [ -f "/usr/local/bin/python3.7" ] && [ -n "$(/usr/local/bin/python3 -V | grep $PYVER)" ]; then
        echo "Python ${PYVER} is already installed"
        echo "To force reinstall, run $0 --force"
        exit 0
    fi
fi

PYXZ="http://hsvdevops01/nexus/repository/raw/linux/swdev/devops/src/Python-${PYVER}.tar.xz"
PYWDIR=`mktemp -d "/tmp/python.XXX"`
cd "$PYWDIR"

echo "Installing Python $PYVER from source..."
curl -s "$PYXZ" --output - | tar xvJf -
cd "Python-${PYVER}"

echo "Checking OpenSSL Version is not 1.0.1..."
if [ -z "$(which openssl 2>/dev/null)" ] || [ -n "$(openssl version | awk '{print $2}' | grep '1.0.1')" ]; then
    SSLDIR="/usr/local/ssl"
    SSLWDIR=`mktemp -d "/tmp/openssl.XXX"`
    SSLGZ="http://hsvdevops01/nexus/repository/raw/linux/swdev/devops/src/openssl-1.0.2s.tar.gz"
    CURSSL="`which openssl 2>/dev/null`"
    SSLBIN=${CURSSL:-'/usr/bin/openssl'}

    echo "Installing OpenSSL from source..."
    curl -s "$SSLGZ" --output - | tar xvzfC - $SSLWDIR
    cd $SSLWDIR/openssl*
    #[ -n "$(which yum 2>/dev/null)" ] && sudo yum remove -y openssl openssl-devel
    ./config --prefix=$SSLDIR --openssldir=$SSLDIR
    sudo make
    sudo make install
    if [ ! "${SSLDIR}" = '/usr' ]; then
        sudo rm -f ${CURSSL}
        sudo ln -s "${SSLDIR}/bin/openssl" "${SSLBIN}"
    fi
    cd -
    rm -rf $SSLWDIR

    # fix the python install Setup.dist
    sed -i "/edit the SSL variable:/a \
SSL=$SSLDIR \n\
_ssl _ssl.c -DUSE_SSL -I\$(SSL)/include -I\$(SSL)/include/openssl -L\$(SSL)/lib -lssl -lcrypto" Modules/Setup.dist
    ./configure --with-openssl=${SSLDIR}
else
    ./configure
fi

sudo make
sudo make install

sudo rm -rf "$PYWDIR"

if [ -z "$(which python3 2>/dev/null)" ] || [ -z "$(python3 -V | grep $PYVER)" ]; then
    echo "Python ${PYVER} installation failed."
    exit 1
fi


