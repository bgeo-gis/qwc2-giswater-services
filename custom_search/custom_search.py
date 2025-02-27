"""
Copyright © 2025 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""

import utils
import re
import psycopg2

import json
import traceback
import sqlalchemy

from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required
from qwc_services_core.auth import optional_auth, get_identity
from sqlalchemy import text, exc

custom_search_bp = Blueprint('custom_search', __name__)


# make themes choosable in search combo
THEMES_CHOOSABLE = True
# zoom to this bbox if a layer is chosen in the search combo [minx, miny, maxx, maxy]
# set to None if extent should not be changed
MAX_BBOX = None

@custom_search_bp.route('/search', methods=['GET'])
@jwt_required()
def search():
    # config = utils.get_config()
    # log = utils.create_log(__name__)

    theme = request.args["theme"]

    searchtables = []; # enter your default searchtable(s) here
    if "searchtables" in request.args:
        searchtables.extend(request.args["searchtables"].split(','))
    querystring = request.args["query"]
    #strip away leading and trailing whitespaces
    querystring = querystring.strip()
    #split on whitespaces
    regex = re.compile(r'\s+')
    querystrings = regex.split(querystring)

    searchtableLength = len(searchtables)
    querystringsLength = len(querystrings)
    errorText = ''

    # any searchtable given?
    # if searchtableLength == 0:
    #     errorText += 'error: no search table'
    #     # write the error message to the error.log
    #     print >> environ['wsgi.errors'], "%s" % errorText
    #     response_headers = [('Content-type', 'text/plain'),
    #                         ('Content-Length', str(len(errorText)))]
    #     start_response('500 INTERNAL SERVER ERROR', response_headers)

    #     return [errorText]

    data = {}
    sql = ""
    for i in range(searchtableLength):
        sql += (
            "SELECT displaytext, '"
            + searchtables[i]
            + r"' AS searchtable, search_category, substring(search_category from 4) AS searchcat_trimmed, showlayer, "
        )
        sql += "'['||replace(regexp_replace(BOX2D(the_geom)::text,'BOX\\(|\\)','','g'),' ',',')||']'::text AS bbox "
        sql += "FROM " + searchtables[i] + " WHERE "

        for j in range(querystringsLength):
            key = f"query{j}"
            data[key] = f"%{querystrings[j]}%"
            sql += f"unaccent(searchstring) ILIKE unaccent(:{key})"

            if j < querystringsLength - 1:
                sql += " AND "

        if i < searchtableLength - 1:
            sql += " UNION "

    sql += " ORDER BY search_category ASC, displaytext ASC;"
    # Convert sql to SQLAlchemy text
    sql = text(sql)

    db = utils.get_db(theme)
    with db.begin() as conn:
        if conn == None:
            return [""]

        rowData = []
        result = conn.execute(sql, data)
        rows = result.mappings().all()

        lastSearchCategory = ''
        for row in rows:
            if lastSearchCategory != row['search_category']:
                rowData.append({
                    "displaytext": row['searchcat_trimmed'],
                    "searchtable": None,
                    "bbox": MAX_BBOX,
                    "showlayer": row['showlayer'],
                    "selectable": "1" if THEMES_CHOOSABLE else "0"
                })
                lastSearchCategory = row['search_category']
            rowData.append({
                "displaytext": row['displaytext'],
                "searchtable": row['searchtable'],
                "bbox": row['bbox'],
                "showlayer": row['showlayer'],
                "selectable": "1"
            })
        resultString = '{"results": ' + json.dumps(rowData) + '}'
        resultString = resultString.replace('"bbox": "[', '"bbox": [').replace(']",', '],')

        #we need to add the name of the callback function if the parameter was specified
        if "cb" in request.args:
            resultString = request.args["cb"] + '(' + resultString + ')'

        response = Response(
            resultString, "200 OK", [("Content-type", "application/javascript"), ("Content-length", str(len(resultString)))]
        )

        return response

@custom_search_bp.route('/searchGeom', methods=['GET'])
@jwt_required()
def searchGeom():
    searchtable = request.args["searchtable"]
    displaytext = request.args["displaytext"]
    theme = request.args["theme"]

    #sanitize
    sql = text("SELECT COALESCE(ST_AsText(the_geom), 'nogeom') AS geom FROM " + searchtable + " WHERE displaytext = :displaytext")
    result = "nogeom"
    if searchtable != "" and searchtable != "null":
        db = utils.get_db(theme)

        with db.begin() as conn:
            if conn == None:
                return [""]

            conn = conn.execution_options(stream_results=True)

            row = conn.execute(sql, {'displaytext': displaytext}).fetchone()
            if row is not None:
                result = row[0]

        response = Response(result,"200 OK",[("Content-type","text/plain"),("Content-length", str(len(result)) )])
        return response