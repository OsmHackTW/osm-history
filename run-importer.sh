#!/bin/bash
# As 2016-12, during import Taiwan's history extract (110MB pbf),
# - db needs 0.5G res mem, 1.5G virt mem, but "docker stats" says 5.7G ?
# - db disk volume 5.5G. 9G after index creation.
# - importer needs 1.9G ram (memory leak??)
POSTGIS_INSTANCE=${1:-"osmdb"}
PBF=${2:-"$PWD/data/history-extract.osh.pbf"}

docker exec -ti osmdb psql -U postgres -c 'CREATE EXTENSION postgis;'
docker exec -ti osmdb psql -U postgres -c 'CREATE EXTENSION hstore;'
docker exec -ti osmdb psql -U postgres -c 'CREATE EXTENSION btree_gist;'

FILE=/history.osh.pbf

docker run -ti --rm \
    --link ${POSTGIS_INSTANCE}:pg \
    -v $PBF:$FILE \
    --name osm-history-importer \
    kcwu/osm-history-importer $FILE

docker exec osmdb psql -U postgres --echo-all < create-db-index.sql
