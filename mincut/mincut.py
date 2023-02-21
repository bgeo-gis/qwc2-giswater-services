import utils
import json
import traceback
from .mincut_utils import handle_db_result, handle_db_result_mincutmanager

from flask import Blueprint, request, jsonify
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc

mincut_bp = Blueprint('mincut', __name__)


@mincut_bp.route('/setmincut', methods=['GET', 'POST'])
@optional_auth
def setmincut():
    """Submit query

    Returns additional information at clicked map position.
    """
    config = utils.get_config()
    log = utils.create_log(__name__)
    identity = get_identity()
    try:
        db = utils.get_db()
    except:
        utils.remove_handlers() 

    # args
    theme = request.args.get("theme")
    epsg = request.args.get("epsg")
    action = request.args.get("action")
    xcoord = request.args.get("xcoord")
    ycoord = request.args.get("ycoord")
    zoomRatio = request.args.get("zoomRatio")
    mincutId = request.args.get("mincutId")

    schema = utils.get_schema_from_theme(theme, config)

    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers()
        return jsonify({"schema": schema})

    log.info(f" Selected schema {str(schema)}")

    req =  {
        "client": {
            "device": 5, "infoType": 1, "lang": "en_US", "epsg": int(epsg), "cur_user": str(identity)
        }, 
        "form": {}, 
        "feature": {},
        "data": {
            "filterFields": {},
            "pageInfo": {},
            "action": str(action),
            "coordinates": {
                "epsg": int(epsg), 
                "xcoord": xcoord, 
                "ycoord": ycoord, 
                "zoomRatio": zoomRatio
            },
            "usePsectors": "False"
        }
    }
    if mincutId is not None:
        req["data"]["mincutId"] = mincutId
    request_json = json.dumps(req)
    sql = f"SELECT {schema}.gw_fct_setmincut($${request_json}$$);"
    log.info(f" Server execution -> {sql}")
    print(f"SERVER EXECUTION: {sql}\n")
    with db.begin() as conn:
        result = dict()
        try:
            result = conn.execute(text(sql)).fetchone()[0]
        except exc.ProgrammingError:
            log.warning(" Server execution failed")
            print(f"Server execution failed\n{traceback.format_exc()}")
            utils.remove_handlers()
        log.info(f" Server response -> {json.dumps(result)}")
        print(f"SERVER RESPONSE: {json.dumps(result)}\n")
        utils.remove_handlers()
        return handle_db_result(result, theme)

@mincut_bp.route('/open', methods=['GET'])
@optional_auth
def openmincut():
    """Submit query

    Returns additional information at clicked map position.
    """
    config = utils.get_config()
    log = utils.create_log(__name__)
    try:
        db = utils.get_db()
    except:
        utils.remove_handlers() 

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    mincut_id = args.get("mincutId")

    schema = utils.get_schema_from_theme(theme, config)

    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers()
        return jsonify({"schema": schema})

    log.info(f" Selected schema {str(schema)}")

    req =  {
            "client": {
                "device": 5, "lang": "en_US"
            }, 
            "data": {
                "mincutId": mincut_id
            }
        }
    request_json = json.dumps(req)
    sql = f"SELECT {schema}.gw_fct_getmincut_ff($${request_json}$$);"
    log.info(f" Server execution -> {sql}")
    print(f"SERVER EXECUTION: {sql}\n")
    with db.begin() as conn:
        result = dict()
        try:
            result = conn.execute(text(sql)).fetchone()[0]
        except exc.ProgrammingError:
            log.warning(" Server execution failed")
            print(f"Server execution failed\n{traceback.format_exc()}")
            utils.remove_handlers()
        log.info(f" Server response -> {json.dumps(result)}")
        print(f"SERVER RESPONSE: {json.dumps(result)}\n")
        utils.remove_handlers()
        return handle_db_result(result, theme)

