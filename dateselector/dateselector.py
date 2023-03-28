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
    identity = get_identity()
    try:
        db = utils.get_db()
    except:
        utils.remove_handlers(log)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    layers = args.get("layers")
    epsg = args.get("epsg")
    dateFrom = args.get("dateFrom")
    dateTo = args.get("dateTo")

    schema = utils.get_schema_from_theme(theme, config)
    if schema is None:
        log.warning(" Schema is None")
        return jsonify({"schema": schema})

    log.info(f" Selected schema -> {str(schema)}")

    layers = utils.parse_layers(layers, config, theme)

    request_json =  {
        "client": {
            "device": 5, "infoType": 1, "lang": "en_US", "cur_user": str(identity)
        }, 
        "form": {}, 
        "feature": {},
        "data": {
            "filterFields":{},
            "pageInfo":{},
            "layers": layers
        }
    }

    if request.method == 'GET':
        request_json["data"]["action"] = "GET"
    else:
        request_json["data"]["action"] = "SET"
        request_json["data"]["date_from"] = dateFrom
        request_json["data"]["date_to"] = dateTo

    request_json = json.dumps(request_json)
    sql = f"SELECT {schema}.gw_fct_dateselector($${request_json}$$);"
    log.info(f" Server execution -> {sql}")
    print(f"SERVER EXECUTION: {sql}\n")
    with db.begin() as conn:
        result = dict()
        try:
            result = conn.execute(text(sql)).fetchone()[0]
        except exc.ProgrammingError:
            log.warning(" Server execution failed")
            print(f"Server execution failed\n{traceback.format_exc()}")
            utils.remove_handlers(log)
        log.info(f" Server response -> {json.dumps(result)}")
        print(f"SERVER RESPONSE: {json.dumps(result)}\n")
        utils.remove_handlers(log)
        return handle_db_result(result, theme)
