FROM osmtw/mapnik2:v2.2.0
MAINTAINER Kuang-che Wu <kcwu@csie.org>

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y git-core

# Install openstreetmap-carto
ENV OSM_CARTO_VERSION=v2.45.1
RUN git clone --depth 1 --branch ${OSM_CARTO_VERSION} https://github.com/gravitystorm/openstreetmap-carto.git /server/openstreetmap-carto

# Fetch and clip shapefiles
RUN cd /server/openstreetmap-carto \
 && apt-get install -y curl unzip gdal-bin \
 && ./get-shapefiles.sh \
 && rm data/*.zip data/*.tgz \
 && cd data \
 && for dir in *; \
	do ogr2ogr -s_srs EPSG:3857 -t_srs EPSG:4326 -clipdst 110 15 135 35 $dir.4326 $dir \
	&& rm -rf $dir \
	&& ogr2ogr -s_srs EPSG:4326 -t_srs EPSG:3857 $dir $dir.4326 \
	&& rm -rf $dir.4326 ; done \
 && shapeindex --shape_files */*.shp

RUN apt-get install -y npm \
 && ln -s /usr/bin/nodejs /usr/bin/node \
 && npm install -g carto \
 && cd /server/openstreetmap-carto \
 && sed -i -e 's/"dbname": "gis"/"host": "@HOST@", "port": "@PORT@", "user": "@USER@", "password": "@PASSWORD@", "dbname":"@DBNAME@"/' project.mml \
 && carto project.mml > style.xml

# font
RUN apt-get install -y \
	ttf-unifont \
	fonts-sipa-arundina \
	ttf-tamil-fonts \
	fonts-taml-tscu \
	ttf-indic-fonts-core \
	ttf-kannada-fonts \
	fonts-sil-padauk \
	fonts-khmeros \
	fonts-tibetan-machine \
	fonts-droid

# my tile server
RUN apt-get install -y \
	supervisor \
	\
	python-psycopg2 \
	python-pylibmc \
	python-cherrypy3
ADD supervisord.conf /etc/supervisord.conf

WORKDIR /server
RUN git clone https://github.com/OsmHackTW/osm-history.git \
 && cd /server/osm-history/server/static \
 && git clone https://github.com/Leaflet/Leaflet.fullscreen.git \
 && git clone https://github.com/turban/Leaflet.Sync.git \
 && git clone https://github.com/ebrelsford/Leaflet.loading.git \
 && git clone https://github.com/mlevans/leaflet-hash.git

# Clean up
RUN apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

CMD ["/usr/bin/supervisord", "--nodaemon", "--configuration=/etc/supervisord.conf"]
