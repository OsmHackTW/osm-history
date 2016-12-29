DATE=20140224

DATA_PATH=data
DATE2!=echo $(DATE) | sed -e 's/..\(..\)\(..\)\(..\)/\1\2\3/'
FILE_FULL_HISTORY=history-$(DATE2).osm.pbf

FILE_HISTORY_EXTRACT=$(DATA_PATH)/history-extract-$(DATE).osh.pbf

all:

###########################################################################################
# extract from full history
###########################################################################################

URL_FULL_HISTORY=http://planet.osm.org/pbf/full-history/$(FILE_FULL_HISTORY)
SPLITTER=osm-history-splitter/build/src/osm-history-splitter

ubuntu-depend:
	sudo apt-get -y install libgeos-dev libgeos++-dev clang
	sudo apt-get -y install cmake cmake-curses-gui make libexpat1-dev zlib1g-dev libbz2-dev
	sudo apt-get -y install libsparsehash-dev libboost-dev libgdal-dev libproj-dev doxygen graphviz

splitter:
	git clone https://github.com/joto/osm-history-splitter.git
	git clone https://github.com/osmcode/libosmium.git
	mkdir osm-history-splitter/build
	cd osm-history-splitter/build; cmake ..; make

taiwan.poly:
	wget http://download.geofabrik.de/asia/taiwan.poly

splitter.config:
	echo 'taiwan.osh.pbf POLY taiwan.poly' > splitter.config

extract: taiwan.poly splitter.config
	wget -c --no-show-progress $(URL_FULL_HISTORY)
	rm -f taiwan.osh.pbf
	time $(SPLITTER) $(FILE_FULL_HISTORY) splitter.config
	mkdir -p $(DATA_PATH)
	mv taiwan.osh.pbf $(FILE_HISTORY_EXTRACT)

# hints: targets with prefix "gcloud-" are invoked on gcloud instances
GCLOUD_SSH=gcloud compute --project "osm-history" ssh --zone "europe-west1-b" "osm-history"
GCLOUD_SCP=gcloud compute copy-files --zone "europe-west1-b"

create-gcloud-boot-disk:
	gcloud compute --project "osm-history" instances create "osm-history" --zone "europe-west1-b" --machine-type "custom-4-8192" --no-restart-on-failure --local-ssd interface="SCSI" --image "/ubuntu-os-cloud/ubuntu-1604-xenial-v20161221" --boot-disk-size "10" --no-boot-disk-auto-delete --boot-disk-device-name "osm-history"
	$(GCLOUD_SSH) sudo apt-get -y install make
	$(GCLOUD_SCP) Makefile "osm-history":/home/$(USER)
	$(GCLOUD_SSH) make ubuntu-depend
	$(GCLOUD_SSH) make splitter
	$(GCLOUD_SSH) sudo shutdown -P now
	echo y | gcloud compute --project "osm-history" instances delete osm-history --zone "europe-west1-b"

# need 60 minutes if > 2 cpu
gcloud-extract:
	#sudo mkfs.ext4 -F -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/disk/by-id/google-local-ssd-0
	#sudo mount /dev/disk/by-id/google-local-ssd-0 /mnt
	#sudo chown $(USER) /mnt
	cd /mnt && make -f $(shell pwd)/Makefile extract SPLITTER=$(shell pwd)/$(SPLITTER)

extract-by-gcloud-task:
	$(GCLOUD_SCP) Makefile "osm-history":/home/$(USER)
	$(GCLOUD_SSH) make gcloud-extract DATE=$(DATE)
	$(GCLOUD_SCP) "osm-history":/mnt/$(FILE_HISTORY_EXTRACT) $(FILE_HISTORY_EXTRACT)
	$(GCLOUD_SSH) sudo shutdown -P now && sleep 10

delete-gcloud-instance:
	echo y | gcloud compute --project "osm-history" instances delete osm-history --zone "europe-west1-b"

extract-by-gcloud:
	#gcloud compute --project "osm-history" instances create "osm-history" --zone "europe-west1-b" --machine-type "custom-4-8192" --no-restart-on-failure --disk "name=osm-history,device-name=osm-history,mode=rw,boot=yes" --local-ssd interface="SCSI"
	-make extract-by-gcloud-task
	-make delete-gcloud-instance
	[ -f "$(FILE_HISTORY_EXTRACT)" ]


###########################################################################################
