#!/bin/bash
source /qwc-services/.venv/bin/activate
CONFIG_PATH=/qwc-services/config/ uwsgi /qwc-services/qwc2-giswater-services/gw-flowtrace-service/gw-flowtrace-service.ini
