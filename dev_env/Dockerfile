FROM ubuntu:bionic

RUN apt-get update && apt-get install -y gnupg2 && apt-get install -y software-properties-common libsecp256k1-dev libsecp256k1-0

RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 8AA7AF1F1091A5FD \
  && add-apt-repository 'deb [arch=amd64] http://repo.sawtooth.me/ubuntu/chime/stable bionic universe' \
  && apt-get update

RUN apt-get install -y -q --no-install-recommends \
  gcc \
  build-essential \
  python3-pip \
  python3-wheel \
  python3-setuptools \
  pkg-config

RUN apt-get install -y -q \
  apt-transport-https \
  ca-certificates \
  libssl-dev \
  sawtooth \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip3 install sawtooth-sdk rethinkdb fastapi
RUN pip3 install --upgrade protobuf