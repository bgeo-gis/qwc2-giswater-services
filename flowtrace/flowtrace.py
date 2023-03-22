import utils

from flask import Blueprint, request
from qwc_services_core.auth import optional_auth

flowtrace_bp = Blueprint('flowtrace', __name__)


@flowtrace_bp.route('/upstream', methods=['GET'])
@optional_auth
def upstream():
    """Upstream

    Runs flowtrace upstream at clicked map position.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")
    coords = args.get("coords").split(',')
    zoom = args.get("zoom")

    # db fct
    coordinates = f'"epsg": {int(epsg)}, "xcoord": {coords[0]}, "ycoord": {coords[1]}, "zoomRatio": {float(zoom)}'
    extras = f'"coordinates": {{{coordinates}}}'
    body = utils.create_body(extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_graphanalytics_upstream', body)

    utils.remove_handlers(log)

    return utils.create_response(result, do_jsonify=True)


@flowtrace_bp.route('/downstream', methods=['GET'])
@optional_auth
def downstream():
    """Downstream

    Runs flowtrace downstream at clicked map position.
    """
    log = utils.create_log(__name__)

    # args
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    epsg = args.get("epsg")
    coords = args.get("coords").split(',')
    zoom = args.get("zoom")

    # db fct
    coordinates = f'"epsg": {int(epsg)}, "xcoord": {coords[0]}, "ycoord": {coords[1]}, "zoomRatio": {float(zoom)}'
    extras = f'"coordinates": {{{coordinates}}}'
    body = utils.create_body(extras=extras)
    result = utils.execute_procedure(log, theme, 'gw_fct_graphanalytics_downstream', body)

    utils.remove_handlers(log)

    return utils.create_response(result, do_jsonify=True)
