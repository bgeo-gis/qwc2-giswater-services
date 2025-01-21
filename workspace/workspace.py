"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils
import json

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from .workspace_utils import manage_response, fill_tab_log

workspace_bp = Blueprint('workspace', __name__)

@workspace_bp.route('/dialog', methods=['GET'])
@jwt_required()
def dialog():
    """
    Open Workspace Management Dialog

    Returns dialog of the Workspace management, dynamically handling `formType` and `layoutName`.
    """
    utils.get_config()
    log = utils.create_log(__name__)

    # Get request arguments
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    formType = args.get("formType", "workspace_manager")  # Default to 'workspace_manager'
    layoutName = args.get("layoutName", "lyt_workspace_mngr")  # Default layout name for workspace_manager

    print("ARGS: ", args)
    print(f"THEME: {theme}, FORM TYPE: {formType}, LAYOUT NAME: {layoutName}")

    # Prepare the form parameter
    form = f'"formName":"generic", "formType":"{formType}"'
    body = utils.create_body(theme, form=form)

    print("REQUEST BODY::::: ", body)

    # Execute procedure to get dialog information
    result = utils.execute_procedure(log, theme, 'gw_fct_get_dialog', body, needs_write=True)

    # Use `manage_response` to dynamically handle the form and layout
    return manage_response(result, log, theme, formType, layoutName)


@workspace_bp.route('/manage', methods=['POST'])
@jwt_required()
def manage_workspace():
    """
    Handles workspace actions including DELETE, CREATE, UPDATE, CHECK, and INFO.
    This function directly calls the `gw_fct_workspacemanager` with the provided action.
    """
    log = utils.create_log(__name__)

    # Get request arguments
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    action = args.get("action")
    workspaceId = args.get("id")
    name = args.get("name")
    descript = args.get("descript")
    is_private = args.get("private")

    # Validate required parameters
    if not theme or not action:
        log.error("Missing required parameters: theme or action.")
        return jsonify({"status": "Failed", "message": "Missing required parameters: theme or action."}), 400

    # Construct the data body for the action
    data = f'"action": "{action}"'

    # Add workspace ID if provided
    if workspaceId:
        data += f', "id": {workspaceId}'

    # Add additional fields for UPDATE or CREATE actions
    if action in ["UPDATE", "CREATE"]:
        if name:
                data += f', "name": "{name}"'  # Only include name if it has changed
        # Always include description if provided
        if descript:
            data += f', "descript": "{descript}"'

        # Always include private if not None
        if is_private is not None:  # Ensure private can be False
            data += f', "private": "{str(is_private).lower()}"'

    # Create the request body for gw_fct_workspacemanager
    body = utils.create_body(theme, extras=data)

    # Execute the gw_fct_workspacemanager function
    result = utils.execute_procedure(log, theme, 'gw_fct_workspacemanager', body, needs_write=True)

    result_data = {}
    if isinstance(result, dict):
        result_data = result

    # Handle INFO action with `fill_tab_log`
    if action == "INFO" and result_data.get("status") == "Accepted":
        try:
            # Process the data using `fill_tab_log`
            context = {"infoText": ""}
            processed_text, _ = fill_tab_log(
                context=context,
                data=result_data.get("body", {}).get("data", {}),
                force_tab=False,
                reset_text=True,
                call_set_tabs_enabled=False,
                close=False
            )

            # Attach processed information to the response
            result_data["body"]["infoText"] = processed_text
        except Exception as e:
            log.error(f"Error processing INFO action with fill_tab_log: {str(e)}")

    # Log the result of the procedure
    log.info(f"Result from gw_fct_workspacemanager (action `{action}`): {json.dumps(result_data)}")

    # Return the response to the client
    return utils.create_response(result_data, theme=theme)


@workspace_bp.route('/getworkspaceobject', methods=['GET'])
@jwt_required()
def get_workspace_object():
    """
    Open Workspace Object Dialog
    Returns a dialog for the workspace object with pre-populated data.
    """
    log = utils.create_log(__name__)

    # Get request arguments
    args = request.get_json(force=True) if request.is_json else request.args
    theme = args.get("theme")
    formType = args.get("formType")
    layoutName = args.get("layoutName")
    tableName = args.get("tableName")
    id = args.get("id")  # Can be None
    idVal = args.get("idVal")  # Can be None

    print("ARGS: ", args)

    # Dynamically construct the form parameter
    form_parts = [
        f'"formName":"generic"',
        f'"formType":"{formType}"',
        f'"tableName":"{tableName}"',
    ]
    if id:  # Add id only if it is provided
        form_parts.append(f'"id":"{id}"')
    if idVal:  # Add idVal only if it is provided
        form_parts.append(f'"idval":"{idVal}"')

    # Join the form parts into the form string
    form = ", ".join(form_parts)

    # Create the body and execute the procedure
    body = utils.create_body(theme, form=form)
    print("REQUEST BODY::::: ", body)

    # Execute the procedure to retrieve the workspace dialog data
    result = utils.execute_procedure(log, theme, 'gw_fct_get_dialog', body, needs_write=True)

    print("RESULT MANAGER::::::::::: ", result)

    # Use `manage_response` to dynamically handle `formtype` and `layoutname`
    return manage_response(result, log, theme, formType, layoutName, idVal)

