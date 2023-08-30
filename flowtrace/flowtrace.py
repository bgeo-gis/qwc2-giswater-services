"""
Copyright © 2023 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from qwc_services_core.auth import optional_auth

flowtrace_bp = Blueprint('flowtrace', __name__)


@flowtrace_bp.route('/upstream', methods=['GET'])
@jwt_required()
def upstream():
    """Upstream

    Runs flowtrace upstream at clicked map position.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")
    coords = args.get("coords").split(',')
    zoom = args.get("zoom")

    # db fct
    coordinates = f'"epsg": {int(epsg)}, "xcoord": {coords[0]}, "ycoord": {coords[1]}, "zoomRatio": {float(zoom)}'
    extras = f'"coordinates": {{{coordinates}}}'
    body = utils.create_body(theme, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_graphanalytics_upstream', body)

    utils.remove_handlers(log)

    return utils.create_response(result, do_jsonify=True, theme=theme)


@flowtrace_bp.route('/downstream', methods=['GET'])
@jwt_required()
def downstream():
    """Downstream

    Runs flowtrace downstream at clicked map position.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")
    coords = args.get("coords").split(',')
    zoom = args.get("zoom")

    # db fct
    coordinates = f'"epsg": {int(epsg)}, "xcoord": {coords[0]}, "ycoord": {coords[1]}, "zoomRatio": {float(zoom)}'
    extras = f'"coordinates": {{{coordinates}}}'
    body = utils.create_body(theme, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_graphanalytics_downstream', body)

    utils.remove_handlers(log)

    return utils.create_response(result, do_jsonify=True, theme=theme)
