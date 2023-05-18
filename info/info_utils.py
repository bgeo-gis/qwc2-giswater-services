"""
Copyright BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

from typing import List, Tuple
import json
from flask import jsonify, Response
from utils import create_widget_xml

def handle_db_result(result: dict) -> Response:
    response = {}
    if 'results' not in result or result['results'] > 0:
        form_xml = create_xml_form(result)
        response = {
            "feature": {
                "id": result["body"]["feature"]["id"],
                "idName": result["body"]["feature"]["idName"],
                "geometry": result["body"]["feature"]["geometry"]["st_astext"]
            },
            "form_xml": form_xml
        }

    return jsonify(response)


def create_xml_form(db_result: dict, simplified: bool=True) -> str:
    form_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    form_xml += '<ui version="4.0">'
    form_xml += '<widget class="QWidget" name="Form">'

    if db_result['body']['form']['template'] == "info_generic":
        form_xml += generic_xml_form(db_result)
    else:
        form_xml += full_xml_form(db_result)

    form_xml += '</widget>'
    form_xml += '</ui>'

    return form_xml


def full_xml_form(db_result):
    form_xml = '<layout class="QHBoxLayout" name="MainLayout">'
    form_xml += '<item>'
    form_xml += '<widget class="QTabWidget" name="tabWidget">'
    form_xml += '<property name="currentIndex">'
    form_xml += '<number>0</number>'
    form_xml += '</property>\n'

    for tab in db_result['body']['form']['visibleTabs']:
        form_xml += f'<widget class="QWidget" name="{tab["tabName"]}">'
        form_xml += '<attribute name="title">'
        form_xml += f'<string>{tab["tabLabel"]}</string>'
        form_xml += '</attribute>'

        form_xml += tab_onelyt_xml(db_result["body"]["data"]["fields"], tab["tabName"])

        form_xml += '</widget>\n'

    form_xml += '</widget>'
    form_xml += '</item>'
    form_xml += '</layout>'

    return form_xml


def generic_xml_form(db_result):
    form_xml = '<layout class="QGridLayout" name="MainLayout">'

    for field in db_result['body']['data']['fields']:
        form_xml += create_widget_xml(field)

    form_xml += '</layout>'

    return form_xml


def tab_onelyt_xml(fields, tab_name):

    layouts = []
    if tab_name == 'tab_data':
        layouts = ['lyt_top_1', 'lyt_bot_1', 'lyt_bot_2', 'lyt_data_1', 'lyt_data_2']
    elif tab_name == 'tab_visit':
        layouts = ['lyt_visit_1', 'lyt_visit_2', 'lyt_visit_3']
    lyt_data_1 = ""

    i = 1
    for field in fields:
        tabname = field.get("tabname")
        if tabname in ('document', 'element', 'relation'):
            tabname += 's'
        if tabname != tab_name.lstrip('tab_'):
            continue
        if tab_name == "tab_data":
            field["iseditable"] = False
            field["web_layoutorder"] = i

        xml = create_widget_xml(field)
        if xml:
            lyt_data_1 += xml
            if tab_name == "tab_data":
                i += 1

    form_xml = ""
    form_xml += f'<layout class="QHBoxLayout" name="lyt_{tab_name.lstrip("tab_")}">'
    form_xml += '  <item>'
    form_xml += f'    <layout class="QGridLayout" name="lyt_{tab_name.lstrip("tab_")}_1">'
    form_xml += lyt_data_1
    form_xml += '    </layout>'
    form_xml += '  </item>'
    form_xml += '</layout>'

    return form_xml

