"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
import utils

import json
import traceback

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc


from flask_mail import Message

util_bp = Blueprint('util', __name__)

@util_bp.route('/getlist', methods=['GET'])
@jwt_required()
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
    limit = request.args.get("limit", -1)

    # Manage filters
    filterFields_dict = {}
    if filterFields not in (None, "", "null", "{}"):
        filterFields = json.loads(str(filterFields))
        for k, v in filterFields.items():
            if v in (None, "", "null"):
                continue
            filterFields_dict[v.get("columnname", k)] = {
                "value": v.get("value"),
                "filterSign": v.get("filterSign", "=")
            }

    filterFields_dict["limit"] = limit

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

    # TODO: This is only for diabling mincut selector in tiled
    theme_conf = utils.get_config().get("themes").get(theme)
    result["body"]["data"]["mincutLayer"] = theme_conf.get("mincut_layer")

    return utils.create_response(result, do_jsonify=True, theme=theme)


@util_bp.route('/setfields', methods=['PUT'])
@jwt_required()
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

    # Manage fields
    fields_dict = {}
    if fields not in (None, "", "null", "{}"):
        fields = json.loads(str(fields))
        for k, v in fields.items():
            if v in (None, "", "null"):
                continue
            if type(v) is str:
                fields_dict[k] = v
                continue
            fields_dict[v.get("columnname", k)] = v.get("value")

    # db fct
    feature = f'"id": "{id_}", "tableName": "{tableName}", "featureType": "{featureType}"'
    fields = json.dumps(fields_dict) if fields_dict else ''
    extras = f'"fields": {fields}'
    body = utils.create_body(theme, feature=feature, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_setfields', body)

    utils.remove_handlers(log)

    return utils.create_response(result, do_jsonify=True, theme=theme)


@util_bp.route('/setinitproject', methods=['POST'])
@jwt_required()
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