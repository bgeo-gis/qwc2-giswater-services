"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

def get_form_with_combos(combos):
    """ Get completed form with values
    """
    form = ""
    for combo in combos:
        for key, value in combo.items():
            form += f'"{key}":"{value if value is not None else ""}",'
    return form[:-1]