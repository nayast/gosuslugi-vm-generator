def match_fields(xsd_fields, json_paths):
    json_lower = [p.lower() for p in json_paths]

    for field in xsd_fields:
        full = field["path"]
        parts = full.lower().split(".")

        assigned = None

        # Пробуем постепенно сокращать путь
        for cut in range(len(parts)):
            shortened = ".".join(parts[cut:])  # пример: ['person','email'] → 'email'
            if shortened in json_lower:
                idx = json_lower.index(shortened)
                assigned = json_paths[idx]
                break

        field["json_path"] = assigned  # добавляем к структуре

    return xsd_fields
