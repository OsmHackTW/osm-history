#!/bin/bash
POSTGIS_INSTANCE=${1:-"osmdb"}

set -x -e

docker run -t -i --rm \
    --link ${POSTGIS_INSTANCE}:pg \
    --link my-memcache:memcache \
    --name osm-history-web \
    -v /home/kcwu/osm-history:/web/osm-history \
    -p 80:8080 \
    kcwu/osm-history-server
