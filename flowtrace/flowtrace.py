import utils
from .flowtrace_utils import handle_db_result

import json
import traceback

from flask import Blueprint, request, jsonify
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc

flowtrace_bp = Blueprint('flowtrace', __name__)


@flowtrace_bp.route('/upstream', methods=['GET'])
@optional_auth
def upstream():
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
    epsg = args.get("epsg")
    coords = args.get("coords").split(',')
    zoom = args.get("zoom")

    schema = utils.get_schema_from_theme(theme, config)

    if schema is None:
        log.warning("Schema is None")
        utils.remove_handlers()
        return jsonify({"schema": schema})

    log.info(f"Selected schema -> {str(schema)}")

    request_json =  {
        "client": {
            "device": 5, "infoType": 1, "lang": "en_US", "epsg": int(epsg)
        }, 
        "form": {}, 
        "feature": {
            
        },
        "data": {
            "filterFields": {},
            "pageInfo": {},
            "coordinates": {
                "epsg": int(epsg),
                "xcoord": coords[0],
                "ycoord": coords[1],
                "zoomRatio": float(zoom)
            }
        }
    }
    request_json = json.dumps(request_json)
    sql = f"SELECT {schema}.gw_fct_graphanalytics_upstream($${request_json}$$);"
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
        return handle_db_result(result)


@flowtrace_bp.route('/downstream', methods=['GET'])
@optional_auth
def downstream():
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
    epsg = args.get("epsg")
    coords = args.get("coords").split(',')
    zoom = args.get("zoom")

    schema = utils.get_schema_from_theme(theme, config)

    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers()
        return jsonify({"schema": schema})

    log.info(f" Selected schema -> {str(schema)}")

    request_json =  {
        "client": {
            "device": 5, "infoType": 1, "lang": "en_US", "epsg": int(epsg)
        }, 
        "form": {}, 
        "feature": {
            
        },
        "data": {
            "filterFields": {},
            "pageInfo": {},
            "coordinates": {
                "epsg": int(epsg),
                "xcoord": coords[0],
                "ycoord": coords[1],
                "zoomRatio": float(zoom)
            }
        }
    }
    request_json = json.dumps(request_json)
    sql = f"SELECT {schema}.gw_fct_graphanalytics_downstream($${request_json}$$);"
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
        return handle_db_result(result)
