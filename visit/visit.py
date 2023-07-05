"""
Copyright BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils
from .visit_utils import manage_response

import json
import traceback
import os
import uuid

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc
from PIL import Image

visit_bp = Blueprint('visit', __name__)


@visit_bp.route('/getvisit', methods=['GET', 'PUT'])
@optional_auth
def getvisit():
    config = utils.get_config()
    log = utils.create_log(__name__)
    extras = ""

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    visitType = args.get("visitType", 1)
    visitId = args.get("visitId") # nomes si obrim des del manager
    #featureType = args.get("featureType")
    #feature_id = args.get("id")
    epsg = args.get("epsg")
    xcoord = args.get("xcoord")
    ycoord = args.get("ycoord")
    zoomRatio = args.get("zoomRatio")
    fields = args.get("fields")

    form = f'"visitType": {visitType}'
    if visitId is not None:
        form += f',"visitId": {visitId}'
    if xcoord is not None:
        extras += f'"coordinates": {{"xcoord": {xcoord}, "ycoord": {ycoord}, "zoomRatio": {zoomRatio}}}'
    if fields is not None:
        if extras:
            extras += f', '
        extras += f'"fields": {json.dumps(fields)}'
    if not extras:
        extras = None
    
    body = utils.create_body(theme, project_epsg=epsg, form=form, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_getvisit', body)

    utils.remove_handlers(log)

    return manage_response(result, log)


@visit_bp.route('/setvisit', methods=['POST'])
@optional_auth
def setvisit():
    """Submit query

    Returns additional information at clicked map position.
    """
    config = utils.get_config()
    log = utils.create_log(__name__)
    tenant = utils.tenant_handler.tenant()

    # args
    args = request.form
    theme = args.get("theme")
    visitId = args.get("visitId")
    tableName = args.get("tableName")
    fields = args.get("fields")
    xcoord = args.get("xcoord")
    ycoord = args.get("ycoord")
    epsg = args.get("epsg")

    print("THEME: ", theme, " VISITID: ", visitId, " tableName: ", tableName, " FIELDS: ", fields)
    # files
    files = request.files.getlist('files[]') if request.files else []

    url_list = []
    filenames = []
    for file in files:
        # extension = os.path.splitext(file.filename)[1]
        extension = ".jpeg"
        filename = f"{uuid.uuid1()}{extension}"
        url = f"{config.get('images_url')}img/{filename}"
        url_list.append(url)
        filenames.append(filename)

    files_json = json.dumps(list(str(x) for x in url_list))
    
    feature = ''
    if visitId is not None:
        feature += f'"visitId": {visitId}'
    print(f"{theme=}")
    print(f"{visitId=}")
    print(f"{fields=}")
    extras = f'"fields": {fields}, "tableName" : "{tableName}", "files":{files_json}'
    if xcoord is not None:
        extras += f', "coordinates": {{"xcoord": {xcoord}, "ycoord": {ycoord}}}'
    body = utils.create_body(theme, project_epsg=epsg, feature=feature, extras=extras)
    print("BODY-------------------------------: ", body)
    result = utils.execute_procedure(log, theme, 'gw_fct_setvisit', body)
    """
    sql = f"SELECT {schema}.gw_fct_setvisit({body});"
    log.info(f" Server execution -> {sql}")
    print(f"SERVER EXECUTION: {sql}\n")
    """
    utils.remove_handlers(log)

    if result or result.get('status') == "Accepted":
        try:
            images_path = config.get('images_path')
            try:
                os.makedirs(images_path)
            except FileExistsError:
                pass

            for file, filename in zip(files, filenames):
                print("=========== FILES IN SET VISIT =========================")
                if not file or file.filename == '':
                    continue
                file = Image.open(file)
                file = file.convert("RGB")
                file.save(os.path.join(images_path, filename), optimize=True, quality=75)
                status = "Accepted"
                message = "File uploaded successfully!"
        except Exception as e:
            status = "Failed"
            message = "Error"
            print(e)

    return utils.create_response(result, do_jsonify=True, theme=theme)

@visit_bp.route('/getvisitmanager', methods=['GET'])
@optional_auth
def getmanager():
    """Get visit manager

    Returns visit manager dialog.
    """
    log = utils.create_log(__name__)

    # args
    theme = request.args.get("theme")

    # db fct
    body = utils.create_body(theme, )
    result = utils.execute_procedure(log, theme, 'gw_fct_getvisit_manager', body)

    return manage_response(result, log, manager=True)

@visit_bp.route('/delete', methods=['DELETE'])
@optional_auth
def deletevisit():
    """Delete visit

    Deletes a visit.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    visitId = args.get("visitId")
    # db fct
    feature= f'"featureType": "visit", "tableName": "om_visit", "id": {visitId}, "idName": "id"'
    body = utils.create_body(theme, feature=feature)
    result = utils.execute_procedure(log, theme, 'gw_fct_setdelete', body)

    return manage_response(result, log, theme)
