FROM ubuntu

MAINTAINER ujnamss "ujnamss@gmail.com"

RUN apt-get update
RUN apt-get install -y python3-pip python3-dev

# update pip
RUN python3 -m pip install --upgrade pip

ADD install/requirements.txt /app/requirements.txt

RUN python3 -m pip install -Ur /app/requirements.txt

ENV HOME_DIR /homedir
ENV src_src_path $HOME_DIR/zb-api/src
ENV PORT 20002
ENV PYTHONIOENCODING utf-8
ENV PYTHONUNBUFFERED TRUE

WORKDIR $HOME_DIR/zb-api/src

CMD python3 -u api.py
