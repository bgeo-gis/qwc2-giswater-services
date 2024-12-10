"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required
from sqlalchemy import text, exc
from .nonvisual_utils import manage_response, get_plot_svg


nonvisual_bp = Blueprint('nonvisual', __name__)

@nonvisual_bp.route('/open', methods=['GET'])
@jwt_required()
def opennonvisualmanager():
    """Open Nonvisual Objects Manager

    Returns dialog of the non visual objects manager.
    """
    # open dialog
    config = utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")

    form = '"formName":"generic", "formType":"nvo_manager"'
    # db fct
    body = utils.create_body(theme, form=form)
    result = utils.execute_procedure(log, theme, 'gw_fct_get_dialog', body, needs_write=True)

    return manage_response(result, log, theme, "nvo_manager", "lyt_nvo_mng")


@nonvisual_bp.route('/getnonvisualobject', methods=['GET'])
@jwt_required()
def getobject():
    """Open Nonvisual Object

    Returns dialog of the non visual object.
    """
    # open dialog
    config = utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    formType = args.get("formType")
    layoutName = args.get("layoutName")
    tableName = args.get("tableName")
    idname = args.get("idname")
    id = args.get("id")

    form = f'"formName":"generic", "formType":"{formType}", "tableName":"{tableName}", "idname":"{idname}", "id":"{id}"'
    # db fct
    body = utils.create_body(theme, form=form)
    result = utils.execute_procedure(log, theme, 'gw_fct_get_dialog', body, needs_write=True)

    return manage_response(result, log, theme, formType, layoutName)



@nonvisual_bp.route('/plot', methods=['POST'])
@jwt_required()
def create_plot():
    try:
        # Read JSON
        data = request.json

        response = get_plot_svg(data);

        return Response(response, mimetype="image/svg+xml")

    except Exception as e:
        return jsonify({"error": str(e)}), 500