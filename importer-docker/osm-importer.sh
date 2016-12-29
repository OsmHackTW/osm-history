#!/bin/bash

PBF=${1:-"/history.osh.pbf"}

if [ -z $PG_ENV_POSTGRES_PASSWORD ] \
    || [ -z $PG_ENV_POSTGRES_DB ] \
    || [ -z $PG_ENV_POSTGRES_USER ] \
    || [ -z $PG_PORT_5432_TCP_ADDR ] \
    || [ -z $PG_PORT_5432_TCP_PORT ] ; then
        echo "missing Progress settings"

cat <<EOF
PG_PORT_5432_TCP_ADDR=$PG_PORT_5432_TCP_ADDR
PG_PORT_5432_TCP_PORT=$PG_PORT_5432_TCP_PORT
PG_ENV_POSTGRES_DB=$PG_ENV_POSTGRES_DB
PG_ENV_POSTGRES_USER=$PG_ENV_POSTGRES_USER
PG_ENV_POSTGRES_PASSWORD=$PG_ENV_POSTGRES_PASSWORD
EOF
exit 1
fi

./osm-history-importer --dsn "host='$PG_PORT_5432_TCP_ADDR' port='$PG_PORT_5432_TCP_PORT' user='$PG_ENV_POSTGRES_USER' dbname='$PG_ENV_POSTGRES_DB' password='$PG_ENV_POSTGRES_PASSWORD'" $PBF
