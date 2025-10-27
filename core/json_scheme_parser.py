
import json

def parse_json_scheme(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    fields = _get_fields(data)
    return fields

def _get_fields(_value):
    fields = []
    if isinstance(_value, dict):
        if _value.get("id"):
            return [_value["id"],]
        for key, value in _value.items():
            fields += _get_fields(value)

    elif isinstance(_value, list):
        for value in _value:
            fields += _get_fields(value)
    else:
        return []
    return fields