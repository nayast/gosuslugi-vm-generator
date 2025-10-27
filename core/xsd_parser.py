import xml.etree.ElementTree as ET

def get_all_xsd_fields(xsd_file_path: str) -> list:
    with open(xsd_file_path, 'r', encoding='utf-8') as file:
        xsd_content = file.read()

    fields = []
    root = ET.fromstring(xsd_content)

    # Ищем все элементы с атрибутом name
    for element in root.iter():
        if 'element' in element.tag:
            field_name = element.get('name')
            if field_name and field_name not in fields:
                fields.append(field_name)

    return sorted(fields)