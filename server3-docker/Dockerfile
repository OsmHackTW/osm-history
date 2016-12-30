FROM osmtw/mapnik3:v3.0.9
MAINTAINER Kuang-che Wu <kcwu@csie.org>

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y git-core

# Install openstreetmap-carto
ENV OSM_CARTO_VERSION=v3.0.1
RUN git clone --depth 1 --branch ${OSM_CARTO_VERSION} https://github.com/gravitystorm/openstreetmap-carto.git /server/openstreetmap-carto

# Fetch and clip shapefiles
RUN cd /server/openstreetmap-carto \
 && apt-get install -y curl gdal-bin \
 && ./scripts/get-shapefiles.py --remove \
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
 && npm cache clean \
 && cd /server/openstreetmap-carto \
 && sed -i -e 's/dbname: "gis"/host: "@HOST@"\n    port: "@PORT@"\n    user: "@USER@"\n    password: "@PASSWORD@"\n    dbname: "@DBNAME@"/' project.mml \
 && carto project.mml > style.xml

# font
RUN apt-get install -y fonts-noto-cjk fonts-noto-hinted fonts-noto-unhinted ttf-unifont

# my tile server
RUN apt-get install -y \
	supervisor \
	\
	python-psycopg2 \
	python-pylibmc \
	python-cherrypy3
ADD supervisord.conf /etc/supervisord.conf

WORKDIR /server
RUN git clone --depth 1 https://github.com/OsmHackTW/osm-history.git \
 && cd /server/osm-history/server/static \
 && git clone --depth 1 https://github.com/Leaflet/Leaflet.fullscreen.git \
 && git clone --depth 1 https://github.com/turban/Leaflet.Sync.git \
 && git clone --depth 1 https://github.com/ebrelsford/Leaflet.loading.git \
 && git clone --depth 1 https://github.com/mlevans/leaflet-hash.git

# Clean up
RUN apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

CMD ["/usr/bin/supervisord", "--nodaemon", "--configuration=/etc/supervisord.conf"]
