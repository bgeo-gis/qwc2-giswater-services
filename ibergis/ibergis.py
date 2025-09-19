"""
Copyright © 2025 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import os
import utils

from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required

from werkzeug.security import safe_join

from pathlib import Path

ibergis_bp = Blueprint('ibergis', __name__)

@ibergis_bp.route('/getresult', methods=['GET'])
@jwt_required()
def getresult():
    """"""
    log = utils.create_log(__name__)
    tenant = utils.tenant_handler.tenant()

    theme = request.args.get("theme")

    path = request.args.get('path')
    if path is None:
        return 400, "Please provide the path of the file"

    return send_file(safe_join('/rasters', tenant, theme, path, "IberGisResults", "Depth.tif"))


@ibergis_bp.route('/getresultlist', methods=['GET'])
@jwt_required()
def getresultlist():
    log = utils.create_log(__name__)
    tenant = utils.tenant_handler.tenant()

    theme = request.args.get("theme")

    root = Path(safe_join('/rasters', tenant, theme))
    runs = [os.path.basename(dir) for dir in root.iterdir() if dir.is_dir()]

    return runs


