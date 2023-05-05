from flask import jsonify, Response
"""
 Copyright BGEO. All rights reserved.
 The program is free software: you can redistribute it and/or modify it under the terms of the GNU
 General Public License as published by the Free Software Foundation, either version 3 of the License,
 or (at your option) any later version
""" 
import logging
import json

from utils import create_widget_xml


def handle_process_db_result(result: dict, parent_vals: int) -> Response:
    response = {}
    if not result:
        logging.warning(" DB returned null")
        return jsonify({"message": "DB returned null"})
    if 'results' not in result or result['results'] > 0:
        form_xml = process_create_xml_form(result["body"]["data"], parent_vals)
        # try:
        # except:
        #     form_xml = None

        response = {
            "status": result['status'],
            "version": result['version'],
            "body": result['body'],
            "form_xml": form_xml
        }
    return jsonify(response)


def process_create_xml_form(function: dict, parent_vals: int) -> str:
    form_xml = f"""
<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <widget class="QWidget" name="dlg_toolbox_manager">
  <layout class="QGridLayout" name="MainLayout">
   <item row="0" column="0">
    <widget class="QTabWidget" name="mainTab">
     <property name="currentIndex">
      <number>0</number>
     </property>
     {get_config_tab_xml(function, parent_vals)}
     {get_log_tab_xml(function)}
    </widget>
   </item>
   <item row="1" column="0">
    {get_buttons_xml(function)}
   </item>
  </layout>
 </widget>
</ui>
    """
    return form_xml

def get_buttons_xml(function: dict) -> str:
    return f"""
<layout class="QHBoxLayout" name="buttons_lyt">
 <item>
  <widget class="QPushButton" name="btn_run">
   <property name="text">
    <string>Run</string>
   </property>
   <property name="widgetfunction">
    <string>
     {json.dumps({
        "functionName": "run"
     })}</string>
   </property>
  </widget>
 </item>
 <item>
  <widget class="QPushButton" name="btn_close">
   <property name="text">
    <string>Close</string>
   </property>
   <property name="widgetfunction">
    <string>
     {json.dumps({
        "functionName": "close"
     })}</string>
   </property>
  </widget>
 </item>
</layout>
    """

def get_log_tab_xml(function: dict):
    return f"""
<widget class="QWidget" name="tab_loginfo">
 <attribute name="title">
  <string>Info Log</string>
 </attribute>
 <layout class="QGridLayout" name="gridLayout_2">
  <item row="0" column="0">
   <widget class="QTextEdit" name="txt_infolog">
    <property name="readOnly">
     <bool>true</bool>
    </property>
    <property name="text">
     <string></string>
    </property>
   </widget>
  </item>
 </layout>
</widget>
    """

def get_config_tab_xml(function: dict, parent_vals: int) -> str:
    return f"""
<widget class="QWidget" name="tab_config">
 <attribute name="title">
  <string>Config</string>
 </attribute>
 <layout class="QGridLayout" name="gridLayout">
  <item row="0" column="1" rowspan="2">
   {get_tool_info_xml(function)}
  </item>
  <item row="0" column="0">
   {get_input_layer_xml(function, parent_vals)}
  </item>
  <item row="1" column="0">
   {get_tool_parameters_xml(function)}
  </item>
 </layout>
</widget>
    """

def get_tool_parameters_xml(function: dict) -> str:
    parameters_xml = ''

    parameters_list = function.get("fields", [])
    if parameters_list is None:
        parameters_list = []

    for i, field in enumerate(parameters_list):
        field["web_layoutorder"] = i
        field["columnname"] = field["widgetname"]
        parameters_xml += create_widget_xml(field)
        # parameters_xml += create_widget_xml(i, field["widgettype"], field["widgetname"], )

    return f"""
<widget class="QGroupBox" name="grb_parameters">
 <property name="title">
  <string>Option parameters:</string>
 </property>
 <layout class="QGridLayout" name="gridLayout_3">
  <item row="0" column="0">
   <layout class="QGridLayout" name="grl_option_parameters" rowstretch="0" columnstretch="0">
    {parameters_xml}
   </layout>
  </item>
  <item row="1" column="0">
   <spacer name="verticalSpacer">
    <property name="orientation">
     <enum>Qt::Vertical</enum>
    </property>
   </spacer>
  </item>
 </layout>
</widget>"""

def get_tool_info_xml(function: dict) -> str:
    return f"""
<widget class="QGroupBox" name="groupBox">
 <property name="title">
  <string>Info:</string>
 </property>
 <layout class="QVBoxLayout" name="verticalLayout">
  <item>
   <widget class="QTextEdit" name="txt_info">
    <property name="enabled">
     <bool>false</bool>
    </property>
    <property name="text">
     <string>{function["descript"]}</string>
    </property>
   </widget>
  </item>
 </layout>
</widget>
    """

def get_input_layer_xml(function: dict, parent_vals: int) -> str:
    print(function)
    if not function["functionparams"]["featureType"]:
        return ''

    print(parent_vals)
    features_type = function["functionparams"]["featureType"]
    print(features_type)
    # Get the value stored in parent_vals, otherwise take the first in features_type
    feature_text = parent_vals.get("cmb_feature_type", {"value": next(iter(features_type.keys()))})["value"]

    # feature_str = list(features_type.items())[selected_index][0]
    print("feature_text", feature_text)


    feature_type_select_xml = ''
    if len(features_type) > 1:
        properties_xml = ''
        for i, name in enumerate(features_type.keys()):
            properties_xml += f"""
             <item>
              <property name="value">
               <string>{name}</string>
              </property>
              <property name="text">
               <string>{name}</string>
              </property>
             </item>
            """
        feature_type_select_xml = f"""
         <widget class="QComboBox" name="cmb_feature_type">
          <property name="value">
           <string>{feature_text}</string>
          </property>
          {properties_xml}
          <property name="isParent">
           <bool>true</bool>
          </property>
          <property name="textIsValue">
           <bool>true</bool>
          </property>
         </widget>
        """

    # print(feature_type_select_xml)
    layer_select_props = ""
    for i, name in enumerate(features_type[feature_text]):
            layer_select_props += f"""
            <item>
             <property name="value">
              <string>{name}</string>
             </property>
             <property name="text">
              <string>{name}</string>
             </property>
            </item>
            """

    layer_select_xml = f"""
    <widget class="QComboBox" name="cmb_layers">
     <property name="value">
      <string>{features_type[feature_text][0]}</string>
     </property>
     {layer_select_props}
     <property name="parentId">
      <string>cmb_feature_type</string>
     </property>
    </widget>
    """
    # print(layer_select_xml)

    return f"""
<widget class="QGroupBox" name="grb_input_layer">
 <property name="title">
  <string>Input layer:</string>
 </property>
 <property name="fit_vertical">
  <bool>true</bool>
 </property>
 <layout class="QGridLayout" name="gridLayout_4">
  <item row="0" column="0">
   {feature_type_select_xml}
  </item>
  <item row="1" column="0">
   {layer_select_xml}
  </item>
 </layout>
</widget>
    """
