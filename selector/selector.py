import utils
from .selector_utils import handle_db_result

import json
import traceback

from flask import Blueprint, request, jsonify
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc

selector_bp = Blueprint('selector', __name__)


@selector_bp.route('/get', methods=['GET'])
@optional_auth
def getselector():
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
    layers = args.get("layers")
    epsg = args.get("epsg")
    currentTab = args.get("currentTab")
    selectorType = args.get("selectorType")
    loadProject = args.get("loadProject")
    #ids = args.get("ids")
    
    #ids = [int(i) for i in ids.split(",")]
    
    schema = utils.get_schema_from_theme(theme, config)

    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers()
        return jsonify({"schema": schema})

    log.info(f" Selected schema {str(schema)}")

    layers = utils.parse_layers(layers, config, theme)

    request_json =  {
        "client": {
            "device": 5, "infoType": 1, "lang": "en_US", "epsg": int(epsg), "cur_user": str(identity)
        }, 
        "form": {
            "currentTab": str(currentTab)
        }, 
        "feature": {},
        "data": {
            "layers": layers,
            "filterFields": {},
            "pageInfo": {},
            "selectorType": str(selectorType),
            "filterText": "",
            "loadProject": loadProject,
        }
    }


    print("request_json ", request_json)
    request_json = json.dumps(request_json)
    sql = f"SELECT {schema}.gw_fct_getselectors($${request_json}$$);"
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


@selector_bp.route('/set', methods=['POST'])
@optional_auth
def setselector():
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
    layers = args.get("layers")
    epsg = args.get("epsg")
    selectorType = args.get("selectorType")
    tabName = args.get("tabName")
    value = args.get("value")
    widget_id = args.get("id")
    isAlone = args.get("isAlone")
    disableParent = args.get("disableParent")
    addSchema = args.get("addSchema")

    schema = utils.get_schema_from_theme(theme, config)
    if schema is None:
        log.warning(f" Schema is None")
        utils.remove_handlers()
        return jsonify({"schema": schema})

    log.info(f" Selected schema {str(schema)}")

    layers = utils.parse_layers(layers, config, theme)

    request_json =  {
        "client": {
            "device": 5, "infoType": 1, "lang": "en_US", "epsg": int(epsg), "cur_user": str(identity)
        }, 
        "form": {}, 
        "feature": {},
        "data": {
            "layers": layers,
            "filterFields": {},
            "pageInfo": {},
            "selectorType": str(selectorType),
            "tabName": str(tabName),
            "addSchema": str(addSchema)
        }
    }
    if widget_id == 'chk_all':
        request_json['data']['checkAll'] = str(value)
    else:
        request_json['data']['id'] = str(widget_id)
        request_json['data']['isAlone'] = str(isAlone)
        request_json['data']['disableParent'] = str(disableParent)
        request_json['data']['value'] = str(value)

    request_json = json.dumps(request_json)
    sql = f"SELECT {schema}.gw_fct_setselectors($${request_json}$$);"
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
        log.info(f" Server response: {str(result)[0:100]}")
        print(f"SERVER RESPONSE: {result}\n\n")
        utils.remove_handlers()
        return handle_db_result(result, theme)
