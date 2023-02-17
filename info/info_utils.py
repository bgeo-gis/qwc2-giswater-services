import json
from flask import jsonify, Response

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
    form_xml += '<layout class="QHBoxLayout" name="MainLayout">'
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

        if (tab["tabName"] == "tab_data"):
            form_xml += tab_onelyt_xml(db_result["body"]["data"]["fields"], tab["tabName"])
        elif (tab["tabName"] in ("tab_visit", "tab_documents")):
            form_xml += tab_onelyt_xml(db_result["body"]["data"]["fields"], tab["tabName"])

        form_xml += '</widget>\n'

    form_xml += '</widget>'
    form_xml += '</item>'  
    form_xml += '</layout>'
    form_xml += '</widget>'
    form_xml += '</ui>'

    return form_xml


def tab_onelyt_xml(fields, tab_name):

    layouts = []
    if tab_name == 'tab_data':
        layouts = ['lyt_top_1', 'lyt_bot_1', 'lyt_bot_2', 'lyt_data_1', 'lyt_data_2']
    elif tab_name == 'tab_visit':
        layouts = ['lyt_visit_1', 'lyt_visit_2', 'lyt_visit_3']
    lyt_data_1 = ""

    for field in fields:
        if field.get('hidden') in (True, 'True', 'true'):
            continue
        tabname = field.get("tabname")
        if tabname in ('document', 'element', 'relation'):
            tabname += 's'
        if tabname != tab_name.lstrip('tab_'):
            continue
        row = field["web_layoutorder"]
        if row is None:
            continue
        value = ""
        if "value" in field:
            value = field["value"]

        widget_type = field['widgettype']
        widget_name = field["column_id"]
        widgetcontrols = field.get('widgetcontrols', {})
        widgetfunction = field.get('widgetfunction', {})
        # print(f"{field['layoutname']}")
        # print(f"          {widget_name} -> {row}")

        xml = ''
        read_only = "false"
        if tab_name == 'tab_data':
            read_only = "true"

        if widget_type == "tableview":
            xml += f'<item row="{row+1}" column="0" colspan="2">'
        else:
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
        elif widget_type == "tableview":
            # QTableWidget
            xml += f'<widget class="QTableView" name="{widget_name}">'
            xml += f'<property name="linkedobject">'
            xml += f'<string>{field.get("linkedobject", "")}</string>'
            xml += f'</property>'
            xml += f'<property name="action">'
            xml += f'<string>{{"name": "getlist", "params": {{"tabName": "visit", "widgetname": "{widget_name}", "tableName": "tbl_visit_x_node", "idName": "node_id", "id": "1000"}}}}</string>'
            xml += f'</property>'
            # xml += f'<property name="text">'
            # xml += f'<string>{value}</string>'
            # xml += f'</property>'
            # if (field["widgetfunction"]["functionName"] == "get_info_node"):
            #     xml += f'<property name="action">'
            #     xml += f'<string>{{"name": "featureLink", "params": {{"id": "{value}", "tableName": "v_edit_node"}}}}</string>'
            #     xml += f'</property>'
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

        lyt_data_1 += xml

    form_xml = ""
    form_xml += f'<layout class="QHBoxLayout" name="lyt_{tab_name.lstrip("tab_")}">'
    form_xml += '  <item>'
    form_xml += f'    <layout class="QGridLayout" name="lyt_{tab_name.lstrip("tab_")}_1">'
    form_xml += lyt_data_1
    form_xml += '    </layout>'
    form_xml += '  </item>'
    form_xml += '</layout>'

    return form_xml

