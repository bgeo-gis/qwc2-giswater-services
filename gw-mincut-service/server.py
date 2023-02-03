from datetime import date
from typing import List, Optional
from xml.dom.minidom import parseString, Document, Element

from flask import Flask, request, jsonify, Response
from flask_restx import Resource, reqparse
import os
import traceback
import requests
import logging
import json
from utils import mincut_create_xml_form, mincutmanager_create_xml_form

from qwc_services_core.api import Api
from qwc_services_core.app import app_nocache
from qwc_services_core.auth import auth_manager, optional_auth, get_identity
from qwc_services_core.api import CaseInsensitiveArgument
from qwc_services_core.tenant_handler import TenantHandler
from qwc_services_core.runtime_config import RuntimeConfig
from qwc_services_core.database import DatabaseEngine
from sqlalchemy import text, exc

# from PyQt5.QtDesigner import QFormBuilder

# Flask application
app = Flask(__name__)
app_nocache(app)
api = Api(app, version='1.0', title='MapInfo service API',
          description="""API for QWC MapInfo service.

Additional information at a geographic position displayed with right mouse click on map.
          """,
          default_label='MapInfo operations', doc='/api/')
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'

# disable verbose 404 error message
app.config['ERROR_404_HELP'] = False

auth = auth_manager(app, api)
tenant_handler = TenantHandler(app.logger)


def get_config() -> RuntimeConfig:
    tenant = tenant_handler.tenant()
    config_handler = RuntimeConfig("gwMincut", app.logger)
    return config_handler.tenant_config(tenant)

def get_db() -> DatabaseEngine:
    print(f"DB URL: {get_config().get('db_url')}")
    logging.basicConfig
    logging.info(f"DB URL: {get_config().get('db_url')}")
    return DatabaseEngine().db_engine(get_config().get("db_url"))

def get_schema_from_theme(theme: str, config: RuntimeConfig) -> Optional[str]:
    themes = config.get("themes")
    theme = themes.get(theme)
    if theme is not None:
        return theme.get("schema")
    return None

def handle_db_result(result: dict, theme: str) -> Response:
    response = {}
    if not result:
        logging.warning(" DB returned null")
        return jsonify({"message": "DB returned null"})
    if 'results' not in result or result['results'] > 0:
        try:
            form_xml = mincut_create_xml_form(result)
        except:
            form_xml = None

        response = {
            "status": result['status'],
            "version": result['version'],
            "body": result['body'],
            "form_xml": form_xml
        }
    return jsonify(response)

def handle_db_result_mincutmanager(result: dict, theme: str) -> Response:
    response = {}
    if not result:
        logging.warning(" DB returned null")
        return jsonify({"message": "DB returned null"})
    if 'results' not in result or result['results'] > 0:
        try:
            form_xml = mincutmanager_create_xml_form(result)
        except:
            form_xml = None

        response = {
            "status": result['status'],
            "version": result['version'],
            "body": result['body'],
            "form_xml": form_xml
        }
    return jsonify(response)

def parse_layers(request_layers: str, config: RuntimeConfig, theme: str) -> List[str]:
    layers = []
    db_layers = get_db_layers(theme)

    for l in request_layers.split(','):
        if l in db_layers:
            layers.append(db_layers[l])
    return layers

def get_db_layers(theme: str) -> List[str]:
    db_layers = []
    theme = get_config().get("themes").get(theme)
    if theme is not None:
        db_layers = theme.get("layers")
    return db_layers

# Create log pointer
def create_log(self):
    print(f"Tenant_name -> {tenant_handler.tenant()}")
    today = date.today()
    today = today.strftime("%Y%m%d")

    # Directory where log file is saved, changes location depending on what tenant is used
    tenant_directory = f"/var/log/qwc2-giswater-services/{tenant_handler.tenant()}"
    if not os.path.exists(tenant_directory):
        os.makedirs(tenant_directory)
    
    # Check if today's direcotry is created
    today_directory = f"{tenant_directory}/{today}"
    if not os.path.exists(today_directory):
        os.makedirs(today_directory)
    
    service_name = os.getcwd().split(os.sep)[-1]
    # Select file name for the log
    log_file = f"{service_name}_{today}.log"

    fileh = logging.FileHandler(f"{today_directory}/{log_file}", "a", encoding="utf-8")
    # Declares how log info is added to the file
    formatter = logging.Formatter("%(asctime)s %(levelname)s:%(message)s", datefmt = "%d/%m/%y %H:%M:%S")
    fileh.setFormatter(formatter)

    # Removes previous handlers on root Logger
    remove_handlers()
    # Gets root Logger and add handdler
    log = logging.getLogger()
    log.addHandler(fileh)
    log.setLevel(logging.DEBUG)
    log.info(f" Executing class {self.__class__.__name__}")
    return log

