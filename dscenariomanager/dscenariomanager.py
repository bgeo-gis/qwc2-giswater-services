"""
Copyright © 2025 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import json
import utils
from .dscenariomanager_utils import manage_response

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

dscenariomanager_bp = Blueprint('dscenariomanager', __name__)

@dscenariomanager_bp.route('/dialog', methods=['GET'])
@jwt_required()
def dialog():
    """Open Epa Results Management

    Returns dialog of the epa results management.
    """
    # open dialog
    utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")

    # db fct
    form = '"formName":"generic", "formType":"dscenario_manager"'
    body = utils.create_body(theme, form=form)

    result = utils.execute_procedure(log, theme, 'gw_fct_get_dialog', body, needs_write=True)
    utils.remove_handlers(log)
    return manage_response(result, log, theme, "dscenario_manager", "lyt_dscenario_mngr")


@dscenariomanager_bp.route('/delete', methods=['DELETE'])
@jwt_required()
def deletedscenario():
    """Delete epa"""
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args

    theme = args.get("theme")
    dscenarioId = args.get("dscenarioId")

    # db fct
    feature= f'"featureType": "dscenario", "tableName": "v_edit_cat_dscenario", "id": "{dscenarioId}", "idName": "dscenario_id"'
    body = utils.create_body(theme, feature=feature)
    result = utils.execute_procedure(log, theme, 'gw_fct_setdelete', body, needs_write=True)
    utils.remove_handlers(log)
    return utils.create_response(result, theme=theme)


@dscenariomanager_bp.route('/setactive', methods=['GET'])
@jwt_required()
def setactive():
    """Set dscenario status"""
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    dscenarioId = args.get("dscenarioId")
    active = not str(args.get("active")).lower() == "true"

    # get feature and extras
    feature = f'"tableName":"v_edit_cat_dscenario","id":"{dscenarioId}"'
    extras = f'"fields": {{"active": "{active}"}}'

    # db fct
    body = utils.create_body(theme,feature=feature, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_setfields', body, needs_write=True)
    utils.remove_handlers(log)
    return utils.create_response(result, theme=theme)

@dscenariomanager_bp.route('/getdscenario', methods=['GET'])
@jwt_required()
def getdscenario():
    """
    Open Dscenario Dialog
    Returns a dialog for the dscenario with pre-populated data
    """
    log = utils.create_log(__name__)

    # Get request arguments
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    formType = args.get("formType")
    layoutName = args.get("layoutName")
    idName = args.get("idName")
    id = args.get("id")

    # Dynamically construct the form parameter
    form_parts = [
        f'"formName":"generic"',
        f'"formType":"{formType}"',
        f'"idname":"{idName}"',
        f'"id":"{id}"'
    ]

    # Join the form parts into the form string
    form = ", ".join(form_parts)

    # Create the body and execute the procedure
    body = utils.create_body(theme, form=form)

    # Execute the procedure to retrieve the workspace dialog data
    result = utils.execute_procedure(log, theme, 'gw_fct_get_dialog', body, needs_write=True)

    # Use `manage_response` to dynamically handle `formtype` and `layoutname`
    return manage_response(result, log, theme, formType, layoutName)
