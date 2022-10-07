import os

from PyQt5 import uic, QtDesigner
from PyQt5.QtCore import Qt, QFile, QIODevice, QCoreApplication
from PyQt5.QtWidgets import QApplication, QDialog, QWidget, QGridLayout, QLabel, QLineEdit, QSizePolicy, QCheckBox, QTabWidget, QSpacerItem
from PyQt5.QtDesigner import QFormBuilder, QDesignerFormWindowInterface, QDesignerPropertySheetExtension


def set_boolean(param, default=True):
    """
    Receives a string and returns a bool
        :param param: String to cast (String)
        :param default: Value to return if the parameter is not one of the keys of the dictionary of values (Boolean)
        :return: default if param not in bool_dict (bool)
    """

    bool_dict = {True: True, "TRUE": True, "True": True, "true": True,
                 False: False, "FALSE": False, "False": False, "false": False}

    return bool_dict.get(param, default)

def create_xml_form_v3(db_result: dict) -> str:
    form_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    form_xml += '<ui version="4.0">'
    form_xml += '<widget class="QWidget" name="Form">'
    form_xml += '<layout class="QHBoxLayout" name="MainLayout">'
    form_xml += '<item>'
    form_xml += '<widget class="QTabWidget" name="tabWidget">'
    form_xml += '<property name="activeTab">'
    form_xml += '<string>currentTab</string>'
    form_xml += '</property>'
    form_xml += '<property name="currentIndex">'
    form_xml += '<number>0</number>'
    form_xml += '</property>\n'

    for tab in db_result['body']['form']['formTabs']:

        form_xml += f'<widget class="QWidget" name="{tab["tabName"]}">'
        form_xml += '<attribute name="title">'
        form_xml += f'<string>{tab["tabLabel"]}</string>'
        form_xml += '</attribute>'

        tab_xml = sel_tab_xml(tab["fields"], tab["tabName"])

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


def sel_tab_xml(fields, tab_name):

    xml = ''
    for idx, field in enumerate(fields):
        row = field["orderby"]
        value = ""
        if "value" in field:
            value = field["value"]
        
        widget_type = field["type"]
        widget_name = field["widgetname"]

        xml += f'<item row="{row}" column="0">'
        xml += '<widget class="QLabel" name="label">'
        xml += '<property name="text">'
        xml += f'<string>{field["label"]}</string>'
        xml += '</property>'
        xml += '</widget>'
        xml += '</item>'
        xml += f'<item row="{row}" column="1">'
        
        if widget_type == "check":
            xml += f'<widget class="QCheckBox" name="{widget_name}">'
            xml += f'<property name="checked">'
            xml += f'<boolean>{value}</boolean>'
            xml += f'</property>'
            # Action setselectors
            xml += f'<property name="action">'
            xml += f'<string>{{"name": "setSelectors", "params": {{"tabName": "{tab_name}", "id": "{widget_name}", "value": "{value}"}}}}</string>'
            xml += f'</property>'
        elif widget_type == "datetime":
            xml += f'<widget class="QDateTimeEdit" name="{widget_name}">'
            xml += f'<property name="value">'
            xml += f'<string>{value}</string>'
            xml += f'</property>'
        elif widget_type == "combo":
            xml += f'<widget class="QComboBox" name="{widget_name}">'
            options = dict(zip(field["comboIds"], field["comboNames"]))
            value = options[field["selectedId"]]

            for val in options.values():
                xml += '<item>'
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
            if (field["widgetfunction"]["functionName"] == "get_info_node"):
                xml += f'<property name="action">'
                xml += f'<string>{{"name": "featureLink", "params": {{"id": "{value}", "tableName": "v_edit_node"}}}}</string>'
                xml += f'</property>'
        else:
            xml += f'<widget class="QLineEdit" name="{widget_name}">'
            xml += f'<property name="text">'
            xml += f'<string>{value}</string>'
            xml += '</property>'

        xml += f'<property name="readOnly">'
        xml += f'<bool>false</bool>'
        xml += '</property>'
        xml += '</widget>'
        xml += '</item>\n'

    return xml
