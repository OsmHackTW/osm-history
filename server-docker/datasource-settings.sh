#!/bin/sh
set -x -e

cd /web/openstreetmap-carto

sed -e "s/\"dbname\": \"gis\"/\"host\": \"$PG_PORT_5432_TCP_ADDR\",\n \
    \"port\": \"$PG_PORT_5432_TCP_PORT\",\n \
    \"user\": \"$PG_ENV_POSTGRES_USER\",\n \
    \"password\": \"$PG_ENV_POSTGRES_PASSWORD\",\n \
    \"dbname\":\"$PG_ENV_POSTGRES_DB\"/" project.mml > project-mod.mml
carto project-mod.mml > style.xml
