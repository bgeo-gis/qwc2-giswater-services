"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

from typing import Optional, List, Tuple, Dict
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
mail = None

def create_body(theme, project_epsg=None, form='', feature='', filter_fields='', tiled=None, extras=None):
    """ Create and return parameters as body to functions"""

    # info_types = {'full': 1}
    info_type = 1
    lang = "es_ES"  # TODO: get from app lang
    if tiled is None:
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


def execute_procedure(log, theme, function_name, parameters=None, set_role=True, needs_write=False):
    """ Manage execution database function
    :param function_name: Name of function to call (text)
    :param parameters: Parameters for function (json) or (query parameters)
    :param log_sql: Show query in qgis log (bool)
    :param set_role: Set role in database with the current user
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

    db = get_db(theme, needs_write=needs_write)
    execution_msg = sql
    response_msg = ""
    
    with db.begin() as conn:
        result = dict()
        print(f"SERVER EXECUTION: {sql}\n")
        if set_role: conn.execute(text(f"SET ROLE {get_identity()};"))
        result = conn.execute(text(sql)).fetchone()[0]
        response_msg = json.dumps(result)
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

def get_db(theme: str = None, needs_write: bool = False) -> DatabaseEngine:
    logging.basicConfig
    db_url = None
    if theme is not None:
        db_url = get_db_url_from_theme(theme, needs_write=needs_write)
    if not db_url:
        db_url = get_config().get("db_url_write" if needs_write else "db_url_read")

    return DatabaseEngine().db_engine(db_url)

def get_schema_from_theme(theme: str, config: RuntimeConfig) -> Optional[str]:
    theme_cfg = get_config().get("themes").get(theme)
    if theme_cfg is not None:
        return theme_cfg.get("schema")
    return None

def get_db_url_from_theme(theme: str, needs_write: bool = False) -> Optional[str]:
    theme_cfg = get_config().get("themes").get(theme)
    if theme_cfg is not None:
        print(theme_cfg)
        return theme_cfg.get("db_url_write" if needs_write else "db_url_read")
    return None

def get_db_layers(theme: str) -> List[str]:
    db_layers = []
    theme_cfg = get_config().get("themes").get(theme)
    if theme_cfg is not None:
        db_layers = theme_cfg.get("layers")
    return db_layers

def parse_layers(request_layers: str, config: RuntimeConfig, theme: str) -> List[str]:
    layers = []
    db_layers = []
    theme_cfg = config.get("themes").get(theme)
    if theme_cfg is not None:
        db_layers = theme_cfg.get("layers")

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

def get_fields_per_layout(all_fields: list) -> dict:
    fields_per_layout: Dict[str, list] = {}
    for field in all_fields:
        fields_per_layout.setdefault(field['layoutname'], []).append(field)
    return fields_per_layout

def get_layouts_per_tab(all_fields: list) -> dict:
    layouts_per_tab: Dict[str, set] = {}
    for field in all_fields:
        layouts_per_tab.setdefault(field.get("tabname"), set()).add(field.get("layoutname"))
    return layouts_per_tab

def filter_fields(fields: list, key: str = "web_layoutorder") -> list:
    sorted_fields = sorted(fields, key=lambda f: (f[key] is None, f[key])) # Keep Nones at the end
    filtered_fields = []
    i = 0
    for field in sorted_fields:
        if (
            field.get(key) is not None and
            field.get("hidden") not in (True, 'True', 'true')
        ):
            field["web_layoutorder"] = i
            filtered_fields.append(field)
            i += 1
    
    return filtered_fields

def get_fields_xml_vertical(fields: list, lyt_name: str, sort: bool = True):
    if sort:
        fields = filter_fields(fields)
    form_xml = f'<layout class="QGridLayout" name="{lyt_name}">'
    for field in fields:
        i = field["web_layoutorder"]
        label_xml, widget_xml = get_field_xml(field)
        colspan = 2 if label_xml is None else 1
        column = 0 if label_xml is None else 1
        if label_xml is not None:
            form_xml += (
                f'<item row="{i}" column="0" colspan="1">'
                 f'{label_xml}'
                f'</item>')
        form_xml += (
            f'<item row="{i}" column="{column}" colspan="{colspan}">'
             f'{widget_xml}'
            f'</item>')

    form_xml += '</layout>'
    return form_xml

def get_fields_xml_horizontal(fields: list, lyt_name: str, sort: bool = True):
    if sort:
        fields = filter_fields(fields)
    form_xml = f'<layout class="QHBoxLayout" name="{lyt_name}">'
    for field in fields:
        label_xml, widget_xml = get_field_xml(field)
        if label_xml is not None:
            form_xml += (
                f'<item>'
                 f'{label_xml}'
                f'</item>')
        form_xml += (
            f'<item>'
             f'{widget_xml}'
            f'</item>')

    form_xml += '</layout>'
    return form_xml

def get_field_xml(field: dict) -> Tuple[Optional[str], str]:
    label_xml = None
    widget_xml = None

    widget_type = field['widgettype']
    widget_name = field["columnname"]
    value = field.get("value", "")

    tooltip = field.get('tooltip')
    tooltip_prop_xml = ''
    if tooltip != None:
        tooltip_prop_xml = (
            f'<property name="toolTip">'
             f'<string>{tooltip}</string>'
            f'</property>')

    if field["label"] not in (None, 'None', ''):
        label_xml = (
            f'<widget class="QLabel" name="{widget_name}_label">'
             f'<property name="text">'
              f'<string>{field["label"]}</string>'
             f'</property>'
             f'{tooltip_prop_xml}'
            f'</widget>')

    widget_props_xml = ""
    widget_class = None

    read_only = str(not field.get('iseditable', True)).lower()
    widget_props_xml += (
        f'<property name="readOnly">'
         f'<bool>{read_only}</bool>'
        f'</property>')    
    
    required = str(field.get('isMandatory', False)).lower()
    widget_props_xml += (
        f'<property name="required">'
         f'<bool>{required}</bool>'
        f'</property>')

    def dict_to_str(x: dict) -> str:
        return json.dumps(x).replace('<', '$lt').replace('>', '$gt')

    widgetcontrols = field.get('widgetcontrols', {})
    widget_props_xml += (
        f'<property name="widgetcontrols">'
         f'<string>{dict_to_str(widgetcontrols)}</string>'
        f'</property>')
    widgetfunction = field.get('widgetfunction', {})
    widget_props_xml += (
        f'<property name="widgetfunction">'
         f'<string>{dict_to_str(widgetfunction)}</string>'
        f'</property>')
    isfilter = field.get('isfilter', False)
    if isfilter is None:
        isfilter = False
    widget_props_xml += (
        f'<property name="isfilter">'
         f'<bool>{str(isfilter).lower()}</bool>'
        f'</property>')
    widget_props_xml += tooltip_prop_xml

    if widget_type in ("hspacer", "vspacer"):
        widget_xml = ''
        widget_xml += f'<spacer name="{widget_name}">'
        widget_xml += '<property name="orientation">'
        if widget_type == "hspacer":
            widget_xml += '<enum>Qt::Horizontal</enum>'
        else:
            widget_xml += '<enum>Qt::Vertical</enum>'
        widget_xml += '</property>'
        widget_xml += '</spacer>'
        return label_xml, widget_xml
    elif widget_type == "check":
        widget_class = "QCheckBox"
        widget_props_xml += (
            f'<property name="checked">'
             f'<bool>{value}</bool>'
            f'</property>')
    elif widget_type == "datetime":
        widget_class = "QDateEdit" if field.get("datatype") == 'date' else "QDateTimeEdit"
        widget_props_xml += (
            f'<property name="value">'
             f'<string>{value}</string>'
            f'</property>')
    elif widget_type == "combo":
        widget_class = "QComboBox"

        if field.get("isNullValue", False) is True:
            field["comboIds"].insert(0, '')
            field["comboNames"].insert(0, '')
        options = dict(zip(field["comboIds"], field["comboNames"]))

        for key, val in options.items():
            widget_props_xml += (
                f'<item>'
                 f'<property name="value">'
                  f'<string>{key}</string>'
                 f'</property>'
                 f'<property name="text">'
                  f'<string>{val}</string>'
                 f'</property>'
                f'</item>'
            )
        if field.get("selectedId"):
            value = field["selectedId"]
        elif len(field["comboIds"]) > 0:
            value = field["comboIds"][0]
        else:
            value = ''

        widget_props_xml += (
            f'<property name="value">'
             f'<string>{value}</string>'
            f'</property>')
    elif widget_type == "button":
        widget_class = "QPushButton"
        widget_props_xml += (
            f'<property name="text">'
             f'<string>{value}</string>'
            f'</property>')
        if (widgetfunction.get("functionName") == "get_info_node"):
            widget_props_xml += (
                f'<property name="action">'
                 f'<string>{{"name": "featureLink", "params": {{"id": "{value}", "tableName": "v_edit_node"}}}}</string>'
                f'</property>')
    elif widget_type in ("tableview", "tablewidget"):
        widget_class = "QTableView" if widget_type == "tableview" else "QTableWidget"
        widget_props_xml += (
            f'<property name="linkedobject">'
             f'<string>{field.get("linkedobject")}</string>'
            f'</property>')
    elif widget_type == "spinbox":
        widget_class = "QSpinBox"
        # xml += f'<property name="value">'
        # xml += f'<number>0</number>'
        # xml += f'<number></number>'
        # xml += '</property>'
    elif widget_type == "textarea":
        widget_class = "QTextEdit"
        widget_props_xml += (
            f'<property name="text">'
             f'<string>{value}</string>'
            f'</property>')
    elif widget_type == "fileselector":
        widget_class = "QgsFileWidget"
        widget_props_xml += (
            f'<property name="text">'
             f'<string>{value}</string>'
            f'</property>')
    else:
        widget_class = "QLineEdit"
        widget_props_xml += (
            f'<property name="text">'
             f'<string>{value}</string>'
            f'</property>')

    widget_xml = (
        f'<widget class="{widget_class}" name="{widget_name}">'
         f'{widget_props_xml}'
        f'</widget>'
    )
    return label_xml, widget_xml
