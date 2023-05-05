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
import utils
from utils import create_widget_xml

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

def visitmanager_create_xml_form(result: dict) -> str:
    layout_xmls = visitmanager_get_layout_xmls(result)

    form_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    form_xml += '<ui version="4.0">'
    form_xml += '<widget class="QWidget" name="dlg_visitmanager">'
    form_xml += '<layout class="QVBoxLayout" name="MainLayout">'

    # Layout 
    form_xml += '<item>'
    form_xml += layout_xmls.get('lyt_visit_mng_1', '')
    form_xml += '</item>'

    form_xml += '</layout>'
    form_xml += '</widget>'
    form_xml += '</ui>'

    return form_xml

def visitmanager_get_layout_xmls(result: dict) -> dict:
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
        if layout in ('lyt_visit_mng_1'):
            layout_class = "QHBoxLayout"
        layout_xml = f'<layout class="{layout_class}" name="{layout}">'
        for field in fields:
            layout_xml += create_widget_xml(field)
        layout_xml += '</layout>'
        layout_xmls[layout] = layout_xml

    return layout_xmls


