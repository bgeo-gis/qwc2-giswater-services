FROM sourcepole/qwc-uwsgi-base:ubuntu-v2023.05.12

ADD ./requirements.txt /srv/qwc_service/requirements.txt

RUN \
    apt-get update && \
    apt-get install -y libpq-dev gcc && \
    pip3 install --no-cache-dir -r /srv/qwc_service/requirements.txt

ADD . /srv/qwc_service

ENV SERVICE_MOUNTPOINT=/giswater
