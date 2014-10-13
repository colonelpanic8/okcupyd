FROM debian:latest

RUN apt-get update && apt-get install -y python python-dev python-pip zlib1g-dev \
     libxml2-dev libxslt1-dev python-dev libncurses5-dev
ADD . /okcupyd
RUN cd /okcupyd && python setup.py install