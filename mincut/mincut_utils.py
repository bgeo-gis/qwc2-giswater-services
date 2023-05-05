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


def manage_response(result, log, theme, manager=False):
    # form xml
    try:
        if manager:
            form_xml = mincutmanager_create_xml_form(result)
        else:
            form_xml = mincut_create_xml_form(result)
    except:
        form_xml = None

    utils.remove_handlers(log)

    return utils.create_response(result, form_xml=form_xml, do_jsonify=True, theme=theme)


def mincut_create_xml_form(result: dict) -> str:
    layout_xmls = get_layout_xmls(result)
    tab_names = {'tab_plan': 'Plan', 'tab_exec': 'Exec', 'tab_hydro': 'Hydro', 'tab_log': 'Log'}

    form_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    form_xml += '<ui version="4.0">'
    form_xml += '<widget class="QWidget" name="dlg_mincut">'
    form_xml += '<layout class="QVBoxLayout" name="MainLayout">'

    # Toolbar
    form_xml += '<item>'
    form_xml += layout_xmls.get('lyt_toolbar', '')
    form_xml += '</item>'

    # Layout top (id, state & work order)
    form_xml += '<item>'
    form_xml += layout_xmls.get('lyt_top_1', '')
    form_xml += '</item>'

    # Tabs
    form_xml += '<item>'
    form_xml += '<widget class="QTabWidget" name="tabWidget">'
    form_xml += '<property name="currentIndex">'
    form_xml += '<number>0</number>'
    form_xml += '</property>'
    for tabname in ['tab_plan', 'tab_exec', 'tab_hydro', 'tab_log']:
        form_xml += f'<widget class="QWidget" name="{tabname}">'
        form_xml += '<attribute name="title">'
        form_xml += f'<string>{tab_names.get(tabname)}</string>'
        form_xml += '</attribute>'
        form_xml += f'<layout class="QVBoxLayout" name="lyt_{tabname}">'

        if tabname == 'tab_plan':
            form_xml += '<item>'
            form_xml += layout_xmls.get('lyt_plan_1', '')
            form_xml += '</item>'
            form_xml += '<item>'
            form_xml += f'<widget class="QGroupBox" name="grb_plan_details">'
            form_xml += f'<property name="title">'
            form_xml += f'<string>Detalles</string>'
            form_xml += '</property>'
            form_xml += layout_xmls.get('lyt_plan_details', '')
            form_xml += f'</widget>'
            form_xml += '</item>'
            form_xml += '<item>'
            form_xml += f'<widget class="QGroupBox" name="grb_plan_fdates">'
            form_xml += f'<property name="title">'
            form_xml += f'<string>Fechas previstas</string>'
            form_xml += '</property>'
            form_xml += layout_xmls.get('lyt_plan_fdates', '')
            form_xml += f'</widget>'
            form_xml += '</item>'
        elif tabname == 'tab_exec':
            form_xml += '<item>'
            form_xml += f'<widget class="QGroupBox" name="grb_exec">'
            form_xml += f'<property name="title">'
            form_xml += f'<string>Fechas reales</string>'
            form_xml += '</property>'
            form_xml += layout_xmls.get('lyt_exec_1', '')
            form_xml += f'</widget>'
            form_xml += '</item>'
        elif tabname == 'tab_hydro':
            form_xml += '<item>'
            form_xml += layout_xmls.get('lyt_hydro_1', '')
            form_xml += '</item>'
        elif tabname == 'tab_log':
            form_xml += '<item>'
            form_xml += layout_xmls.get('lyt_log_1', '')
            form_xml += '</item>'
        
        form_xml += f'</layout>'

        form_xml += '</widget>'

    form_xml += '</widget>'
    form_xml += '</item>'

    # Layout bot (btn_accept, btn_cancel)
    form_xml += '<item>'
    form_xml += layout_xmls.get('lyt_bot_1', '')
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
        if layout in ('lyt_top_1', 'lyt_bot_1', 'lyt_toolbar'):
            layout_class = "QHBoxLayout"
        layout_xml = f'<layout class="{layout_class}" name="{layout}">'
        for field in fields:
            layout_xml += create_widget_xml(field)
        layout_xml += '</layout>'
        layout_xmls[layout] = layout_xml

    return layout_xmls


def mincutmanager_create_xml_form(result: dict) -> str:
    layout_xmls = mincutmanager_get_layout_xmls(result)

    form_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    form_xml += '<ui version="4.0">'
    form_xml += '<widget class="QWidget" name="dlg_mincutmanager">'
    form_xml += '<layout class="QVBoxLayout" name="MainLayout">'

    # Layout top (id, state & work order)
    form_xml += '<item>'
    form_xml += layout_xmls.get('lyt_mincut_mng_1', '')
    form_xml += '</item>'

    # Layout mid
    form_xml += '<item>'
    form_xml += layout_xmls.get('lyt_mincut_mng_2', '')
    form_xml += '</item>'

    # Layout bot (btn_accept, btn_cancel)
    form_xml += '<item>'
    form_xml += layout_xmls.get('lyt_mincut_mng_3', '')
    form_xml += '</item>'

    form_xml += '</layout>'
    form_xml += '</widget>'
    form_xml += '</ui>'

    return form_xml

def mincutmanager_get_layout_xmls(result: dict) -> dict:
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
        if layout in ('lyt_mincut_mng_1', 'lyt_mincut_mng_2', 'lyt_mincut_mng_3'):
            layout_class = "QHBoxLayout"
        layout_xml = f'<layout class="{layout_class}" name="{layout}">'
        for field in fields:
            layout_xml += create_widget_xml(field)
        layout_xml += '</layout>'
        layout_xmls[layout] = layout_xml

    return layout_xmls
