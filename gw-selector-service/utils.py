import os

from PyQt5 import uic, QtDesigner
from PyQt5.QtCore import Qt, QFile, QIODevice, QCoreApplication
from PyQt5.QtWidgets import QApplication, QDialog, QWidget, QGridLayout, QLabel, QLineEdit, QSizePolicy, QCheckBox, QTabWidget, QSpacerItem
from PyQt5.QtDesigner import QFormBuilder, QDesignerFormWindowInterface, QDesignerPropertySheetExtension


def add_checkbox(field):

    widget = QCheckBox()
    widget.setObjectName(field['widgetname'])
    widget.setProperty('columnname', field['columnname'])
    if field.get('value') in ("t", "true", True):
        widget.setChecked(True)
    if 'iseditable' in field:
        widget.setEnabled(field['iseditable'])
    return widget

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


def create_form_builder(db_result: dict) -> str:
    form_xml = create_xml_form_v3(db_result)
    return form_xml

def create_xml_form_v3(db_result: dict) -> str:
    form_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    form_xml += '<ui version="4.0">'
    form_xml += '<widget class="QWidget" name="Form">'
    form_xml += '<layout class="QHBoxLayout" name="MainLayout">'
    form_xml += '<item>'
    form_xml += '<widget class="QTabWidget" name="tabWidget">'
    form_xml += '<property name="currentIndex">'
    form_xml += '<number>0</number>'
    form_xml += '</property>\n'

    for tab in db_result['body']['form']['formTabs']:

        form_xml += f'<widget class="QWidget" name="{tab["tabName"]}">'
        form_xml += '<attribute name="title">'
        form_xml += f'<string>{tab["tabLabel"]}</string>'
        form_xml += '</attribute>'

        tab_xml = sel_tab_xml(tab["fields"], tab["tabName"], tab["manageAll"])

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


def sel_tab_xml(fields, tab_name, manage_all):

    xml = ''
    chk_all_xml = ''
    tab_xml = ''
    chk_all = False
    all_checked = True

    for idx, field in enumerate(fields):
        row = field["orderby"]
        if chk_all:
            row += 1
        value = ""
        if "value" in field:
            value = field["value"]
            if value is False:
                all_checked = False
        
        widget_type = field["type"]
        widget_name = field["widgetname"]

        tab_xml += f'<item row="{row}" column="0">'
        tab_xml += '<widget class="QLabel" name="label">'
        tab_xml += '<property name="text">'
        tab_xml += f'<string>{field["label"]}</string>'
        tab_xml += '</property>'
        tab_xml += '</widget>'
        tab_xml += '</item>'
        tab_xml += f'<item row="{row}" column="1">'
        
        if widget_type == "check":
            tab_xml += f'<widget class="QCheckBox" name="{widget_name}">'
            tab_xml += f'<property name="checked">'
            tab_xml += f'<boolean>{value}</boolean>'
            tab_xml += f'</property>'
            # Action setselectors
            tab_xml += f'<property name="action">'
            tab_xml += f'<string>{{"name": "setSelectors", "params": {{"tabName": "{tab_name}", "id": "{widget_name}", "value": "{value}"}}}}</string>'
            tab_xml += f'</property>'
        elif widget_type == "datetime":
            tab_xml += f'<widget class="QDateTimeEdit" name="{widget_name}">'
            tab_xml += f'<property name="value">'
            tab_xml += f'<string>{value}</string>'
            tab_xml += f'</property>'
        elif widget_type == "combo":
            tab_xml += f'<widget class="QComboBox" name="{widget_name}">'
            options = dict(zip(field["comboIds"], field["comboNames"]))
            value = options[field["selectedId"]]

            for val in options.values():
                tab_xml += '<item>'
                tab_xml += '<property name="text">'
                tab_xml += f'<string>{val}</string>'
                tab_xml += '</property>'
                tab_xml += '</item>'
            tab_xml += f'<property name="value">'
            tab_xml += f'<string>{value}</string>'
            tab_xml += f'</property>'
        elif widget_type == "button":
            tab_xml += f'<widget class="QPushButton" name="{widget_name}">'
            tab_xml += f'<property name="text">'
            tab_xml += f'<string>{value}</string>'
            tab_xml += f'</property>'
            if (field["widgetfunction"]["functionName"] == "get_info_node"):
                tab_xml += f'<property name="action">'
                tab_xml += f'<string>{{"name": "featureLink", "params": {{"id": "{value}", "tableName": "v_edit_node"}}}}</string>'
                tab_xml += f'</property>'
        else:
            tab_xml += f'<widget class="QLineEdit" name="{widget_name}">'
            tab_xml += f'<property name="text">'
            tab_xml += f'<string>{value}</string>'
            tab_xml += '</property>'

        tab_xml += f'<property name="readOnly">'
        tab_xml += f'<bool>false</bool>'
        tab_xml += '</property>'
        tab_xml += '</widget>'
        tab_xml += '</item>\n'

    # Add check_all if necessary
    if manage_all.lower() == "true":
        chk_all = True
        chk_all_xml += f'<item row="0" column="0">'
        chk_all_xml += '<widget class="QLabel" name="label">'
        chk_all_xml += '<property name="text">'
        chk_all_xml += f'<string>Check all</string>'
        chk_all_xml += '</property>'
        chk_all_xml += '</widget>'
        chk_all_xml += '</item>'
        chk_all_xml += f'<item row="0" column="1">'

        chk_all_xml += f'<widget class="QCheckBox" name="chk_all_{tab_name}">'
        chk_all_xml += f'<property name="checked">'
        chk_all_xml += f'<boolean>{all_checked}</boolean>'
        chk_all_xml += f'</property>'
        # Action setselectors
        chk_all_xml += f'<property name="action">'
        chk_all_xml += f'<string>{{"name": "setSelectors", "params": {{"tabName": "{tab_name}", "id": "chk_all", "value": "{all_checked}"}}}}</string>'
        chk_all_xml += f'</property>'

        chk_all_xml += f'<property name="readOnly">'
        chk_all_xml += f'<bool>false</bool>'
        chk_all_xml += '</property>'
        chk_all_xml += '</widget>'
        chk_all_xml += '</item>\n'

    xml = chk_all_xml + tab_xml
    return xml

