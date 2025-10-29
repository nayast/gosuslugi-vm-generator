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
    # element_nsmap не нужен для генерации строки шаблона, но сохраняем для информации
    # element_nsmap = {k: v for k, v in original_nsmap.items() if k != 'xs' and v != xsd_ns}
    # Сохраняем оригинальный nsmap, чтобы знать префиксы
    relevant_nsmap = {k: v for k, v in original_nsmap.items() if k != 'xs' and v != xsd_ns}

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

    return global_elements, global_types, schema_doc, target_ns, relevant_nsmap

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

# ... (вставьте сюда весь предыдущий код, заменив только эту функцию) ...

def build_velocity_template_recursive(element_or_type_def, schema_doc, global_types, target_ns, xsd_ns_map, nsmap, visited_types=None, element_name_hint=None, depth=0):
    """
    Рекурсивно строит строку-шаблон Apache Velocity на основе определения элемента или типа.
    """
    if visited_types is None:
        visited_types = set()

    indent = "  " * depth
    tag = etree.QName(element_or_type_def).localname
    is_element = tag == 'element'
    is_complex_type = tag == 'complexType'
    is_simple_type = tag == 'simpleType'

    name = element_or_type_def.get('name')
    if is_element and name:
        elem_name = name
    elif element_name_hint:
        elem_name = element_name_hint # Используем hint, если он есть
    else:
        elem_name = "AnonymousTypeElement"

    # --- Обработка SimpleType ---
    if is_simple_type:
        # Простые типы не создают вложенных элементов, они определяют тип значения.
        # Возвращаем пустую строку или значение по умолчанию, если оно есть.
        # Для шаблона, это просто переменная $elem_name
        # Однако, elem_name здесь - это имя типа (например, stringNN-250), если hint не был передан.
        # Нам нужно имя элемента, для которого используется этот тип.
        # Это имя передается через element_name_hint.
        # Если hint не был передан, используем name (имя типа), но это неправильно для переменной.
        # В идеале, hint всегда должен передаваться для типов, используемых элементами.
        # Поэтому используем elem_name (которое теперь равно hint или name).
        # Если hint не был передан, и name - это имя типа, а не элемента, переменная будет неправильной.
        # Но в текущем контексте, hint *должен* быть передан из обработки элемента.
        return f"$request.{elem_name}"

    # --- Обработка ComplexType ---
    if is_complex_type:
        # Проверяем на циклические зависимости
        if name in visited_types:
            print(f"Предотвращена циклическая зависимость для типа: {name}")
            # Возвращаем пустой элемент как комментарий или пустую строку
            return f"{indent}<!-- Циклическая зависимость: {name} -->\n"

        new_visited = visited_types | {name}

        # Проверяем на simpleContent или complexContent (наследование)
        simple_content = element_or_type_def.find('xs:simpleContent', namespaces=xsd_ns_map)
        complex_content = element_or_type_def.find('xs:complexContent', namespaces=xsd_ns_map)

        # Если есть simpleContent, это расширение/ограничение простого типа с атрибутами
        if simple_content is not None:
            ext_or_res = simple_content.xpath('(xs:extension | xs:restriction)', namespaces=xsd_ns_map)
            if ext_or_res:
                base_type_name = ext_or_res[0].get('base')
                # Устанавливаем значение $elem_name, если базовый тип - встроенный XSD.
                if ":" in base_type_name:
                    qname_base = etree.QName(base_type_name.split(":")[1])
                else:
                    qname_base = etree.QName(base_type_name)
                base_local_name = qname_base.localname
                base_namespace = qname_base.namespace
                if base_namespace == xsd_ns_map['xs']:
                    # Создаём элемент с текстовым содержимым $elem_name и атрибутами
                    full_elem_name = f"{{http://socit.ru/kalin/orders/2.0.0}}{elem_name}" if target_ns else elem_name
                    # Или используем префикс, если он есть в nsmap
                    elem_prefix = None
                    for p, uri in nsmap.items():
                        if uri == target_ns:
                            elem_prefix = p
                            break
                    if elem_prefix:
                        full_elem_name = f"{elem_prefix}:{elem_name}"
                    else:
                        full_elem_name = elem_name

                    attr_str = ""
                    for attr_elem in ext_or_res[0].xpath('xs:attribute', namespaces=xsd_ns_map):
                        attr_name = attr_elem.get('name')
                        if attr_name:
                             attr_str += f' {attr_name}="$request.{attr_name}"'
                    return f"{indent}<{full_elem_name}{attr_str}>$request.{elem_name}</{full_elem_name}>\n"
                # Если базовый тип - не встроенный, обработка как у complexContent?
                # Нет, simpleContent означает, что у него *есть* базовый простой тип.
                # Если он не встроенный, но простой - это редкий случай, обрабатываем как строку.
                # Но по спецификации, extension/restriction в simpleContent должны ссылаться на simpleType.
                # Пока оставим как есть, если базовый тип не встроенный - возвращаем пустую строку или комментарий.
                # Но если он определён как simpleType, его можно обработать рекурсивно.
                # Проверим, есть ли он в global_types и является ли simpleType.
                if base_namespace is None or base_namespace == target_ns:
                     if base_local_name in global_types:
                         base_type_def = global_types[base_local_name]
                         if etree.QName(base_type_def).localname == 'simpleType':
                             # --- ИЗМЕНЕНО ---
                             # Передаем elem_name как hint, чтобы рекурсивный вызов для simpleType знал имя элемента
                             base_val_template = build_velocity_template_recursive(base_type_def, schema_doc, global_types, target_ns, xsd_ns_map, nsmap, new_visited, elem_name, depth)
                             full_elem_name = f"{{http://socit.ru/kalin/orders/2.0.0}}{elem_name}" if target_ns else elem_name
                             elem_prefix = None
                             for p, uri in nsmap.items():
                                 if uri == target_ns:
                                     elem_prefix = p
                                     break
                             if elem_prefix:
                                 full_elem_name = f"{elem_prefix}:{elem_name}"
                             else:
                                 full_elem_name = elem_name
                             attr_str = ""
                             for attr_elem in ext_or_res[0].xpath('xs:attribute', namespaces=xsd_ns_map):
                                 attr_name = attr_elem.get('name')
                                 if attr_name:
                                      attr_str += f' {attr_name}="$request.{attr_name}"'
                             return f"{indent}<{full_elem_name}{attr_str}>{base_val_template}</{full_elem_name}>\n"
                return f"{indent}<!-- Необработанный simpleContent для {elem_name} -->\n"

        # Если есть complexContent, это наследование сложного типа
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
                 if ":" in base_type_name:
                     qname_base = etree.QName(base_type_name.split(":")[1])
                 else:
                     qname_base = etree.QName(base_type_name)
                 base_local_name = qname_base.localname
                 base_namespace = qname_base.namespace

                 if base_namespace == xsd_ns_map['xs']:
                     # Если базовый тип - встроенный XSD (например, xsd:string), но это complexContent - ошибка в схеме.
                     # Обычно complexContent расширяет/ограничивает другой complexType.
                     print(f"Предупреждение: complexContent расширяет встроенный простой тип {base_type_name} для {name}. Это необычно.")
                     # Создаём элемент с текстовым содержимым $elem_name и атрибутами
                     full_elem_name = f"{{http://socit.ru/kalin/orders/2.0.0}}{elem_name}" if target_ns else elem_name
                     elem_prefix = None
                     for p, uri in nsmap.items():
                         if uri == target_ns:
                             elem_prefix = p
                             break
                     if elem_prefix:
                         full_elem_name = f"{elem_prefix}:{elem_name}"
                     else:
                         full_elem_name = elem_name
                     attr_str = ""
                     content_to_process = ext_elem if ext_elem is not None else res_elem
                     if content_to_process is not None:
                         for attr_elem in content_to_process.xpath('xs:attribute', namespaces=xsd_ns_map):
                             attr_name = attr_elem.get('name')
                             if attr_name:
                                  attr_str += f' {attr_name}="$request.{attr_name}"'
                     return f"{indent}<{full_elem_name}{attr_str}>$request.{elem_name}</{full_elem_name}>\n"
                 elif base_namespace is None or base_namespace == target_ns:
                     base_local_name = qname_base.localname
                     if base_local_name in global_types:
                         base_type_def = global_types[base_local_name]

            full_elem_name = f"{{http://socit.ru/kalin/orders/2.0.0}}{elem_name}" if target_ns else elem_name
            elem_prefix = None
            for p, uri in nsmap.items():
                if uri == target_ns:
                    elem_prefix = p
                    break
            if elem_prefix:
                full_elem_name = f"{elem_prefix}:{elem_name}"
            else:
                full_elem_name = elem_name

            attr_str = ""
            # Обрабатываем атрибуты в extension/restriction
            content_to_process = ext_elem if ext_elem is not None else res_elem
            if content_to_process is not None:
                 for attr_elem in content_to_process.xpath('xs:attribute', namespaces=xsd_ns_map):
                     attr_name = attr_elem.get('name')
                     if attr_name:
                          attr_str += f' {attr_name}="$request.{attr_name}"'

            xml_str = f"{indent}<{full_elem_name}{attr_str}>\n"

            # Сначала обрабатываем структуру базового типа, если он есть
            if base_type_def is not None:
                 # --- ИЗМЕНЕНО ---
                 base_content = build_velocity_template_recursive(base_type_def, schema_doc, global_types, target_ns, xsd_ns_map, nsmap, new_visited, elem_name, depth + 1)
                 xml_str += base_content

            # Затем обрабатываем содержимое ext_elem или res_elem (обычно sequence/all/choice внутри extension)
            if content_to_process is not None:
                for particle_type in ['sequence', 'choice', 'all']:
                    particle = content_to_process.find(f'xs:{particle_type}', namespaces=xsd_ns_map)
                    if particle is not None:
                        if particle_type == 'choice':
                            # Для choice генерируем #if-ы для каждой ветки
                            choice_name = f"{elem_name}_choice" # Имя переменной для выбора ветки
                            for i, child_elem_def in enumerate(particle.xpath('xs:element', namespaces=xsd_ns_map)):
                                child_name = child_elem_def.get('name')
                                child_min_occurs = int(child_elem_def.get('minOccurs', '1'))
                                child_max_occurs = child_elem_def.get('maxOccurs', '1')
                                unbounded = child_max_occurs == 'unbounded'
                                max_count = int(child_max_occurs) if not unbounded else 1 # Для шаблона ограничим

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

                                # Генерируем #if для этой ветки
                                xml_str += f"{indent}  ## Выбор ветки {child_name} для {choice_name}\n"
                                xml_str += f"{indent}  #if($request.velocityCount == {i+1}) ## Используем $request.velocityCount или другую переменную\n"
                                # Внутри цикла обработки particle в complexType:
                                if child_type_def is not None:
                                    # --- ИЗМЕНЕНО ---
                                    # Получаем содержимое типа
                                    child_template_content = build_velocity_template_recursive(child_type_def,
                                                                                               schema_doc, global_types,
                                                                                               target_ns, xsd_ns_map,
                                                                                               nsmap, new_visited,
                                                                                               child_name, depth + 1)
                                    # Создаём тег для дочернего элемента и помещаем в него содержимое типа
                                    full_child_name = f"{{http://socit.ru/kalin/orders/2.0.0}}{child_name}" if target_ns else child_name
                                    child_elem_prefix = None
                                    for p, uri in nsmap.items():
                                        if uri == target_ns:
                                            child_elem_prefix = p
                                            break
                                    if child_elem_prefix:
                                        full_child_name = f"{child_elem_prefix}:{child_name}"
                                    else:
                                        full_child_name = child_name
                                    xml_str += f"{indent}  <{full_child_name}>{child_template_content}</{full_child_name}>\n"
                                else:
                                    # Если тип не определён (или inline simpleType), создаём элемент с переменной
                                    full_child_name = f"{{http://socit.ru/kalin/orders/2.0.0}}{child_name}" if target_ns else child_name
                                    child_elem_prefix = None
                                    for p, uri in nsmap.items():
                                        if uri == target_ns:
                                            child_elem_prefix = p
                                            break
                                    if child_elem_prefix:
                                        full_child_name = f"{child_elem_prefix}:{child_name}"
                                    else:
                                        full_child_name = child_name
                                    xml_str += f"{indent}  <{full_child_name}>$request.{child_name}</{full_child_name}>\n"
                                xml_str += f"{indent}  #end\n"
                        else: # sequence, all
                            for child_elem_def in particle.xpath('xs:element', namespaces=xsd_ns_map):
                                child_name = child_elem_def.get('name')
                                child_min_occurs = int(child_elem_def.get('minOccurs', '1'))
                                child_max_occurs = child_elem_def.get('maxOccurs', '1')
                                unbounded = child_max_occurs == 'unbounded'
                                max_count = int(child_max_occurs) if not unbounded else 1 # Для шаблона ограничим

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
                                    # --- ИЗМЕНЕНО ---
                                    child_template = build_velocity_template_recursive(child_type_def, schema_doc, global_types, target_ns, xsd_ns_map, nsmap, new_visited, child_name, depth + 1)
                                    xml_str += child_template
                                else:
                                    # --- ИЗМЕНЕНО ---
                                    full_child_name = f"{{http://socit.ru/kalin/orders/2.0.0}}{child_name}" if target_ns else child_name
                                    child_elem_prefix = None
                                    for p, uri in nsmap.items():
                                        if uri == target_ns:
                                            child_elem_prefix = p
                                            break
                                    if child_elem_prefix:
                                        full_child_name = f"{child_elem_prefix}:{child_name}"
                                    else:
                                        full_child_name = child_name
                                    xml_str += f"{indent}  <{full_child_name}>$request.{child_name}</{full_child_name}>\n"

            xml_str += f"{indent}</{full_elem_name}>\n"
            return xml_str


        # Если нет ни simpleContent, ни complexContent, это "обычный" complexType
        full_elem_name = f"{{http://socit.ru/kalin/orders/2.0.0}}{elem_name}" if target_ns else elem_name
        elem_prefix = None
        for p, uri in nsmap.items():
            if uri == target_ns:
                elem_prefix = p
                break
        if elem_prefix:
            full_elem_name = f"{elem_prefix}:{elem_name}"
        else:
            full_elem_name = elem_name

        attr_str = ""
        # Обрабатываем атрибуты на уровне complexType
        for attr_elem in element_or_type_def.xpath('xs:attribute', namespaces=xsd_ns_map):
            attr_name = attr_elem.get('name')
            if attr_name:
                 attr_str += f' {attr_name}="$request.{attr_name}"'

        xml_str = f"{indent}<{full_elem_name}{attr_str}>\n"

        # Обрабатываем sequence, choice, all
        for particle_type in ['sequence', 'choice', 'all']:
            particle = element_or_type_def.find(f'xs:{particle_type}', namespaces=xsd_ns_map)
            if particle is not None:
                if particle_type == 'choice':
                    # Для choice генерируем #if-ы для каждой ветки
                    choice_name = f"{elem_name}_choice" # Имя переменной для выбора ветки
                    for i, child_elem_def in enumerate(particle.xpath('xs:element', namespaces=xsd_ns_map)):
                        child_name = child_elem_def.get('name')
                        child_min_occurs = int(child_elem_def.get('minOccurs', '1'))
                        child_max_occurs = child_elem_def.get('maxOccurs', '1')
                        unbounded = child_max_occurs == 'unbounded'
                        max_count = int(child_max_occurs) if not unbounded else 1 # Для шаблона ограничим

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

                        # Генерируем #if для этой ветки
                        xml_str += f"{indent}  ## Выбор ветки {child_name} для {choice_name}\n"
                        xml_str += f"{indent}  #if($request.velocityCount == {i+1}) ## Используем $request.velocityCount или другую переменную\n"
                        if child_type_def is not None:
                            # --- ИЗМЕНЕНО ---
                            child_template = build_velocity_template_recursive(child_type_def, schema_doc, global_types, target_ns, xsd_ns_map, nsmap, new_visited, child_name, depth + 2)
                            xml_str += child_template
                        else:
                            # --- ИЗМЕНЕНО ---
                            full_child_name = f"{{http://socit.ru/kalin/orders/2.0.0}}{child_name}" if target_ns else child_name
                            child_elem_prefix = None
                            for p, uri in nsmap.items():
                                if uri == target_ns:
                                    child_elem_prefix = p
                                    break
                            if child_elem_prefix:
                                full_child_name = f"{child_elem_prefix}:{child_name}"
                            else:
                                full_child_name = child_name
                            xml_str += f"{indent}    <{full_child_name}>$request.{child_name}</{full_child_name}>\n"
                        xml_str += f"{indent}  #end\n"
                else: # sequence, all
                    for child_elem_def in particle.xpath('xs:element', namespaces=xsd_ns_map):
                        child_name = child_elem_def.get('name')
                        child_min_occurs = int(child_elem_def.get('minOccurs', '1'))
                        child_max_occurs = child_elem_def.get('maxOccurs', '1')
                        unbounded = child_max_occurs == 'unbounded'
                        max_count = int(child_max_occurs) if not unbounded else 1 # Для шаблона ограничим

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
                            # --- ИЗМЕНЕНО ---
                            child_template = build_velocity_template_recursive(child_type_def, schema_doc, global_types, target_ns, xsd_ns_map, nsmap, new_visited, child_name, depth + 1)
                            xml_str += child_template
                        else:
                            # --- ИЗМЕНЕНО ---
                            full_child_name = f"{{http://socit.ru/kalin/orders/2.0.0}}{child_name}" if target_ns else child_name
                            child_elem_prefix = None
                            for p, uri in nsmap.items():
                                if uri == target_ns:
                                    child_elem_prefix = p
                                    break
                            if child_elem_prefix:
                                full_child_name = f"{child_elem_prefix}:{child_name}"
                            else:
                                full_child_name = child_name
                            xml_str += f"{indent}  <{full_child_name}>$request.{child_name}</{full_child_name}>\n"

        xml_str += f"{indent}</{full_elem_name}>\n"
        return xml_str

    # --- Обработка Элемента ---
    if is_element:
        # Определяем тип элемента
        type_def, type_name = resolve_type(element_or_type_def, schema_doc, global_types, target_ns, xsd_ns_map)

        # Если тип не найден, проверим, не определён ли он inline
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
            # --- ИСПРАВЛЕНО ---
            # Рекурсивно вызываем для типа элемента.
            # Передаем elem_name как hint, чтобы тип знал, как его "зовут" в этом контексте.
            # Тип сам должен создать соответствующую структуру, включая корневой тег с именем elem_name.
            # НЕ оборачиваем результат в дополнительный тег <elem_name> здесь.
            return build_velocity_template_recursive(type_def, schema_doc, global_types, target_ns, xsd_ns_map, nsmap, visited_types, elem_name, depth)
        else:
            # Если тип не определён (или inline simpleType), создаём элемент с переменной
            # Этот случай для элементов без явного типа или с inline-типами.
            full_elem_name = f"{{http://socit.ru/kalin/orders/2.0.0}}{elem_name}" if target_ns else elem_name
            elem_prefix = None
            for p, uri in nsmap.items():
                if uri == target_ns:
                    elem_prefix = p
                    break
            if elem_prefix:
                full_elem_name = f"{elem_prefix}:{elem_name}"
            else:
                full_elem_name = elem_name
            attr_str = ""
            for attr_elem in element_or_type_def.xpath('xs:attribute', namespaces=xsd_ns_map):
                attr_name = attr_elem.get('name')
                if attr_name:
                     attr_str += f' {attr_name}="$request.{attr_name}"'
            return f"{indent}<{full_elem_name}{attr_str}>$request.{elem_name}</{full_elem_name}>\n"

    return f"{indent}<!-- Неизвестный тип -->\n"

