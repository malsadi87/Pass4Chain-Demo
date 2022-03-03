FROM ubuntu:impish

ENV VERSION=AUTO_STRICT
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED=1

RUN apt-get update

RUN apt-get install -y -q --no-install-recommends \
  python3-pip \
  python3-wheel \
  python3-setuptools

RUN pip3 install rethinkdb fastapi pydantic uvicorn websockets
# RUN pip3 install --upgrade protobuf

WORKDIR /supply_chain
ENV PATH $PATH:/supply_chain/bin