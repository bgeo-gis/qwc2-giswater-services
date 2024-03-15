"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-


import utils

from flask import jsonify, Response

def get_parcelfilter_ui() -> str:
    response = ""
    f = None
    try:
        f = open("parcelfilter/ui/parcel_filter.ui")
        response = f.read()
        print("XML: ",response)
    except:
        response = jsonify({"message": f"Can't open file {f}"})
    finally:
        if f:
            f.close()
        return response
