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
from utils import create_xml_form_v3

from PyQt5.QtWidgets import QApplication

from qwc_services_core.api import Api
from qwc_services_core.app import app_nocache
from qwc_services_core.auth import auth_manager, optional_auth
from qwc_services_core.api import CaseInsensitiveArgument
from qwc_services_core.tenant_handler import TenantHandler
from qwc_services_core.runtime_config import RuntimeConfig
from qwc_services_core.database import DatabaseEngine
from sqlalchemy import text, exc

# from PyQt5.QtDesigner import QFormBuilder

# Flask application
app = Flask(__name__)
app_nocache(app)
api = Api(app, version='1.0', title='Flowtrace service API',
          description="""API for QWC Giswater Flow trace/exit service.
          """,
          default_label='Gw Flowtrace operations', doc='/api/')
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'

# disable verbose 404 error message
app.config['ERROR_404_HELP'] = False

auth = auth_manager(app, api)

tenant_handler = TenantHandler(app.logger)

upstream_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
upstream_parser.add_argument('theme', required=True)
upstream_parser.add_argument('epsg', required=True)
upstream_parser.add_argument('coords', required=True)
upstream_parser.add_argument('zoom', required=True)

downstream_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
downstream_parser.add_argument('theme', required=True)
downstream_parser.add_argument('epsg', required=True)
downstream_parser.add_argument('coords', required=True)
downstream_parser.add_argument('zoom', required=True)

def get_config() -> RuntimeConfig:
    tenant = tenant_handler.tenant()
    config_handler = RuntimeConfig("gwFlowtrace", app.logger)
    return config_handler.tenant_config(tenant)

def get_db() -> DatabaseEngine:
    return DatabaseEngine().db_engine(get_config().get("db_url"))

def get_schema_from_theme(theme: str, config: RuntimeConfig) -> Optional[str]:
    themes = config.get("themes")
    theme = themes.get(theme)
    if theme is not None:
        return theme.get("schema")
    return None

def handle_db_result(result: dict) -> Response:
    response = {}
    if 'results' not in result or result['results'] > 0:
        # form_xml = create_xml_form_v3(result)
        response = result
    return jsonify(response)

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

@api.route('/upstream')
class GwUpstream(Resource):
    @api.expect(upstream_parser)
    @optional_auth
    def get(self):
        """Submit query

        Returns additional information at clicked map position.
        """
        config = get_config()
        log = create_log(self)
        args = upstream_parser.parse_args()
        coords = args["coords"].split(',')
        try:
            db = get_db()
        except:
            remove_handlers() 
        schema = get_schema_from_theme(args["theme"], config)

        if schema is None:
            log.warning("Schema is None")
            remove_handlers()
            return jsonify({"schema": schema})

        log.info(f"Selected schema -> {str(schema)}")

        request =  {
            "client": {
                "device": 5, "infoType": 1, "lang": "en_US", "epsg": int(args['epsg'])
            }, 
            "form": {}, 
            "feature": {
                
            },
            "data": {
                "filterFields": {},
                "pageInfo": {},
                "coordinates": {
                    "epsg": int(args['epsg']),
                    "xcoord": coords[0],
                    "ycoord": coords[1],
                    "zoomRatio": float(args['zoom'])
                }
            }
        }
        request_json = json.dumps(request)
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
                remove_handlers()
            log.info(f" Server response: {str(result)[0:100]}")
            print(f"SERVER RESPONSE: {result}\n\n")
            remove_handlers()
            return handle_db_result(result)


@api.route('/downstream')
class GwDownstream(Resource):
    @api.expect(downstream_parser)
    @optional_auth
    def get(self):
        """Submit query

        Returns additional information at clicked map position.
        """
        config = get_config()
        log = create_log(self)
        args = downstream_parser.parse_args()
        coords = args["coords"].split(',')
        try:
            db = get_db()
        except:
            remove_handlers() 

        schema = get_schema_from_theme(args["theme"], config)
        
        if schema is None:
            log.warning(" Schema is None")
            remove_handlers()
            return jsonify({"schema": schema})

        log.info(f" Selected schema -> {str(schema)}")

        request =  {
            "client": {
                "device": 5, "infoType": 1, "lang": "en_US", "epsg": int(args['epsg'])
            }, 
            "form": {}, 
            "feature": {
                
            },
            "data": {
                "filterFields": {},
                "pageInfo": {},
                "coordinates": {
                    "epsg": int(args['epsg']),
                    "xcoord": coords[0],
                    "ycoord": coords[1],
                    "zoomRatio": float(args['zoom'])
                }
            }
        }
        request_json = json.dumps(request)
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
                remove_handlers()
            log.info(f" Server response: {str(result)[0:100]}")
            print(f"SERVER RESPONSE: {result}\n\n")
            remove_handlers()
            return handle_db_result(result)


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
    print("Starting Giswater Flowtrace service...")
    app.run(host='localhost', port=5019, debug=True)

