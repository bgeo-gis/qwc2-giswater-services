"""
Copyright © 2025 by BGEO. All rights reserved.
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
from flask_jwt_extended import jwt_required
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc

mincut_bp = Blueprint('mincut', __name__)


@mincut_bp.route('/setmincut', methods=['GET', 'POST'])
@jwt_required()
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
    xcoord = args.get("xcoord", "null")
    ycoord = args.get("ycoord", "null")
    zoomRatio = args.get("zoomRatio", "null")
    mincutId = args.get("mincutId")

    theme_conf = utils.get_config().get("themes").get(theme)
    mincut_layer = theme_conf.get("mincut_layer")

    tiled = theme_conf.get("tiled", False) or mincut_layer is None
    # db fct
    coordinates = f'"epsg": {epsg}, "xcoord": {xcoord}, "ycoord": {ycoord}, "zoomRatio": {zoomRatio}'
    extras = f'"action": "{action}", "usePsectors": "False", "coordinates": {{{coordinates}}}, "status": "check"'
    if mincutId is not None:
        extras += f', "mincutId": {mincutId}'
    body = utils.create_body(theme, project_epsg=epsg, extras=extras, tiled=tiled)
    result = utils.execute_procedure(log, theme, 'gw_fct_setmincut', body, needs_write=True)
    result["body"]["data"]["mincutLayer"] = mincut_layer

    return manage_response(result, log, theme)


@mincut_bp.route('/open', methods=['GET'])
@jwt_required()
def openmincut():
    """Open mincut

    Returns dialog of a wanted mincut.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    mincut_id = args.get("mincutId")

    theme_conf = utils.get_config().get("themes").get(theme)

    mincut_layer = theme_conf.get("mincut_layer")
    tiled = theme_conf.get("tiled", False) or mincut_layer is None

    # db fct
    extras = f'"mincutId": {mincut_id}'
    body = utils.create_body(theme, extras=extras, tiled=tiled)
    result = utils.execute_procedure(log, theme, 'gw_fct_getmincut', body, needs_write=True)
    result["body"]["data"]["mincutLayer"] = mincut_layer

    return manage_response(result, log, theme)


@mincut_bp.route('/cancel', methods=['GET', 'POST'])
@jwt_required()
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
    result = utils.execute_procedure(log, theme, 'gw_fct_setmincut', body, needs_write=True)

    return manage_response(result, log, theme)


@mincut_bp.route('/delete', methods=['DELETE'])
@jwt_required()
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
    result = utils.execute_procedure(log, theme, 'gw_fct_setmincut', body, needs_write=True)

    return manage_response(result, log, theme)


@mincut_bp.route('/accept', methods=['POST'])
@jwt_required()
def accept():
    """Accept mincut

    Calls gw_fct_setmincut with action 'mincutAccept'.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    mincutId = args.get("mincutId")
    fields = args.get("fields")
    usePsectors = args.get("usePsectors")

    # db fct
    feature = f'"featureType": "", "tableName": "om_mincut", "id": {mincutId}'
    extras = (
        f'"action": "mincutAccept", "mincutId": {mincutId}, "status": "check", "usePsectors": "{usePsectors}", ' \
        f'"fields": {json.dumps(fields)}'
    )
    body = utils.create_body(theme, feature=feature, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_setmincut', body, needs_write=True)

    return manage_response(result, log, theme)


@mincut_bp.route('/changevalvestatus', methods=['GET', 'POST'])
@jwt_required()
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
    result = utils.execute_procedure(log, theme, 'gw_fct_setchangevalvestatus', body, needs_write=True)

    return manage_response(result, log, theme)


@mincut_bp.route('/getmincutmanager', methods=['GET'])
@jwt_required()
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
