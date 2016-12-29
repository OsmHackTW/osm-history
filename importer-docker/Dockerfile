FROM ubuntu:xenial
MAINTAINER Kuang-che Wu <kcwu@csie.org>

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y --no-install-recommends \
        make \
        git-core \
	ca-certificates \
	g++ \
	\
        libboost-dev \
        libexpat1-dev \
        libgeos++-dev \
	libosmium-dev \
	libosmpbf-dev \
	libsparsehash-dev \
        zlib1g-dev \
	\
        libpq-dev \
	libproj-dev

RUN git clone https://github.com/MaZderMind/osm-history-renderer.git --single-branch \
 && make -C osm-history-renderer/importer CXX=g++

# clean up
RUN apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /osm-history-renderer/importer
ADD ./osm-importer.sh /osm-history-renderer/importer
ENTRYPOINT ["/bin/bash", "./osm-importer.sh"]
