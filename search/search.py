"""
Copyright © 2023 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
import utils
import json

import json
import traceback

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc


search_bp = Blueprint('search', __name__)

@search_bp.route('/getsearch', methods=['GET'])
@jwt_required()
def getsearch():
    """Get search
    Get current user's search results.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    filterFields = args.get("filterFields")
    
    # db fct
    body = utils.create_body(theme, filter_fields=filterFields)

    result = utils.execute_procedure(log, theme, 'gw_fct_getsearch', body)

    utils.remove_handlers(log)

    return utils.create_response(result, do_jsonify=True, theme=theme)


@search_bp.route('/setsearch', methods=['GET', 'POST'])
@jwt_required()
def setsearch():
    """Set search
    Calls gw_fct_set_new_search.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    extras = args.get("extras")
    print("extras: ", extras)

    # db fct
    body = utils.create_body(theme, extras=extras)
    print("body: ", body)
    result = utils.execute_procedure(log, theme, 'gw_fct_setsearch', body)

    utils.remove_handlers(log)

    return utils.create_response(result, do_jsonify=True, theme=theme)