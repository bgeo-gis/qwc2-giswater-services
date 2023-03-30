"""
Copyright BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils
from .visit_utils import handle_db_result

import json
import traceback
import os

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc

visit_bp = Blueprint('visit', __name__)


@visit_bp.route('/get', methods=['GET'])
@optional_auth
def getvisit():
    config = utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    visitType = args.get("visitType")
    visitId = args.get("visitId") # nomes si obrim des del manager
    #featureType = args.get("featureType")
    #feature_id = args.get("id")
    epsg = request.args.get("epsg")
    xcoord = request.args.get("xcoord")
    ycoord = request.args.get("ycoord")
    zoomRatio = request.args.get("zoomRatio")

    try:
        db = utils.get_db(theme)
    except:
        utils.remove_handlers(log)

    schema = utils.get_schema_from_theme(theme, config)

    form = f'"visitType": {visitType}'
    if visitId is not None:
        feature += f', "visitId": {visitId}'
    extras = f'"coordinates": {{"xcoord": {xcoord}, "ycoord": {ycoord}, "zoomRatio": {zoomRatio}}}'
    body = utils.create_body(project_epsg=epsg, form=form, extras=extras)
    sql = f"SELECT {schema}.gw_fct_getvisit({body});"

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
    return handle_db_result(result)


@visit_bp.route('/set', methods=['POST'])
@optional_auth
def setvisit():
    """Submit query

    Returns additional information at clicked map position.
    """
    config = utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.form
    theme = args.get("theme")
    visitId = args.get("visitId")
    fields = args.get("fields")
    # files
    files = request.files.getlist('files[]') if request.files else []

    try:
        db = utils.get_db(theme)
    except:
        utils.remove_handlers(log)

    schema = utils.get_schema_from_theme(theme, config)

    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers(log)
        return jsonify({"schema": schema})

    log.info(f" Selected schema {str(schema)}")

    feature = ''
    if visitId is not None:
        feature += f'"visitId": {visitId}'
    print(f"{theme=}")
    print(f"{visitId=}")
    print(f"{fields=}")
    extras = f'"fields": {fields}'
    body = utils.create_body(feature=feature, extras=extras)
    sql = f"SELECT {schema}.gw_fct_setvisit({body});"
    log.info(f" Server execution -> {sql}")
    print(f"SERVER EXECUTION: {sql}\n")

    utils.remove_handlers(log)

    return utils.create_response(status=False, do_jsonify=True)
    with db.begin() as conn:
        result = dict()
        try:
            result = conn.execute(text(sql)).fetchone()[0]
        except exc.ProgrammingError:
            log.warning(" Server execution failed")
            print(f"Server execution failed\n{traceback.format_exc()}")
            utils.remove_handlers(log)
        log.info(f" Server response -> {json.dumps(result)}")
        print(f"SERVER RESPONSE: {json.dumps(result)}\n")
        utils.remove_handlers(log)
        return handle_db_result(result, theme)

    status = "Failed"
    message = ""
    try:
        for file in files:
            if not file or file.filename == '':
                continue
            filename = secure_filename(file.filename)
            file.save(os.path.join(config.get('images_path'), filename))
            status = "Accepted"
            message = "File uploaded successfully!"

            # Insert url to om_visit_photo
            sql = f"INSERT INTO {schema}.om_visit_photo(visit_id, value) VALUES ({visit_id}, '{config.get('images_url')}{filename}');"

            log.info(f" Server execution -> {sql}")
            print(f"SERVER EXECUTION: {sql}\n")
            try:
                db.execute(sql)
            except exc.ProgrammingError:
                log.warning(" Server execution failed")
                print(f"Server execution failed\n{traceback.format_exc()}")
                utils.remove_handlers(log)

            utils.remove_handlers(log)
    except Exception as e:
        status = "Failed"
        message = "Error"
        print(e)
    finally:
        utils.remove_handlers(log)
        return utils.create_response(status=status, message=message, do_jsonify=True)



@visit_bp.route('/file', methods=['POST'])
@optional_auth
def uploadfile():

    if not request.files:
        print("No files")
        utils.remove_handlers(log)
        msg = "No files provided"
        return utils.create_response(status=False, message=msg, do_jsonify=True)
    files = request.files.getlist('files[]')

    # args
    args = request.form
    theme = args.get("theme")
    visit_id = args.get("visit_id")
    # visit_type = args.get("visit_type")
    # featureType = args.get("featureType")
    # feature_id = args.get("id")

    config = utils.get_config()
    log = utils.create_log(__name__)
    try:
        db = utils.get_db(theme)
    except:
        utils.remove_handlers(log)

    schema = utils.get_schema_from_theme(theme, config)

    if files:
        status = "Failed"
        message = ""
        try:
            for file in files:
                if not file or file.filename == '':
                    continue
                filename = secure_filename(file.filename)
                file.save(os.path.join('/home/bgeoadmin/bgeo/images/', filename))
                status = "Accepted"
                message = "File uploaded successfully!"

                # Insert url to om_visit_photo
                sql = f"INSERT INTO {schema}.om_visit_photo(visit_id, value) VALUES ({visit_id}, '{config.get('images_url')}{filename}');"

                log.info(f" Server execution -> {sql}")
                print(f"SERVER EXECUTION: {sql}\n")
                try:
                    db.execute(sql)
                except exc.ProgrammingError:
                    log.warning(" Server execution failed")
                    print(f"Server execution failed\n{traceback.format_exc()}")
                    utils.remove_handlers(log)

                utils.remove_handlers(log)
        except Exception as e:
            status = "Failed"
            message = "Error"
            print(e)
        finally:
            utils.remove_handlers(log)
            return utils.create_response(status=status, message=message, do_jsonify=True)


@visit_bp.route('/getlist', methods=['GET'])
@optional_auth
def getlist():
    # args
    theme = request.args.get("theme")
    tabName = request.args.get("tabName")
    widgetname = request.args.get("widgetname")
    formtype = request.args.get("formtype")
    tableName = request.args.get("tableName")
    filterFields = request.args.get("filterFields")

    config = utils.get_config()
    log = utils.create_log(__name__)
    try:
        db = utils.get_db(theme)
    except:
        utils.remove_handlers(log)

    schema = utils.get_schema_from_theme(theme, config)

    if schema is None:
        log.warning(" Schema is None")
        utils.remove_handlers(log)
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
            utils.remove_handlers(log)

    log.info(f" Server response {str(result)[0:100]}")
    print(f"SERVER RESPONSE: {json.dumps(result)}\n\n")
    utils.remove_handlers(log)
    return jsonify(result)
