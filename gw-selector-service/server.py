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
from utils import create_xml_form_v3

from PyQt5.QtWidgets import QApplication

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

getselector_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
getselector_parser.add_argument('theme', required=True)
getselector_parser.add_argument('epsg', required=True)
getselector_parser.add_argument('currentTab', required=True)
getselector_parser.add_argument('selectorType', required=True)
getselector_parser.add_argument('layers', required=True)
getselector_parser.add_argument('loadProject', required=True)

setselector_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
setselector_parser.add_argument('theme', required=True)
setselector_parser.add_argument('epsg', required=True)
setselector_parser.add_argument('selectorType', required=True)
setselector_parser.add_argument('tabName', required=True)
setselector_parser.add_argument('id', required=True)
setselector_parser.add_argument('isAlone', required=True)
setselector_parser.add_argument('disableParent', required=True)
setselector_parser.add_argument('value', required=True)
setselector_parser.add_argument('addSchema', required=True)
setselector_parser.add_argument('layers', required=True)

def get_config() -> RuntimeConfig:
    tenant = tenant_handler.tenant()
    config_handler = RuntimeConfig("gwSelector", app.logger)
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
        form_xml = create_xml_form_v3(result)
        layer_columns = {}
        db_layers = get_db_layers(theme)
        
        for k, v in db_layers.items():
            if v in result['body']['data']['layerColumns']:
                layer_columns[k] = result['body']['data']['layerColumns'][v]

        response = {
            "feature": {},
            "data": {
                "userValues": result['body']['data']['userValues'],
                "geometry": result['body']['data']['geometry'],
                "layerColumns": layer_columns
            },
            "form": result['body']['form'],
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

@api.route('/getselector')
class GwGetSelector(Resource):
    @api.expect(getselector_parser)
    @optional_auth
    def get(self):
        """Submit query

        Returns additional information at clicked map position.
        """
        config = get_config()
        log = create_log(self)
        args = getselector_parser.parse_args()
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

        # layers = args['layers'].split(',')
        layers = parse_layers(args["layers"], config, args["theme"])

        request =  {
            "client": {
                "device": 5, "infoType": 1, "lang": "en_US", "epsg": int(args['epsg']), "cur_user": str(identity)
            }, 
            "form": {
                "currentTab": str(args["currentTab"])
            }, 
            "feature": {},
            "data": {
                "layers": layers,
                "filterFields": {},
                "pageInfo": {},
                "selectorType": str(args["selectorType"]),
                "filterText": "",
                "loadProject": args["loadProject"]
            }
        }
        request_json = json.dumps(request)
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
                remove_handlers()
            log.info(f" Server response -> {json.dumps(result)}")
            print(f"SERVER RESPONSE: {json.dumps(result)}\n")
            remove_handlers()
            return handle_db_result(result, args["theme"])


@api.route('/setselector')
class GwSetSelector(Resource):
    @api.expect(setselector_parser)
    @optional_auth
    def get(self):
        """Submit query

        Returns additional information at clicked map position.
        """
        config = get_config()
        log = create_log(self)
        args = setselector_parser.parse_args()
        identity = get_identity()
        try:
            db = get_db()
        except:
            remove_handlers()
        
        schema = get_schema_from_theme(args["theme"], config)
        if schema is None:
            log.warning(f" Schema is None")
            remove_handlers()
            return jsonify({"schema": schema})

        log.info(f" Selected schema {str(schema)}")

        # layers = args['layers'].split(',')
        layers = parse_layers(args["layers"], config, args["theme"])

        request =  {
            "client": {
                "device": 5, "infoType": 1, "lang": "en_US", "epsg": int(args['epsg']), "cur_user": str(identity)
            }, 
            "form": {}, 
            "feature": {},
            "data": {
                "layers": layers,
                "filterFields": {},
                "pageInfo": {},
                "selectorType": str(args["selectorType"]),
                "tabName": str(args['tabName']),
                "addSchema": str(args['addSchema'])
            }
        }
        if args['id'] == 'chk_all':
            request['data']['checkAll'] = str(args['value'])
        else:
            request['data']['id'] = str(args['id'])
            request['data']['isAlone'] = str(args['isAlone'])
            request['data']['disableParent'] = str(args['disableParent'])
            request['data']['value'] = str(args['value'])

        request_json = json.dumps(request)
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
                remove_handlers()
            log.info(f" Server response: {str(result)[0:100]}")
            print(f"SERVER RESPONSE: {result}\n\n")
            remove_handlers()
            return handle_db_result(result, args["theme"])


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

