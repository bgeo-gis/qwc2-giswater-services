"""
Copyright © 2024 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-


import io
import matplotlib.pyplot as plt
import numpy as np
import utils
from utils import create_xml_generic_form
from scipy.interpolate import CubicSpline
from flask import jsonify


def manage_response(result, log, theme, formtype, layoutname):

    form_xml = create_xml_generic_form(result, formtype, layoutname)
    utils.remove_handlers(log)

    return utils.create_response(result, form_xml=form_xml, do_jsonify=True, theme=theme)


def get_plot_svg(data):

    # TODO: Manage different plot types (curves, patterns, etc.)

    # Get X and Y values
        field_data = data.get("body", {}).get("data", {}).get("fields", [])
        if not field_data:
            return jsonify({"error": "No data provided"}), 400

        values = field_data[0].get("value", [])
        x_list = [v["x_value"] for v in values]
        y_list = [v["y_value"] for v in values]

        # Create figure and plot
        fig, ax = plt.subplots()
        curve_type = data.get("curve_type")

        # Manage 'PUMP'
        if len(x_list) == 1 and curve_type == 'PUMP':
            x = x_list[0]
            y = y_list[0]
            if x != 0:
                x_array = np.array([0, x, 2 * x])
                y_array = np.array([1.33 * y, y, 0])
                xnew = np.linspace(x_array.min(), x_array.max(), 100)
                spl = CubicSpline(x_array, y_array)
                y_smooth = spl(xnew)
                ax.plot(xnew, y_smooth, color='indianred')
            else:
                return jsonify({"error": "Flow cannot be zero"}), 400
        # Manage 'SHAPE'
        elif len(x_list) >= 1 and curve_type == 'SHAPE':
            geom1 = data.get("geom1", 1)
            geom2 = data.get("geom2", 1)

            x_list = [x * float(geom1) for x in x_list]
            y_list = [y * float(geom1) for y in y_list]

            area = np.trapz(y_list, x_list) * 2
            ax.plot(y_list, x_list, color="blue")

            y_list_inverted = [-y for y in y_list]
            ax.plot(y_list_inverted, x_list, color="blue")
            ax.plot([y_list_inverted[0], y_list[0]], [x_list[0], x_list[0]], color="blue")
            ax.plot([y_list[-1], y_list[-1]], [x_list[0], x_list[-1]], color="grey", alpha=0.5, linestyle="dashed")
            ax.text(min(y_list_inverted) * 1.1, max(x_list) * 1.07, f"Area: {round(area, 2)} units²", fontsize=8)

        else:
            ax.plot(x_list, y_list, color='indianred')

        fig.set_size_inches(3, 3)  # plot size

        # Generate SVG as a string
        output = io.StringIO()
        plt.savefig(output, format="svg", dpi=300)
        plt.close(fig)
        result = output.getvalue()
        output.close()

        return result;