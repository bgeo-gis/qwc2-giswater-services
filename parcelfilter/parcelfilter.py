"""
Copyright © 2025 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-


import utils
from .parcelfilter_utils import get_parcelfilter_ui

import json
import traceback

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required


parcelfilter_bp = Blueprint('parcelfilter', __name__)

@parcelfilter_bp.route('/dialog', methods=['GET'])
@jwt_required()
def dialog():
    """Submit query
    
    Returns dateselector dialog.
    """
    log = utils.create_log(__name__)
    # Get dialog
    form_xml = get_parcelfilter_ui()
    # Response
    response = {
        "feature": {},
        "data": {},
        "form_xml": form_xml
    }
    utils.remove_handlers(log)
    return jsonify(response)

