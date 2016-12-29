FROM ubuntu:xenial
MAINTAINER Kuang-che Wu <kcwu@csie.org>

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y --no-install-recommends \
	git-core \
	ca-certificates \
	cmake \
	make \
	\
	g++ \
	libboost-dev \
	libbz2-dev \
	libexpat1-dev \
	libgeos++-dev \
	zlib1g-dev

WORKDIR /splitter
RUN git clone https://github.com/joto/osm-history-splitter.git \
 && git clone https://github.com/osmcode/libosmium.git \
 && mkdir osm-history-splitter/build \
 && cd osm-history-splitter/build \
 && cmake .. \
 && make install

# clean up
RUN apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /data
ENTRYPOINT ["/usr/local/bin/osm-history-splitter"]
