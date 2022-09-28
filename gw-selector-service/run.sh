#!/bin/bash
source /qwc-services/.venv/bin/activate
CONFIG_PATH=/qwc-services/config/ uwsgi /qwc-services/gw-selector-service/gw-selector-service.ini