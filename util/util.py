"""
Copyright © 2025 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
import utils

import json
import traceback

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from qwc_services_core.auth import optional_auth, get_identity, get_username
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
        if isinstance(filterFields, str):
            try:
                filterFields = json.loads(filterFields)
            except json.JSONDecodeError as e:
                print("Error at filterFields JSON:", e)
                filterFields = {}

        if isinstance(filterFields, dict):
            for k, v in filterFields.items():
                if isinstance(v, dict) and v.get("value") not in (None, "", "null"):
                    column_name = v.get("columnname", k)
                    filterFields_dict[column_name] = {
                        "value": v.get("value"),
                        "filterSign": v.get("filterSign", "=")
                    }
                elif isinstance(v, str):
                    filterFields_dict[k] = {
                        "value": v,
                        "filterSign": "="
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

@util_bp.route('/getlayers', methods=['GET'])
@jwt_required()
def getlayers():
    """ Get layers of theme"""
    # args
    theme = request.args.get("theme")
    result = utils.get_config().get("themes").get(theme).get("groups")
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
    result = utils.execute_procedure(log, theme, 'gw_fct_setfields', body, needs_write=True)

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
    result = utils.execute_procedure(log, theme, 'gw_fct_setinitproject', body, set_role=False, needs_write=True)

    utils.remove_handlers(log)

    return utils.create_response(result, do_jsonify=True, theme=theme)

@util_bp.route('/dialog', methods=['GET'])
@jwt_required()
def dialog():
    """Open Dialog

    Returns XML structure dialog.
    """
    # open dialog
    utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    dialog_name = args.get("dialogName")
    layout_name = args.get("layoutName")

    # db fct
    form = f'"formName":"generic", "formType":"{dialog_name}"'

    if args.get("idName") is not None:
        form += f', "idname":"{args.get("idName")}"'

    if args.get("id") is not None:
        form += f', "id":"{args.get("id")}"'

    if args.get("tableName") is not None:
        form += f', "tableName":"{args.get("tableName")}"'


    body = utils.create_body(theme, form=form)

    result = utils.execute_procedure(log, theme, 'gw_fct_get_dialog', body, needs_write=True)
    utils.remove_handlers(log)
    form_xml = utils.create_xml_generic_form(result, dialog_name, layout_name)
    return utils.create_response(result, form_xml=form_xml, do_jsonify=True, theme=theme)


@util_bp.route('/getfilters', methods=['GET'])
@jwt_required()
def getfilters():

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    schema_name = utils.get_schema_from_theme(theme, utils.get_config())
    db = utils.get_db(theme, needs_write=True)

    with db.begin() as conn:
        sector_options = dict()
        identity = get_username(get_identity())
        conn.execute(text(f"SET ROLE '{identity}';"))

        # Get basic_selector_options param
        sql = f"SELECT value FROM {schema_name}.config_param_system WHERE parameter = 'basic_selector_options'"
        sector_options = conn.execute(text(sql)).fetchone()[0]

    json_options = json.loads(sector_options)

    print("json_options: ", json_options)

    muni_option = json_options.get('muniClientFilter', False)
    sector_option = json_options.get('sectorClientFilter', False)

    # Build and Apply filters
    muni_filter, sector_filter = _build_filter(theme)

    # Create a dict to manage filters
    filters = {
        "muni_filter": muni_filter if muni_option and muni_filter else None,
        "sector_filter": sector_filter if sector_option and sector_filter else None,
    }
    return filters

def _build_filter(theme):

    log = utils.create_log(__name__)

    # Call get_selectors
    extras = f'"selectorType":"selector_basic", "filterText":""'
    body = utils.create_body(theme,extras=extras)
    json_result = utils.execute_procedure(log,theme,'gw_fct_getselectors', body, set_role=False, needs_write=True)

    muni_filter = []
    sector_filter = []

    if json_result is not None:
        try:
            form_tabs = json_result.get('body', {}).get('form', {}).get('formTabs', [])
            for selector in form_tabs:
                if selector.get('tableName') == 'selector_municipality':
                    filter = []
                    for field in selector.get('fields', []):
                        if field.get('value'):
                            column_name = field.get('columnname')
                            if column_name:
                                filter.append(field[column_name])
                    if filter:
                        muni_filter = filter

                elif selector.get('tableName') == 'selector_sector':
                    filter = []
                    for field in selector.get('fields', []):
                        if field.get('value'):
                            column_name = field.get('columnname')
                            if column_name:
                                filter.append(field[column_name])
                    if filter:
                        sector_filter = filter

        except KeyError as e:
            print(f"KeyError encountered: {e}")

    return muni_filter, sector_filter