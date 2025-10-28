from lxml import etree

def parse_xsd_element_names(xsd_path):
    """
    Возвращает упорядоченный список полных путей к элементам от корня.
    Более точная версия с учетом структуры XSD.
    """
    ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
    tree = etree.parse(str(xsd_path))

    all_paths = []

    def process_element(element, current_path=""):
        """Обрабатывает элемент и его дочерние элементы"""
        element_name = element.get("name")
        if not element_name:
            return

        # Строим новый путь
        new_path = f"{current_path}/{element_name}" if current_path else element_name
        all_paths.append(new_path)

        # Ищем complexType этого элемента
        complex_type = element.find("./xs:complexType", namespaces=ns)
        if complex_type is not None:
            # Обрабатываем все элементы внутри complexType
            process_complex_type(complex_type, new_path)

        # Проверяем, ссылается ли элемент на named complexType
        type_attr = element.get("type")
        if type_attr:
            # Ищем named complexType в схеме
            type_name = type_attr.split(":")[-1] if ":" in type_attr else type_attr
            named_type = tree.xpath(f"/xs:schema/xs:complexType[@name='{type_name}']", namespaces=ns)
            if named_type:
                process_complex_type(named_type[0], new_path)

    def process_complex_type(complex_type, parent_path):
        """Обрабатывает complexType и его дочерние элементы"""
        # Ищем sequence
        sequence = complex_type.find("./xs:sequence", namespaces=ns)
        if sequence is not None:
            for child_element in sequence.findall("./xs:element[@name]", namespaces=ns):
                process_element(child_element, parent_path)

        # Также проверяем другие возможные контейнеры
        for container in complex_type.xpath("./xs:sequence | ./xs:all | ./xs:choice", namespaces=ns):
            for child_element in container.findall("./xs:element[@name]", namespaces=ns):
                process_element(child_element, parent_path)

    # Начинаем с корневых элементов
    for root_element in tree.xpath("/xs:schema/xs:element[@name]", namespaces=ns):
        process_element(root_element)

    # Удаляем дубликаты, сохраняя порядок
    seen = set()
    ordered_paths = []
    for path in all_paths:
        if path not in seen:
            seen.add(path)
            ordered_paths.append(path)

    return ordered_paths



