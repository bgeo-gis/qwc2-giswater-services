import utils
import json
import traceback
from .mincut_utils import mincut_create_xml_form, mincutmanager_create_xml_form

from flask import Blueprint, request, jsonify
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc

mincut_bp = Blueprint('mincut', __name__)


@mincut_bp.route('/setmincut', methods=['GET', 'POST'])
@optional_auth
def setmincut():
    """Set mincut

    Calls gw_fct_setmincut.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")
    action = args.get("action")
    xcoord = args.get("xcoord")
    ycoord = args.get("ycoord")
    zoomRatio = args.get("zoomRatio")
    mincutId = args.get("mincutId")

    # db fct
    coordinates = f'"epsg": {epsg}, "xcoord": {xcoord}, "ycoord": {ycoord}, "zoomRatio": {zoomRatio}'
    extras = f'"action": "{action}", "usePsectors": "False", "coordinates": {{{coordinates}}}'
    if mincutId is not None:
        extras += f', "mincutId": {mincutId}'
    body = utils.create_body(project_epsg=epsg, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_setmincut', body)

    # form xml
    try:
        form_xml = mincut_create_xml_form(result)
    except:
        form_xml = None

    utils.remove_handlers(log)

    return utils.create_response(result, form_xml=form_xml, do_jsonify=True)


@mincut_bp.route('/open', methods=['GET'])
@optional_auth
def openmincut():
    """Open mincut

    Returns dialog of a wanted mincut.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    mincut_id = args.get("mincutId")

    # db fct
    extras = f'"mincutId": {mincut_id}'
    body = utils.create_body(extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_getmincut_ff', body)

    # form xml
    try:
        form_xml = mincut_create_xml_form(result)
    except:
        form_xml = None

    utils.remove_handlers(log)

    return utils.create_response(result, form_xml=form_xml, do_jsonify=True)


@mincut_bp.route('/cancel', methods=['GET', 'POST'])
@optional_auth
def cancelmincut():
    """Cancel mincut

    Calls gw_fct_setmincut with action 'mincutCancel'.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    mincutId = args.get("mincutId")

    # db fct
    extras = f'"action": "mincutCancel", "mincutId": {mincutId}'
    body = utils.create_body(extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_setmincut', body)

    # form xml
    try:
        form_xml = mincut_create_xml_form(result)
    except:
        form_xml = None

    utils.remove_handlers(log)

    return utils.create_response(result, form_xml=form_xml, do_jsonify=True)


@mincut_bp.route('/delete', methods=['DELETE'])
@optional_auth
def deletemincut():
    """Delete mincut

    Deletes a mincut.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    mincut_id = args.get("mincutId")

    # db fct
    extras = f'"action": "mincutDelete", "mincutId": {mincut_id}'
    body = utils.create_body(extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_setmincut', body)

    # form xml
    try:
        form_xml = mincut_create_xml_form(result)
    except:
        form_xml = None

    utils.remove_handlers(log)

    return utils.create_response(result, form_xml=form_xml, do_jsonify=True)


@mincut_bp.route('/accept', methods=['POST'])
@optional_auth
def accept():
    """Accept mincut

    Calls gw_fct_setmincut with action 'mincutAccept'.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")
    mincutId = args.get("mincutId")
    fields = args.get("fields")
    usePsectors = args.get("usePsectors")
    xcoord = args.get("xcoord")
    ycoord = args.get("ycoord")
    zoomRatio = args.get("zoomRatio")

    # db fct
    feature = f'"featureType": "", "tableName": "om_mincut", "id": {mincutId}'
    coordinates = f'"epsg": {int(epsg)}, "xcoord": {xcoord}, "ycoord": {ycoord}, "zoomRatio": {zoomRatio}'
    extras = f'"action": "mincutAccept", "mincutClass": 1, "status": "check", "mincutId": {mincutId}, "usePsectors": "{usePsectors}", ' \
             f'"fields": {json.dumps(fields)}, "coordinates": {{{coordinates}}}'
    body = utils.create_body(feature=feature, extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_setmincut', body)

    # form xml
    try:
        form_xml = mincut_create_xml_form(result)
    except:
        form_xml = None

    utils.remove_handlers(log)

    return utils.create_response(result, form_xml=form_xml, do_jsonify=True)


@mincut_bp.route('/getmincutmanager', methods=['GET'])
@optional_auth
def getmanager():
    """Get mincut manager

    Returns mincut manager dialog.
    """
    log = utils.create_log(__name__)

    # args
    theme = request.args.get("theme")

    # db fct
    body = utils.create_body()
    result = utils.execute_procedure(log, theme, 'gw_fct_getmincut_manager', body)

    # form xml
    try:
        form_xml = mincutmanager_create_xml_form(result)
    except:
        form_xml = None

    utils.remove_handlers(log)

    return utils.create_response(result, form_xml=form_xml, do_jsonify=True)


@mincut_bp.route('/getlist', methods=['GET'])
@optional_auth
def getlist():
    """Get list

    Returns list of mincuts (for the manager).
    """
    log = utils.create_log(__name__)

    # args
    theme = request.args.get("theme")
    tabName = request.args.get("tabName")
    widgetname = request.args.get("widgetname")
    formtype = request.args.get("formtype")
    tableName = request.args.get("tableName")
    filterFields = request.args.get("filterFields")

    # Manage filters
    filterFields_dict = {}
    if filterFields in (None, "", "null", "{}"):
        filterFields_dict = None
    else:
        filterFields = json.loads(str(filterFields))
        for k, v in filterFields.items():
            if v in (None, "", "null"):
                continue
            filterFields_dict[k] = {
            #   "columnname": v["columnname"],
                "value": v["value"],
                "filterSign": v["filterSign"]
            }

    # db fct
    form = f'"formName": "", "tabName": "{tabName}", "widgetname": "{widgetname}", "formtype": "{formtype}"'
    feature = f'"tableName": "{tableName}"'
    filter_fields = json.dumps(filterFields_dict) if filterFields_dict else ''
    body = utils.create_body(form=form, feature=feature, filter_fields=filter_fields)
    result = utils.execute_procedure(log, theme, 'gw_fct_getlist', body)

    utils.remove_handlers(log)

    return utils.create_response(result, do_jsonify=True)
