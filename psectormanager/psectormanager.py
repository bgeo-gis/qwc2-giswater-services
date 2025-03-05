"""
Copyright © 2025 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils
import json

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from qwc_services_core.auth import optional_auth, get_identity, get_username
from sqlalchemy import text, exc
from decimal import Decimal

psectormanager_bp = Blueprint('psectormanager', __name__)

@psectormanager_bp.route('/getbudget', methods=['GET'])
@jwt_required()
def getbudget():

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    psector_id = args.get("psectorId")

    # db connection
    schema_name = utils.get_schema_from_theme(theme, utils.get_config())
    db = utils.get_db(theme, needs_write=True)

    result_dict = {}
    with db.begin() as conn:
        fields = ["total_arc", "total_node", "total_other", "pem", "pec", "pec_vat", "gexpenses", "vat", "other", "pca"]

        # Get values from v_plan_psector
        query = text(f"SELECT {', '.join(fields)} FROM {schema_name}.v_plan_psector WHERE psector_id = {psector_id}")
        row = conn.execute(query).fetchone()

        if row:
            result_dict = {
                "fields": {
                    **{field: float(value) if isinstance(value, Decimal) else value for field, value in zip(fields, row)}
                }
            }
            result_dict["fields"]["gexpenses_total"] = round(result_dict["fields"]["gexpenses"] * result_dict["fields"]["pem"] / 100, 2)
            result_dict["fields"]["vat_total"] = round(result_dict["fields"]["vat"] * result_dict["fields"]["pec"] / 100, 2)
            result_dict["fields"]["other_total"] = round(result_dict["fields"]["other"] * result_dict["fields"]["pec_vat"] / 100, 2)

    return utils.create_response(result_dict, theme=theme)

@psectormanager_bp.route('/getpsectorfeatures', methods=['PUT'])
@jwt_required()
def getpsectorfeatures():

    # log
    utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    psector_id = args.get("psectorIds")

    # db fct
    extras = f'"psector_id":"{psector_id}"'
    body = utils.create_body(theme, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_getpsectorfeatures', body, needs_write=True)

    utils.remove_handlers(log)

    return utils.create_response(result, theme=theme)