# ============================================
# ------------- NOT WORKING CODE -------------
# We tried to use PyQt to create the form,
# but there is no known way of showing a
# form created by python in QWC2
# ============================================


def _get_ui_class(ui_file_name):
    """ Get UI Python class from @ui_file_name """

    # Folder that contains UI files
    ui_folder_path = f"{os.path.dirname(__file__)}{os.sep}templates"

    ui_file_path = os.path.abspath(os.path.join(ui_folder_path, ui_file_name))
    return uic.loadUiType(ui_file_path)[0]

FROM_CLASS = _get_ui_class('selector.ui')
class GwSelectorUi(QDialog, FROM_CLASS):
    pass

class GwSelectorForm(QDialog):
    def __init__(self):
        # self.app = QApplication([])
        super().__init__()
        # self.setupUi(self)

        self.ignore_properties = ["acceptDrops", "windowModified", "mouseTracking", "autoFillBackground", "sizeGripEnabled",
            "palette", "windowOpacity", "accessibleDescription", "locale", "layoutDirection", "modal", "sizeIncrement",
            "baseSize", "tabletTracking", "inputMethodHints", "statusTip", "accessibleName", "windowModality", "windowFilePath",
            "contextMenuPolicy", "autoDefault", "autoExclusive", "down", "shortcut", "autoRepeatInterval", "flat",
            "horizontalScrollBarPolicy", "frameShape", "verticalScrollBarPolicy", "frameShadow", "midLineWidth", "lineWidth"]
        self.loadedForm = None
        self.ui_path = f"{os.path.dirname(__file__)}{os.sep}templates"
        self.builder = QFormBuilder()
        # self.builder.computeProperties = lambda o: self._computeProperties(o)
        self.buildForm()

    def buildForm(self):
        file = QFile(f"{self.ui_path}{os.sep}selector.ui")
        file.open(QIODevice.ReadOnly)
        self.loadedForm = self.builder.load(file, self)
        file.close()

    def saveForm(self):
        file = QFile(f"{self.ui_path}{os.sep}selector_filled.ui")
        file.open(QIODevice.ReadWrite)
        # self.builder.computeProperties(self.loadedForm)
        self.builder.save(file, self.loadedForm)
        file.close()

    def _computeProperties(self, object):
        print(f"TEST _computeProperties")
        properties = []

        # Get property sheet
        propertySheet = None
        # form = QDesignerFormWindowInterface()
        form = QDesignerFormWindowInterface.findFormWindow(object)
        editor = form.core()
        manager = editor.extensionManager()
        # manager = QDesignerFormEditorInterface.extensionManager()
        propertySheet = QtDesigner.qt_extension<QDesignerPropertySheetExtension>(manager, object)
        # dynamicSheet = QtDesigner.qt_extension<QDesignerDynamicPropertySheetExtension>(manager, object)

        sheet_count = propertySheet.count()

        for idx in range(0, sheet_count):
            propertyName = propertySheet.propertyName(idx)
            if propertyName in self.ignore_properties:
                continue
            value = propertySheet.propertyName(idx)
            p = self.builder.createProperty(object, propertyName, value)
            if p:
                properties.append(p)

        return properties


