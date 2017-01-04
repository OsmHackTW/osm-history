#!/bin/sh
DATE=${1:-"latest"}

set -x -e

cd data
wget -c --no-show-progress http://planet.osm.org/pbf/full-history/history-$DATE.osm.pbf

docker run --rm \
	-v $PWD:/data \
	kcwu/osm-history-splitter \
	history-$DATE.osm.pbf splitter.config
