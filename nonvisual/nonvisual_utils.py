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
    """Generate SVG plot from curve or pattern data """
    is_curve = data.get("curve_type")

    # Check if the plot is a curve or a pattern
    if is_curve and is_curve != 'None':
        # Get X and Y values
        field_data = data.get("body", {}).get("data", {}).get("fields", [])
        if not field_data:
            return jsonify({"error": "No data provided"}), 400

        values = field_data[0].get("value", [])
        if not values:
            return jsonify({"error": "No curve data found"}), 400

        x_list = [v.get("x_value", 0) for v in values]
        y_list = [v.get("y_value", 0) for v in values]

        # Create figure and plot
        fig, ax = plt.subplots()
        curve_type = data.get("curve_type")

        if curve_type == 'PUMP' and len(x_list) == 1:
            # Handle 'PUMP' curve
            x, y = x_list[0], y_list[0]
            if x == 0:
                return jsonify({"error": "Flow cannot be zero"}), 400

            x_array = np.array([0, x, 2 * x])
            y_array = np.array([1.33 * y, y, 0])
            xnew = np.linspace(x_array.min(), x_array.max(), 100)
            spl = CubicSpline(x_array, y_array)
            ax.plot(xnew, spl(xnew), color='indianred')

        elif curve_type == 'SHAPE' and x_list:
            # Handle 'SHAPE' curve
            geom1 = float(data.get("geom1", 1))
            geom2 = float(data.get("geom2", 1))  # Unused but kept for potential use

            x_list = [x * geom1 for x in x_list]
            y_list = [y * geom1 for y in y_list]

            area = np.trapz(y_list, x_list) * 2
            ax.plot(y_list, x_list, color="blue")

            y_list_inverted = [-y for y in y_list]
            ax.plot(y_list_inverted, x_list, color="blue")
            ax.plot([y_list_inverted[0], y_list[0]], [x_list[0], x_list[0]], color="blue")
            ax.plot([y_list[-1], y_list[-1]], [x_list[0], x_list[-1]], color="grey", alpha=0.5, linestyle="dashed")
            ax.text(min(y_list_inverted) * 1.1, max(x_list) * 1.07, f"Area: {round(area, 2)} units²", fontsize=8)

        else:
            # Default curve plot
            ax.plot(x_list, y_list, color='indianred')

        fig.set_size_inches(3, 3)
        return generate_svg(fig)

    else:
        # Handle 'patterns' plots
        fig, ax = plt.subplots()

        # Read data for patterns
        field_data = data.get("body", {}).get("data", {}).get("fields", [])
        if not field_data:
            return jsonify({"error": "No data provided"}), 400

        value_list = field_data[0].get("value", [])
        if not value_list:
            return jsonify({"error": "No pattern data found"}), 400

        # Convert JSON structure to a list of lists of factors
        float_list = [
            [float(value) for value in row.values() if value is not None]
            for row in value_list
        ]

        # Create bar plot with offsets
        x_offset = 0
        for row in float_list:
            if row:
                df_list = [0] * x_offset + row
                ax.bar(range(len(df_list)), df_list, width=1, align='edge', color='lightcoral', edgecolor='indianred')
                x_offset += len(row)

        # Customize plot
        ax.set_xticks(range(0, x_offset))
        fig.set_size_inches(7, 3.5)
        return generate_svg(fig)


def generate_svg(fig):
    """Generate SVG output from a Matplotlib figure."""
    output = io.StringIO()
    plt.savefig(output, format="svg", dpi=300)
    plt.close(fig)
    result = output.getvalue()
    output.close()
    return result