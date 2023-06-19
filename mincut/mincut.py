"""
Copyright BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils
import json
import traceback
from .mincut_utils import manage_response

from flask import Blueprint, request, jsonify
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc

mincut_bp = Blueprint('mincut', __name__)


@mincut_bp.route('/setmincut', methods=['GET', 'POST'])
@optional_auth
def setmincut():
    """Set mincut

    Calls gw_fct_setmincut.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")
    action = args.get("action")
    xcoord = args.get("xcoord")
    ycoord = args.get("ycoord")
    zoomRatio = args.get("zoomRatio")
    mincutId = args.get("mincutId")

    if xcoord is None:
        xcoord = "null"
        ycoord = "null"
    
    theme_conf = utils.get_config().get("themes").get(theme)
    mincut_layer = theme_conf.get("mincut_layer")
    
    tiled = theme_conf.get("tiled", False) or mincut_layer is None
    # db fct
    coordinates = f'"epsg": {epsg}, "xcoord": {xcoord}, "ycoord": {ycoord}, "zoomRatio": {zoomRatio}'
    extras = f'"action": "{action}", "usePsectors": "False", "coordinates": {{{coordinates}}}'
    if mincutId is not None:
        extras += f', "mincutId": {mincutId}'
    body = utils.create_body(theme, project_epsg=epsg, extras=extras, tiled=tiled)
    result = utils.execute_procedure(log, theme, 'gw_fct_setmincut', body)
    result["body"]["data"]["mincutLayer"] = mincut_layer

    return manage_response(result, log, theme)


@mincut_bp.route('/open', methods=['GET'])
@optional_auth
def openmincut():
    """Open mincut

    Returns dialog of a wanted mincut.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    mincut_id = args.get("mincutId")

    # db fct
    extras = f'"mincutId": {mincut_id}'
    body = utils.create_body(theme, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_getmincut', body)

    return manage_response(result, log, theme)


@mincut_bp.route('/cancel', methods=['GET', 'POST'])
@optional_auth
def cancelmincut():
    """Cancel mincut

    Calls gw_fct_setmincut with action 'mincutCancel'.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    mincutId = args.get("mincutId")

    # db fct
    extras = f'"action": "mincutCancel", "mincutId": {mincutId}'
    body = utils.create_body(theme, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_setmincut', body)

    return manage_response(result, log, theme)


@mincut_bp.route('/delete', methods=['DELETE'])
@optional_auth
def deletemincut():
    """Delete mincut

    Deletes a mincut.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    mincut_id = args.get("mincutId")

    # db fct
    extras = f'"action": "mincutDelete", "mincutId": {mincut_id}'
    body = utils.create_body(theme, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_setmincut', body)

    return manage_response(result, log, theme)


@mincut_bp.route('/accept', methods=['POST'])
@optional_auth
def accept():
    """Accept mincut

    Calls gw_fct_setmincut with action 'mincutAccept'.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")
    mincutId = args.get("mincutId")
    fields = args.get("fields")
    usePsectors = args.get("usePsectors")
    xcoord = args.get("xcoord")
    ycoord = args.get("ycoord")
    zoomRatio = args.get("zoomRatio")

    if xcoord is None:
        xcoord = "null"
        ycoord = "null"

    # db fct
    feature = f'"featureType": "", "tableName": "om_mincut", "id": {mincutId}'
    coordinates = f'"epsg": {int(epsg)}, "xcoord": {xcoord}, "ycoord": {ycoord}, "zoomRatio": {zoomRatio}'
    extras = f'"action": "mincutAccept", "mincutClass": 1, "status": "check", "mincutId": {mincutId}, "usePsectors": "{usePsectors}", ' \
             f'"fields": {json.dumps(fields)}, "coordinates": {{{coordinates}}}'
    body = utils.create_body(theme, feature=feature, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_setmincut', body)

    return manage_response(result, log, theme)


@mincut_bp.route('/changevalvestatus', methods=['GET', 'POST'])
@optional_auth
def change_valve_status():
    """Change valve status

    Calls gw_fct_setchangevalvestatus.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")
    action = args.get("action")
    xcoord = args.get("xcoord")
    ycoord = args.get("ycoord")
    zoomRatio = args.get("zoomRatio")
    mincutId = args.get("mincutId")
    usePsectors = args.get("usePsectors", False)

    # db fct
    coordinates = f'"epsg": {epsg}, "xcoord": {xcoord}, "ycoord": {ycoord}, "zoomRatio": {zoomRatio}'
    extras = f'"mincutId": "{mincutId}", "usePsectors": "{usePsectors}", "coordinates": {{{coordinates}}}'
    body = utils.create_body(theme, project_epsg=epsg, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_setchangevalvestatus', body)

    return manage_response(result, log, theme)


@mincut_bp.route('/getmincutmanager', methods=['GET'])
@optional_auth
def getmanager():
    """Get mincut manager

    Returns mincut manager dialog.
    """
    log = utils.create_log(__name__)

    # args
    theme = request.args.get("theme")

    # db fct
    body = utils.create_body(theme, )
    result = utils.execute_procedure(log, theme, 'gw_fct_getmincut_manager', body)

    return manage_response(result, log, theme, manager=True)


@mincut_bp.route('/getlist', methods=['GET'])
@optional_auth
def getlist():
    """Get list

    Returns list of mincuts (for the manager).
    """
    log = utils.create_log(__name__)

    # args
    theme = request.args.get("theme")
    tabName = request.args.get("tabName")
    widgetname = request.args.get("widgetname")
    formtype = request.args.get("formtype")
    tableName = request.args.get("tableName")
    filterFields = request.args.get("filterFields")

    # Manage filters
    filterFields_dict = {}
    if filterFields in (None, "", "null", "{}"):
        filterFields_dict = None
    else:
        filterFields = json.loads(str(filterFields))
        for k, v in filterFields.items():
            if v in (None, "", "null"):
                continue
            filterFields_dict[k] = {
            #   "columnname": v["columnname"],
                "value": v["value"],
                "filterSign": v["filterSign"]
            }

    # db fct
    form = f'"formName": "", "tabName": "{tabName}", "widgetname": "{widgetname}", "formtype": "{formtype}"'
    feature = f'"tableName": "{tableName}"'
    filter_fields = json.dumps(filterFields_dict) if filterFields_dict else ''
    body = utils.create_body(theme, form=form, feature=feature, filter_fields=filter_fields)
    result = utils.execute_procedure(log, theme, 'gw_fct_getlist', body)

    return manage_response(result, log, theme)
