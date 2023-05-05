"""
Copyright BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-


import utils
from .dateselector_utils import handle_db_result, get_dateselector_ui

import json
import traceback

from flask import Blueprint, request, jsonify
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc


dateselector_bp = Blueprint('dateselector', __name__)

@dateselector_bp.route('/dialog', methods=['GET'])
@optional_auth
def dialog():
    """Submit query

    Returns dateselector dialog.
    """
    log = utils.create_log(__name__)

    # Get dialog
    form_xml = get_dateselector_ui()

    # Response
    response = {
        "feature": {},
        "data": {},
        "form_xml": form_xml
    }
    utils.remove_handlers(log)
    return jsonify(response)


@dateselector_bp.route('/dates', methods=['GET', 'PUT'])
@optional_auth
def dates():
    """Submit query

    Get current user's dates.
    """

    # Get current dates
    config = utils.get_config()
    log = utils.create_log(__name__)
    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    layers = args.get("layers")
    epsg = args.get("epsg")
    dateFrom = args.get("dateFrom")
    dateTo = args.get("dateTo")

    layers = utils.parse_layers(layers, config, theme)
 
    #extras = f'"layers": "{layers}", '
    if request.method == 'GET':
        extras =f'"action": "GET"'
        #request_json["data"]["action"] = "GET"
    else:
        #request_json["data"]["action"] = "SET"
        #request_json["data"]["date_from"] = dateFrom
        #request_json["data"]["date_to"] = dateTo
        extras = f'"action": "SET", "date_from" : "{dateFrom}", "date_to" : "{dateTo}"'
    body = utils.create_body(theme=theme, project_epsg=epsg, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_dateselector', body)

    utils.remove_handlers(log)
    return handle_db_result(result, theme)
