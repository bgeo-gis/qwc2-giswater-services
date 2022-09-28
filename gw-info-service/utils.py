
def get_demo_form() -> str:
    return open("./templates/test.ui").read()

def create_xml_form(db_result: dict) -> str:
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
        form_xml += f'<layout class="QFormLayout" name="lay_{tab["tabName"]}">\n'

        for i, field in enumerate(db_result["body"]["data"]["fields"]):
            if field["layoutname"] == "lyt_data_1":
                row = field["orderby"]
                value = ""
                if "value" in field:
                    value = field["value"]

                widget_type = field['widgettype']
                widget_name = field["column_id"]

                form_xml += f'<item row="{row}" column="0">'
                form_xml += '<widget class="QLabel" name="label">'
                form_xml += '<property name="text">'
                form_xml += f'<string>{field["label"]}</string>'
                form_xml += '</property>'
                form_xml += '</widget>'
                form_xml += '</item>'
                form_xml += f'<item row="{row}" column="1">'
                
                if widget_type == "check":
                    form_xml += f'<widget class="QCheckBox" name="{widget_name}">'
                    form_xml += f'<property name="checked">'
                    form_xml += f'<boolean>{value}</boolean>'
                    form_xml += f'</property>'
                elif widget_type == "datetime":
                    form_xml += f'<widget class="QDateTimeEdit" name="{widget_name}">'
                    form_xml += f'<property name="value">'
                    form_xml += f'<string>{value}</string>'
                    form_xml += f'</property>'
                elif widget_type == "combo":
                    form_xml += f'<widget class="QComboBox" name="{widget_name}">'
                    options = dict(zip(field["comboIds"], field["comboNames"]))
                    value = options[field["selectedId"]]

                    for val in options.values():
                        form_xml += '<item>'
                        form_xml += '<property name="text">'
                        form_xml += f'<string>{val}</string>'
                        form_xml += '</property>'
                        form_xml += '</item>'
                    form_xml += f'<property name="value">'
                    form_xml += f'<string>{value}</string>'
                    form_xml += f'</property>'
                elif widget_type == "button":
                    form_xml += f'<widget class="QPushButton" name="{widget_name}">'
                    form_xml += f'<property name="text">'
                    form_xml += f'<string>{value}</string>'
                    form_xml += f'</property>'
                    if (field["widgetfunction"]["functionName"] == "get_info_node"):
                        form_xml += f'<property name="action">'
                        form_xml += f'<string>{{"name": "featureLink", "params": {{"id": "{value}", "tableName": "v_edit_node"}}}}</string>'
                        form_xml += f'</property>'
                else:
                    form_xml += f'<widget class="QLineEdit" name="{widget_name}">'
                    form_xml += f'<property name="text">'
                    form_xml += f'<string>{value}</string>'
                    form_xml += '</property>'

                form_xml += f'<property name="readOnly">'
                form_xml += f'<bool>false</bool>'
                form_xml += '</property>'
                form_xml += '</widget>'
                form_xml += '</item>\n'

        form_xml += '</layout>'
        form_xml += '</widget>\n'

    form_xml += '</widget>'
    form_xml += '</item>'  
    form_xml += '</layout>'
    form_xml += '</widget>'
    form_xml += '</ui>'

    return form_xml

def create_xml_form_v2(db_result: dict) -> str:
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
            form_xml += data_tab_xml(db_result["body"]["data"]["fields"])

        form_xml += '</widget>\n'

    form_xml += '</widget>'
    form_xml += '</item>'  
    form_xml += '</layout>'
    form_xml += '</widget>'
    form_xml += '</ui>'

    return form_xml

def data_tab_xml(fields):

    lyt_data_1 = ""
    lyt_data_2 = ""

    for field in fields:
        if field["layoutname"] == "lyt_data_1" or field["layoutname"] == "lyt_data_2":
            row = field["layoutorder"]
            value = ""
            if "value" in field:
                value = field["value"]

            widget_type = field['widgettype']
            widget_name = field["column_id"]


            xml = ''
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

            if field["layoutname"] == "lyt_data_1":
                lyt_data_1 += xml
            elif field["layoutname"] == "lyt_data_2":
                lyt_data_2 += xml

    form_xml = ""
    form_xml += '<layout class="QHBoxLayout" name="lyt_data">'
    form_xml += '  <item>'
    form_xml += '    <layout class="QGridLayout" name="lyt_data_1">'
    form_xml += lyt_data_1
    form_xml += '    </layout>'
    form_xml += '  </item>'
    form_xml += '  <item>'
    form_xml += '    <layout class="QGridLayout" name="lyt_data_2">'
    form_xml += lyt_data_2
    form_xml += '    </layout>'
    form_xml += '  </item>'
    form_xml += '</layout>'

    return form_xml