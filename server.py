"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils
import os
from flask import Flask, jsonify, Response, request
from qwc_services_core.api import Api
from qwc_services_core.app import app_nocache
from qwc_services_core.auth import auth_manager
from qwc_services_core.tenant_handler import TenantHandler

from flask_mail import Mail

from info.info import info_bp
from mincut.mincut import mincut_bp
from flowtrace.flowtrace import flowtrace_bp
from selector.selector import selector_bp
from profile.profile import profile_bp
from dateselector.dateselector import dateselector_bp
from visit.visit import visit_bp
from search.search import search_bp
from toolbox.toolbox import toolbox_bp
from util.util import util_bp
from custom_search.custom_search import custom_search_bp
from parcelfilter.parcelfilter import parcelfilter_bp
from nonvisual.nonvisual import nonvisual_bp

import traceback
import html

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
# app.config['JSON_SORT_KEYS'] = False
app.json.sort_keys = False

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
app.register_blueprint(toolbox_bp, url_prefix='/toolbox')
app.register_blueprint(util_bp, url_prefix='/util')
app.register_blueprint(custom_search_bp, url_prefix='/customSearch')
app.register_blueprint(parcelfilter_bp, url_prefix='/parcelfilter')
app.register_blueprint(nonvisual_bp, url_prefix='/nonvisual')
app.register_blueprint(forward_bp, url_prefix="/forward")
# Setup mailer
def mail_config_from_env(app):
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False') == 'True'
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

try:
    # Código para configurar y utilizar Flask-Mail
    mail_config_from_env(app)
    mail = Mail(app)
    utils.mail = mail
    #Controller(app,mail)
except Exception as e:
    print(f"Excepcion===: {str(e)}")

print("------------------------------------")
print(f"MAIL_SERVER: {app.config['MAIL_SERVER']}")
print(f"MAIL_PORT: {app.config['MAIL_PORT']}")
print(f"MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
print(f"MAIL_PASSWORD: {app.config['MAIL_PASSWORD']}")
print(f"MAIL_USE_TLS: {app.config['MAIL_USE_TLS']}")
print(f"MAIL_USE_SSL: {app.config['MAIL_USE_SSL']}")

@app.errorhandler(Exception)
def hande_error(e: Exception):
    print("=========== ERROR OCCURRED ===========")
    request_str = request.url
    request_json = None
    try:
        request_json = request.get_json()
    except Exception:
        request_json = "{unknown}"

    if request_json:
        request_str += f" {request_json}"
    # request_str = html.escape(request_str)
    # request_str = request_str.replace("'", "\\'")

    print(request_str)

    log = utils.create_log("-")

    trace = traceback.format_exc()
    trace_escaped = html.escape(trace).replace('\n', '<br>')

    print(trace)

    log.error(f"{request_str}|||{trace_escaped}") 
    utils.remove_handlers(log)

    return "Internal server error", 500

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
