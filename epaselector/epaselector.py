"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils
import json
from .epaselector_utils import get_form_with_combos

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

epaselector_bp = Blueprint('epaselector', __name__)

@epaselector_bp.route('/dialog', methods=['PUT'])
@jwt_required()
def dialog():
    """
    Open Epa Results Selector
    Returns dialog of the epa results selector.
    """
    utils.get_config()
    log = utils.create_log(__name__)

    # Retrieve arguments
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    combos = args.get("combos")
    combo_childs = args.get("comboChilds")

    # Build form and body
    form = get_form_with_combos(combos) if combos else '"formName":"generic", "formType":"epa_selector"'
    feature = f'"childs":{json.dumps(combo_childs)}' if combo_childs else ''
    body = utils.create_body(theme, form=form, feature=feature)

    # Execute DB procedure
    result = utils.execute_procedure(log, theme, 'gw_fct_get_epa_selector', body, needs_write=True)

    # Create XML form only if combos are not provided
    form_xml = utils.create_xml_generic_form(result, "epa_selector", "lyt_epa_select") if not combos else None

    utils.remove_handlers(log)
    return utils.create_response(result, form_xml=form_xml, do_jsonify=True, theme=theme)


@epaselector_bp.route('/accept', methods=['PUT'])
@jwt_required()
def accept():
    """Button Accept clicked in Epa Results Selector
    """
    utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    combos = args.get("combos")

    # fill form with values
    form = get_form_with_combos(combos)

    # db fct
    body = utils.create_body(theme, form=form)
    result = utils.execute_procedure(log, theme, 'gw_fct_set_epa_selector', body, needs_write=True)

    utils.remove_handlers(log)
    return utils.create_response(result, do_jsonify=True, theme=theme)


@epaselector_bp.route('/getcomparethemeid', methods=['GET'])
@jwt_required()
def getcomparethemeid():
    """Returns theme id from Compare Project
    """
    log = utils.create_log(__name__)

    # args
    theme = request.args.get("theme")

    # compare project
    compare_theme = utils.get_config().get("themes").get(theme).get("epa_compare_project")

    # tenant
    tenant = utils.tenant_handler.tenant()

    result = { "themeId" : f"{tenant}/{compare_theme}"  }
    utils.remove_handlers(log)
    return utils.create_response(result, do_jsonify=True, theme=theme)