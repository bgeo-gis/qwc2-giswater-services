"""
Copyright BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils
from .selector_utils import create_xml_form_v3

import json
import traceback

from flask import Blueprint, request, jsonify
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc

selector_bp = Blueprint('selector', __name__)


@selector_bp.route('/get', methods=['GET'])
@optional_auth
def getselector():
    """Get selector

    Returns selector dialog.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")
    currentTab = args.get("currentTab")
    selectorType = args.get("selectorType")
    ids = args.get("ids")

    # db fct
    form = f'"currentTab": "{currentTab}"'
    extras = f'"selectorType": "{selectorType}", "filterText": ""'
    if ids:
        ids = ids.split(",")
        ids_list = [int(x) for x in ids]
        extras += f', "ids": {ids_list}'
    body = utils.create_body(project_epsg=epsg, form=form, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_getselectors', body)

    # form xml
    try:
        form_xml = create_xml_form_v3(result)
    except:
        form_xml = None

    return utils.create_response(result, form_xml=form_xml, do_jsonify=True)


@selector_bp.route('/set', methods=['POST'])
@optional_auth
def setselector():
    """Set selector

    Updates selectors based on user input (and returns updated dialog).
    """
    log = utils.create_log(__name__)
    
    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")
    selectorType = args.get("selectorType")
    tabName = args.get("tabName")
    value = args.get("value")
    widget_id = args.get("id")
    isAlone = args.get("isAlone")
    disableParent = args.get("disableParent")
    addSchema = args.get("addSchema")

    # db fct
    extras = f'"selectorType": "{selectorType}", "tabName": "{tabName}", "addSchema": "{addSchema}"'
    if widget_id == 'chk_all':
        extras += f', "checkAll": "{value}"'
    else:
        extras += f', "id": "{widget_id}", "isAlone": "{isAlone}", "disableParent": "{disableParent}", "value": "{value}"'

    body = utils.create_body(project_epsg=epsg, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_setselectors', body)

    # form xml
    try:
        form_xml = create_xml_form_v3(result)
    except:
        form_xml = None

    return utils.create_response(result, form_xml=form_xml, do_jsonify=True)
