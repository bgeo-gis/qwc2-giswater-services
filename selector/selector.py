"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils
from .selector_utils import make_response

import json
import traceback

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from qwc_services_core.auth import optional_auth
from sqlalchemy import text, exc

selector_bp = Blueprint('selector', __name__)


@selector_bp.route('/get', methods=['GET'])
@jwt_required()
def getselector():
    """Get selector

    Returns selector dialog.
    """
    config = utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")
    currentTab = args.get("currentTab")
    selectorType = args.get("selectorType")
    ids = args.get("ids")

    # db fct
    form = f'"currentTab": "{currentTab}"'
    extras = f'"selectorType": "{selectorType}", "filterText": ""'
    if ids:
        ids = ids.split(",")
        ids_list = [int(x) for x in ids]
        extras += f', "ids": {ids_list}'
    body = utils.create_body(theme, project_epsg=epsg, form=form, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_getselectors', body)

    return make_response(result, theme, config, log)


@selector_bp.route('/set', methods=['POST'])
@jwt_required()
def setselector():
    """Set selector

    Updates selectors based on user input (and returns updated dialog).
    """
    config = utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")
    selectorType = args.get("selectorType")
    tabName = args.get("tabName")
    value = args.get("value")
    widget_id = args.get("id")
    isAlone = args.get("isAlone")
    disableParent = args.get("disableParent")
    addSchema = args.get("addSchema")
    ids = args.get("ids")

    theme_conf = utils.get_config().get("themes").get(theme)
    tiled = theme_conf.get("tiled", False)
    # db fct
    extras = f'"selectorType": "{selectorType}", "tabName": "{tabName}", "addSchema": "{addSchema}"'
    if ids:
        ids = ids.split(",")
        ids_list = [int(x) for x in ids]
        extras += f', "ids": {ids_list}'
    if widget_id == 'chk_all':
        extras += f', "checkAll": "{value}"'
    else:
        extras += f', "id": "{widget_id}", "isAlone": "{isAlone}", "disableParent": "{disableParent}", "value": "{value}"'

    body = utils.create_body(theme, project_epsg=epsg, extras=extras, tiled=tiled)
    result = utils.execute_procedure(log, theme, 'gw_fct_setselectors', body, needs_write=True)

    return make_response(result, theme, config, log)


@selector_bp.route('/getlayersfiltered', methods=['PUT'])
@jwt_required()
def getlayersfiltered():
    """Get layers filtered

    Returns WMS layers that contain the indicated columns.
    """

    config = utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    filter_columns = args.get("filter")
    queryLayers = args.get("queryLayers")

    # db fct
    extras = f'"filter": {json.dumps(filter_columns)}, "layers": {json.dumps(queryLayers)}'
    body = utils.create_body(theme, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_getlayerstofilter', body, needs_write=True)

    return make_response(result, theme, config, log)
