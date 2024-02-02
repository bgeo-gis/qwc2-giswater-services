"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

from flask import jsonify, Response

import logging
import json
import utils
from utils import get_fields_per_layout, get_fields_xml_horizontal, get_fields_xml_vertical

def manage_response(result, log, manager=False):
    # form xml
    try:
        if manager:
            form_xml = visitmanager_create_xml_form(result)
        else:
            form_xml = visit_create_xml_form(result)
    except:
        form_xml = None

    utils.remove_handlers(log)

    return utils.create_response(result, form_xml=form_xml, do_jsonify=True)


def visit_create_xml_form(result: dict) -> str:
    fields_per_layout = get_fields_per_layout(result['body']['data']['fields'])
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
            form_xml += get_fields_xml_vertical(fields_per_layout.get("lyt_data_1", []), "lyt_data_1")
            form_xml += '</item>'

            # Layout 2
            form_xml += '<item>'
            form_xml += get_fields_xml_horizontal(fields_per_layout.get("lyt_data_2", []), "lyt_data_2")
            form_xml += '</item>'
        elif tabname == 'tab_file':
            # Layout 1
            form_xml += '<item>'
            form_xml += get_fields_xml_vertical(fields_per_layout.get("lyt_files_1", []), "lyt_files_1")
            form_xml += '</item>'

            # Layout 2
            form_xml += '<item>'
            form_xml += get_fields_xml_vertical(fields_per_layout.get("lyt_files_2", []), "lyt_files_2")
            form_xml += '</item>'
        
        form_xml += f'</layout>'

        form_xml += '</widget>'

    form_xml += '</widget>'
    form_xml += '</item>'

    form_xml += '</layout>'
    form_xml += '</widget>'
    form_xml += '</ui>'

    return form_xml

def visitmanager_create_xml_form(result: dict) -> str:
    fields_per_layout = get_fields_per_layout(result['body']['data']['fields'])

    form_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    form_xml += '<ui version="4.0">'
    form_xml += '<widget class="QWidget" name="dlg_visitmanager">'
    form_xml += '<layout class="QVBoxLayout" name="MainLayout">'

    # Layout 
    form_xml += '<item>'
    form_xml += get_fields_xml_horizontal(fields_per_layout.get("lyt_visit_mng_1", []), "lyt_visit_mng_1")
    form_xml += '</item>'

    form_xml += '</layout>'
    form_xml += '</widget>'
    form_xml += '</ui>'

    return form_xml



