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
    try:
        db = utils.get_db()
    except:
        utils.remove_handlers() 

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    visit_type = args.get("visit_type")
    visit_id = args.get("visit_id")
    featureType = args.get("featureType")
    feature_id = args.get("id")

    schema = utils.get_schema_from_theme(theme, config)

    form = f'"visit_id": {visit_id}, "visit_type": {visit_type}'
    feature = f'"featureType": "{featureType}", "id": {feature_id}'
    body = utils.create_body(form=form, feature=feature)
    sql = f"SELECT {schema}.gw_fct_getvisit({body});"

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


@visit_bp.route('/file', methods=['POST'])
@optional_auth
def uploadfile():
    if 'file' not in request.files:
        print("No file")
        utils.remove_handlers()
        return jsonify({ "message": "No file provided"})
    file = request.files['file']
    if file.filename == '':
        print("No selected file")
        utils.remove_handlers()
        return jsonify({ "message": "No file selected"})

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
        utils.remove_handlers()

    schema = utils.get_schema_from_theme(theme, config)

    if file:
        status = "Failed"
        message = ""
        try:
            filename = secure_filename(file.filename)
            file.save(os.path.join('/home/bgeoadmin/bgeo/images/', filename))
            status = "Accepted"
            message = "File uploaded successfully!"

            # Insert url to om_visit_photo
            sql = f"INSERT INTO {schema}.om_visit_photo(visit_id, value) VALUES ({visit_id}, 'https://qwc2dev.bgeo.es/bgeo/photos/{filename}');"

            log.info(f" Server execution -> {sql}")
            print(f"SERVER EXECUTION: {sql}\n")
            try:
                db.execute(sql)
            except exc.ProgrammingError:
                log.warning(" Server execution failed")
                print(f"Server execution failed\n{traceback.format_exc()}")
                utils.remove_handlers()

            utils.remove_handlers()
        except Exception as e:
            status = "Failed"
            message = "Error"
            print(e)
        finally:
            utils.remove_handlers()
            return jsonify({ "status": status, "message": message })


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
        utils.remove_handlers()

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
