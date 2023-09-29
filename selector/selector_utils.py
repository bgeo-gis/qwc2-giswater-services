"""
Copyright © 2023 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils

import logging
from flask import jsonify, Response
from qwc_services_core.runtime_config import RuntimeConfig


def make_response(db_result: dict, theme: str, config: RuntimeConfig, log):
    theme_cfg = config.get("themes").get(theme)

    if theme_cfg.get("tiled"):
        layersVisibility = {}
        
        for formTab in db_result["body"]["form"]["formTabs"]:
            if formTab["tabName"] == "tab_exploitation":
                for field in formTab["fields"]:
                    expl_config = theme_cfg.get("exploitations")
                    project_layer = expl_config.get(str(field["expl_id"]))
                    layersVisibility[project_layer] = field["value"]
        
        db_result["body"]["data"]["layersVisibility"] = layersVisibility

    # form xml
    try:
        form_xml = create_xml_form_v3(db_result)
    except:
        form_xml = None

    utils.remove_handlers(log)

    return utils.create_response(db_result, form_xml=form_xml, do_jsonify=True, theme=theme)

def create_xml_form_v3(db_result: dict) -> str:
    form_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    form_xml += '<ui version="4.0">'
    form_xml += '<widget class="QWidget" name="Form">'
    form_xml += '<layout class="QHBoxLayout" name="MainLayout">'
    form_xml += '<item>'
    form_xml += '<widget class="QTabWidget" name="tabWidget">'
    form_xml += '<property name="currentIndex">'
    form_xml += '<number>0</number>'
    form_xml += '</property>\n'

    for tab in db_result['body']['form']['formTabs']:

        form_xml += f'<widget class="QWidget" name="{tab["tabName"]}">'
        form_xml += '<attribute name="title">'
        form_xml += f'<string>{tab["tabLabel"]}</string>'
        form_xml += '</attribute>'

        tab_xml = set_tab_xml(tab["fields"], tab["tabName"], tab["manageAll"], tab["selectorType"])

        form_xml += f'<layout class="QGridLayout" name="lyt_{tab["tabName"]}">'
        form_xml += tab_xml
        form_xml += '</layout>'

        form_xml += '</widget>\n'

    form_xml += '</widget>'
    form_xml += '</item>'  
    form_xml += '</layout>'
    form_xml += '</widget>'
    form_xml += '</ui>'

    return form_xml


def set_tab_xml(fields, tab_name, manage_all, selector_type):

    xml = ''
    chk_all_xml = ''
    tab_xml = ''
    chk_all = False
    all_checked = True

    fields = utils.filter_fields(fields, key="orderby")

    for idx, field in enumerate(fields):
        row = field["web_layoutorder"]
        if manage_all.lower() == "true":
            row += 1
        value = ""
        if "value" in field:
            value = field["value"]
            if value is False:
                all_checked = False
        
        widget_type = field["type"]
        widget_name = field["widgetname"]

        tab_xml += f'<item row="{row}" column="0">'
        tab_xml += '<widget class="QLabel" name="label">'
        tab_xml += '<property name="text">'
        tab_xml += f'<string>{field["label"]}</string>'
        tab_xml += '</property>'
        tab_xml += '</widget>'
        tab_xml += '</item>'
        tab_xml += f'<item row="{row}" column="1">'
        
        if widget_type == "check":
            tab_xml += f'<widget class="QCheckBox" name="{widget_name}">'
            tab_xml += f'<property name="checked">'
            tab_xml += f'<boolean>{value}</boolean>'
            tab_xml += f'</property>'
            # Action setselectors
            tab_xml += f'<property name="action">'
            tab_xml += f'<string>{{"name": "setSelectors", "params": {{"tabName": "{tab_name}", "selectorType": "{selector_type}", "id": "{widget_name}", "value": "{value}"}}}}</string>'
            tab_xml += f'</property>'
        elif widget_type == "datetime":
            tab_xml += f'<widget class="QDateTimeEdit" name="{widget_name}">'
            tab_xml += f'<property name="value">'
            tab_xml += f'<string>{value}</string>'
            tab_xml += f'</property>'
        elif widget_type == "combo":
            tab_xml += f'<widget class="QComboBox" name="{widget_name}">'
            options = dict(zip(field["comboIds"], field["comboNames"]))
            value = options[field["selectedId"]]

            for val in options.values():
                tab_xml += '<item>'
                tab_xml += '<property name="text">'
                tab_xml += f'<string>{val}</string>'
                tab_xml += '</property>'
                tab_xml += '</item>'
            tab_xml += f'<property name="value">'
            tab_xml += f'<string>{value}</string>'
            tab_xml += f'</property>'
        elif widget_type == "button":
            tab_xml += f'<widget class="QPushButton" name="{widget_name}">'
            tab_xml += f'<property name="text">'
            tab_xml += f'<string>{value}</string>'
            tab_xml += f'</property>'
            if (field["widgetfunction"]["functionName"] == "get_info_node"):
                tab_xml += f'<property name="action">'
                tab_xml += f'<string>{{"name": "featureLink", "params": {{"id": "{value}", "tableName": "v_edit_node"}}}}</string>'
                tab_xml += f'</property>'
        else:
            tab_xml += f'<widget class="QLineEdit" name="{widget_name}">'
            tab_xml += f'<property name="text">'
            tab_xml += f'<string>{value}</string>'
            tab_xml += '</property>'

        tab_xml += f'<property name="readOnly">'
        tab_xml += f'<bool>false</bool>'
        tab_xml += '</property>'
        tab_xml += '</widget>'
        tab_xml += '</item>\n'

    # Add check_all if necessary
    if manage_all.lower() == "true":
        chk_all = True
        chk_all_xml += f'<item row="0" column="0">'
        chk_all_xml += '<widget class="QLabel" name="label">'
        chk_all_xml += '<property name="text">'
        chk_all_xml += f'<string>Check all</string>'
        chk_all_xml += '</property>'
        chk_all_xml += '</widget>'
        chk_all_xml += '</item>'
        chk_all_xml += f'<item row="0" column="1">'

        chk_all_xml += f'<widget class="QCheckBox" name="chk_all_{tab_name}">'
        chk_all_xml += f'<property name="checked">'
        chk_all_xml += f'<boolean>{all_checked}</boolean>'
        chk_all_xml += f'</property>'
        # Action setselectors
        chk_all_xml += f'<property name="action">'
        chk_all_xml += f'<string>{{"name": "setSelectors", "params": {{"tabName": "{tab_name}", "id": "chk_all", "value": "{all_checked}", "selectorType": "{selector_type}"}}}}</string>'
        chk_all_xml += f'</property>'

        chk_all_xml += f'<property name="readOnly">'
        chk_all_xml += f'<bool>false</bool>'
        chk_all_xml += '</property>'
        chk_all_xml += '</widget>'
        chk_all_xml += '</item>\n'

    xml = chk_all_xml + tab_xml
    return xml
