from typing import List, Optional
from xml.dom.minidom import parseString, Document, Element

from flask import Flask, request, jsonify, Response
from flask_restx import Resource, reqparse
import os
import traceback
import requests
import logging
import json
from datetime import date
from utils import get_demo_form, create_xml_form, create_xml_form_v2

from qwc_services_core.api import Api
from qwc_services_core.app import app_nocache
from qwc_services_core.auth import auth_manager, optional_auth
from qwc_services_core.api import CaseInsensitiveArgument
from qwc_services_core.tenant_handler import TenantHandler
from qwc_services_core.runtime_config import RuntimeConfig
from qwc_services_core.database import DatabaseEngine

from sqlalchemy import exc

# from PyQt5.QtDesigner import QFormBuilder

# Flask application
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
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
    config_handler = RuntimeConfig("gwInfo", app.logger)
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
        # form_xml = create_xml_form(result)
        form_xml = create_xml_form_v2(result)
        # form_xml = get_demo_form()
        response = {
            "feature": {
                "id": result["body"]["feature"]["id"],
                "idName": result["body"]["feature"]["idName"],
                "geometry": result["body"]["feature"]["geometry"]["st_astext"]
            },
            "form_xml": form_xml
        }
    print(jsonify(response))
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

getinfofromcoordinates_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
getinfofromcoordinates_parser.add_argument('theme', required=True)
getinfofromcoordinates_parser.add_argument('epsg', required=True)
getinfofromcoordinates_parser.add_argument('xcoord', required=True)
getinfofromcoordinates_parser.add_argument('ycoord', required=True)
getinfofromcoordinates_parser.add_argument('zoomRatio', required=True)
getinfofromcoordinates_parser.add_argument('layers', required=True)
@api.route('/fromcoordinates')
class GwGetInfoFromCoordinates(Resource):
    @api.expect(getinfofromcoordinates_parser)
    @optional_auth
    def get(self):
        """Submit query

        Returns additional information at clicked map position.
        """
        config = get_config()
        log = create_log(self)
        args = getinfofromcoordinates_parser.parse_args()
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

        layers = self.__parse_layers(args["layers"], config, args["theme"])

        request =  {
            "client": {
                "device": 5, "infoType": 1, "lang": "en_US"
            }, 
            "form": {
                "editable": "False"
            }, 
            "data": {
                "activeLayer": layers[0],
                "visibleLayer": layers,
                "coordinates": {
                    "epsg": int(args['epsg']),
                    "xcoord": float(args['xcoord']),
                    "ycoord": float(args['ycoord']),
                    "zoomRatio": float(args['zoomRatio']),
                }
            }
        }
        request_json = json.dumps(request)
        sql = f"SELECT {schema}.gw_fct_getinfofromcoordinates($${request_json}$$);"
        log.info(f" Server execution -> {sql}")
        print(f"SERVER EXECUTION: {sql}\n")
        result = dict()
        try:
             result = db.execute(sql).fetchone()[0]
        except exc.ProgrammingError:
             log.warning(" Server execution failed")
             print(f"Server execution failed\n{traceback.format_exc()}")
             remove_handlers()
        result: dict = db.execute(sql).fetchone()[0]
        log.info(f" Server response: {str(result)[0:100]}")
        print(f"SERVER RESPONSE: {result}\n\n")
        remove_handlers()
        return handle_db_result(result)


    def __parse_layers(self, request_layers: str, config: RuntimeConfig, theme: str) -> List[str]:
        layers = []
        db_layers = []
        theme = config.get("themes").get(theme)
        if theme is not None:
            db_layers = theme.get("layers")

        for l in request_layers.split(','):
            if l in db_layers:
                layers.append(db_layers[l])
        return layers


getinfofromid_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
getinfofromid_parser.add_argument('theme', required=True)
getinfofromid_parser.add_argument('tableName', required=True)
getinfofromid_parser.add_argument('id', required=True)
@api.route('/fromid')
class GwGetInfoFromId(Resource):
    @api.expect(getinfofromid_parser)
    @optional_auth
    def get(self):
        config = get_config()
        log = create_log(self)
        args = getinfofromid_parser.parse_args()
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
                "editable": "False"
            }, 
            "feature": {
                "tableName": args["tableName"],
                "id": args["id"]
            },
            "data": {}
        }
        request_json = json.dumps(request)
        sql = f"SELECT {schema}.gw_fct_getinfofromid($${request_json}$$);"
        log.info(f" Server execution -> {sql}")
        print(f"SERVER EXECUTION: {sql}\n")
        result = dict()
        try:
             result = db.execute(sql).fetchone()[0]
        except exc.ProgrammingError:
             log.warning(" Server execution failed")
             print(f"Server execution failed\n{traceback.format_exc()}")
             remove_handlers()
             
        log.info(f" Server response")
        print(f"SERVER RESPONSE: {result}\n\n")
        remove_handlers()
        return handle_db_result(result)


getlist_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
getlist_parser.add_argument('theme', required=True)
getlist_parser.add_argument('tabName', required=True)
getlist_parser.add_argument('widgetname', required=True)
getlist_parser.add_argument('formtype', required=False, default="form_feature")
getlist_parser.add_argument('tableName', required=True)
getlist_parser.add_argument('idName', required=True)
getlist_parser.add_argument('id', required=True)
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
                "tableName": args["tableName"],
                "idName": args["idName"],
                "id": args["id"]
            },
            "data": {
                "filterFields": {
                    args["idName"]: {
                        "value": args["id"],
                        "filterSign": str(args["filterSign"])
                    }
                },
                "pageInfo": {}
            }
        }

        # Manage filters
        filterFields = json.loads(args["filterFields"])
        for k, v in filterFields.items():
            if v in (None, "", "null"):
                continue
            request["data"]["filterFields"][k] = {
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

        log.info(f" Server response")
        print(f"SERVER RESPONSE: {result}\n\n")
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
    print("Starting Giswater Feature Info service...")
    app.run(host='localhost', port=5015, debug=True)

