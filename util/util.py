"""
 Copyright BGEO. All rights reserved.
 The program is free software: you can redistribute it and/or modify it under the terms of the GNU
 General Public License as published by the Free Software Foundation, either version 3 of the License,
 or (at your option) any later version
""" 
import utils

import json
import traceback

from flask import Blueprint, request, jsonify
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc

util_bp = Blueprint('util', __name__)

@util_bp.route('/getlist', methods=['GET'])
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
    idName = request.args.get("idName")
    feature_id = request.args.get("id")

    # Manage filters
    filterFields_dict = {}
    if filterFields in (None, "", "null", "{}"):
        filterFields_dict = None
    else:
        filterFields = json.loads(str(filterFields))
        for k, v in filterFields.items():
            if v in (None, "", "null"):
                continue
            filterFields_dict[v.get("columnname", k)] = {
                "value": v.get("value"),
                "filterSign": v.get("filterSign", "=")
            }

    # db fct
    form = f'"formName": "", "tabName": "{tabName}", "widgetname": "{widgetname}", "formtype": "{formtype}"'
    if tableName  and feature_id:
        feature = f'"tableName": "{tableName}", "idName": "{idName}","id": "{feature_id}"'
    else:
        feature = f'"tableName": "{tableName}"'
    filter_fields = json.dumps(filterFields_dict)[1:-1] if filterFields_dict else ''
    body = utils.create_body(theme, form=form, feature=feature, filter_fields=filter_fields)
    result = utils.execute_procedure(log, theme, 'gw_fct_getlist', body)

    utils.remove_handlers(log)

    return utils.create_response(result, do_jsonify=True, theme=theme)