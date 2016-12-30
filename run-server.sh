#!/bin/bash
POSTGIS_INSTANCE=${1:-"osmdb"}

EXTRA_OPTIONS=

if [ -d ./server ]; then
	echo "[1;33m*** Found 'server' directory, use it to override docker image ***[m"
	EXTRA_OPTIONS="-v $PWD/server:/server/osm-history/server"
fi

set -x -e

docker run -t -i --rm \
    --link ${POSTGIS_INSTANCE}:pg \
    --link my-memcache:memcache \
    --name osm-history-server \
    $EXTRA_OPTIONS \
    -p 80:8080 \
    kcwu/osm-history-server
