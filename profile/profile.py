import utils
from .profile_utils import handle_db_result, get_profiletool_ui, generate_profile_svg

import json
import traceback
import os

from flask import Blueprint, request, jsonify
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/getdialog', methods=['GET'])
@optional_auth
def getdialog(self):
    """Submit query

    Returns profiletool dialog.
    """
    # Get dialog
    form_xml = get_profiletool_ui()

    # Response
    response = {
        "feature": {},
        "form_xml": form_xml
    }
    utils.remove_handlers()
    return jsonify(response)


@profile_bp.route('/nodefromcoordinates', methods=['GET'])
@optional_auth
def nodefromcoordinates():
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
    coords = args.get("coords")
    zoom = args.get("zoom")
    # xcoord = args.get("xcoord")
    # ycoord = args.get("ycoord")
    # zoomRatio = args.get("zoomRatio")

    schema = utils.get_schema_from_theme(theme, config)
    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers()
        return jsonify({"schema": schema})

    log.info(f" Selected schema -> {str(schema)}")
    coords = coords.split(',')
    layers = utils.parse_layers(layers, config, theme)
    request_json =  {
        "client": {
            "device": 5, "infoType": 1, "lang": "en_US", "epsg": int(epsg), "cur_user": str(identity)
        }, 
        "form": {}, 
        "feature": {
        },
        "data": {
            "activeLayer": layers[0],
            "visibleLayer": layers,
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
    sql = f"SELECT {schema}.gw_fct_checknode($${request_json}$$);"
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


@profile_bp.route('/profileinfo', methods=['GET'])
@optional_auth
def profileinfo():
    """
    Submit query
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
    initNode = args.get("initNode")
    endNode = args.get("endNode")

    schema = utils.get_schema_from_theme(theme, config)
    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers()
        return jsonify({"schema": schema})

    request_json =  {
        "client": {
            "device": 5, "lang": "es_ES", "infoType": 1, "epsg": int(epsg)
        }, 
        "form": {}, 
        "feature": {},
        "data": {
            "filterFields": {},
            "pageInfo": {},
            "initNode": initNode,
            "endNode": endNode,
            "linksDistance": "1"
        }
    }
    request_json = json.dumps(request_json)
    sql = f"SELECT {schema}.gw_fct_getprofilevalues($${request_json}$$);"
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


@profile_bp.route('/profilesvg', methods=['GET', 'DELETE'])
@optional_auth
def profilesvg():
    config = utils.get_config()
    log = utils.create_log(__name__)
    args = request.get_json(force=True) if request.is_json else request.args

    if request.method == 'DELETE':
        # args
        img_path = args.get("img_path")

        _, file_extension = os.path.splitext(img_path)
        if (file_extension == ".svg"):
            print("deleting")
            os.remove(img_path)
    else:
        try:
            db = utils.get_db()
        except:
            utils.remove_handlers()

        # args
        theme = args.get("theme")
        epsg = args.get("epsg")
        initNode = args.get("initNode")
        endNode = args.get("endNode")
        vnode_dist = args.get("vnode_dist")
        title = args.get("title")
        date = args.get("date")

        schema = utils.get_schema_from_theme(theme, config)

        if schema is None:
            log.warning(" Schema is None")
            utils.remove_handlers()
            return jsonify({"schema": schema})

        log.info(f" Selected schema -> {str(schema)}")

        request_json =  {
            "client": {
                "device": 5, "lang": "es_ES", "infoType": 1, "epsg": int(epsg)
            }, 
            "form": {}, 
            "feature": {},
            "data": {
                "filterFields": {},
                "pageInfo": {},
                "initNode": initNode,
                "endNode": endNode, 
                "linksDistance": vnode_dist
            }
        }
        request_json = json.dumps(request_json)
        sql = f"SELECT {schema}.gw_fct_getprofilevalues($${request_json}$$);"
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
            #result = handle_db_result(result)
        
        params = {'title': title, 'date': date}

        img_path = generate_profile_svg(result, params)
        print(img_path)
        return img_path