def create_xml_form_pyqt(db_result: dict, dialog: QDialog) -> str:

    # app = QApplication([])

    json_result = db_result
    if not json_result or json_result['status'] == 'Failed':
        return False

    # dialog = GwSelectorUi()
    main_tab = dialog.findChild(QTabWidget, 'main_tab')

    # Get styles
    stylesheet = json_result['body']['form'].get('style')
    color_rows = False
    if stylesheet:
        # Color selectors zebra-styled
        color_rows = set_boolean(stylesheet.get('rowsColor'), False)

    for form_tab in json_result['body']['form']['formTabs']:

        selection_mode = form_tab['selectionMode']

        # Create one tab for each form_tab and add to QTabWidget
        tab_widget = QWidget(main_tab)
        tab_widget.setObjectName(form_tab['tabName'])
        tab_widget.setProperty('selector_type', form_tab['selectorType'])

        main_tab.addTab(tab_widget, form_tab['tabLabel'])

        typeaheadForced = form_tab.get('typeaheadForced')
        if typeaheadForced is not None:
            tab_widget.setProperty('typeahead_forced', typeaheadForced)

        # Create a new QGridLayout and put it into tab
        gridlayout = QGridLayout()
        gridlayout.setObjectName("lyt" + form_tab['tabName'])
        tab_widget.setLayout(gridlayout)
        field = {}
        i = 0

        if 'typeaheadFilter' in form_tab:
            label = QLabel()
            label.setObjectName('lbl_filter')
            label.setText('Filter:')
            if dialog.findChild(QWidget, f"txt_filter_{form_tab['tabName']}") is None:
                widget = QLineEdit()
                widget.setObjectName('txt_filter_' + str(form_tab['tabName']))
                widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                # widget.textChanged.connect(partial(self.get_selector, dialog, selector_type, filter=True,
                #                                     widget=widget, current_tab=current_tab))
                widget.setLayoutDirection(Qt.RightToLeft)

            else:
                widget = dialog.findChild(QWidget, f"txt_filter_{form_tab['tabName']}")

            field['layoutname'] = gridlayout.objectName()
            field['layoutorder'] = i
            i = i + 1
            gridlayout.addWidget(label, int(field['layoutorder']), 0)
            gridlayout.addWidget(widget, int(field['layoutorder']), 2)
            widget.setFocus()

        if 'manageAll' in form_tab:
            if (form_tab['manageAll']).lower() == 'true':
                if dialog.findChild(QWidget, f"chk_all_{form_tab['tabName']}") is None:
                    widget = QCheckBox()
                    widget.setObjectName('chk_all_' + str(form_tab['tabName']))
                    # widget.stateChanged.connect(partial(self._manage_all, dialog, widget))
                    widget.setLayoutDirection(Qt.LeftToRight)
                else:
                    widget = dialog.findChild(QWidget, f"chk_all_{form_tab['tabName']}")
                widget.setText('Check all')
                # if hasattr(self, 'checkall'):
                #     widget.stateChanged.disconnect()
                #     widget.setChecked(self.checkall)
                #     widget.stateChanged.connect(partial(self._manage_all, dialog, widget))
                field['layoutname'] = gridlayout.objectName()
                field['layoutorder'] = i
                i = i + 1
                gridlayout.addWidget(widget, int(field['layoutorder']), 0, 1, -1)

        for order, field in enumerate(form_tab['fields']):
            try:
                # Create checkbox
                widget = add_checkbox(field)
                widget.setText(field['label'])
                # widget.stateChanged.connect(partial(self._set_selection_mode, dialog, widget, selection_mode))
                widget.setLayoutDirection(Qt.LeftToRight)

                # Set background color every other item (if enabled)
                if color_rows and order % 2 == 0:
                    widget.setStyleSheet(f"background-color: #E9E7E3")

                # Add widget to layout
                field['layoutname'] = gridlayout.objectName()
                field['layoutorder'] = order + i + 1
                gridlayout.addWidget(widget, int(field['layoutorder']), 0, 1, -1)
            except Exception:
                msg = f"key 'comboIds' or/and comboNames not found WHERE columname='{field['columnname']}' AND " \
                        f"widgetname='{field['widgetname']}'"
                print(msg)

        vertical_spacer1 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        gridlayout.addItem(vertical_spacer1)

    # Set last tab used by user as current tab
    tabname = json_result['body']['form']['currentTab']
    tab = main_tab.findChild(QWidget, tabname)

    if tab:
        main_tab.setCurrentWidget(tab)
