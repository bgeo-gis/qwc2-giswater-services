"""
Copyright BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

from flask import jsonify, Response
import os
import json
import math
os.environ['MPLCONFIGDIR'] = os.getcwd() + "/.config/matplotlib"
import matplotlib.pyplot as plt
from collections import OrderedDict
from decimal import Decimal
import datetime


class GwNodeData:

    def __init__(self):

        self.start_point = None
        self.top_elev = None
        self.ymax = None
        self.z1 = None
        self.z2 = None
        self.cat_geom = None
        self.geom = None
        self.slope = None
        self.elev1 = None
        self.elev2 = None
        self.y1 = None
        self.y2 = None
        self.node_id = None
        self.elev = None
        self.code = None
        self.node_1 = None
        self.node_2 = None
        self.total_distance = None
        self.descript = None
        self.data_type = None
        self.surface_type = None
        self.none_values = None

class GwGenerateSvg:
    def __init__(self, profile_json, arcs, nodes, terrains, params):
        self.list_of_selected_nodes = []
        self.nodes = []
        self.links = []
        self.lastnode_datatype = 'REAL'
        self.none_values = []
        self.profile_json = profile_json
        self.img_path = ""
        self.params = params
        self._draw_profile(arcs, nodes, terrains)
        

    def _draw_profile(self, arcs, nodes, terrains):
        # Clear plot
        plt.gcf().clear()

        # Set main parameters
        self._set_profile_variables(arcs, nodes, terrains)
        self._fill_profile_variables(arcs, nodes, terrains)
        self._set_guitar_parameters()

        # Draw start node
        self._draw_start_node(self.nodes[0])

        # Draw nodes and precedessor arcs between start and end nodes
        for i in range(1, self.n - 1):
            self._draw_nodes(self.nodes[i], self.nodes[i - 1], i)

        # Draw terrain
        for i in range(1, self.t):
            # define variables
            # start_point = total_x
            self.first_top_x = self.links[i - 1].start_point
            # start_point = total_x
            self.node_top_x = self.links[i].start_point
            self.first_top_y = self.links[i - 1].node_id  # node_id = top_n1
            self.node_top_y = self.links[i - 1].geom  # geom = top_n2

            # Draw terrain
            self._draw_terrain(i)

            # Fill text terrain
            self._fill_guitar_text_terrain(self.node_top_x, i)
            self._draw_guitar_auxiliar_lines(self.node_top_x, first_vl=False)

        # Draw last node and precedessor arc
        self._draw_end_node(
            self.nodes[self.n - 1], self.nodes[self.n - 2], self.n - 1)

        # Draw guitar & grid
        self._draw_guitar_horitzontal_lines()
        self._draw_grid()

        # Manage layout and plot
        self._set_profile_layout()
        #self.plot = plt

        # If file profile.png exist overwrite
        current_time_ms = int(datetime.datetime.now().microsecond)
        self.img_path = f"/qwc-services/qwc2-giswater-services/profile/tmp/profile_{current_time_ms}.svg"
        #self.img_path = f"/media/qwc2/qgis-projects/bgeo/svg/profile.svg"
        """
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)
        else:
            tools_log.log_info(f"User settings file: {img_path}")
        """
        
        #fig_size = plt.rcParams["figure.figsize"]

        # Set figure width to 10.4  and height to 4.8
        #fig_size[0] = 60.4
        #fig_size[1] = 4.8
        #plt.rcParams["figure.figsize"] = fig_size
        plt.gcf().set_size_inches(14, 9)
        # Save profile with dpi = 300
        #plt.canvas.draw()
        #plt.figure(1).tight_layout()
        plt.savefig(self.img_path, dpi=300)

    def _set_profile_layout(self):
        """ Set properties of main window """

        # Set window name
        #self.win = plt.gcf()
        #self.win.canvas.set_window_title('Draw Profile')

        # Hide axes
        self.axes = plt.gca()
        self.axes.set_axis_off()

        # Set background color of window
        #self.fig1 = plt.figure(1)
        #self.fig1.tight_layout()
        #self.rect = self.fig1.patch
        #self.rect.set_facecolor('white')

    def _set_profile_variables(self, arcs, nodes, terrains):
        """ Get and calculate parameters and values for drawing """

        # Declare list elements
        self.list_of_selected_arcs = arcs
        self.list_of_selected_nodes = []
        self.list_of_selected_terrains = []

        # Populate list nodes
        for node in nodes:
            self.list_of_selected_nodes.append(node)

        # Populate list terrains
        for terrain in terrains:
                self.list_of_selected_terrains.append(terrain)

        self.gis_length = [0]
        self.arc_dimensions = []
        self.arc_catalog = []
        self.start_point = [0]

        # Get arcs between nodes (on shortest path)
        self.n = len(self.list_of_selected_nodes)
        self.t = len(self.list_of_selected_terrains)

        for arc in arcs:
            self.gis_length.append(arc['length'])
            self.arc_dimensions.append(json.loads(
                arc['descript'], object_pairs_hook=OrderedDict)['dimensions'])
            self.arc_catalog.append(json.loads(
                arc['descript'], object_pairs_hook=OrderedDict)['catalog'])

        # Calculate start_point (coordinates) of drawing for each node
        n = len(self.gis_length)
        for i in range(1, n):
            x = self.start_point[i - 1] + self.gis_length[i]
            self.start_point.append(x)
            i += 1

    def _fill_profile_variables(self, arcs, nodes, terrains):
        """ Get parameters from database. Fill self.nodes with parameters postgres """

        # Get parameters and fill the nodes
        n = 0
        for node in nodes:
            parameters = GwNodeData()
            parameters.start_point = self.start_point[n]
            parameters.top_elev = node['top_elev']
            parameters.ymax = node['ymax']
            parameters.elev = node['elev']
            parameters.node_id = node['node_id']
            parameters.geom = node['cat_geom1']
            parameters.descript = [json.loads(
                node['descript'], object_pairs_hook=OrderedDict)][0]
            parameters.data_type = node['data_type']
            parameters.surface_type = node['surface_type']

            self.nodes.append(parameters)
            n = n + 1

        # Get parameters and fill the links
        n = 0
        for terrain in terrains:
            parameters = GwNodeData()
            parameters.start_point = terrain['total_x']
            parameters.top_elev = json.loads(
                terrain['label_n1'], object_pairs_hook=OrderedDict)['top_elev']
            parameters.node_id = terrain['top_n1']
            parameters.geom = terrain['top_n2']
            parameters.descript = [json.loads(
                terrain['label_n1'], object_pairs_hook=OrderedDict)][0]
            parameters.surface_type = terrain['surface_type']

            self.links.append(parameters)
            n = n + 1

        # Populate node parameters with associated arcs
        n = 0
        for arc in arcs:
            self.nodes[n].z1 = arc['z1']
            self.nodes[n].z2 = arc['z2']
            self.nodes[n].cat_geom = arc['cat_geom1']
            self.nodes[n].elev1 = arc['elev1']
            self.nodes[n].elev2 = arc['elev2']
            self.nodes[n].y1 = arc['y1']
            self.nodes[n].y2 = arc['y2']
            self.nodes[n].slope = 1
            self.nodes[n].node_1 = arc['node_1']
            self.nodes[n].node_2 = arc['node_2']
            n += 1

    def _set_guitar_parameters(self):
        """
        Define parameters of table
        :return:
        """

        # Search y coordinate min_top_elev ( top_elev- ymax)
        self.min_top_elev = Decimal(
            self.nodes[0].top_elev - self.nodes[0].ymax)

        # self.min_top_elev_descript = Decimal(self.nodes[0].descript['top_elev'] - self.nodes[0].descript['ymax'])
        for i in range(1, self.n):
            if (self.nodes[i].top_elev - self.nodes[i].ymax) < self.min_top_elev:
                self.min_top_elev = Decimal(
                    self.nodes[i].top_elev - self.nodes[i].ymax)

        # Search y coordinate max_top_elev
        self.max_top_elev = self.nodes[0].top_elev
        self.max_top_elev_descript = self.nodes[0].descript['top_elev']
        for i in range(1, self.n):
            if self.nodes[i].top_elev > self.max_top_elev:
                self.max_top_elev = self.nodes[i].top_elev

        # Calculating dimensions of x-fixed part of table
        self.fix_x = Decimal(
            Decimal(0.15) * Decimal(self.nodes[self.n - 1].start_point))

        # Calculating dimensions of y-fixed part of table
        # Height y = height of table + height of graph
        self.z = Decimal(self.max_top_elev) - Decimal(self.min_top_elev)
        self.height_row = (Decimal(self.z) * Decimal(0.97)) / Decimal(5)

        # Height of graph + table
        self.height_y = Decimal(self.z * 2)

    def _draw_start_node(self, node):
        """ Draw first node """

        # Get superior points
        s1x = -node.geom / 2
        s1y = node.top_elev
        s2x = node.geom / 2
        s2y = node.top_elev
        s3x = node.geom / 2
        s3y = node.top_elev - node.ymax + node.z1 + node.cat_geom

        # Get inferior points
        i1x = -node.geom / 2
        i1y = node.top_elev - node.ymax
        i2x = node.geom / 2
        i2y = node.top_elev - node.ymax
        i3x = node.geom / 2
        i3y = node.top_elev - node.ymax + node.z1

        # Create list points
        xinf = [s1x, i1x, i2x, i3x]
        yinf = [s1y, i1y, i2y, i3y]
        xsup = [s1x, s2x, s3x]
        ysup = [s1y, s2y, s3y]

        # draw first node bottom line
        plt.plot(xinf, yinf, zorder=100, linestyle=self._get_stylesheet(node.data_type)[0],
                 color=self._get_stylesheet(node.data_type)[1], linewidth=self._get_stylesheet(node.data_type)[2])

        # draw first node upper line
        plt.plot(xsup, ysup, zorder=100, linestyle=self._get_stylesheet(node.data_type)[0],
                 color=self._get_stylesheet(node.data_type)[1], linewidth=self._get_stylesheet(node.data_type)[2])

        self.first_top_x = 0
        self.first_top_y = node.top_elev

        # Save last points for first node
        self.slast = [s3x, s3y]
        self.ilast = [i3x, i3y]

        # Save last points for first node
        self.slast2 = [s3x, s3y]
        self.ilast2 = [i3x, i3y]

        # Fill table with start node values
        self._fill_guitar_text_node(0, 0)

        # Draw header
        self._draw_guitar_vertical_lines(node.start_point)
        self._fill_guitar_text_legend()
        self._draw_guitar_auxiliar_lines(0)

    def _draw_nodes(self, node, prev_node, index):
        """ Draw nodes between first and last node """

        z1 = prev_node.z2
        z2 = node.z1

        if node.node_1 is None:
            return

        # Get superior points
        s1x = self.slast[0]
        s1y = self.slast[1]

        if node.geom is None:
            node.geom = 0

        s2x = node.start_point - node.geom / 2
        s2y = node.top_elev - node.ymax + z1 + prev_node.cat_geom
        s3x = node.start_point - node.geom / 2
        s3y = node.top_elev
        s4x = node.start_point + node.geom / 2
        s4y = node.top_elev
        s5x = node.start_point + node.geom / 2
        s5y = node.top_elev - node.ymax + z2 + node.cat_geom

        # Get inferior points
        i1x = self.ilast[0]
        i1y = self.ilast[1]
        i2x = node.start_point - node.geom / 2
        i2y = node.top_elev - node.ymax + z1
        i3x = node.start_point - node.geom / 2
        i3y = node.top_elev - node.ymax
        i4x = node.start_point + node.geom / 2
        i4y = node.top_elev - node.ymax
        i5x = node.start_point + node.geom / 2
        i5y = node.top_elev - node.ymax + z2

        # Create arc list points
        xainf = [i1x, i2x]
        yainf = [i1y, i2y]
        xasup = [s1x, s2x]
        yasup = [s1y, s2y]

        # Create node list points
        xninf = [i2x, i3x, i4x, i5x]
        yninf = [i2y, i3y, i4y, i5y]

        if node.surface_type == 'TOP':
            xnsup = [s2x, s3x, s4x, s5x]
            ynsup = [s2y, s3y, s4y, s5y]
        else:
            xnsup = [s2x, s5x]
            ynsup = [s2y, s5y]

        # draw node bottom line
        plt.plot(xninf, yninf,
                 zorder=100,
                 linestyle=self._get_stylesheet(node.data_type)[0],
                 color=self._get_stylesheet(node.data_type)[1],
                 linewidth=self._get_stylesheet(node.data_type)[2])

        # draw node upper line
        plt.plot(xnsup, ynsup,
                 zorder=100,
                 linestyle=self._get_stylesheet(node.data_type)[0],
                 color=self._get_stylesheet(node.data_type)[1],
                 linewidth=self._get_stylesheet(node.data_type)[2])

        if self.lastnode_datatype == 'INTERPOLATED' or node.data_type == 'INTERPOLATED':
            data_type = 'INTERPOLATED'
        else:
            data_type = 'REAL'

        # draw arc bottom line
        plt.plot(xainf, yainf,
                 zorder=100,
                 linestyle=self._get_stylesheet(data_type)[0],
                 color=self._get_stylesheet(data_type)[1],
                 linewidth=self._get_stylesheet(data_type)[2])

        # draw arc upper line
        plt.plot(xasup, yasup,
                 zorder=100,
                 linestyle=self._get_stylesheet(data_type)[0],
                 color=self._get_stylesheet(data_type)[1],
                 linewidth=self._get_stylesheet(data_type)[2])

        self.node_top_x = node.start_point
        self.node_top_y = node.top_elev
        self.first_top_x = prev_node.start_point
        self.first_top_y = prev_node.top_elev

        # Draw guitar auxiliar lines
        self._draw_guitar_auxiliar_lines(node.start_point)

        # Fill table
        self._fill_guitar_text_node(node.start_point, index)

        # Save last points before the last node
        self.slast = [s5x, s5y]
        self.ilast = [i5x, i5y]
        self.lastnode_datatype = node.data_type

        # Save last points for draw ground
        self.slast2 = [s3x, s3y]
        self.ilast2 = [i3x, i3y]

    def _draw_terrain(self, index):
        # getting variables
        line_color = self.profile_json['body']['data']['stylesheet']['terrain']['color']
        line_style = self.profile_json['body']['data']['stylesheet']['terrain']['style']
        line_width = self.profile_json['body']['data']['stylesheet']['terrain']['width']

        # Draw marker
        if index == 1:
            plt.plot(self.first_top_x, self.first_top_y,
                     marker='|', color=line_color)
        else:
            plt.plot(self.node_top_x, self.node_top_y,
                     marker='|', color=line_color)

        # Draw line
        x = [self.first_top_x, self.node_top_x]
        y = [self.first_top_y, self.node_top_y]
        plt.plot(x, y, color=line_color,
                 linewidth=line_width, linestyle=line_style)

    def _fill_guitar_text_terrain(self, start_point, index):

        if str(self.links[index].surface_type) == 'VNODE':

            # Get stylesheet values
            text_color = self.profile_json['body']['data']['stylesheet']['guitar']['text']['color']
            text_weight = self.profile_json['body']['data']['stylesheet']['guitar']['text']['weight']

            # Fill top_elevation
            s = ' ' + '\n' + \
                str(self.links[index].descript['top_elev']) + '\n' + ' '
            xy = (Decimal(start_point), self.min_top_elev -
                  Decimal(self.height_row * Decimal(1.8) + self.height_row / 2))
            plt.annotate(s, xy=xy, fontsize=6, color=text_color, fontweight=text_weight, rotation='vertical',
                         horizontalalignment='center', verticalalignment='center')

            # Fill code
            plt.text(0 + start_point, self.min_top_elev - Decimal(self.height_row * Decimal(5) + self.height_row / 2),
                     self.links[index].descript['code'],
                     fontsize=7.5,
                     color=text_color, fontweight=text_weight,
                     horizontalalignment='center', verticalalignment='center')

            # Fill y_max
            plt.annotate(
                str(self.links[index].descript['ymax']),
                xy=(Decimal(0 + start_point),
                    self.min_top_elev - Decimal(self.height_row * Decimal(2.60) + self.height_row / 2)),
                fontsize=6,
                color=text_color, fontweight=text_weight,
                rotation='vertical', horizontalalignment='center', verticalalignment='center')

            # Fill elevation
            plt.annotate(
                str(self.links[index].descript['elev']),
                xy=(Decimal(0 + start_point),
                    self.min_top_elev - Decimal(self.height_row * Decimal(3.40) + self.height_row / 2)),
                fontsize=6,
                color=text_color, fontweight=text_weight,
                rotation='vertical', horizontalalignment='center', verticalalignment='center')

            # Fill total length
            plt.annotate(str(self.links[index].descript['total_distance']),
                         xy=(Decimal(0 + start_point),
                             self.min_top_elev - Decimal(self.height_row * Decimal(4.20) + self.height_row / 2)),
                         fontsize=6,
                         color=text_color, fontweight=text_weight,
                         rotation='vertical', horizontalalignment='center', verticalalignment='center')

    def _fill_guitar_text_node(self, start_point, index):

        # Get stylesheet values
        text_color = self.profile_json['body']['data']['stylesheet']['guitar']['text']['color']
        text_weight = self.profile_json['body']['data']['stylesheet']['guitar']['text']['weight']

        # Fill top_elevation
        s = ' ' + '\n' + \
            str(self.nodes[index].descript['top_elev']) + '\n' + ' '
        xy = (Decimal(start_point), self.min_top_elev -
              Decimal(self.height_row * Decimal(1.8) + self.height_row / 2))
        plt.annotate(s, xy=xy, fontsize=6, color=text_color, fontweight=text_weight, rotation='vertical',
                     horizontalalignment='center', verticalalignment='center')
        # Fill code
        plt.text(0 + start_point, self.min_top_elev - Decimal(self.height_row * 5 + self.height_row / 2),
                 self.nodes[index].descript['code'], fontsize=7.5, color=text_color, fontweight=text_weight,
                 horizontalalignment='center', verticalalignment='center')

        # Node init
        if index == 0:

            y1 = self.nodes[0].y1
            elev1 = self.nodes[0].elev1

            # Fill y_max
            plt.annotate(' ' + '\n' + str(self.nodes[0].descript['ymax']) + '\n' + str(y1),
                         xy=(Decimal(0 + start_point),
                             self.min_top_elev - Decimal(self.height_row * Decimal(2.60) + self.height_row / 2)),
                         fontsize=6,
                         color=text_color, fontweight=text_weight,
                         rotation='vertical', horizontalalignment='center', verticalalignment='center')

            # Fill elevation
            plt.annotate(' ' + '\n' + str(self.nodes[0].descript['elev']) + '\n' + str(elev1),
                         xy=(Decimal(0 + start_point),
                             self.min_top_elev - Decimal(self.height_row * Decimal(3.40) + self.height_row / 2)),
                         fontsize=6,
                         color=text_color, fontweight=text_weight,
                         rotation='vertical', horizontalalignment='center', verticalalignment='center')

            # Fill total length
            plt.annotate(str(self.nodes[index].descript['total_distance']),
                         xy=(Decimal(0 + start_point),
                             self.min_top_elev - Decimal(
                                 self.height_row * Decimal(4.20) + self.height_row / 2)),
                         fontsize=6,
                         color=text_color, fontweight=text_weight,
                         rotation='vertical', horizontalalignment='center', verticalalignment='center')

        # Nodes between init and end
        elif index < self.n - 1:

            # defining variables
            y2_prev = self.nodes[index - 1].y2
            elev2_prev = self.nodes[index - 1].elev2
            y1 = self.nodes[index].y1
            elev1 = self.nodes[index].elev1

            if y2_prev in (None, 'None') or self.nodes[index].descript['ymax'] in (None, 'None') or y1 in (None, 'None')\
                    or elev2_prev in (None, 'None') or self.nodes[index].descript['elev'] in (None, 'None') or elev1 in (None, 'None'):
                self.none_values.append(self.nodes[index].descript['code'])

            # Fill y_max
            plt.annotate(
                str(y2_prev) + '\n' +
                str(self.nodes[index].descript['ymax']) + '\n' + str(y1),
                xy=(Decimal(0 + start_point),
                    self.min_top_elev - Decimal(self.height_row * Decimal(2.60) + self.height_row / 2)),
                fontsize=6,
                color=text_color, fontweight=text_weight,
                rotation='vertical', horizontalalignment='center', verticalalignment='center')

            # Fill elevation
            plt.annotate(
                str(elev2_prev) + '\n' +
                str(self.nodes[index].descript['elev']) + '\n' + str(elev1),
                xy=(Decimal(0 + start_point),
                    self.min_top_elev - Decimal(self.height_row * Decimal(3.40) + self.height_row / 2)),
                fontsize=6,
                color=text_color, fontweight=text_weight,
                rotation='vertical', horizontalalignment='center', verticalalignment='center')

            # Fill total length
            plt.annotate(str(self.nodes[index].descript['total_distance']),
                         xy=(Decimal(0 + start_point),
                         self.min_top_elev - Decimal(self.height_row * Decimal(4.20) + self.height_row / 2)),
                         fontsize=6,
                         color=text_color, fontweight=text_weight,
                         rotation='vertical', horizontalalignment='center', verticalalignment='center')
        # Node end
        elif index == self.n - 1:

            # Fill y_max
            plt.annotate(
                str(self.nodes[index - 1].y2) + '\n' +
                str(self.nodes[index].descript['ymax']),
                xy=(Decimal(0 + start_point),
                    self.min_top_elev - Decimal(self.height_row * Decimal(2.60) + self.height_row / 2)),
                fontsize=6,
                color=text_color, fontweight=text_weight,
                rotation='vertical', horizontalalignment='center', verticalalignment='center')

            # Fill elevation
            plt.annotate(
                str(self.nodes[index - 1].elev2) + '\n' +
                str(self.nodes[index].descript['elev']),
                xy=(Decimal(0 + start_point),
                    self.min_top_elev - Decimal(self.height_row * Decimal(3.40) + self.height_row / 2)),
                fontsize=6,
                color=text_color, fontweight=text_weight,
                rotation='vertical', horizontalalignment='center', verticalalignment='center')

            # Fill total length
            plt.annotate(str(self.nodes[index].descript['total_distance']),
                         xy=(Decimal(0 + start_point),
                         self.min_top_elev - Decimal(self.height_row * Decimal(4.20) + self.height_row / 2)),
                         fontsize=6,
                         color=text_color, fontweight=text_weight,
                         rotation='vertical', horizontalalignment='center', verticalalignment='center')

        # Fill diameter and slope / length
        if index != self.n - 1:

            # Fill diameter
            center = self.gis_length[index + 1] / 2
            plt.text(center + start_point, self.min_top_elev - 1 * self.height_row - Decimal(0.35) * self.height_row,
                     self.arc_catalog[index],
                     fontsize=7.5,
                     color=text_color, fontweight=text_weight,
                     horizontalalignment='center')  # PUT IN THE MIDDLE PARAMETRIZATION

            # Fill slope / length
            plt.text(center + start_point, self.min_top_elev - 1 * self.height_row - Decimal(0.68) * self.height_row,
                     self.arc_dimensions[index],
                     fontsize=7.5,
                     color=text_color, fontweight=text_weight,
                     horizontalalignment='center')  # PUT IN THE MIDDLE PARAMETRIZATION

    def _fill_guitar_text_legend(self):

        # Get stylesheet values
        text_color = self.profile_json['body']['data']['stylesheet']['guitar']['text']['color']
        text_weight = self.profile_json['body']['data']['stylesheet']['guitar']['text']['weight']
        title_color = self.profile_json['body']['data']['stylesheet']['title']['text']['color']
        title_weight = self.profile_json['body']['data']['stylesheet']["title"]['text']['weight']
        title_size = self.profile_json['body']['data']['stylesheet']["title"]['text']['size']

        legend = self.profile_json['body']['data']['legend']
        c = (self.fix_x - self.fix_x * Decimal(0.2)) / 2
        plt.text(-(c + self.fix_x * Decimal(0.2)),
                 self.min_top_elev - 1 * self.height_row -
                 Decimal(0.35) * self.height_row, legend['catalog'],
                 fontsize=7.5, color=text_color, fontweight=text_weight, horizontalalignment='center')

        plt.text(-(c + self.fix_x * Decimal(0.2)),
                 self.min_top_elev - 1 * self.height_row -
                 Decimal(0.68) * self.height_row, legend['dimensions'],
                 fontsize=7.5, color=text_color, fontweight=text_weight, horizontalalignment='center')

        c = (self.fix_x * Decimal(0.25)) / 2
        plt.text(-(c + self.fix_x * Decimal(0.74)),
                 self.min_top_elev -
                 Decimal(2) * self.height_row - self.height_row *
                 3 / 2, legend['ordinates'],
                 fontsize=7.5, color=text_color, fontweight=text_weight, rotation='vertical',
                 horizontalalignment='center', verticalalignment='center')

        plt.text(-self.fix_x * Decimal(0.70), self.min_top_elev - Decimal(1.85) * self.height_row - self.height_row / 2,
                 legend['topelev'], fontsize=7.5, color=text_color, fontweight=text_weight, verticalalignment='center')

        plt.text(-self.fix_x * Decimal(0.70), self.min_top_elev - Decimal(2.65) * self.height_row - self.height_row / 2,
                 legend['ymax'], fontsize=7.5, color=text_color, fontweight=text_weight, verticalalignment='center')

        plt.text(-self.fix_x * Decimal(0.70), self.min_top_elev - Decimal(3.45) * self.height_row - self.height_row / 2,
                 legend['elev'], fontsize=7.5, color=text_color, fontweight=text_weight, verticalalignment='center')

        plt.text(-self.fix_x * Decimal(0.70), self.min_top_elev - Decimal(4.25) * self.height_row - self.height_row / 2,
                 legend['distance'], fontsize=7.5, color=text_color, fontweight=text_weight, verticalalignment='center')

        c = (self.fix_x - self.fix_x * Decimal(0.2)) / 2
        plt.text(-(c + self.fix_x * Decimal(0.2)),
                 self.min_top_elev -
                 Decimal(self.height_row * 5 +
                         self.height_row / 2), legend['code'],
                 fontsize=7.5, color=text_color, fontweight=text_weight, horizontalalignment='center',
                 verticalalignment='center')

        title = self.params['title']
        if (title == ""):
            title = f"PROFILE {self.nodes[0].node_id} - {self.nodes[len(self.nodes) - 1].node_id}"

        plt.text(-self.fix_x * Decimal(1), self.min_top_elev - Decimal(5.75) * self.height_row - self.height_row / 2,
                 title, fontsize=title_size, color=title_color, fontweight=title_weight,
                 verticalalignment='center')
        
        date = self.params['date']
        if (date == ""):
            date = datetime.datetime.today().strftime('%Y/%m/%d')
        else:
            actual_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            date = actual_date.strftime('%Y/%m/%d')
        plt.text(-self.fix_x * Decimal(1), self.min_top_elev - Decimal(6) * self.height_row - self.height_row / 2,
                 date, fontsize=title_size * 0.7, color=title_color, fontweight=title_weight, verticalalignment='center')

    def _draw_guitar_auxiliar_lines(self, start_point, first_vl=True):
        """ Draw marks for each node """

        # Get stylesheet
        auxline_color = self.profile_json['body']['data']['stylesheet']['guitar']['auxiliarlines']['color']
        auxline_style = self.profile_json['body']['data']['stylesheet']['guitar']['auxiliarlines']['style']
        auxline_width = self.profile_json['body']['data']['stylesheet']['guitar']['auxiliarlines']['width']

        if first_vl:  # separator for first slope / length (only for nodes)
            # Vertical line [0,0]
            x = [start_point, start_point]
            y = [self.min_top_elev - 1 * self.height_row,
                 self.min_top_elev - Decimal(1.9) * self.height_row]
            plt.plot(x, y, linestyle=auxline_style, color=auxline_color,
                     linewidth=auxline_width, zorder=100)

        # Vertical lines
        x = [start_point, start_point]
        y = [self.min_top_elev - Decimal(1.90) * self.height_row,
             self.min_top_elev - Decimal(2.05) * self.height_row]
        plt.plot(x, y, linestyle=auxline_style, color=auxline_color,
                 linewidth=auxline_width, zorder=100)

        x = [start_point, start_point]
        y = [self.min_top_elev - Decimal(2.60) * self.height_row,
             self.min_top_elev - Decimal(2.85) * self.height_row]
        plt.plot(x, y, linestyle=auxline_style, color=auxline_color,
                 linewidth=auxline_width, zorder=100)

        x = [start_point, start_point]
        y = [self.min_top_elev - Decimal(3.4) * self.height_row,
             self.min_top_elev - Decimal(3.65) * self.height_row]
        plt.plot(x, y, linestyle=auxline_style, color=auxline_color,
                 linewidth=auxline_width, zorder=100)

        x = [start_point, start_point]
        y = [self.min_top_elev - Decimal(4.20) * self.height_row,
             self.min_top_elev - Decimal(4.45) * self.height_row]
        plt.plot(x, y, linestyle=auxline_style, color=auxline_color,
                 linewidth=auxline_width, zorder=100)

        x = [start_point, start_point]
        y = [self.min_top_elev - Decimal(5) * self.height_row,
             self.min_top_elev - Decimal(5.25) * self.height_row]
        plt.plot(x, y, linestyle=auxline_style, color=auxline_color,
                 linewidth=auxline_width, zorder=100)

        x = [start_point, start_point]
        y = [self.min_top_elev - Decimal(5.85) * self.height_row,
             self.min_top_elev - Decimal(5.7) * self.height_row]
        plt.plot(x, y, linestyle=auxline_style, color=auxline_color,
                 linewidth=auxline_width, zorder=100)

    def _draw_guitar_vertical_lines(self, start_point):
        """ Draw fixed part of table """

        # Get stylesheet
        line_color = self.profile_json['body']['data']['stylesheet']['guitar']['lines']['color']
        line_style = self.profile_json['body']['data']['stylesheet']['guitar']['lines']['style']
        line_width = self.profile_json['body']['data']['stylesheet']['guitar']['lines']['width']

        # Vertical line [-1,0]
        # x = [start_point - self.fix_x * Decimal(0.2), start_point - self.fix_x * Decimal(0.2)]
        # y = [self.min_top_elev - 1 * self.height_row, self.min_top_elev - Decimal(5.85) * self.height_row]
        # plt.plot(x, y, linestyle=line_style, color=line_color, linewidth=line_width, zorder=100)

        # Vertical line [-2,0]
        x = [start_point - self.fix_x *
             Decimal(0.75), start_point - self.fix_x * Decimal(0.75)]
        y = [self.min_top_elev - Decimal(1.9) * self.height_row,
             self.min_top_elev - Decimal(5.10) * self.height_row]
        plt.plot(x, y, linestyle=line_style, color=line_color,
                 linewidth=line_width, zorder=100)

        # Vertical line [-3,0]
        x = [start_point - self.fix_x, start_point - self.fix_x]
        y = [self.min_top_elev - 1 * self.height_row,
             self.min_top_elev - Decimal(5.85) * self.height_row]
        plt.plot(x, y, linestyle=line_style, color=line_color,
                 linewidth=line_width, zorder=100)

    def _draw_end_node(self, node, prev_node, index):
        """
        draws last arc and nodes of profile
        :param node:
        :param prev_node:
        :param index:
        :return:
        """

        s1x = self.slast[0]
        s1y = self.slast[1]

        s2x = node.start_point - node.geom / 2
        s2y = node.top_elev - node.ymax + prev_node.z2 + prev_node.cat_geom
        s3x = node.start_point - node.geom / 2
        s3y = node.top_elev
        s4x = node.start_point + node.geom / 2
        s4y = node.top_elev

        # Get inferior points
        i1x = self.ilast[0]
        i1y = self.ilast[1]
        i2x = node.start_point - node.geom / 2
        i2y = node.top_elev - node.ymax + prev_node.z2
        i3x = node.start_point - node.geom / 2
        i3y = node.top_elev - node.ymax
        i4x = node.start_point + node.geom / 2
        i4y = node.top_elev - node.ymax

        # Create arc list points
        xainf = [i1x, i2x]
        yainf = [i1y, i2y]
        xasup = [s1x, s2x]
        yasup = [s1y, s2y]

        # Create node list points
        xninf = [i2x, i3x, i4x]
        yninf = [i2y, i3y, i4y]
        xnsup = [s2x, s3x, s4x, i4x]
        ynsup = [s2y, s3y, s4y, i4y]

        # draw node bottom line
        plt.plot(xninf, yninf,
                 zorder=100,
                 linestyle=self._get_stylesheet(node.data_type)[0],
                 color=self._get_stylesheet(node.data_type)[1],
                 linewidth=self._get_stylesheet(node.data_type)[2])

        # draw node upper line
        plt.plot(xnsup, ynsup,
                 zorder=100,
                 linestyle=self._get_stylesheet(node.data_type)[0],
                 color=self._get_stylesheet(node.data_type)[1],
                 linewidth=self._get_stylesheet(node.data_type)[2])

        # draw arc bottom line
        plt.plot(xainf, yainf,
                 zorder=100,
                 linestyle=self._get_stylesheet(self.lastnode_datatype)[0],
                 color=self._get_stylesheet(self.lastnode_datatype)[1],
                 linewidth=self._get_stylesheet(self.lastnode_datatype)[2])

        # draw arc upper line
        plt.plot(xasup, yasup,
                 zorder=100,
                 linestyle=self._get_stylesheet(self.lastnode_datatype)[0],
                 color=self._get_stylesheet(self.lastnode_datatype)[1],
                 linewidth=self._get_stylesheet(self.lastnode_datatype)[2])

        self.first_top_x = self.slast2[0]
        self.first_top_y = self.slast2[1]

        self.node_top_x = node.start_point
        self.node_top_y = node.top_elev

        # Draw table-marks
        self._draw_guitar_auxiliar_lines(node.start_point)

        # Fill table
        self._fill_guitar_text_node(node.start_point, index)

        # Reset lastnode_datatype
        self.lastnode_datatype = 'REAL'

    def _get_stylesheet(self, data_type='REAL'):

        # TODO: Enhance this function, manage all case for data_type, harmonie REAL/TOP-REAL...
        # getting stylesheet
        line_style = ''
        line_color = ''
        line_width = ''
        if data_type in ('REAL', 'TOP-REAL'):
            line_style = self.profile_json['body']['data']['stylesheet']['infra']['real']['style']
            line_color = self.profile_json['body']['data']['stylesheet']['infra']['real']['color']
            line_width = self.profile_json['body']['data']['stylesheet']['infra']['real']['width']
        elif data_type == 'INTERPOLATED':
            line_style = self.profile_json['body']['data']['stylesheet']['infra']['interpolated']['style']
            line_color = self.profile_json['body']['data']['stylesheet']['infra']['interpolated']['color']
            line_width = self.profile_json['body']['data']['stylesheet']['infra']['interpolated']['width']

        return line_style, line_color, line_width

    def _draw_guitar_horitzontal_lines(self):
        """
        Draw horitzontal lines of table
        :return:
        """
        line_color = self.profile_json['body']['data']['stylesheet']['guitar']['lines']['color']
        line_style = self.profile_json['body']['data']['stylesheet']['guitar']['lines']['style']
        line_width = self.profile_json['body']['data']['stylesheet']['guitar']['lines']['width']

        self._set_guitar_parameters()

        # Draw upper horizontal lines (long ones)
        x = [self.nodes[self.n - 1].start_point,
             self.nodes[0].start_point - self.fix_x]
        y = [self.min_top_elev - self.height_row,
             self.min_top_elev - self.height_row]
        plt.plot(x, y, color=line_color, linestyle=line_style,
                 linewidth=line_width, zorder=100)

        x = [self.nodes[self.n - 1].start_point,
             self.nodes[0].start_point - self.fix_x]
        y = [self.min_top_elev - Decimal(1.9) * self.height_row,
             self.min_top_elev - Decimal(1.9) * self.height_row]
        plt.plot(x, y, color=line_color, linestyle=line_style,
                 linewidth=line_width, zorder=100)

        # Draw middle horizontal lines (short ones)
        x = [self.nodes[self.n - 1].start_point,
             self.nodes[0].start_point - self.fix_x * Decimal(0.75)]
        y = [self.min_top_elev - Decimal(2.70) * self.height_row,
             self.min_top_elev - Decimal(2.70) * self.height_row]
        plt.plot(x, y, color=line_color, linestyle=line_style,
                 linewidth=line_width, zorder=100)
        x = [self.nodes[self.n - 1].start_point,
             self.nodes[0].start_point - self.fix_x * Decimal(0.75)]
        y = [self.min_top_elev - Decimal(3.50) * self.height_row,
             self.min_top_elev - Decimal(3.50) * self.height_row]
        plt.plot(x, y, color=line_color, linestyle=line_style,
                 linewidth=line_width, zorder=100)
        x = [self.nodes[self.n - 1].start_point,
             self.nodes[0].start_point - self.fix_x * Decimal(0.75)]
        y = [self.min_top_elev - Decimal(4.30) * self.height_row,
             self.min_top_elev - Decimal(4.30) * self.height_row]
        plt.plot(x, y, color=line_color, linestyle=line_style,
                 linewidth=line_width, zorder=100)

        # Draw lower horizontal lines (long ones)
        x = [self.nodes[self.n - 1].start_point,
             self.nodes[0].start_point - self.fix_x]
        y = [self.min_top_elev - Decimal(5.10) * self.height_row,
             self.min_top_elev - Decimal(5.10) * self.height_row]
        plt.plot(x, y, color=line_color, linestyle=line_style,
                 linewidth=line_width, zorder=100)
        x = [self.nodes[self.n - 1].start_point,
             self.nodes[0].start_point - self.fix_x]
        y = [self.min_top_elev - Decimal(5.85) * self.height_row,
             self.min_top_elev - Decimal(5.85) * self.height_row]
        plt.plot(x, y, color=line_color, linestyle=line_style,
                 linewidth=line_width, zorder=100)

    def _draw_grid(self):

        # get values for lines
        line_color = self.profile_json['body']['data']['stylesheet']['grid']['lines']['color']
        line_style = self.profile_json['body']['data']['stylesheet']['grid']['lines']['style']
        line_width = self.profile_json['body']['data']['stylesheet']['grid']['lines']['width']

        # get values for boundary
        boundary_color = self.profile_json['body']['data']['stylesheet']['grid']['boundary']['color']
        boundary_style = self.profile_json['body']['data']['stylesheet']['grid']['boundary']['style']
        boundary_width = self.profile_json['body']['data']['stylesheet']['grid']['boundary']['width']

        # get values for text
        text_color = self.profile_json['body']['data']['stylesheet']['grid']['text']['color']
        text_weight = self.profile_json['body']['data']['stylesheet']['grid']['text']['weight']

        start_point = self.nodes[self.n - 1].start_point
        geom1 = self.nodes[self.n - 1].geom

        # Draw main text
        try:
            reference_plane = self.profile_json['body']['data']['legend']['referencePlane']
        except KeyError:
            reference_plane = "REFERENCE"
        plt.text(-self.fix_x * Decimal(1), self.min_top_elev - Decimal(0.5) * self.height_row - self.height_row / 2,
                 f"{reference_plane}: {round(self.min_top_elev - 1 * self.height_row, 2)}\n ",
                 fontsize=8.5,
                 color=text_color, fontweight=text_weight,
                 verticalalignment='center')

        # Draw boundary
        x = [0, 0]
        y = [self.min_top_elev - 1 * self.height_row,
             int(math.ceil(self.max_top_elev) + 1)]
        plt.plot(x, y, color=boundary_color, linestyle=boundary_style,
                 linewidth=boundary_width, zorder=100)
        x = [start_point, start_point]
        y = [self.min_top_elev - 1 * self.height_row,
             int(math.ceil(self.max_top_elev) + 1)]
        plt.plot(x, y, color=boundary_color, linestyle=boundary_style,
                 linewidth=boundary_width, zorder=100)
        x = [0, start_point]
        y = [int(math.ceil(self.max_top_elev) + 1),
             int(math.ceil(self.max_top_elev) + 1)]
        plt.plot(x, y, color=boundary_color, linestyle=boundary_style,
                 linewidth=boundary_width, zorder=100)

        # Draw horitzontal lines
        y = int(math.ceil(self.min_top_elev - 1 * self.height_row))
        x = int(math.floor(self.max_top_elev))
        if x % 2 == 0:
            x = x + 2
        else:
            x = x + 1

        for i in range(y, x):
            if i % 2 == 0:
                x1 = [0, start_point]
                y1 = [i, i]
            else:
                i = i + 1
                x1 = [0, start_point]
                y1 = [i, i]

            # set line
            plt.plot(x1, y1, color=line_color, linestyle=line_style,
                     linewidth=line_width, zorder=1)

            # set texts
            plt.text(0 - Decimal(geom1) * Decimal(1.5), i, str(i),
                     fontsize=7.5,
                     color=text_color, fontweight=text_weight,
                     horizontalalignment='right', verticalalignment='center')
            plt.text(Decimal(start_point) + Decimal(geom1) * Decimal(1.5), i, str(i),
                     fontsize=7.5,
                     color=text_color, fontweight=text_weight,
                     horizontalalignment='left', verticalalignment='center')

        # Draw vertical lines
        x = int(math.floor(start_point))
        for i in range(50, x, 50):
            x1 = [i, i]
            y1 = [self.min_top_elev - 1 * self.height_row,
                  int(math.ceil(self.max_top_elev) + 1)]

            # set line
            plt.plot(x1, y1, color=line_color, linestyle=line_style,
                     linewidth=line_width, zorder=1)

            # set texts
            plt.annotate(str(i) + '\n' + ' ', xy=(i, int(math.ceil(self.max_top_elev) + 1)),
                         fontsize=6.5, color=text_color, fontweight=text_weight, horizontalalignment='center')


def handle_db_result(result: dict) -> Response:
    response = {}
    if 'results' not in result or result['results'] > 0:
        # form_xml = create_xml_form_v3(result)
        response = result
    return jsonify(response)


def get_profiletool_ui() -> str:
    return open("profile/ui/profile_tool.ui").read()


def generate_profile_svg(result, params):
    print(result)
    
    svg_object = GwGenerateSvg(result, result['body']['data']['arc'], result['body']['data']['node'],
                  result['body']['data']['terrain'], params)

    return svg_object.img_path
