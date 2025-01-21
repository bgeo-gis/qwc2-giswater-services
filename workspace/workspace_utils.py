"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils

def manage_response(result, log, theme, formtype, layoutname, id=None):
    print("MANAGE RESPONSE VALUES TO FORM::::::::::: ", result, log, theme, formtype, layoutname)
    form_xml = utils.create_xml_generic_form(result, formtype, layoutname)
    utils.remove_handlers(log)
    print("FORM XML WORKSPACE::::::::::: ", form_xml)
    print("IDDDDDDDD WORKSPACE::::::::::: ", id)
    if id is not None:
        result["id"] = id
    return utils.create_response(result, form_xml=form_xml, do_jsonify=True, theme=theme)

def fill_tab_log(context, data, force_tab=True, reset_text=True, tab_index=1, call_set_tabs_enabled=True, close=False, end="\n"):
    """
    Populate the `info` text area and manage tab states.

    :param context: The context (React-like state object or any dict-like structure).
    :param data: The JSON response data.
    :param force_tab: Whether to force showing a specific tab.
    :param reset_text: Whether to reset the text before appending.
    :param tab_index: The index of the tab to switch to.
    :param call_set_tabs_enabled: Whether to enable/disable tabs dynamically.
    :param close: Whether to hide/disable buttons.
    :param end: The string to append at the end of each message.
    :return: Tuple (text, change_tab).
    """

    # Validate the data structure
    if not data or 'info' not in data or 'values' not in data['info']:
        return "No additional information available.", False

    text = "" if reset_text else context.get("infoText", "")  # Initialize or reset text
    change_tab = False

    # Extract messages from the info.values array
    for item in data['info']['values']:
        if 'message' in item:
            if item['message']:
                text += str(item['message']) + end
                if force_tab:
                    change_tab = True
            else:
                text += end  # Add an empty line for missing messages

    # Update the context (simulating React state updates)
    context["infoText"] = text.strip()

    # Handle tab management (if applicable)
    if change_tab and "tabs" in context:
        tabs = context.get("tabs", [])
        if call_set_tabs_enabled:
            # Enable all tabs except the last one
            for index, tab in enumerate(tabs):
                tab["enabled"] = index != len(tabs) - 1
        if force_tab:
            context["currentTab"] = tab_index

    # Manage buttons (if applicable)
    if close:
        context["buttonsVisible"] = False

    return text, change_tab