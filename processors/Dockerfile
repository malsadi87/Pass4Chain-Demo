FROM ubuntu:bionic

ENV VERSION=AUTO_STRICT
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y gnupg2 && apt-get install -y software-properties-common libsecp256k1-dev libsecp256k1-0
RUN apt-get install -y -q --no-install-recommends \
 python3.8 \
 python3-pip \
 python3-wheel

RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 8AA7AF1F1091A5FD \
  && add-apt-repository 'deb [arch=amd64] http://repo.sawtooth.me/ubuntu/chime/stable bionic universe' \
  && apt-get update \
  && apt-get install -y -q \
  apt-transport-https \
  build-essential \
  ca-certificates \
  gcc \
  libssl-dev \
  python3-setuptools \
  sawtooth \
  pkg-config \
  && apt-get clean \
&& rm -rf /var/lib/apt/lists/*

RUN pip3 install grpcio-tools sawtooth-sdk
RUN pip3 install --upgrade protobuf

WORKDIR /supply-chain
ENV PATH $PATH:/supply-chain/bin