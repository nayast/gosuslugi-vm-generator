import json
import os

def parse_json_scheme(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    file_name = os.path.basename(file_path)

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

def print_json_fields(fields, name="name"):
    print(f"Имя файла - {name}")
    for key, value in fields.items():
        print_json_field(key, value)
def print_json_field(key, value):
    print(f"{key}:{value}")