@mincut_bp.route('/cancel', methods=['GET', 'POST'])
@optional_auth
def cancelmincut():
    """Submit query

    Returns additional information at clicked map position.
    """
    config = utils.get_config()
    log = utils.create_log(__name__)
    identity = get_identity()
    try:
        db = utils.get_db()
    except:
        utils.remove_handlers() 

    # args
    #print(f"request args ============> {request.get_json(force=True)}")
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    mincutId = args.get("mincutId")

    schema = utils.get_schema_from_theme(theme, config)

    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers()
        return jsonify({"schema": schema})

    log.info(f" Selected schema {str(schema)}")

    request_json =  {
        "client": {
            "device": 5, "infoType": 1, "lang": "en_US", "cur_user": str(identity)
        }, 
        "form": {}, 
        "feature": {},
        "data": {
            "filterFields": {},
            "pageInfo": {},
            "action": "mincutCancel",
            "mincutId": mincutId
        }
    }
    request_json = json.dumps(request_json)
    sql = f"SELECT {schema}.gw_fct_setmincut($${request_json}$$);"
    log.info(f" Server execution -> {sql}")
    print(f"SERVER EXECUTION: {sql}\n")
    with db.begin() as conn:
        result = dict()
        try:
            result = conn.execute(text(sql)).fetchone()[0]
        except exc.ProgrammingError:
            log.warning(" Server execution failed")
            print(f"Server execution failed\n{traceback.format_exc()}")
            utils.remove_handlers()
        log.info(f" Server response -> {json.dumps(result)}")
        print(f"SERVER RESPONSE: {json.dumps(result)}\n")
        utils.remove_handlers()
        return handle_db_result(result, theme)


@mincut_bp.route('/delete', methods=['DELETE'])
@optional_auth
def deletemincut():
    """Submit query

    Returns additional information at clicked map position.
    """
    config = utils.get_config()
    log = utils.create_log(__name__)
    identity = get_identity()
    try:
        db = utils.get_db()
    except:
        utils.remove_handlers() 

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    mincut_id = args.get("mincutId")

    schema = utils.get_schema_from_theme(theme, config)

    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers()
        return jsonify({"schema": schema})

    log.info(f" Selected schema {str(schema)}")

    req =  {
        "client": {
            "device": 5, "infoType": 1, "lang": "en_US", "cur_user": str(identity)
        }, 
        "form": {}, 
        "feature": {},
        "data": {
            "filterFields": {},
            "pageInfo": {},
            "action": "mincutDelete",
            "mincutId": mincut_id
        }
    }
    print(req)
    request_json = json.dumps(req)
    sql = f"SELECT {schema}.gw_fct_setmincut($${request_json}$$);"
    log.info(f" Server execution -> {sql}")
    print(f"SERVER EXECUTION: {sql}\n")
    with db.begin() as conn:
        result = dict()
        try:
            result = conn.execute(text(sql)).fetchone()[0]
        except exc.ProgrammingError:
            log.warning(" Server execution failed")
            print(f"Server execution failed\n{traceback.format_exc()}")
            utils.remove_handlers()
        log.info(f" Server response -> {json.dumps(result)}")
        print(f"SERVER RESPONSE: {json.dumps(result)}\n")
        utils.remove_handlers()
        return handle_db_result(result, theme)

