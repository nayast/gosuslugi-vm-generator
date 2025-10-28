import json
from typing import Dict, List, Any, Union

def parse_json_scheme(schema):
    def traverse(node, path=""):
        ids = []
        if isinstance(node, dict):
            if 'id' in node:
                ids.append(f"{path}.{node['id']}" if path else node['id'])
            for key, value in node.items():
                new_path = f"{path}.{key}" if path else key
                ids.extend(traverse(value, new_path))
        elif isinstance(node, list):
            for item in node:
                ids.extend(traverse(item, path))
        return ids

    if isinstance(schema, str):
        with open(schema, 'r') as f:
            schema = json.load(f)

    return traverse(schema)