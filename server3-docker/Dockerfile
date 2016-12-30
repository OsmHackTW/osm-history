FROM osmtw/mapnik3:v3.0.9
MAINTAINER Kuang-che Wu <kcwu@csie.org>

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y git-core

# Install openstreetmap-carto
# TODO clip shapefile
ENV OSM_CARTO_VERSION=v3.0.1
RUN apt-get install -y curl unzip \
 && git clone --branch ${OSM_CARTO_VERSION} https://github.com/gravitystorm/openstreetmap-carto.git /server/openstreetmap-carto
 && cd /server/openstreetmap-carto \
 && ./scripts/get-shapefiles.py

RUN apt-get install -y npm \
 && ln -s /usr/bin/nodejs /usr/bin/node \
 && npm install -g carto \
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
