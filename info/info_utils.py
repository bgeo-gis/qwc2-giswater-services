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
from utils import (
    get_fields_per_layout,
    get_fields_xml_vertical,
    get_fields_xml_horizontal,
    filter_fields,
    get_layouts_per_tab,
    get_field_xml,
)

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


def full_xml_form(db_result: dict, editable: bool) -> str:
    all_fields = db_result["body"]["data"]["fields"]
    fields_per_layout = get_fields_per_layout(all_fields)
    layouts_per_tab = get_layouts_per_tab(all_fields)

    # Move epa_type field to the epa tab
    top_fields: list = fields_per_layout.get("lyt_top_1", [])
    epa_type_index = next((i for i, field in enumerate(top_fields) if field["columnname"] == "epa_type"), None)
    if epa_type_index is not None:
        epa_type_field = top_fields.pop(epa_type_index)
        fields_per_layout.setdefault("lyt_epa_1", []).append(epa_type_field)

    form_xml = '<layout class="QGridLayout" name="MainLayout">'
    # if 'lyt_toolbar' in fields_per_layout:
    #     # Toolbar
    #     form_xml += '<item>'
    #     form_xml += get_fields_xml_horizontal(fields_per_layout['lyt_toolbar'], 'lyt_toolbar')
    #     form_xml += '</item>'
    # Tabs
    form_xml += '<item row="0" column="0">'
    # form_xml += '<spacer>'
    # form_xml += '<property name="orientation">'
    # form_xml += '<enum>Qt::Vertical</enum>'
    # form_xml += '</property>'
    # form_xml += '</spacer>'
    form_xml += '<widget class="QTabWidget" name="tabWidget">'
    form_xml += '<property name="currentIndex">'
    form_xml += '<number>0</number>'
    form_xml += '</property>'

    # print(f"{db_result['body']['form']['visibleTabs'] = }")

    for tab in db_result['body']['form']['visibleTabs']:
        form_xml += f'<widget class="QWidget" name="{tab["tabName"]}">'
        form_xml += '<attribute name="title">'
        form_xml += f'<string>{tab["tabLabel"]}</string>'
        form_xml += '</attribute>'

        form_xml += get_tab_xml(tab["tabName"], all_fields, fields_per_layout, layouts_per_tab, editable)

        form_xml += '</widget>'

    form_xml += '</widget>'
    form_xml += '</item>'
    # form_xml += '<item>'
    # form_xml += '<spacer>'
    # form_xml += '<property name="orientation">'
    # form_xml += '<enum>Qt::Vertical</enum>'
    # form_xml += '</property>'
    # form_xml += '</spacer>'
    # form_xml += '</item>'

    form_xml += (
        '<item row="1" column="0">'
         '<layout class="QHBoxLayout" name="lyt_buttons">'
#          '<property name="fit_vertical">'
#   '<bool>true</bool>'
#  '</property>'
          '<item>'
           '<widget class="QPushButton" name="btn_accept">'
            '<property name="text">'
             '<string>Accept</string>'
            '</property>'
            '<property name="widgetfunction">'
             '<string>'
              '{"functionName": "accept"}'
             '</string>'
            '</property>'
           '</widget>'
          '</item>'
          '<item>'
           '<widget class="QPushButton" name="btn_apply">'
            '<property name="text">'
             '<string>Apply</string>'
            '</property>'
            '<property name="widgetfunction">'
             '<string>'
              '{"functionName": "apply"}'
             '</string>'
            '</property>'
           '</widget>'
          '</item>'
          '<item>'
           '<widget class="QPushButton" name="btn_cancel">'
            '<property name="text">'
             '<string>Cancel</string>'
            '</property>'
            '<property name="widgetfunction">'
             '<string>'
              '{"functionName": "cancel"}'
             '</string>'
            '</property>'
           '</widget>'
          '</item>'
         '</layout>'
        '</item>'
    )

    # if 'lyt_buttons' in fields_per_layout:
    #     # Buttons
    #     form_xml += '<item>'
    #     form_xml += get_fields_xml_horizontal(fields_per_layout['lyt_buttons'], 'lyt_buttons')
    #     form_xml += '</item>'
    
    form_xml += '</layout>'

    return form_xml


def get_tab_xml(tab_name: str, fields: list, fields_per_layout: dict, layouts_per_tab: dict, editable: bool) -> str:
    layouts = layouts_per_tab.get(tab_name, [])
    print(f"{layouts_per_tab = }")
    layout_name = f"lyt_{tab_name}"
    if tab_name == "tab_data":          return get_combined_layout_xml(layout_name, fields_per_layout, layouts, editable)
    if tab_name == "tab_connections":   return get_connections_tab_xml(layout_name, fields_per_layout, layouts)
    if tab_name == "tab_plan":          return get_form_xml(layout_name, "form_plan")
    if tab_name == "tab_epa":           return get_epa_tab_xml(layout_name, fields_per_layout)
    # else:                               return get_combined_layout_xml(layout_name, fields_per_layout, layouts)
    else:                               return get_generic_tab_xml(layout_name, fields_per_layout, layouts)


