"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

from typing import List, Tuple, Optional, Union, Callable
import json
from flask import jsonify, Response
from utils import get_fields_per_layout, get_fields_xml_vertical, get_fields_xml_horizontal, filter_fields, get_layouts_per_tab

def create_xml_form(db_result: dict, editable: bool) -> str:
    form_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    form_xml += '<ui version="4.0">'
    form_xml += '<widget class="QWidget" name="Form">'

    if db_result['body']['form']['template'] == "info_generic":
        # form_xml += generic_xml_form(db_result)
        form_xml += get_fields_xml_vertical(db_result['body']['data']['fields'], "MainLayout")
    else:
        form_xml += full_xml_form(db_result, editable)

    form_xml += '</widget>'
    form_xml += '</ui>'

    return form_xml


def full_xml_form(db_result, editable: bool):
    all_fields = db_result["body"]["data"]["fields"]
    fields_per_layout = get_fields_per_layout(all_fields)
    layouts_per_tab = get_layouts_per_tab(all_fields)

    form_xml = '<layout class="QVBoxLayout" name="MainLayout">'
    if 'lyt_toolbar' in fields_per_layout:
        # Toolbar
        form_xml += '<item>'
        form_xml += get_fields_xml_horizontal(fields_per_layout['lyt_toolbar'], 'lyt_toolbar')
        form_xml += '</item>'
    # Tabs
    form_xml += '<item>'
    form_xml += '<widget class="QTabWidget" name="tabWidget">'
    form_xml += '<property name="currentIndex">'
    form_xml += '<number>0</number>'
    form_xml += '</property>'

    for tab in db_result['body']['form']['visibleTabs']:
        form_xml += f'<widget class="QWidget" name="{tab["tabName"]}">'
        form_xml += '<attribute name="title">'
        form_xml += f'<string>{tab["tabLabel"]}</string>'
        form_xml += '</attribute>'

        form_xml += get_tab_xml(tab["tabName"], all_fields, fields_per_layout, layouts_per_tab, editable)

        form_xml += '</widget>'

    form_xml += '</widget>'
    form_xml += '</item>'
    if 'lyt_buttons' in fields_per_layout:
        # Buttons
        form_xml += '<item>'
        form_xml += get_fields_xml_horizontal(fields_per_layout['lyt_buttons'], 'lyt_buttons')
        form_xml += '</item>'
    form_xml += '</layout>'

    return form_xml


def get_tab_xml(tab_name: str, fields: list, fields_per_layout: dict, layouts_per_tab: dict, editable: bool) -> str:
    layouts = layouts_per_tab.get(tab_name, [])
    layout_name = f"lyt_{tab_name}"
    if tab_name == "tab_data":  return get_combined_layout_xml(layout_name, fields_per_layout, layouts, editable)
    else:                       return get_generic_tab_xml(layout_name, fields_per_layout, layouts)


def get_combined_layout_xml(layout_name: str, fields_per_layout: dict, layouts: list, editable: bool) -> str:
    fields = []
    for layout in layouts:
        fields.extend(fields_per_layout.get(layout, []))
    if not editable:
        for field in fields:
            field["iseditable"] = False
    return get_fields_xml_vertical(fields, layout_name)


def get_generic_tab_xml(layout_name: str, fields_per_layout: dict, layouts: list) -> str:
    xml = f'<layout class="QVBoxLayout" name="{layout_name}">'
    for layout in sorted(layouts):
        fields = filter_fields(fields_per_layout.get(layout, []))
        if len(fields) > 0:
            xml += (
                f'<item>'
                 f'{get_fields_xml_vertical(fields, layout, sort=False)}'
                f'</item>'
            )

    xml += '</layout>'
    return xml
