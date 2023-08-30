"""
Copyright © 2023 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils
from .info_utils import create_xml_form

import json
import traceback

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc

info_bp = Blueprint('info', __name__)


@info_bp.route('/fromcoordinates', methods=['GET'])
@jwt_required()
def fromcoordinates():
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
    xcoord = args.get("xcoord")
    ycoord = args.get("ycoord")
    zoomRatio = args.get("zoomRatio")

    layers = utils.parse_layers(layers, config, theme)

    # db fct
    form = f'"editable": "False"'
    coordinates = f'"epsg": {int(epsg)}, "xcoord": {xcoord}, "ycoord": {ycoord}, "zoomRatio": {zoomRatio}'
    extras = f'"activeLayer": "{layers[0]}", "visibleLayers": {json.dumps(layers)}, "coordinates": {{{coordinates}}}'
    body = utils.create_body(theme, form=form, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_getinfofromcoordinates', body)

    editable = config.get("themes").get(theme).get("editable", False)
    # form xml
    try:
        form_xml = create_xml_form(result, editable)
    except:
        form_xml = None

    utils.remove_handlers(log)

    return utils.create_response(result, form_xml=form_xml, do_jsonify=True, theme=theme)


@info_bp.route('/fromid', methods=['GET'])
@jwt_required()
def fromid():
    config = utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    tableName = args.get("tableName")
    feature_id = args.get("id")

    # db fct
    form = f'"editable": "False"'
    feature = f'"tableName": "{tableName}", "id": "{feature_id}"'
    body = utils.create_body(theme, form=form, feature=feature)
    result = utils.execute_procedure(log, theme, 'gw_fct_getinfofromid', body)

    editable = config.get("themes").get(theme).get("editable", False)
    # form xml
    try:
        form_xml = create_xml_form(result, editable)
    except Exception as e:
        print(e)
        form_xml = None

    utils.remove_handlers(log)

    return utils.create_response(result, form_xml=form_xml, do_jsonify=True, theme=theme)


@info_bp.route('/getlist', methods=['GET'])
@jwt_required()
def getlist():
    config = utils.get_config()
    log = utils.create_log(__name__)
    try:
        db = utils.get_db()
    except:
        utils.remove_handlers(log)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    tabName = args.get("tabName")
    widgetname = args.get("widgetname")
    formtype = args.get("formtype")
    tableName = args.get("tableName")
    idName = args.get("idName")
    feature_id = args.get("id")
    filterSign = args.get("filterSign") or "="
    filterFields = args.get("filterFields") or {}

    schema = utils.get_schema_from_theme(theme, config)

    request_json =  {
        "client": {
            "device": 5, "infoType": 1, "lang": "en_US"
        },
        "form": {
            "formName": "",
            "tabName": str(tabName),
            "widgetname": str(widgetname),
            "formtype": str(formtype)
        },
        "feature": {
            "tableName": tableName,
            "idName": idName,
            "id": feature_id
        },
        "data": {
            "filterFields": {
                idName: {
                    "columnname": idName,
                    "value": feature_id,
                    "filterSign": str(filterSign)
                }
            },
            "pageInfo": {}
        }
    }

    # Manage filters
    filterFields = json.loads(filterFields) if type(filterFields) == str else filterFields
    # if filterFields:
    for k, v in filterFields.items():
        if v in (None, "", "null"):
            continue
        request_json["data"]["filterFields"][v.get("columnname")] = {
            "value": v.get("value"),
            "filterSign": v.get("filterSign", "=")
    }

    request_json = json.dumps(request_json)

    result = utils.execute_procedure(log, theme, 'gw_fct_getlist', f"$${request_json}$$")
    utils.remove_handlers(log)
    return utils.create_response(result, do_jsonify=True, theme=theme)


@info_bp.route('/getgraph', methods=['GET'])
@jwt_required()
def getgraph():
    """
    Submit query
    Returns additional information at clicked map position.
    """

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    node_id = args.get("node_id")

    log = utils.create_log(__name__)
    feature= f'"type":"node", "id": {node_id}, "parameter":"", "interval":"","result_id":"e96"'

    body = utils.create_body(theme=theme, feature=feature)
    result = utils.execute_procedure(log, theme, 'gw_fct_gettimeseries', body)

    return utils.create_response(db_result=result, do_jsonify=True, theme=theme)

    request_json = json.dumps(request_json)
    sql = f"SELECT {schema}.gw_fct_gettimeseries($${request_json}$$);"
    log.info(f" Server execution -> {sql}")
    print(f"SERVER EXECUTION: {sql}\n")
    result = dict()
    try:
        result = db.execute(sql).fetchone()[0]
    except exc.ProgrammingError:
        log.warning(" Server execution failed")
        print(f"Server execution failed\n{traceback.format_exc()}")
        utils.remove_handlers(log)

    log.info(f" Server response {str(result)[0:100]}")
    print(f"SERVER RESPONSE: {json.dumps(result)}\n\n")
    utils.remove_handlers(log)
    return jsonify(result)


@info_bp.route('/getdma', methods=['GET'])
@jwt_required()
def getdma():
    """
    Submit query
    Returns additional information at clicked map position.
    """
    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    # layers = args.get("layers")
    epsg = args.get("epsg")
    xcoord = args.get("xcoord")
    ycoord = args.get("ycoord")
    zoomRatio = args.get("zoomRatio")
 
    config = utils.get_config()
    log = utils.create_log(__name__)
    try:
        db = utils.get_db(theme)
    except:
        utils.remove_handlers(log)

    schema = utils.get_schema_from_theme(theme, config)
    # print(f"theme -> {args['theme']} -> {config}")
    # print(f"schema -> {schema}")
    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers(log)
        return jsonify({"schema": schema})

    log.info(f" Selected schema -> {str(schema)}")
    
    request_json =  {
        "client": {
            "device": 5, "infoType":1, "lang":"ES"
        }, 
        "form": {}, 
        "feature": {
            "tableName" : "v_edit_dma", "id":"1" #Hardcoded
        },
        "data": {
            "filterFields":{},
            "pageInfo":{},
            "selectionMode": "wholeSelection",
            "coordinates": {
                "epsg": int(epsg),
                "xcoord": float(xcoord),
                "ycoord": float(ycoord),
                "zoomRatio": float(zoomRatio),
            }
        }
    }
    request_json = json.dumps(request_json)
    sql = f"SELECT {schema}.gw_fct_getdmabalance($${request_json}$$);"
    log.info(f" Server execution -> {sql}")
    print(f"SERVER EXECUTION: {sql}\n")
    result = dict()
    try:
        result = db.execute(sql).fetchone()[0]
    except exc.ProgrammingError:
        log.warning(" Server execution failed")
        print(f"Server execution failed\n{traceback.format_exc()}")
        utils.remove_handlers(log)

    log.info(f" Server response {str(result)[0:100]}")
    print(f"SERVER RESPONSE: {json.dumps(result)}\n\n")
    utils.remove_handlers(log)
    return jsonify(result)


@info_bp.route('/getlayersfromcoordinates', methods=['GET'])
@jwt_required()
def getlayersfromcoordinates():
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
    xcoord = args.get("xcoord")
    ycoord = args.get("ycoord")
    zoomRatio = args.get("zoomRatio")

    layers = utils.parse_layers(layers, config, theme)

    # db fct
    coordinates = f'"epsg": {int(epsg)}, "xcoord": {xcoord}, "ycoord": {ycoord}, "zoomRatio": {zoomRatio}'
    extras = f'"visibleLayers": {json.dumps(layers)}, "pointClickCoords": {{{coordinates}}}, "zoomScale": {zoomRatio}'
    body = utils.create_body(theme, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_getlayersfromcoordinates', body)

    utils.remove_handlers(log)

    return utils.create_response(result, do_jsonify=True, theme=theme)
