"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import utils

def manage_response(result, log, theme, dialog_name, layout_name):

    form_xml = utils.create_xml_generic_form(result, dialog_name, layout_name)
    utils.remove_handlers(log)
    return utils.create_response(result, form_xml=form_xml, do_jsonify=True, theme=theme)