def generate_velocity_template_from_xsd(xsd_path):
    global_elements, global_types, schema_doc, target_ns, nsmap = get_schema_elements_and_types(xsd_path)
    if schema_doc is None:
        print("Не удалось загрузить XSD-схему.")
        return None

    xsd_ns_map = {'xs': "http://www.w3.org/2001/XMLSchema"}

    # Начинаем генерацию с корня. Создаём общий корень для шаблона.
    output_root_name = "FullyGeneratedVMTemplateFromXSD"
    # Определяем префикс для targetNamespace
    root_elem_prefix = None
    for p, uri in nsmap.items():
        if uri == target_ns:
            root_elem_prefix = p
            break
    full_root_name = f"{root_elem_prefix}:{output_root_name}" if root_elem_prefix else output_root_name

    # Генерируем пространства имён в корне
    ns_decl_str = ' '.join([f'xmlns:{prefix}="{uri}"' for prefix, uri in nsmap.items() if prefix])
    if root_elem_prefix: # Добавляем default namespace, если оно есть и используется для корня
        ns_decl_str += f' xmlns="{target_ns}"'

    template_str = f"<{full_root_name} {ns_decl_str}>\n"

    for elem_name, elem_def in global_elements.items():
        # Создаём шаблонную часть для каждого глобального элемента
        elem_template = build_velocity_template_recursive(elem_def, schema_doc, global_types, target_ns, xsd_ns_map, nsmap)
        template_str += elem_template

    template_str += f"</{full_root_name}>\n"
    return template_str

def main():
    xsd_file_path = r"C:/Users/1/Desktop/MPITGOSUSLUGI/assets/схема вида сведений.xsd"
    template_str = generate_velocity_template_from_xsd(xsd_file_path)

    if template_str is not None:
        print(template_str)
        # Опционально: сохранить в файл
        # output_file = "generated_velocity_template.vm"
        # with open(output_file, 'w', encoding='utf-8') as f:
        #     f.write(template_str)
        # print(f"Шаблон сохранён в {output_file}")
    else:
        print("Не удалось сгенерировать шаблон Velocity.")


if __name__ == "__main__":
    main()