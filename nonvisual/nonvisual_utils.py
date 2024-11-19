"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

from flask import jsonify, Response

import logging
import json

import utils
from utils import create_xml_generic_form


def manage_response(result, log, theme, formtype, layoutname):

    form_xml = create_xml_generic_form(result, formtype, layoutname)
    utils.remove_handlers(log)

    return utils.create_response(result, form_xml=form_xml, do_jsonify=True, theme=theme)
