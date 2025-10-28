
import json


def parse_json_scheme(schema):
    def traverse(node, path=""):
        ids = []
        if isinstance(node, dict):
            if 'id' in node:
                # Сохраняем текущий id как часть пути для вложенных полей
                current_id = node['id']
                full_path = f"{path}.{current_id}" if path else current_id
                ids.append(full_path)

            # Обрабатываем вложенные fields с правильным путем
            if 'fields' in node:
                current_path = f"{path}.{node['id']}" if path and 'id' in node else (
                    node['id'] if 'id' in node else path)
                ids.extend(traverse(node['fields'], current_path))

            # Обрабатываем остальные поля
            for key, value in node.items():
                if key != 'fields' and key != 'id':
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