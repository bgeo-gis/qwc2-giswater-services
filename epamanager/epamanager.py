"""
Copyright © 2025 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import json
import utils
from .epamanager_utils import manage_response

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

epamanager_bp = Blueprint('epamanager', __name__)

@epamanager_bp.route('/dialog', methods=['GET'])
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
    form = '"formName":"generic", "formType":"epa_manager"'
    body = utils.create_body(theme, form=form)

    result = utils.execute_procedure(log, theme, 'gw_fct_get_dialog', body, needs_write=True)
    utils.remove_handlers(log)
    return manage_response(result, log, theme)


@epamanager_bp.route('/delete', methods=['DELETE'])
@jwt_required()
def deleteepa():
    """Delete epa"""
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args

    theme = args.get("theme")
    epaId = args.get("epaId")

    # db fct
    feature= f'"featureType": "epa", "tableName": "v_ui_rpt_cat_result", "id": "{epaId}", "idName": "result_id"'
    body = utils.create_body(theme, feature=feature)
    result = utils.execute_procedure(log, theme, 'gw_fct_setdelete', body, needs_write=True)
    utils.remove_handlers(log)
    return utils.create_response(result, theme=theme)


@epamanager_bp.route('/editdescript', methods=['GET'])
@jwt_required()
def editdescript():
    """Edit epa description"""
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    result_id = args.get("resultId")
    new_descript = args.get("newDescript")

    # get feature and extras
    feature = f'"tableName":"v_ui_rpt_cat_result","id":"{result_id}"'
    extras = f'"fields": {{"descript": "{new_descript}"}}'

    # db fct
    body = utils.create_body(theme,feature=feature, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_setfields', body, needs_write=True)
    utils.remove_handlers(log)
    return utils.create_response(result, theme=theme)


@epamanager_bp.route('/showinpdata', methods=['PUT'])
@jwt_required()
def showinpdata():
    """Show inp data"""
    log = utils.create_log(__name__)

    # args
    args = request.get_json()
    theme = args.get("theme")
    result_ids = args.get("resultIds")

    # db fct
    input_param = {"result_ids": result_ids}
    result_ids_json = f"'{json.dumps(input_param)}'::json"
    result = utils.execute_procedure(log, theme, 'gw_fct_getinpdata', result_ids_json, needs_write=True)

    utils.remove_handlers(log)
    return utils.create_response(result, theme=theme)


@epamanager_bp.route('/togglerptarchived', methods=['GET'])
@jwt_required()
def togglerptarchived():
    """Toggle archived"""
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    result_id = args.get("resultId")

    # check corporate
    status = args.get("status")
    action = 'RESTORE' if status == 'ARCHIVED' else 'ARCHIVE'

    # db fct
    extras = f'"result_id":"{result_id}", "action":"{action}"'
    body = utils.create_body(theme,extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_set_rpt_archived', body, needs_write=True)

    utils.remove_handlers(log)
    return utils.create_response(result, theme=theme)


@epamanager_bp.route('/togglecorporate', methods=['GET'])
@jwt_required()
def togglecorporate():
    """Toggle corporate"""
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    result_id = args.get("resultId")

    # check is corporate
    is_corporate = not str(args.get("isCorporate")).lower() == "true"

    # db fct 1
    extras = f'"resultId":"{result_id}", "action": "CHECK"'
    body = utils.create_body(theme,extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_epa2data', body, needs_write=True)

    # db fct 2
    extras = f'"resultId":"{result_id}", "isCorporate": {str(is_corporate).lower()}'
    body = utils.create_body(theme,extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_epa2data', body, needs_write=True)

    utils.remove_handlers(log)
    return utils.create_response(result, theme=theme)