@mincut_bp.route('/accept', methods=['POST'])
@optional_auth
def accept():
    """Submit query

    Returns additional information at clicked map position.
    """
    config = utils.get_config()
    log = utils.create_log(__name__)
    identity = get_identity()
    try:
        db = utils.get_db()
    except:
        utils.remove_handlers() 
     # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")
    mincutId = args.get("mincutId")
    fields = args.get("fields")
    usePsectors = args.get("usePsectors")
    xcoord = args.get("xcoord")
    ycoord = args.get("ycoord")
    zoomRatio = args.get("zoomRatio")

    schema = utils.get_schema_from_theme(theme, config)

    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers()
        return jsonify({"schema": schema})

    log.info(f" Selected schema {str(schema)}")

    req =  {
        "client": {
            "device": 5, "infoType": 1, "lang": "en_US", "epsg": int(epsg), "cur_user": str(identity)
        }, 
        "form": {}, 
        "feature": {
            "featureType": "",
            "tableName": "om_mincut",
            "id": int(mincutId)
        },
        "data": {
            "filterFields": {},
            "pageInfo": {},
            "action": "mincutAccept",
            "mincutClass": 1,
            "status": "check",
            "mincutId": int(mincutId),
            "usePsectors": usePsectors,
            "fields": dict(fields),
            "coordinates": {
                "epsg": int(epsg), 
                "xcoord": xcoord, 
                "ycoord": ycoord, 
                "zoomRatio": zoomRatio
            }
        }
    }
    request_json = json.dumps(req)
    sql = f"SELECT {schema}.gw_fct_setmincut($${request_json}$$);"
    log.info(f" Server execution -> {sql}")
    print(f"SERVER EXECUTION: {sql}\n")
    with db.begin() as conn:
        result = dict()
        try:
            result = conn.execute(text(sql)).fetchone()[0]
        except exc.ProgrammingError:
            log.warning(" Server execution failed")
            print(f"Server execution failed\n{traceback.format_exc()}")
            utils.remove_handlers()
        log.info(f" Server response -> {json.dumps(result)}")
        print(f"SERVER RESPONSE: {json.dumps(result)}\n")
        utils.remove_handlers()
        return handle_db_result(result, theme)

@mincut_bp.route('/getmincutmanager', methods=['GET'])
@optional_auth
def getmanager():
    """Submit query

    Returns additional information at clicked map position.
    """
    print("hola")
    config = utils.get_config()
    log = utils.create_log(__name__)
    try:
        db = utils.get_db()
    except:
        utils.remove_handlers()

    # args
    theme = request.args.get("theme")

    schema = utils.get_schema_from_theme(theme, config)
    print("theme -> ", schema)
    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers()
        return jsonify({"schema": schema})

    log.info(f" Selected schema {str(schema)}")

    request_json = {}

    sql = f"SELECT {schema}.gw_fct_getmincut_manager($${request_json}$$);"
    log.info(f" Server execution -> {sql}")
    print(f"SERVER EXECUTION: {sql}\n")
    with db.begin() as conn:
        result = dict()
        try:
            result = conn.execute(text(sql)).fetchone()[0]
        except exc.ProgrammingError:
            log.warning(" Server execution failed")
            print(f"Server execution failed\n{traceback.format_exc()}")
            utils.remove_handlers()
        log.info(f" Server response -> {json.dumps(result)}")
        print(f"SERVER RESPONSE: {json.dumps(result)}\n")
        utils.remove_handlers()
        return handle_db_result_mincutmanager(result, theme)

@mincut_bp.route('/getlist', methods=['GET'])
@optional_auth
def getlist():
    config = utils.get_config()
    log = utils.create_log(__name__)
    try:
        db = utils.get_db()
    except:
        utils.remove_handlers()

    # args
    theme = request.args.get("theme")
    tabName = request.args.get("tabName")
    widgetname = request.args.get("widgetname")
    formtype = request.args.get("formtype")
    tableName = request.args.get("tableName")
    filterFields = request.args.get("filterFields")

    schema = utils.get_schema_from_theme(theme, config)

    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers()
        return jsonify({"schema": schema})

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
            "tableName": tableName
        },
        "data": {
            "filterFields": {},
            "pageInfo": {}
        }
    }

    # Manage filters
    print("filterFields -> ", filterFields)
    if filterFields in (None, "", "null", "{}"):
        request_json["data"]["filterFields"] = {}
    else:
        filterFields = json.loads(str(filterFields))
        for k, v in filterFields.items():
            if v in (None, "", "null"):
                continue
            request_json["data"]["filterFields"][k] = {
            #   "columnname": v["columnname"],
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
