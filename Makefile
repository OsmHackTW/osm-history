DATE=20140224

CURL=curl
#CURL=aria2c -x 4 --retry-wait=120 --max-tries=10

DATA_PATH=data
DATE2!=echo $(DATE) | sed -e 's/\(....\)\(..\)\(..\)/\1-\2-\3/'
URL_FULL_HISTORY=http://planet.osm.org/planet/experimental/history-$(DATE2).osm.pbf
FILE_FULL_HISTORY=$(DATA_PATH)/history-$(DATE).osh.pbf
FILE_HISTORY_EXTRACT=$(DATA_PATH)/history-extract-$(DATE).osh.pbf

SPLITTER=/home/data/repos/git/osm/osm-history-splitter/osm-history-splitter
IMPORTER_DIR=/home/data/repos/git/osm/osm-history-renderer/importer
IMPORTER=$(IMPORTER_DIR)/osm-history-importer

DB_ADMIN=kcwu
DB_USER=osm
DB_NAME=osm_$(DATE)

all:

init:
	# TODO
	git clone 

# first time
init_db:
	# TODO

# depend network speed, may need hours
fetch_full_history:
	$(CURL) -o $(FILE_FULL_HISTORY) $(URL_FULL_HISTORY)

# need 100 minutes
extract_history:
	# --hardcut is faster than --sortcut (150 minutes)
	# should not have big difference
	$(SPLITTER) --hardcut $(FILE_FULL_HISTORY) taiwan-splitter.config
	mv history-extract.osh.pbf $(FILE_HISTORY_EXTRACT)


create_db:
	createdb -EUTF8 -O$(DB_USER) $(DB_NAME)
	echo 'CREATE EXTENSION postgis;' | psql $(DB_NAME) $(DB_ADMIN)
	echo 'CREATE EXTENSION hstore;' | psql $(DB_NAME) $(DB_ADMIN)
	echo 'CREATE EXTENSION btree_gist;' | psql $(DB_NAME) $(DB_ADMIN)
	echo "GRANT ALL ON geometry_columns TO $(DB_USER)" | psql $(DB_NAME) $(DB_ADMIN)
	echo "GRANT ALL ON spatial_ref_sys TO $(DB_USER)" | psql $(DB_NAME) $(DB_ADMIN)

import_db:
	ln -sf $(IMPORTER_DIR)/scheme
	# need 3-4 minutes
	$(IMPORTER) --dsn "user='$(DB_USER)' dbname='$(DB_NAME)'" $(FILE_HISTORY_EXTRACT)
	time python ./history_tile.py post_import_db $(DATE)

drop_db:
	dropdb $(DB_NAME)

list_db:
	echo '\list' | psql -U$(DB_USER)

update: fetch_full_history extract_history create_db import_db
