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


def create_body(theme, project_epsg=None, form='', feature='', filter_fields='', extras=None):
    """ Create and return parameters as body to functions"""

    # info_types = {'full': 1}
    info_type = 1
    lang = "es_ES"  # TODO: get from app lang
    try:
        tiled = get_config().get("themes").get(theme).get("tiled", False)
    except:
        tiled = False

    client = f'$${{"client":{{"device": 5, "lang": "{lang}", "cur_user": "{str(get_identity())}", "tiled": "{tiled}"'
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

def create_response(db_result=None, form_xml=None, status=None, message=None, do_jsonify=False, theme=None):
    """ Create and return a json response to send to the client """

    try:
        tiled = get_config().get("themes").get(theme).get("tiled", False)
    except:
        tiled = False

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
    response["tiled"] = tiled
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
    execution_msg = sql
    response_msg = ""
    
    with db.begin() as conn:
        result = dict()
        print(f"SERVER EXECUTION: {sql}\n")
        try:
            conn.execute(text(f"SET ROLE {get_identity()};"))
            result = conn.execute(text(sql)).fetchone()[0]
            response_msg = json.dumps(result)
        except exc.ProgrammingError as e:
            response_msg = traceback.format_exc()
            log.warning(f"{execution_msg}|||{response_msg}")
            print(f"Server execution failed\n{traceback.format_exc()}")
            remove_handlers()
            return create_response(status=False, message=e, do_jsonify=True, theme=theme)
        if not result or result.get('status') == "Failed":
            log.warning(f"{execution_msg}|||{response_msg}") 
        else:
            log.info(f"{execution_msg}|||{response_msg}") 
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
            db_layer = db_layers[l]
            if isinstance(db_layer, str):
                layers.append(db_layer)
            elif isinstance(db_layer, list):
                layers += db_layer
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


def create_widget_xml(field: dict) -> str:
    xml = ''
    if field.get('hidden') in (True, 'True', 'true'):
        return xml
    row = field.get("web_layoutorder")
    if row is None:
        return xml
    value = ""
    if "value" in field:
        value = field["value"]

    widget_type = field['widgettype']
    widget_name = field["columnname"]
    widgetcontrols = field.get('widgetcontrols', {})
    if not widgetcontrols:
        widgetcontrols = {}
    widgetfunction = field.get('widgetfunction', {})
    if not widgetfunction:
        widgetfunction = {}
    # print(f"{field['layoutname']}")
    # print(f"          {widget_name} -> {row}")

    xml = ''
    read_only = "false"
    if 'iseditable' in field:
        read_only = str(not field['iseditable']).lower()

    if field["label"] in (None, 'None', ''):
        xml += f'<item row="{row}" column="0" colspan="2">'
    elif widget_type == "tableview":
        xml += f'<item row="{row+1}" column="0" colspan="2">'
    else:
        xml += f'<item row="{row}" column="0">\n'
        xml += '<widget class="QLabel" name="label">\n'
        xml += '<property name="text">'
        xml += f'<string>{field["label"]}</string>'
        xml += '</property>\n'
        xml += '</widget>\n'
        xml += '</item>\n'
        xml += f'<item row="{row}" column="1">\n'

    if widget_type == "check":
        xml += f'<widget class="QCheckBox" name="{widget_name}">'
        xml += f'<property name="checked">'
        xml += f'<bool>{value}</bool>'
        xml += f'</property>'
    elif widget_type == "datetime":
        widget_class = "QDateTimeEdit"
        if field.get("datatype") == 'date':
            widget_class = "QDateEdit"
        xml += f'<widget class="{widget_class}" name="{widget_name}">'
        xml += f'<property name="value">'
        xml += f'<string>{value}</string>'
        xml += f'</property>'
    elif widget_type == "combo":
        xml += f'<widget class="QComboBox" name="{widget_name}">'
        if field.get("isNullValue", False) is True:
            field["comboIds"].insert(0, '')
            field["comboNames"].insert(0, '')
        options = dict(zip(field["comboIds"], field["comboNames"]))

        if (field.get("selectedId")):
            value = field["selectedId"]
        else:
            if len(field["comboIds"]) > 0:
                value = field["comboIds"][0]
            else:
                value = ''

        for key, val in options.items():
            xml += '<item>'
            xml += '<property name="value">'
            xml += f'<string>{key}</string>'
            xml += '</property>'
            xml += '<property name="text">'
            xml += f'<string>{val}</string>'
            xml += '</property>'
            xml += '</item>'
        xml += f'<property name="value">'
        xml += f'<string>{value}</string>'
        xml += f'</property>'
    elif widget_type == "button":
        xml += f'<widget class="QPushButton" name="{widget_name}">'
        xml += f'<property name="text">'
        xml += f'<string>{value}</string>'
        xml += f'</property>'
        if (widgetfunction.get("functionName") == "get_info_node"):
            xml += f'<property name="action">'
            xml += f'<string>{{"name": "featureLink", "params": {{"id": "{value}", "tableName": "v_edit_node"}}}}</string>'
            xml += f'</property>'
    elif widget_type in ("tableview", "tablewidget"):
        if widget_type == "tableview":
            # QTableView
            xml += f'<widget class="QTableView" name="{widget_name}">'
        else:
            # QTableWidget
            xml += f'<widget class="QTableWidget" name="{widget_name}">'
        xml += f'<property name="linkedobject">'
        xml += f'<string>{field.get("linkedobject")}</string>'
        xml += f'</property>'
    elif widget_type == "spinbox":
        xml += f'<widget class="QSpinBox" name="{widget_name}">'
        # xml += f'<property name="value">'
        # xml += f'<number>0</number>'
        # xml += f'<number></number>'
        # xml += '</property>'
    elif widget_type == "textarea":
        xml += f'<widget class="QTextEdit" name="{widget_name}">'
        xml += f'<property name="text">'
        xml += f'<string>{value}</string>'
        xml += '</property>'
    elif widget_type in ("hspacer", "vspacer"):
        xml += f'<spacer name="{widget_name}">'
        xml += f'<property name="orientation">'
        if widget_type == "hspacer":
            xml += f'<enum>Qt::Horizontal</enum>'
        else:
            xml += f'<enum>Qt::Vertical</enum>'
        xml += '</property>'
    elif widget_type == "fileselector":
        xml += f'<widget class="QgsFileWidget" name="{widget_name}">'
        xml += f'<property name="text">'
        xml += f'<string>{value}</string>'
        xml += f'</property>'
    else:
        xml += f'<widget class="QLineEdit" name="{widget_name}">'
        xml += f'<property name="text">'
        xml += f'<string>{value}</string>'
        xml += '</property>'

    xml += f'<property name="readOnly">'
    xml += f'<bool>{read_only}</bool>'
    xml += '</property>'
    widgetcontrols = json.dumps(widgetcontrols).replace('<', '$lt').replace('>', '$gt')
    xml += f'<property name="widgetcontrols">'
    xml += f'<string>{widgetcontrols}</string>'
    xml += '</property>'
    widgetfunction = json.dumps(widgetfunction).replace('<', '$lt').replace('>', '$gt')
    xml += f'<property name="widgetfunction">'
    xml += f'<string>{widgetfunction}</string>'
    xml += '</property>'
    if widget_type in ("hspacer", "vspacer"):
        xml += '</spacer>'
    else:
        xml += '</widget>'
    xml += '</item>\n'

    return xml