def get_form_xml(layout_name: str, widget_name: str) -> str:
    return (
        f'<layout class="QVBoxLayout" name="{layout_name}">'
         f'<item>'
          f'<widget class="GwQtDesignerForm" name="{widget_name}"/>'
         f'</item>'
        f'</layout>'
    )

def get_epa_tab_xml(layout_name: str, fields_per_layout: dict) -> str:
    return (
        f'<layout class="QGridLayout" name="{layout_name}">'
         f'<item row="0" column="0">'
          f'{get_fields_xml_vertical(fields_per_layout.get("lyt_epa_1", []), "lyt_epa_1")}'
         f'</item>'
         f'<item row="1" column="0">'
          f'<widget class="GwQtDesignerForm" name="form_epa"/>'
         f'</item>'
        f'</layout>'
    )


def get_connections_tab_xml(layout_name: str, fields_per_layout: dict, layouts: list) -> str:
    # print(f"{fields_per_layout = }")
    # print(f"{layouts = }")
    xml = f'<layout class="QGridLayout" name="{layout_name}">'

    i = 0
    for layout in sorted(layouts):
        fields = filter_fields(fields_per_layout.get(layout, []))
        if len(fields) > 0:
            for field in fields:
                label_xml, field_xml = get_field_xml(field)

                xml += f'<item row="{i}" column="0">'
                xml += label_xml
                xml += '</item>'
                i += 1

                xml += f'<item row="{i}" column="0">'
                xml += field_xml
                xml += '</item>'
                i += 1

    # xml += (
    #     '<item>'
    #         '<spacer>'
    #             '<property name="orientation">'
    #                 '<enum>Qt::Vertical</enum>'
    #             '</property>'
    #         '</spacer>'
    #     '</item>'
    # )

    xml += '</layout>'
    print(xml)
    return xml


def get_combined_layout_xml(layout_name: str, fields_per_layout: dict, layouts: list, editable: bool = True) -> str:
    fields = []
    for layout in sorted(layouts):
        fields.extend(fields_per_layout.get(layout, []))
    if not editable:
        for field in fields:
            field["iseditable"] = False
    return get_fields_xml_vertical(fields, layout_name, final_spacer=False)


def get_generic_tab_xml(layout_name: str, fields_per_layout: dict, layouts: list) -> str:
    xml = f'<layout class="QGridLayout" name="{layout_name}">'
    i = 0
    for layout in sorted(layouts):
        fields = filter_fields(fields_per_layout.get(layout, []))
        if len(fields) > 0:
            xml += (
                f'<item row="{i}" column="0">'
                 f'{get_fields_xml_vertical(fields, layout, sort=False)}'
                f'</item>'
            )
            i += 1

    xml += '</layout>'
    return xml


def create_epa_xml_form(db_result: dict) -> str:
    fields = db_result["body"]["data"]["fields"]
    fields = filter(lambda field: field["tabname"] == "tab_epa", fields)
    fields_per_layout = get_fields_per_layout(fields)

    inp_xml = get_fields_xml_vertical(
        fields_per_layout.get("lyt_epa_data_1", []),
        "lyt_epa_data_1",
        sort_key="layoutorder",
    )

    rpt_xml = get_fields_xml_vertical(
        fields_per_layout.get("lyt_epa_data_2", []),
        "lyt_epa_data_2",
        sort_key="layoutorder",
    )

    form_xml = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<ui version="4.0">'
        f'<widget class="QWidget" name="epa_main_form">'
         f'<layout class="QVBoxLayout" name="lyt_epa_1">'
          f'<item>'
           f'<widget class="QGroupBox" name="grb_epa_inp">'
            f'<property name="title">'
             f'<string>INP</string>'
            f'</property>'
            f'{inp_xml}'
           f'</widget>'
          f'</item>'
          f'<item>'
           f'<widget class="QGroupBox" name="grb_epa_rpt">'
            f'<property name="title">'
             f'<string>RPT</string>'
            f'</property>'
            f'{rpt_xml}'
           f'</widget>'
          f'</item>'
          f'<item>'
           f'<spacer>'
            f'<property name="orientation">'
             f'<enum>Qt::Vertical</enum>'
            f'</property>'
           f'</spacer>'
          f'</item>'
         f'</layout>'
        f'</widget>'
        f'</ui>'
    )

    return form_xml


def create_plan_xml_form(db_result: dict) -> str:
    fields = db_result["body"]["data"]["fields"]
    fields = filter_fields(fields, "layoutorder")

    form_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    form_xml += '<ui version="4.0">'
    form_xml += '<widget class="QWidget" name="plan_form">'

    def callback(field: dict):
        if field["widgettype"] == "label":
            field["widgetprops"] = (
                '<property name="alignment">'
                 '<set>Qt::AlignRight</set>'
                '</property>')

    form_xml += get_fields_xml_vertical(
        fields,
        "lyt_plan_1",
        sort_key="layoutorder",
        field_callback=callback,
        final_spacer=True
    )

    form_xml += '</widget>'
    form_xml += '</ui>'

    return form_xml