# Removes previous handlers on root Logger
def remove_handlers():
    log = logging.getLogger()
    for hdlr in log.handlers[:]:
        log.removeHandler(hdlr)

# region /setmincut
setmincut_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
setmincut_parser.add_argument('theme', required=True)
setmincut_parser.add_argument('epsg', required=True)
setmincut_parser.add_argument('xcoord', required=True)
setmincut_parser.add_argument('ycoord', required=True)
setmincut_parser.add_argument('zoomRatio', required=True)
setmincut_parser.add_argument('action', required=True)
setmincut_parser.add_argument('mincutId', required=False, default=None)

@api.route('/setmincut')
class GwSetMincut(Resource):
    @api.expect(setmincut_parser)
    @optional_auth
    def get(self):
        """Submit query

        Returns additional information at clicked map position.
        """
        config = get_config()
        log = create_log(self)
        args = setmincut_parser.parse_args()
        identity = get_identity()
        try:
            db = get_db()
        except:
            remove_handlers() 

        schema = get_schema_from_theme(args["theme"], config)

        if schema is None:
            log.warning(" Schema is None")
            remove_handlers()
            return jsonify({"schema": schema})

        log.info(f" Selected schema {str(schema)}")

        req =  {
            "client": {
                "device": 5, "infoType": 1, "lang": "en_US", "epsg": int(args['epsg']), "cur_user": str(identity)
            }, 
            "form": {}, 
            "feature": {},
            "data": {
                "filterFields": {},
                "pageInfo": {},
                "action": str(args["action"]),
                "coordinates": {
                    "epsg": int(args['epsg']), 
                    "xcoord": args['xcoord'], 
                    "ycoord": args['ycoord'], 
                    "zoomRatio": args['zoomRatio']
                },
                "usePsectors": "False"
            }
        }
        if args["mincutId"] is not None:
            req["data"]["mincutId"] = args["mincutId"]
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
                remove_handlers()
            log.info(f" Server response -> {json.dumps(result)}")
            print(f"SERVER RESPONSE: {json.dumps(result)}\n")
            remove_handlers()
            return handle_db_result(result, args["theme"])
# endregion

# region /cancel
cancelmincut_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
cancelmincut_parser.add_argument('theme', required=True)
cancelmincut_parser.add_argument('mincutId', required=True)

@api.route('/cancel')
class GwCancelMincut(Resource):
    @api.expect(cancelmincut_parser)
    @optional_auth
    def get(self):
        """Submit query

        Returns additional information at clicked map position.
        """
        config = get_config()
        log = create_log(self)
        args = cancelmincut_parser.parse_args()
        identity = get_identity()
        try:
            db = get_db()
        except:
            remove_handlers() 

        schema = get_schema_from_theme(args["theme"], config)

        if schema is None:
            log.warning(" Schema is None")
            remove_handlers()
            return jsonify({"schema": schema})
        
        mincut_id = args["mincutId"]

        log.info(f" Selected schema {str(schema)}")

        request =  {
            "client": {
                "device": 5, "infoType": 1, "lang": "en_US", "cur_user": str(identity)
            }, 
            "form": {}, 
            "feature": {},
            "data": {
                "filterFields": {},
                "pageInfo": {},
                "action": "mincutCancel",
                "mincutId": mincut_id
            }
        }
        request_json = json.dumps(request)
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
                remove_handlers()
            log.info(f" Server response -> {json.dumps(result)}")
            print(f"SERVER RESPONSE: {json.dumps(result)}\n")
            remove_handlers()
            return handle_db_result(result, args["theme"])
# endregion

# region /accept
acceptmincut_parser = reqparse.RequestParser()
acceptmincut_parser.add_argument('theme', required=True, location='json')
acceptmincut_parser.add_argument('mincutId', required=True, location='json')
acceptmincut_parser.add_argument('fields', required=True, type=dict, location='json')
acceptmincut_parser.add_argument('epsg', required=True, location='json')
acceptmincut_parser.add_argument('xcoord', required=True, location='json')
acceptmincut_parser.add_argument('ycoord', required=True, location='json')
acceptmincut_parser.add_argument('zoomRatio', required=True, location='json')
acceptmincut_parser.add_argument('usePsectors', required=True, type=bool, location='json')

