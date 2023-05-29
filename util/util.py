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


@util_bp.route('/setfields', methods=['PUT'])
@optional_auth
def setfields():
    """Submit query

    Returns additional information at clicked map position.
    """
    config = utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    id_ = args.get("id")
    tableName = args.get("tableName")
    featureType = args.get("featureType")
    fields = args.get("fields")

    # db fct
    feature = f'"id": "{id_}", "tableName": "{tableName}", "featureType": "{featureType}"'
    extras = f'"fields": {json.dumps(fields)}'
    body = utils.create_body(theme, feature=feature, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_setfields', body)

    utils.remove_handlers(log)

    return utils.create_response(result, do_jsonify=True, theme=theme)


@util_bp.route('/setinitproject', methods=['POST'])
@optional_auth
def setinitproject():
    """Submit query

    gw_fct_setinitproject
    """
    config = utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")

    # db fct
    body = utils.create_body(theme, project_epsg=epsg)
    result = utils.execute_procedure(log, theme, 'gw_fct_setinitproject', body)

    utils.remove_handlers(log)

    return utils.create_response(result, do_jsonify=True, theme=theme)
