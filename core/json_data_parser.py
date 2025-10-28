import json
import os

def parse_json_scheme(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    fields = dict_to_fields(data)

    return fields

def dict_to_fields(_dict:dict) -> dict:
    fields = {}
    for key, value in _dict.items():
        if isinstance(value, dict):
            fields.update(dict_to_fields(value))
        # elif isinstance(value, list):
        #     print("не обработано (list)")
        else:
            fields[key]=value
    return fields


