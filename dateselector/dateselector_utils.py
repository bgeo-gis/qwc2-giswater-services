"""
Copyright © 2023 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-


import utils

from flask import jsonify, Response

def handle_db_result(result: dict, theme: str) -> Response:
    response = {}
    if not result:
        response = utils.create_response(result, theme=theme)
        return jsonify(response)
    if 'results' not in result or result['results'] > 0:
        layer_columns = {}
        db_layers = utils.get_db_layers(theme)
        
        for k, v in db_layers.items():
            if v in result['body']['data']['layerColumns']:
                layer_columns[k] = result['body']['data']['layerColumns'][v]
        
        response = utils.create_response(result, theme=theme)
        response["body"]["data"]["layerColumns"] = layer_columns

    return jsonify(response)


def get_dateselector_ui() -> str:
    response = ""
    f = None
    try:
        f = open("dateselector/ui/date_selector.ui")
        response = f.read()
    except:
        response = jsonify({"message": f"Can't open file {f}"})
    finally:
        if f:
            f.close()
        return response