@workspace_bp.route('/setcurrent', methods=['POST'])
@jwt_required()
def set_current_workspace():
    """
    Set the current workspace and update the selector information.

    Parameters:
    - theme (str): The theme for the workspace.
    - id (int): The ID of the workspace to set as current.

    Returns:
    - JSON response with status and message.
    """
    log = utils.create_log(__name__)
    log.info("Entered set_current_workspace")

    try:
        # Get request arguments
        args = request.get_json(force=True)
        theme = args.get("theme")
        workspace_id = args.get("id")

        # Validate required parameters
        if not theme or not workspace_id:
            log.error("Missing required parameters: theme or workspace_id.")
            return jsonify({
                "status": "Failed",
                "message": "Missing required parameters: theme or workspace_id."
            }), 400

        # 1. Call `gw_fct_workspacemanager` for the CURRENT action
        log.info(f"Calling gw_fct_workspacemanager to set workspace {workspace_id} as current...")
        wm_extras = f'"action":"CURRENT", "id": "{workspace_id}"'
        wm_body = utils.create_body(theme=theme, extras=wm_extras)
        wm_result = utils.execute_procedure(log, theme, 'gw_fct_workspacemanager', wm_body)

        if wm_result.get('status') != 'Accepted':
            log.error(f"Failed to set workspace {workspace_id} as current using gw_fct_workspacemanager.")
            return jsonify({
                "status": "Failed",
                "message": "Failed to set workspace as current."
            }), 400

        # 2. Call `gw_fct_set_current`
        log.info("Calling gw_fct_set_current to apply workspace configuration...")
        sc_extras = f'"type":"workspace"'
        sc_body = utils.create_body(theme=theme, extras=sc_extras)
        sc_result = utils.execute_procedure(log, theme, 'gw_fct_set_current', sc_body)

        if sc_result.get('status') != 'Accepted':
            log.error(f"Failed to apply workspace configuration using gw_fct_set_current.")
            return jsonify({
                "status": "Failed",
                "message": "Failed to apply workspace configuration."
            }), 400

        # 3. Call `gw_fct_getselectors` to update selectors
        log.info("Calling gw_fct_getselectors to refresh selector information...")

        # Selector for tab_exploitation
        selector1_extras = f'"selectorType":"selector_basic", "filterText":"", "addSchema":"NULL"'
        selector1_form = f'"currentTab":"tab_exploitation"'
        selector1_body = utils.create_body(theme=theme, extras=selector1_extras, form=selector1_form)
        selector1_result = utils.execute_procedure(log, theme, 'gw_fct_getselectors', selector1_body)

        if selector1_result.get('status') != 'Accepted':
            log.error(f"Failed to update selectors for tab_exploitation.")
            return jsonify({
                "status": "Failed",
                "message": "Failed to update selectors for tab_exploitation."
            }), 400

        # Selector for the default tab
        selector2_extras = f'"selectorType":"selector_basic", "filterText":""'
        selector2_body = utils.create_body(theme=theme, extras=selector2_extras)
        selector2_result = utils.execute_procedure(log, theme, 'gw_fct_getselectors', selector2_body)

        if selector2_result.get('status') != 'Accepted':
            log.error(f"Failed to update selectors for the default tab.")
            return jsonify({
                "status": "Failed",
                "message": "Failed to update selectors for the default tab."
            }), 400

        # If all steps are successful
        log.info(f"Workspace {workspace_id} set as current and selectors updated successfully.")
        return jsonify({
            "status": "Accepted",
            "message": "Workspace set as current and selectors updated successfully.",
            "selectors": {
                "tab_exploitation": selector1_result.get('body', {}),
                "default_tab": selector2_result.get('body', {})
            }
        })

    except Exception as e:
        log.error(f"Error in set_current_workspace: {str(e)}")
        return jsonify({
            "status": "Failed",
            "message": "An error occurred while setting the current workspace.",
            "error": str(e)
        }), 500




