FROM ubuntu:bionic
ENV VERSION=AUTO_STRICT
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --allow-unauthenticated -q \
    python3-pip \
    python3-setuptools \
    python3-wheel

RUN pip3 install --upgrade pip
RUN pip3 install --upgrade setuptools

RUN pip3 install --upgrade protobuf
RUN pip3 install grpcio-tools

WORKDIR /supply-chain

ENV PATH $PATH:/supply-chain/bin