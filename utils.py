"""
Copyright BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

from typing import Optional, List
from datetime import date
from flask import jsonify
from sqlalchemy import text, exc

from qwc_services_core.runtime_config import RuntimeConfig
from qwc_services_core.database import DatabaseEngine
from qwc_services_core.auth import get_identity

import os
import logging
import json
import traceback


app = None
api = None
tenant_handler = None


def create_body(project_epsg=None, form='', feature='', filter_fields='', extras=None):
    """ Create and return parameters as body to functions"""

    # info_types = {'full': 1}
    info_type = 1
    lang = "es_ES"  # TODO: get from app lang

    client = f'$${{"client":{{"device": 5, "lang": "{lang}", "cur_user": "{str(get_identity())}"'
    if info_type is not None:
        client += f', "infoType": {info_type}'
    if project_epsg is not None:
        client += f', "epsg": {project_epsg}'
    client += f'}}, '

    form = f'"form":{{{form}}}, '
    feature = f'"feature":{{{feature}}}, '
    filter_fields = f'"filterFields":{{{filter_fields}}}'
    page_info = f'"pageInfo":{{}}'
    data = f'"data":{{{filter_fields}, {page_info}'
    if extras is not None:
        data += ', ' + extras
    data += f'}}}}$$'
    body = "" + client + form + feature + data

    return body

def create_response(db_result=None, form_xml=None, status=None, message=None, do_jsonify=False):
    """ Create and return a json response to send to the client """

    response = {"status": "Failed", "message": {}, "version": {}, "body": {}}

    if status is not None:
        if status in (True, "Accepted"):
            response["status"] = "Accepted"
            if message:
                response["message"] = {"level": 3, "text": message}
        else:
            response["status"] = "Failed"
            if message:
                response["message"] = {"level": 2, "text": message}
            
        if do_jsonify:
            response = jsonify(response)
        return response

    if not db_result and not form_xml:
        response["status"] = "Failed"
        response["message"] = {"level": 2, "text": "DB returned null"}
        if do_jsonify:
            response = jsonify(response)
        return response
    elif form_xml:
        response["status"] = "Accepted"

    if db_result:
        response = db_result
    response["form_xml"] = form_xml

    if do_jsonify:
        response = jsonify(response)
    return response


def execute_procedure(log, theme, function_name, parameters=None):
    """ Manage execution database function
    :param function_name: Name of function to call (text)
    :param parameters: Parameters for function (json) or (query parameters)
    :param log_sql: Show query in qgis log (bool)
    :return: Response of the function executed (json)
    """

    # Manage schema_name and parameters
    schema_name = get_schema_from_theme(theme, get_config())
    if schema_name is None:
        log.warning(" Schema is None")
        remove_handlers()
        return create_response(status=False, message=f"Schema for theme '{theme}' not found")
    sql = f"SELECT {schema_name}.{function_name}("
    if parameters:
        sql += f"{parameters}"
    sql += f");"

    db = get_db(theme)
    with db.begin() as conn:
        result = dict()
        log.info(f" Server execution -> {sql}")
        print(f"SERVER EXECUTION: {sql}\n")
        try:
            conn.execute(text(f"SET ROLE {get_identity()};"))
            result = conn.execute(text(sql)).fetchone()[0]
        except exc.ProgrammingError as e:
            log.warning(" Server execution failed")
            print(f"Server execution failed\n{traceback.format_exc()}")
            remove_handlers()
            return create_response(status=False, message=e, do_jsonify=True)
        log.info(f" Server response -> {json.dumps(result)}")
        print(f"SERVER RESPONSE: {json.dumps(result)}\n")
        return result


def get_config() -> RuntimeConfig:
    tenant = tenant_handler.tenant()
    config_handler = RuntimeConfig("giswater", app.logger)
    return config_handler.tenant_config(tenant)

def get_db(theme: str = None) -> DatabaseEngine:
    logging.basicConfig
    db_url = None
    if theme is not None:
        db_url = get_db_url_from_theme(theme)
    if not db_url:
        db_url = get_config().get("db_url")

    return DatabaseEngine().db_engine(db_url)

def get_schema_from_theme(theme: str, config: RuntimeConfig) -> Optional[str]:
    themes = get_config().get("themes")
    theme = themes.get(theme)
    if theme is not None:
        return theme.get("schema")
    return None

def get_db_url_from_theme(theme: str) -> Optional[str]:
    themes = get_config().get("themes")
    theme = themes.get(theme)
    if theme is not None:
        return theme.get("db_url")
    return None

def get_db_layers(theme: str) -> List[str]:
    db_layers = []
    theme = get_config().get("themes").get(theme)
    if theme is not None:
        db_layers = theme.get("layers")
    return db_layers

def parse_layers(request_layers: str, config: RuntimeConfig, theme: str) -> List[str]:
    layers = []
    db_layers = []
    theme = config.get("themes").get(theme)
    if theme is not None:
        db_layers = theme.get("layers")

    for l in request_layers.split(','):
        if l in db_layers:
            layers.append(db_layers[l])
    return layers


# Create log pointer
def create_log(class_name):
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
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s:%(name)s:%(message)s", datefmt = "%d/%m/%y %H:%M:%S")
    fileh.setFormatter(formatter)

    # Removes previous handlers on root Logger
    remove_handlers()
    # Gets root Logger and add handler
    logger_name = f"{tenant_handler.tenant()}:{get_identity()}:{class_name.split('.')[-1]}"
    log = logging.getLogger(logger_name)
    # log = logging.getLogger()
    log.addHandler(fileh)
    log.setLevel(logging.DEBUG)
    return log

# Removes previous handlers on root Logger
def remove_handlers(log=logging.getLogger()):
    for hdlr in log.handlers[:]:
        log.removeHandler(hdlr)
