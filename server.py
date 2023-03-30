"""
Copyright BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils

from flask import Flask, jsonify, Response
from qwc_services_core.api import Api
from qwc_services_core.app import app_nocache
from qwc_services_core.auth import auth_manager
from qwc_services_core.tenant_handler import TenantHandler

from info.info import info_bp
from mincut.mincut import mincut_bp
from flowtrace.flowtrace import flowtrace_bp
from selector.selector import selector_bp
from profile.profile import profile_bp
from dateselector.dateselector import dateselector_bp
from visit.visit import visit_bp
from search.search import search_bp


# Flask application
app = Flask(__name__)
app_nocache(app)
api = Api(app, version='1.0', title='Giswater service API',
          description="""API for QWC Giswater service.""",
          default_label='Giswater', doc='/api/')
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'

# disable verbose 404 error message
app.config['ERROR_404_HELP'] = False
# disable sorting of json keys
app.config['JSON_SORT_KEYS'] = False

auth = auth_manager(app, api)
tenant_handler = TenantHandler(app.logger)

utils.app = app
utils.api = api
utils.tenant_handler = tenant_handler


app.register_blueprint(info_bp, url_prefix='/info')
app.register_blueprint(mincut_bp, url_prefix='/mincut')
app.register_blueprint(flowtrace_bp, url_prefix='/flowtrace')
app.register_blueprint(selector_bp, url_prefix='/selector')
app.register_blueprint(profile_bp, url_prefix='/profile')
app.register_blueprint(dateselector_bp, url_prefix='/dateselector')
app.register_blueprint(visit_bp, url_prefix='/visit')
app.register_blueprint(search_bp, url_prefix='/search')

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
    print("Starting blueprint test service...")
    app.run(host='162.55.174.222', port=5069, debug=True)
