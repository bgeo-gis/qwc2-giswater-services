"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""

# DEPRECATED: Now inside mapproxy-service

import utils

import html
import json

from flask import Blueprint, request, make_response
from flask_jwt_extended import jwt_required
from qwc_services_core.auth import optional_auth
import subprocess

tiling_bp = Blueprint('tiling', __name__)


@tiling_bp.route('/update', methods=['GET'])
@jwt_required()
def update():
    """Submit query
    """
    config = utils.get_config()
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    
    tileUpdateScript = config.get("themes").get(theme).get("tileUpdateScript")
    print(tileUpdateScript)

    if tileUpdateScript:
        print("Executing...")
        result = subprocess.run(tileUpdateScript, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # result = subprocess.run(tileUpdateScript)

        stdout = result.stdout.decode()
        print(stdout)
        code = 200 if result.returncode == 0 else 500

        escaped_msg = html.escape(stdout).replace('\n', '<br>')
        log.info(f"{tileUpdateScript}|||{escaped_msg}")

        utils.remove_handlers(log)

        response = make_response(stdout, code)
        response.mimetype = "text/plain"
        return response
    else:
        error_str = f"Theme `{theme}` does not have a tiling script setup"
        log.warning(f"{request.url}|||{error_str}")
        return error_str, 400
