import utils

from flask import jsonify, Response

def handle_db_result(result: dict, theme: str) -> Response:
    response = {}
    if not result:
        return jsonify({"message": "DB returned null"})
    if 'results' not in result or result['results'] > 0:
        layer_columns = {}
        db_layers = utils.get_db_layers(theme)
        
        for k, v in db_layers.items():
            if v in result['body']['data']['layerColumns']:
                layer_columns[k] = result['body']['data']['layerColumns'][v]

        response = {
            "feature": {},
            "data": {
                #"userValues": result['body']['data']['userValues'],
                #"geometry": result['body']['data']['geometry'],
                "date_from": result['body']['data']['date_from'],
                "date_to": result['body']['data']['date_to'],
                "layerColumns": layer_columns
            },
            "form": {},
            "form_xml": None
        }
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
