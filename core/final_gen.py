import os
from lxml import etree

def get_schema_elements_and_types(xsd_path):
    try:
        with open(xsd_path, 'r', encoding='utf-8') as f:
            schema_doc = etree.parse(f)
    except etree.XMLSyntaxError as e:
        print(f"Ошибка парсинга XSD: {e}")
        return {}, {}, None, "", {}
    except FileNotFoundError:
        print(f"Файл XSD не найден: {xsd_path}")
        return {}, {}, None, "", {}

    root = schema_doc.getroot()
    xsd_ns = "http://www.w3.org/2001/XMLSchema"
    nsmap = {'xs': xsd_ns}

    target_ns = root.get('targetNamespace')
    original_nsmap = root.nsmap
    element_nsmap = {k: v for k, v in original_nsmap.items() if k != 'xs' and v != xsd_ns}

    global_elements = {}
    global_types = {}

    for elem in root.xpath('xs:element[@name]', namespaces=nsmap):
        name = elem.get('name')
        if name:
            global_elements[name] = elem

    for elem in root.xpath('(xs:complexType[@name] | xs:simpleType[@name])', namespaces=nsmap):
        name = elem.get('name')
        if name:
            global_types[name] = elem

    return global_elements, global_types, schema_doc, target_ns, element_nsmap

def resolve_type(element_or_attr, schema_doc, global_types, target_ns, xsd_ns_map):
    type_name = element_or_attr.get('type')
    if type_name:
        if ":" in type_name:
            qname = etree.QName(type_name.split(":")[1])
        else:
            qname = etree.QName(type_name)
        if qname.namespace is None or qname.namespace == target_ns:
            local_name = qname.localname
            if local_name in global_types:
                return global_types[local_name], local_name
    return None, None

