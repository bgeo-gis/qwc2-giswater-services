import utils
from .info_utils import handle_db_result

import json
import traceback

from flask import Blueprint, request, jsonify
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc

info_bp = Blueprint('info', __name__)


@info_bp.route('/fromcoordinates', methods=['GET'])
@optional_auth
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

    try:
        db = utils.get_db(theme)
    except:
        utils.remove_handlers()

    schema = utils.get_schema_from_theme(theme, config)
    
    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers()
        return jsonify({"schema": schema})

    log.info(f" Selected schema {str(schema)}")

    layers = utils.parse_layers(layers, config, theme)

    request_json =  {
        "client": {
            "device": 5, "infoType": 1, "lang": "en_US"
        }, 
        "form": {
            "editable": "False"
        }, 
        "data": {
            "activeLayer": layers[0],
            "visibleLayer": layers,
            "coordinates": {
                "epsg": int(epsg),
                "xcoord": float(xcoord),
                "ycoord": float(ycoord),
                "zoomRatio": float(zoomRatio),
            }
        }
    }
    request_json = json.dumps(request_json)
    sql = f"SELECT {schema}.gw_fct_getinfofromcoordinates($${request_json}$$);"
    log.info(f" Server execution -> {sql}")
    print(f"SERVER EXECUTION: {sql}\n")
    result = dict()
    try:
        result = db.execute(sql).fetchone()[0]
    except exc.ProgrammingError:
        log.warning(" Server execution failed")
        print(f"Server execution failed\n{traceback.format_exc()}")
        utils.remove_handlers()
    result: dict = db.execute(sql).fetchone()[0]
    log.info(f" Server response: {str(result)[0:100]}")
    print(f"SERVER RESPONSE: {json.dumps(result)}\n\n")
    utils.remove_handlers()
    return handle_db_result(result)


@info_bp.route('/fromid', methods=['GET'])
@optional_auth
def fromid():
    config = utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    tableName = args.get("tableName")
    feature_id = args.get("id")

    try:
        db = utils.get_db(theme)
    except:
        utils.remove_handlers()

    schema = utils.get_schema_from_theme(theme, config)

    request_json =  {
        "client": {
            "device": 5, "infoType": 1, "lang": "en_US"
        }, 
        "form": {
            "editable": "False"
        }, 
        "feature": {
            "tableName": tableName,
            "id": feature_id
        },
        "data": {}
    }
    request_json = json.dumps(request_json)
    sql = f"SELECT {schema}.gw_fct_getinfofromid($${request_json}$$);"
    log.info(f" Server execution -> {sql}")
    print(f"SERVER EXECUTION: {sql}\n")
    result = dict()
    try:
        result = db.execute(sql).fetchone()[0]
    except exc.ProgrammingError:
        log.warning(" Server execution failed")
        print(f"Server execution failed\n{traceback.format_exc()}")
        utils.remove_handlers()
            
    log.info(f" Server response {str(result)[0:100]}")
    print(f"SERVER RESPONSE: {json.dumps(result)}\n\n")
    utils.remove_handlers()
    return handle_db_result(result)


@info_bp.route('/getlist', methods=['GET'])
@optional_auth
def getlist():
    config = utils.get_config()
    log = utils.create_log(__name__)
    try:
        db = utils.get_db()
    except:
        utils.remove_handlers()

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
        request_json["data"]["filterFields"][k] = {
            "columnname": v["columnname"],
            "value": v["value"],
            "filterSign": v["filterSign"]
    }

    request_json = json.dumps(request_json)
    sql = f"SELECT {schema}.gw_fct_getlist($${request_json}$$);"
    log.info(f" Server execution -> {sql}")
    print(f"SERVER EXECUTION: {sql}\n")
    result = dict()
    try:
            result = db.execute(sql).fetchone()[0]
    except exc.ProgrammingError:
            log.warning(" Server execution failed")
            print(f"Server execution failed\n{traceback.format_exc()}")
            utils.remove_handlers()

    log.info(f" Server response {str(result)[0:100]}")
    print(f"SERVER RESPONSE: {json.dumps(result)}\n\n")
    utils.remove_handlers()
    return jsonify(result)


@info_bp.route('/getgraph', methods=['GET'])
@optional_auth
def getgraph():
    """
    Submit query
    Returns additional information at clicked map position.
    """

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    node_id = args.get("node_id")

    config = utils.get_config()
    log = utils.create_log(__name__)
    try:
        db = utils.get_db(theme)
    except:
        utils.remove_handlers() 

    schema = utils.get_schema_from_theme(theme, config)

    # print(f"theme -> {args['theme']} -> {config}")
    # print(f"schema -> {schema}")
    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers()
        return jsonify({"schema": schema})

    log.info(f" Selected schema -> {str(schema)}")

    request_json =  {
        "client": {
            "device": 5, "infoType":1, "lang":"ES"
        }, 
        "form": {}, 
        "feature": {
            "type":"node",
            "id": node_id,
            "parameter":"",
            "interval":"",
            "result_id":"e96"
        },
        "data": {}
    }
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
        utils.remove_handlers()

    log.info(f" Server response {str(result)[0:100]}")
    print(f"SERVER RESPONSE: {json.dumps(result)}\n\n")
    utils.remove_handlers()
    return jsonify(result)


@info_bp.route('/getdma', methods=['GET'])
@optional_auth
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
        utils.remove_handlers()

    schema = utils.get_schema_from_theme(theme, config)
    # print(f"theme -> {args['theme']} -> {config}")
    # print(f"schema -> {schema}")
    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers()
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
        utils.remove_handlers()

    log.info(f" Server response {str(result)[0:100]}")
    print(f"SERVER RESPONSE: {json.dumps(result)}\n\n")
    utils.remove_handlers()
    return jsonify(result)
