FROM sourcepole/qwc-uwsgi-base:ubuntu-v2023.05.12

ADD . /srv/qwc_service

RUN \
    apt-get update && \
    apt-get install -y libpq-dev gcc && \
    pip3 install --no-cache-dir -r /srv/qwc_service/requirements.txt

ENV SERVICE_MOUNTPOINT=/giswater