def build_empty_xml_recursive(element_or_type_def, schema_doc, global_types, target_ns, xsd_ns_map, element_nsmap, visited_types=None, element_name_hint=None):
    if visited_types is None:
        visited_types = set()

    tag = etree.QName(element_or_type_def).localname
    is_element = tag == 'element'
    is_complex_type = tag == 'complexType'
    is_simple_type = tag == 'simpleType'

    name = element_or_type_def.get('name')
    if is_element and name:
        elem_name = name
    elif element_name_hint:
        elem_name = element_name_hint
    else:
        elem_name = "AnonymousTypeElement"

    if is_simple_type:
        default_val = element_or_type_def.get('default', '')
        return default_val

    if is_complex_type:
        if name in visited_types:
            print(f"Предотвращена циклическая зависимость для типа: {name}")
            full_elem_name = etree.QName(target_ns, elem_name) if target_ns else elem_name
            return etree.Element(full_elem_name, nsmap=element_nsmap)
        new_visited = visited_types | {name}

        simple_content = element_or_type_def.find('xs:simpleContent', namespaces=xsd_ns_map)
        complex_content = element_or_type_def.find('xs:complexContent', namespaces=xsd_ns_map)

        if simple_content:
            ext_or_res = simple_content.xpath('(xs:extension | xs:restriction)', namespaces=xsd_ns_map)
            if ext_or_res:
                base_type_name = ext_or_res[0].get('base')
                full_elem_name = etree.QName(target_ns, elem_name) if target_ns else elem_name
                xml_elem = etree.Element(full_elem_name, nsmap=element_nsmap)
                for attr_elem in ext_or_res[0].xpath('xs:attribute', namespaces=xsd_ns_map):
                    attr_name = attr_elem.get('name')
                    if attr_name:
                        xml_elem.set(attr_name, "")
                return xml_elem

        if complex_content:
            ext_elem = complex_content.find('xs:extension', namespaces=xsd_ns_map)
            res_elem = complex_content.find('xs:restriction', namespaces=xsd_ns_map)
            base_type_def = None
            base_type_name = None
            if ext_elem is not None:
                base_type_name = ext_elem.get('base')
            elif res_elem is not None:
                base_type_name = res_elem.get('base')

            if base_type_name:
                 qname_base = etree.QName(base_type_name)
                 if qname_base.namespace is None or qname_base.namespace == target_ns:
                     base_local_name = qname_base.localname
                     if base_local_name in global_types:
                         base_type_def = global_types[base_local_name]

            full_elem_name = etree.QName(target_ns, elem_name) if target_ns else elem_name
            xml_elem = etree.Element(full_elem_name, nsmap=element_nsmap)

            if base_type_def is not None:
                 base_content = build_empty_xml_recursive(base_type_def, schema_doc, global_types, target_ns, xsd_ns_map, element_nsmap, new_visited, elem_name)
                 if base_content is not None and hasattr(base_content, 'tag'):
                     pass

            content_to_process = ext_elem if ext_elem is not None else res_elem
            if content_to_process is not None:
                for particle_type in ['sequence', 'choice', 'all']:
                    particle = content_to_process.find(f'xs:{particle_type}', namespaces=xsd_ns_map)
                    if particle is not None:
                        for child_elem_def in particle.xpath('xs:element', namespaces=xsd_ns_map):
                            child_name = child_elem_def.get('name')
                            child_min_occurs = int(child_elem_def.get('minOccurs', '1'))
                            child_max_occurs = child_elem_def.get('maxOccurs', '1')
                            unbounded = child_max_occurs == 'unbounded'
                            max_count = int(child_max_occurs) if not unbounded else 1

                            child_type_def, child_type_name = resolve_type(child_elem_def, schema_doc, global_types, target_ns, xsd_ns_map)

                            if child_type_def is None:
                                inline_ct = child_elem_def.find('xs:complexType', namespaces=xsd_ns_map)
                                inline_st = child_elem_def.find('xs:simpleType', namespaces=xsd_ns_map)
                                if inline_ct is not None:
                                    child_type_def = inline_ct
                                    child_type_name = None
                                elif inline_st is not None:
                                    child_type_def = inline_st
                                    child_type_name = None

                            if child_type_def is not None:
                                for _ in range(max(1, child_min_occurs)):
                                    child_xml = build_empty_xml_recursive(child_type_def, schema_doc, global_types, target_ns, xsd_ns_map, element_nsmap, new_visited, child_name)
                                    if child_xml is not None:
                                        if hasattr(child_xml, 'tag'):
                                            xml_elem.append(child_xml)
                            else:
                                full_child_name = etree.QName(target_ns, child_name) if target_ns else child_name
                                child_xml = etree.Element(full_child_name, nsmap=element_nsmap)
                                xml_elem.append(child_xml)

                        for attr_elem in content_to_process.xpath('xs:attribute', namespaces=xsd_ns_map):
                            attr_name = attr_elem.get('name')
                            if attr_name:
                                xml_elem.set(attr_name, "")
            return xml_elem

        full_elem_name = etree.QName(target_ns, elem_name) if target_ns else elem_name
        xml_elem = etree.Element(full_elem_name, nsmap=element_nsmap)

        for particle_type in ['sequence', 'choice', 'all']:
            particle = element_or_type_def.find(f'xs:{particle_type}', namespaces=xsd_ns_map)
            if particle is not None:
                for child_elem_def in particle.xpath('xs:element', namespaces=xsd_ns_map):
                    child_name = child_elem_def.get('name')
                    child_min_occurs = int(child_elem_def.get('minOccurs', '1'))
                    child_max_occurs = child_elem_def.get('maxOccurs', '1')
                    unbounded = child_max_occurs == 'unbounded'
                    max_count = int(child_max_occurs) if not unbounded else 1

                    child_type_def, child_type_name = resolve_type(child_elem_def, schema_doc, global_types, target_ns, xsd_ns_map)

                    if child_type_def is None:
                        inline_ct = child_elem_def.find('xs:complexType', namespaces=xsd_ns_map)
                        inline_st = child_elem_def.find('xs:simpleType', namespaces=xsd_ns_map)
                        if inline_ct is not None:
                            child_type_def = inline_ct
                            child_type_name = None
                        elif inline_st is not None:
                            child_type_def = inline_st
                            child_type_name = None

                    if child_type_def is not None:
                        for _ in range(max(1, child_min_occurs)):
                            child_xml = build_empty_xml_recursive(child_type_def, schema_doc, global_types, target_ns, xsd_ns_map, element_nsmap, new_visited, child_name)
                            if child_xml is not None:
                                if hasattr(child_xml, 'tag'):
                                    xml_elem.append(child_xml)
                    else:
                        full_child_name = etree.QName(target_ns, child_name) if target_ns else child_name
                        child_xml = etree.Element(full_child_name, nsmap=element_nsmap)
                        xml_elem.append(child_xml)

                for attr_elem in particle.xpath('xs:attribute', namespaces=xsd_ns_map):
                    attr_name = attr_elem.get('name')
                    if attr_name:
                        xml_elem.set(attr_name, "")

        for attr_elem in element_or_type_def.xpath('xs:attribute', namespaces=xsd_ns_map):
            attr_name = attr_elem.get('name')
            if attr_name:
                xml_elem.set(attr_name, "")

        return xml_elem

    if is_element:
        type_def, type_name = resolve_type(element_or_type_def, schema_doc, global_types, target_ns, xsd_ns_map)

        if type_def is None:
            inline_ct = element_or_type_def.find('xs:complexType', namespaces=xsd_ns_map)
            inline_st = element_or_type_def.find('xs:simpleType', namespaces=xsd_ns_map)
            if inline_ct is not None:
                type_def = inline_ct
                type_name = None
            elif inline_st is not None:
                type_def = inline_st
                type_name = None

        if type_def is not None:
            return build_empty_xml_recursive(type_def, schema_doc, global_types, target_ns, xsd_ns_map, element_nsmap, visited_types, elem_name)
        else:
            full_elem_name = etree.QName(target_ns, elem_name) if target_ns else elem_name
            xml_elem = etree.Element(full_elem_name, nsmap=element_nsmap)
            return xml_elem

    return None


def generate_full_xml_from_xsd(xsd_path):
    global_elements, global_types, schema_doc, target_ns, element_nsmap = get_schema_elements_and_types(xsd_path)
    if schema_doc is None:
        print("Не удалось загрузить XSD-схему.")
        return None

    xsd_ns_map = {'xs': "http://www.w3.org/2001/XMLSchema"}

    output_root_name = "FullyGeneratedXMLFromXSD"
    full_root_name = etree.QName(target_ns, output_root_name) if target_ns else output_root_name
    output_root = etree.Element(full_root_name, nsmap=element_nsmap)

    for elem_name, elem_def in global_elements.items():
        xml_part = build_empty_xml_recursive(elem_def, schema_doc, global_types, target_ns, xsd_ns_map, element_nsmap)
        if xml_part is not None and hasattr(xml_part, 'tag'):
            output_root.append(xml_part)
        else:
            print(f"Предупреждение: Не удалось сгенерировать XML для глобального элемента '{elem_name}'.")

    return output_root

def main():
    xsd_file_path = r"C:/Users/1/Desktop/MPITGOSUSLUGI/assets/схема вида сведений.xsd"
    combined_xml_root = generate_full_xml_from_xsd(xsd_file_path)

    if combined_xml_root is not None:
        print(etree.tostring(combined_xml_root, pretty_print=True, encoding='unicode'))
    else:
        print("Не удалось сгенерировать полный XML.")


if __name__ == "__main__":
    main()