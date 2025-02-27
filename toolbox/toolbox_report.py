"""
Copyright © 2025 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""

from flask import jsonify, Response
import logging
import json

from utils import get_fields_xml_vertical


def handle_report_db_result(result: dict, parent_vals: dict) -> Response:
    response = {}
    if not result:
        logging.warning(" DB returned null")
        return jsonify({"message": "DB returned null"})
    if 'results' not in result or result['results'] > 0:
        form_xml = create_xml_form(result["body"]["data"], parent_vals)
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

def create_xml_form(function: dict, parent_vals: dict) -> str:
    values = next(field for field in function.get("fields") if field["widgettype"] == "list")["value"]
    form = None
    if values is not None:
        form = {
            "headers": [{"accessorKey": k, "header": k} for k in values[0].keys()],
            "table": {
                "initialState": {
                    "density": "compact"
                }
            }
        }
    form_xml = f"""
<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <widget class="QWidget" name="dlg_toolbox_manager">
  <layout class="QGridLayout" name="MainLayout">
   <item row="0" column="0">
    <widget class="QTableWidget">
     <property name="values">
      <string>
       {json.dumps(values)}
      </string>
     </property>
     <property name="form">
      <string>
       {json.dumps(form)}
      </string>
     </property>
    </widget>
   </item>
  </layout>
 </widget>
</ui>
    """
    return form_xml
