#!/bin/bash
source /qwc-services/.venv/bin/activate
CONFIG_PATH=/qwc-services/config/ uwsgi /qwc-services/gw-info-service/gw-info-service.ini