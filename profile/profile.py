"""
Copyright © 2023 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils
from .profile_utils import handle_db_result, get_profiletool_ui, generate_profile_svg

import os

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/getdialog', methods=['GET'])
@jwt_required()
def getdialog():
    """Submit query

    Returns profiletool dialog.
    """
    log = utils.create_log(__name__)

    # Get dialog
    form_xml = get_profiletool_ui()

    # Response
    response = {
        "feature": {},
        "form_xml": form_xml
    }
    utils.remove_handlers(log)
    return jsonify(response)


@profile_bp.route('/nodefromcoordinates', methods=['GET'])
@jwt_required()
def nodefromcoordinates():
    """Submit query

    Returns additional information at clicked map position.
    """
    config = utils.get_config()
    log = utils.create_log(__name__)
   
    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    layers = args.get("layers")
    epsg = args.get("epsg")
    coords = args.get("coords")
    zoom = args.get("zoom")
    # xcoord = args.get("xcoord")
    # ycoord = args.get("ycoord")
    # zoomRatio = args.get("zoomRatio")

    coords = coords.split(',')
    #layers = utils.parse_layers(layers, config, theme)

    extras = f'"coordinates": {{ "epsg": {int(epsg)},"xcoord": {coords[0]},"ycoord": {coords[1]},"zoomRatio": {float(zoom)}}}'

    body = utils.create_body(theme=theme, project_epsg=epsg, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_checknode', body)

    return handle_db_result(result)


@profile_bp.route('/profileinfo', methods=['GET'])
@jwt_required()
def profileinfo():
    """
    Submit query
    Returns additional information at clicked map position.
    """
    log = utils.create_log(__name__)
    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")
    initNode = args.get("initNode")
    endNode = args.get("endNode")

    extras = f'"initNode": {initNode}, "endNode": {endNode}, "linksDistance": "1"'

    body = utils.create_body(theme=theme, project_epsg=epsg, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_getprofilevalues', body)

    utils.remove_handlers(log)
    return handle_db_result(result)


@profile_bp.route('/profilesvg', methods=['GET'])
@jwt_required()
def profilesvg():
    log = utils.create_log(__name__)
    config = utils.get_config()
    args = request.get_json(force=True) if request.is_json else request.args

    # args
    theme = args.get("theme")
    epsg = args.get("epsg")
    initNode = args.get("initNode")
    endNode = args.get("endNode")
    vnodeDist = args.get("vnodeDist")
    title = args.get("title")
    date = args.get("date")
    
    extras = f'"initNode": {initNode}, "endNode": {endNode}, "linksDistance": {vnodeDist}'

    body = utils.create_body(theme=theme, project_epsg=epsg, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_getprofilevalues', body)
    
    utils.remove_handlers(log)
    
    params = {'title': title, 'date': date}

    images_url = config.get('images_url')
    img_path = generate_profile_svg(result, params)
    img_path = f'{images_url}profile/{os.path.basename(img_path)}'
    return img_path