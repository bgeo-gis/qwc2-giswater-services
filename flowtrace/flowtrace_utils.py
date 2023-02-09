from flask import jsonify, Response

def handle_db_result(result: dict) -> Response:
    response = {}
    if 'results' not in result or result['results'] > 0:
        response = result
    return jsonify(response)
