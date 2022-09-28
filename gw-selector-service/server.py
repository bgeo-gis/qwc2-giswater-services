from typing import List, Optional
from xml.dom.minidom import parseString, Document, Element

from flask import Flask, request, jsonify, Response
from flask_restx import Resource, reqparse
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
from sqlalchemy import text

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
getselector_parser.add_argument('layers', required=False)

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
setselector_parser.add_argument('layers', required=False)

def get_config() -> RuntimeConfig:
    tenant = tenant_handler.tenant()
    config_handler = RuntimeConfig("gwSelector", app.logger)
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
        form_xml = create_xml_form_v3(result)
        response = {
            "feature": {},
            "data": result['body']['data'],
            "form": result['body']['form'],
            "form_xml": form_xml
        }
    return jsonify(response)

@api.route('/getselector')
class GwGetSelector(Resource):
    @api.expect(getselector_parser)
    @optional_auth
    def get(self):
        """Submit query

        Returns additional information at clicked map position.
        """
        args = getselector_parser.parse_args()

        config = get_config()
        db = get_db()
        schema = get_schema_from_theme(args["theme"], config)
        if schema is None:
            return jsonify({"schema": schema})

        layers = args['layers'].split(',')

        request =  {
            "client": {
                "device": 5, "infoType": 1, "lang": "en_US", "epsg": int(args['epsg']), "cur_user": "test"
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
                "filterText": ""
            }
        }
        request_json = json.dumps(request)
        sql = f"SELECT {schema}.gw_fct_getselectors($${request_json}$$);"
        print(sql)
        with db.begin() as conn:
            result: dict = conn.execute(text(sql)).fetchone()[0]
            print(result)
            return handle_db_result(result)


@api.route('/setselector')
class GwSetSelector(Resource):
    @api.expect(setselector_parser)
    @optional_auth
    def get(self):
        """Submit query

        Returns additional information at clicked map position.
        """
        args = setselector_parser.parse_args()

        config = get_config()
        db = get_db()
        schema = get_schema_from_theme(args["theme"], config)
        if schema is None:
            return jsonify({"schema": schema})

        layers = args['layers'].split(',')

        request =  {
            "client": {
                "device": 5, "infoType": 1, "lang": "en_US", "epsg": int(args['epsg']), "cur_user": "test"
            }, 
            "form": {}, 
            "feature": {},
            "data": {
                "layers": layers,
                "filterFields": {},
                "pageInfo": {},
                "selectorType": str(args["selectorType"]),
                "tabName": str(args['tabName']),
                "id": str(args['id']),
                "isAlone": str(args['isAlone']),
                "disableParent": str(args['disableParent']),
                "value": str(args['value']),
                "addSchema": str(args['addSchema'])
            }
        }
        request_json = json.dumps(request)
        sql = f"SELECT {schema}.gw_fct_setselectors($${request_json}$$);"
        print(sql)
        with db.begin() as conn:
            result: dict = conn.execute(text(sql)).fetchone()[0]
            print(result)
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
    print("Starting Giswater Selector service...")
    app.run(host='localhost', port=5017, debug=True)

