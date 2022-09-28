from typing import List, Optional
from xml.dom.minidom import parseString, Document, Element

from flask import Flask, request, jsonify, Response
from flask_restx import Resource, reqparse
import requests
import json
from utils import get_demo_form, create_xml_form, create_xml_form_v2

from qwc_services_core.api import Api
from qwc_services_core.app import app_nocache
from qwc_services_core.auth import auth_manager, optional_auth
from qwc_services_core.api import CaseInsensitiveArgument
from qwc_services_core.tenant_handler import TenantHandler
from qwc_services_core.runtime_config import RuntimeConfig
from qwc_services_core.database import DatabaseEngine

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

getinfofromcoordinates_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
getinfofromcoordinates_parser.add_argument('theme', required=True)
getinfofromcoordinates_parser.add_argument('epsg', required=True)
getinfofromcoordinates_parser.add_argument('xcoord', required=True)
getinfofromcoordinates_parser.add_argument('ycoord', required=True)
getinfofromcoordinates_parser.add_argument('zoomRatio', required=True)
getinfofromcoordinates_parser.add_argument('layers', required=True)

getinfofromid_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
getinfofromid_parser.add_argument('theme', required=True)
getinfofromid_parser.add_argument('tableName', required=True)
getinfofromid_parser.add_argument('id', required=True)

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
                "geometry": result["body"]["feature"]["geometry"]["st_astext"]
            },
            "form_xml": form_xml
        }
    return jsonify(response)

@api.route('/fromcoordinates')
class GwGetInfoFromCoordinates(Resource):
    @api.expect(getinfofromcoordinates_parser)
    @optional_auth
    def get(self):
        """Submit query

        Returns additional information at clicked map position.
        """
        args = getinfofromcoordinates_parser.parse_args()

        config = get_config()
        db = get_db()
        schema = get_schema_from_theme(args["theme"], config)
        if schema is None:
            return jsonify({"schema": schema})

        layers = self.__parse_layers(args["layers"], config, args["theme"])

        request =  {
            "client": {
                "device": 4, "infoType": 1, "lang": "en_US"
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
        result: dict = db.execute(sql).fetchone()[0]

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


@api.route('/fromid')
class GwGetInfoFromId(Resource):
    @api.expect(getinfofromid_parser)
    @optional_auth
    def get(self):
        args = getinfofromid_parser.parse_args()

        config = get_config()
        db = get_db()

        schema = get_schema_from_theme(args["theme"], config)

        request =  {
            "client": {
                "device": 4, "infoType": 1, "lang": "en_US"
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
        result: dict = db.execute(sql).fetchone()[0]
        # print(result)
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
    print("Starting Giswater Feature Info service...")
    app.run(host='localhost', port=5015, debug=True)

