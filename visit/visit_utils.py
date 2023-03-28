"""
Copyright BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

from flask import jsonify, Response

import logging
import json


def handle_db_result(result: dict) -> Response:
    response = {}
    if not result:
        logging.warning(" DB returned null")
        return jsonify({"message": "DB returned null"})
    if 'results' not in result or result['results'] > 0:
        try:
            form_xml = visit_create_xml_form(result)
        except:
            form_xml = None

        response = {
            "status": result['status'],
            "version": result['version'],
            "body": result['body'],
            "form_xml": form_xml
        }
    return jsonify(response)


def visit_create_xml_form(result: dict) -> str:
    layout_xmls = get_layout_xmls(result)
    # tab_names = {'tab_plan': 'Plan', 'tab_exec': 'Exec', 'tab_hydro': 'Hydro', 'tab_log': 'Log'}
    tabs = result["body"]["data"]["form"].get('visibleTabs', [])

    form_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    form_xml += '<ui version="4.0">'
    form_xml += '<widget class="QWidget" name="dlg_visit">'
    form_xml += '<layout class="QVBoxLayout" name="MainLayout">'

    # Tabs
    form_xml += '<item>'
    form_xml += '<widget class="QTabWidget" name="tabWidget">'
    form_xml += '<property name="currentIndex">'
    form_xml += '<number>0</number>'
    form_xml += '</property>'

    for tab in tabs:
        tabname = tab.get('tabName')
        tablabel = tab.get('tabLabel', tabname)
        if not tabname:
            continue

        form_xml += f'<widget class="QWidget" name="{tabname}">'
        form_xml += '<attribute name="title">'
        form_xml += f'<string>{tablabel}</string>'
        form_xml += '</attribute>'
        form_xml += f'<layout class="QVBoxLayout" name="lyt_{tabname}">'

        if tabname == 'tab_data':
            # Layout 1
            form_xml += '<item>'
            form_xml += layout_xmls.get('lyt_data_1', '')
            form_xml += '</item>'

            # Layout 2
            form_xml += '<item>'
            form_xml += layout_xmls.get('lyt_data_2', '')
            form_xml += '</item>'
        elif tabname == 'tab_file':
            # Layout 1
            form_xml += '<item>'
            form_xml += layout_xmls.get('lyt_files_1', '')
            form_xml += '</item>'

            # Layout 2
            form_xml += '<item>'
            form_xml += layout_xmls.get('lyt_files_2', '')
            form_xml += '</item>'
        
        form_xml += f'</layout>'

        form_xml += '</widget>'

    form_xml += '</widget>'
    form_xml += '</item>'

    form_xml += '</layout>'
    form_xml += '</widget>'
    form_xml += '</ui>'

    return form_xml


def get_layout_xmls(result: dict) -> dict:
    widgets_x_layouts = {}
    for field in result['body']['data']['fields']:
        layoutname = field['layoutname']
        if layoutname not in widgets_x_layouts:
            widgets_x_layouts[layoutname] = []
        widgets_x_layouts[layoutname].append(field)
    
    layout_xmls = {}
    for layout, fields in widgets_x_layouts.items():
        # TODO: Improve this, extract from get_layout_xmls. Maybe the <layout> tags can go in {class}_create_xml_form
        layout_class = "QGridLayout"
        if layout in ('lyt_data_2'):
            layout_class = "QHBoxLayout"
        layout_xml = f'<layout class="{layout_class}" name="{layout}">'
        for field in fields:
            layout_xml += create_widget_xml(field)
        layout_xml += '</layout>'
        layout_xmls[layout] = layout_xml

    return layout_xmls


# TODO: MOVE THIS TO UTILS
def create_widget_xml(field: dict) -> str:
    xml = ''
    if field.get('hidden') in (True, 'True', 'true'):
        return xml
    row = field["web_layoutorder"]
    if row is None:
        return xml
    value = ""
    if "value" in field:
        value = field["value"]

    widget_type = field['widgettype']
    widget_name = field["column_id"]
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
        xml += f'<item row="{row}" column="0">'
        xml += f'<widget class="QLabel" name="lbl_{widget_name}">'
        xml += '<property name="text">'
        xml += f'<string>{field["label"]}</string>'
        xml += '</property>'
        xml += '</widget>'
        xml += '</item>'
        xml += f'<item row="{row}" column="1">'

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
        if field["isNullValue"] is True:
            field["comboIds"].insert(0, '')
            field["comboNames"].insert(0, '')
        options = dict(zip(field["comboIds"], field["comboNames"]))
        # print(options)
        try:
            value = options[field["selectedId"]]
        except KeyError:
            value = list(options.values())[0]

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
    elif widget_type == "tableview":
        # QTableWidget
        xml += f'<widget class="QTableView" name="{widget_name}">'
        xml += f'<property name="linkedobject">'
        xml += f'<string>tbl_visit_x_node</string>'
        xml += f'</property>'
        xml += f'<property name="action">'
        xml += f'<string>{{"name": "getlist", "params": {{"tabName": "visit", "widgetname": "{widget_name}", "tableName": "tbl_visit_x_node", "idName": "node_id", "id": "1000"}}}}</string>'
        xml += f'</property>'
        # xml += f'<property name="text">'
        # xml += f'<string>{value}</string>'
        # xml += f'</property>'
        # if (widgetfunction.get("functionName") == "get_info_node"):
        #     xml += f'<property name="action">'
        #     xml += f'<string>{{"name": "featureLink", "params": {{"id": "{value}", "tableName": "v_edit_node"}}}}</string>'
        #     xml += f'</property>'
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
    xml += '</widget>'
    xml += '</item>\n'

    return xml