@api.route('/accept', methods=['POST'])
class GwAcceptMincut(Resource):
    @api.expect(acceptmincut_parser)
    @optional_auth
    def post(self):
        """Submit query

        Returns additional information at clicked map position.
        """
        config = get_config()
        log = create_log(self)
        args = acceptmincut_parser.parse_args()
        identity = get_identity()
        try:
            db = get_db()
        except:
            remove_handlers() 

        print(args)
        schema = get_schema_from_theme(args["theme"], config)

        if schema is None:
            log.warning(" Schema is None")
            remove_handlers()
            return jsonify({"schema": schema})

        log.info(f" Selected schema {str(schema)}")

        req =  {
            "client": {
                "device": 5, "infoType": 1, "lang": "en_US", "epsg": int(args['epsg']), "cur_user": str(identity)
            }, 
            "form": {}, 
            "feature": {
                "featureType": "",
                "tableName": "om_mincut",
                "id": int(args["mincutId"])
            },
            "data": {
                "filterFields": {},
                "pageInfo": {},
                "action": "mincutAccept",
                "mincutClass": 1,
                "status": "check",
                "mincutId": int(args["mincutId"]),
                "usePsectors": args["usePsectors"],
                "fields": dict(args["fields"]),
                "coordinates": {
                    "epsg": int(args['epsg']), 
                    "xcoord": args['xcoord'], 
                    "ycoord": args['ycoord'], 
                    "zoomRatio": args['zoomRatio']
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
                remove_handlers()
            log.info(f" Server response -> {json.dumps(result)}")
            print(f"SERVER RESPONSE: {json.dumps(result)}\n")
            remove_handlers()
            return handle_db_result(result, args["theme"])
# endregion


getmincut_manager = reqparse.RequestParser()
getmincut_manager.add_argument('theme', required=True)

@api.route('/getmincutmanager')
class GwMincutManager(Resource):
    @api.expect(getmincut_manager)
    @optional_auth
    def get(self):
        """Submit query

        Returns additional information at clicked map position.
        """
        print("hola")
        config = get_config()
        log = create_log(self)
        args = getmincut_manager.parse_args()
        try:
            db = get_db()
        except:
            remove_handlers() 

        schema = get_schema_from_theme(args["theme"], config)
        print("theme -> ", schema)
        if schema is None:
            log.warning(" Schema is None")
            remove_handlers()
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
                remove_handlers()
            log.info(f" Server response -> {json.dumps(result)}")
            print(f"SERVER RESPONSE: {json.dumps(result)}\n")
            remove_handlers()
            return handle_db_result_mincutmanager(result, args["theme"])


getlist_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
getlist_parser.add_argument('theme', required=True)
getlist_parser.add_argument('tabName', required=True)
getlist_parser.add_argument('widgetname', required=True)
getlist_parser.add_argument('formtype', required=False, default="form_feature")
getlist_parser.add_argument('tableName', required=True)
getlist_parser.add_argument('filterSign', required=False, default="=")
getlist_parser.add_argument('filterFields', required=False, default={})
@api.route('/getlist')
class GwGetList(Resource):
    @api.expect(getlist_parser)
    @optional_auth
    def get(self):
        config = get_config()
        log = create_log(self)
        args = getlist_parser.parse_args()
        try:
            db = get_db()
        except:
            remove_handlers()

        schema = get_schema_from_theme(args["theme"], config)

        request =  {
            "client": {
                "device": 5, "infoType": 1, "lang": "en_US"
            },
            "form": {
                "formName": "",
                "tabName": str(args['tabName']),
                "widgetname": str(args['widgetname']),
                "formtype": str(args['formtype'])
            },
            "feature": {
                "tableName": args["tableName"]
            },
            "data": {
                "filterFields": {},
                "pageInfo": {}
            }
        }

        # Manage filters
        print("args[filterFields] -> ", args["filterFields"])
        if args["filterFields"] in (None, "", "null", "{}"):
            request["data"]["filterFields"] = {}
        else:
            filterFields = json.loads(args["filterFields"])
            for k, v in filterFields.items():
                if v in (None, "", "null"):
                    continue
                request["data"]["filterFields"][k] = {
                #   "columnname": v["columnname"],
                    "value": v["value"],
                    "filterSign": v["filterSign"]
                }

        request_json = json.dumps(request)
        sql = f"SELECT {schema}.gw_fct_getlist($${request_json}$$);"
        log.info(f" Server execution -> {sql}")
        print(f"SERVER EXECUTION: {sql}\n")
        result = dict()
        try:
             result = db.execute(sql).fetchone()[0]
        except exc.ProgrammingError:
             log.warning(" Server execution failed")
             print(f"Server execution failed\n{traceback.format_exc()}")
             remove_handlers()

        log.info(f" Server response {str(result)[0:100]}")
        print(f"SERVER RESPONSE: {json.dumps(result)}\n\n")
        remove_handlers()
        return jsonify(result)


""" readyness probe endpoint """
@app.route("/ready", methods=['GET'])
def ready():
    return jsonify({"status": "OK"})


""" liveness probe endpoint """
@app.route("/healthz", methods=['GET'])
def healthz():
    return jsonify({"status": "OK"})


# local webserver
if __name__ == '__main__':
    print("Starting Giswater Selector service...")
    app.run(host='localhost', port=5017, debug=True)

