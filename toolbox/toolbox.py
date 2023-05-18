"""
 Copyright BGEO. All rights reserved.
 The program is free software: you can redistribute it and/or modify it under the terms of the GNU
 General Public License as published by the Free Software Foundation, either version 3 of the License,
 or (at your option) any later version
""" 
import utils
from .toolbox_utils import handle_process_db_result

import json
import traceback

from flask import Blueprint, request, jsonify
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc

toolbox_bp = Blueprint('toolbox', __name__)


@toolbox_bp.route('/gettoolbox', methods=['GET'])
@optional_auth
def gettoolbox():
    """Submit query

    Returns additional information at clicked map position.
    """
    config = utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    search_filter = args.get("filter", "")
    
    extras = f'"isToolbox": true, "filterText": "{search_filter}"'
    body = utils.create_body(theme, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_gettoolbox', body)

    tools_whitelist = config.get("themes").get(theme).get("toolsWhitelist")
    if tools_whitelist:
        fields = result["body"]["data"]["processes"]["fields"]
        new_fields = {}
        for tab, tools in fields.items():
            for tool in tools:
                if tool["id"] in tools_whitelist:
                    new_fields.setdefault(tab, []).append(tool)
        result["body"]["data"]["processes"]["fields"] = new_fields

    utils.remove_handlers(log)

    return utils.create_response(result, do_jsonify=True, theme=theme)

@toolbox_bp.route('/getprocess', methods=['POST'])
@optional_auth
def getprocess():
    """Submit query

    Returns additional information at clicked map position.
    """
    config = utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    func_id = args.get("id")
    parent_vals = args.get("parentVals", {})

    extras = f'"functionId": "{func_id}"'
    body = utils.create_body(theme, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_getprocess', body)

    utils.remove_handlers(log)

    return handle_process_db_result(result, parent_vals)


@toolbox_bp.route('/execute_process', methods=['POST'])
@optional_auth
def execute_process():
    """Submit query

    Returns additional information at clicked map position.
    """
    config = utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    function_name = args.get("functionname")
    params = args.get("params")
    feature_type = args.get("featureType")
    table_name = args.get("tableName")

    print(args)

    extras = f'"parameters": {json.dumps(params)}'

    feature = ''
    if table_name is not None:
        feature = f'"featureType": "{feature_type}", "tableName": "{table_name}"'

    body = utils.create_body(theme, feature=feature, extras=extras)
    result = utils.execute_procedure(log, theme, function_name, body)

    utils.remove_handlers(log)

    return jsonify(result)
