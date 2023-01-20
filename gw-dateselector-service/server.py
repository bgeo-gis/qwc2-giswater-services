from datetime import date
from typing import List, Optional
from xml.dom.minidom import parseString, Document, Element

from flask import Flask, request, jsonify, Response
from flask_restx import Resource, reqparse
import os
import traceback
import logging
import requests
import json
from utils import get_dateselector_ui, create_xml_form_v3

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
api = Api(app, version='1.0', title='Date Selector service API',
          description="""API for QWC GwDateSelector service.

Functions to work with visit dates.
          """,
          default_label='GwDateSelector operations', doc='/api/')
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'

# disable verbose 404 error message
app.config['ERROR_404_HELP'] = False

auth = auth_manager(app, api)

tenant_handler = TenantHandler(app.logger)


def get_config() -> RuntimeConfig:
    tenant = tenant_handler.tenant()
    config_handler = RuntimeConfig("gwDateselector", app.logger)
    return config_handler.tenant_config(tenant)

def get_db() -> DatabaseEngine:
    print(f"DB URL: {get_config().get('db_url')}")
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
        return jsonify({"message": "DB returned null"})
    if 'results' not in result or result['results'] > 0:
        layer_columns = {}
        db_layers = get_db_layers(theme)
        
        for k, v in db_layers.items():
            if v in result['body']['data']['layerColumns']:
                layer_columns[k] = result['body']['data']['layerColumns'][v]

        response = {
            "feature": {},
            "data": {
                #"userValues": result['body']['data']['userValues'],
                #"geometry": result['body']['data']['geometry'],
                "date_from": result['body']['data']['date_from'],
                "date_to": result['body']['data']['date_to'],
                "layerColumns": layer_columns
            },
            "form": {},
            "form_xml": None
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


@api.route('/getdialog')
class GwGetDialog(Resource):
    @optional_auth
    def get(self):
        """Submit query

        Returns dateselector dialog.
        """
        # Get dialog
        form_xml = get_dateselector_ui()

        # Response
        response = {
            "feature": {},
            "data": {},
            "form_xml": form_xml
        }
        remove_handlers()
        return jsonify(response)


getdates_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
getdates_parser.add_argument('theme', required=True)
getdates_parser.add_argument('layers', required=True)
@api.route('/getdates')
class GwGetDates(Resource):
    @api.expect(getdates_parser)
    @optional_auth
    def get(self):
        """Submit query

        Get current user's dates.
        """

        # Get current dates
        config = get_config()
        log = create_log(self)
        args = getdates_parser.parse_args()
        identity = get_identity()
        try:
            db = get_db()
        except:
            remove_handlers() 

        schema = get_schema_from_theme(args["theme"], config)
        if schema is None:
            log.warning(" Schema is None")
            return jsonify({"schema": schema})

        log.info(f" Selected schema -> {str(schema)}")

        layers = parse_layers(args["layers"], config, args["theme"])
        request =  {
            "client": {
                "device": 5, "infoType": 1, "lang": "en_US", "cur_user": str(identity)
            }, 
            "form": {}, 
            "feature": {},
            "data": {
                "filterFields":{},
                "pageInfo":{},
                "action": "GET",
                "layers": layers
            }
        }
        request_json = json.dumps(request)
        sql = f"SELECT {schema}.gw_fct_dateselector($${request_json}$$);"
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


setdates_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
setdates_parser.add_argument('theme', required=True)
setdates_parser.add_argument('dateFrom', required=True)
setdates_parser.add_argument('dateTo', required=True)
setdates_parser.add_argument('layers', required=True)
@api.route('/setdates')
class GwSetDates(Resource):
    @api.expect(setdates_parser)
    @optional_auth
    def get(self):
        """Submit query

        Updates current user's dates and returns them.
        """
        config = get_config()
        log = create_log(self)
        args = setdates_parser.parse_args()
        identity = get_identity()
        try:
            db = get_db()
        except:
            remove_handlers() 

        schema = get_schema_from_theme(args["theme"], config)
        if schema is None:
            log.warning(" Schema is None")
            return jsonify({"schema": schema})

        log.info(f" Selected schema -> {str(schema)}")
        

        from_date = args["dateFrom"]
        to_date = args["dateTo"]
        layers = parse_layers(args["layers"], config, args["theme"])
        request =  {
            "client": {
                "device": 5, "infoType": 1, "lang": "en_US", "cur_user": str(identity)
            }, 
            "form": {}, 
            "feature": {},
            "data": {
                "filterFields":{},
                "pageInfo":{},
                "action": "SET",
                "date_from": from_date,
                "date_to": to_date,
                "layers": layers
            }
        }
        request_json = json.dumps(request)
        sql = f"SELECT {schema}.gw_fct_dateselector($${request_json}$$);"
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
    print("Starting Giswater Date Selector service...")
    app.run(host='localhost', port=5017, debug=True)

