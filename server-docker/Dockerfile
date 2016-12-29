FROM osmtw/mapnik2:v2.2.0
MAINTAINER Kuang-che Wu <kcwu@csie.org>

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y git-core

# Install openstreetmap-carto
# TODO clip shapefile
ENV OSM_CARTO_VERSION=v2.39.0
RUN apt-get install -y curl unzip \
 && git clone --depth 1 --branch ${OSM_CARTO_VERSION} https://github.com/gravitystorm/openstreetmap-carto.git /server/openstreetmap-carto \
 && cd /server/openstreetmap-carto \
 && ./get-shapefiles.sh \
 && rm data/*.zip data/*.tgz

RUN apt-get install -y npm \
 && ln -s /usr/bin/nodejs /usr/bin/node \
 && npm install -g carto

# font for 16.04
#RUN apt-get install -y fonts-noto-cjk fonts-noto-hinted fonts-noto-unhinted ttf-unifont
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

# supervisor
ADD supervisord.conf /etc/supervisord.conf
RUN apt-get install -y supervisor
  
ADD datasource-settings.sh /server/datasource-settings.sh
RUN chmod 755 /server/datasource-settings.sh \
 && chown -R www-data /server/openstreetmap-carto

# my tile server
RUN apt-get install -y \
	python-psycopg2 \
	python-pylibmc \
	python-cherrypy3

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
