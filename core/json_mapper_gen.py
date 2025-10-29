# auto_field_mapper_v3.py
import json
import re
import difflib  # Для нечеткого сравнения строк
from collections import defaultdict
from lxml import etree


# --- 1. Анализ XSD-схемы ---
class XSDSchemaAnalyzer:
    def __init__(self, xsd_path):
        self.xsd_path = xsd_path
        self.schema_doc = None
        self.nsmap = {'xs': 'http://www.w3.org/2001/XMLSchema', 'soc': 'http://socit.ru/kalin/orders/2.0.0'}
        self.target_ns = "http://socit.ru/kalin/orders/2.0.0"
        self.global_elements = {}
        self.global_types = {}
        self.element_paths_info = {}  # {full_xpath: {info}}
        self.choice_info = {}  # {parent_xpath: [choice_branch_xpaths]}
        self._load_schema()

    def _load_schema(self):
        try:
            with open(self.xsd_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.search(r'targetNamespace\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                self.target_ns = match.group(1)
                print(f"Найден targetNamespace: {self.target_ns}")
                if 'socit.ru' in self.target_ns:
                    self.nsmap['soc'] = self.target_ns

            self.schema_doc = etree.fromstring(content.encode('utf-8'))
            print(f"XSD-схема успешно загружена из {self.xsd_path}")
        except FileNotFoundError:
            print(f"Ошибка: Файл XSD {self.xsd_path} не найден.")
            return
        except etree.XMLSyntaxError as e:
            print(f"Ошибка синтаксиса XML в XSD {self.xsd_path}: {e}")
            return
        except Exception as e:
            print(f"Ошибка при загрузке XSD-схемы {self.xsd_path}: {e}")
            return

        for elem in self.schema_doc.xpath('//xs:element[@name]', namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'}):
            name = elem.get('name')
            if name and not (elem.getparent() is not None and etree.QName(elem.getparent()).localname in ['complexType',
                                                                                                          'schema']):
                self.global_elements[name] = elem

        for elem in self.schema_doc.xpath('//xs:complexType[@name] | //xs:simpleType[@name]',
                                          namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'}):
            name = elem.get('name')
            if name:
                self.global_types[name] = elem

        print(f"  Найдено {len(self.global_elements)} глобальных элементов.")
        print(f"  Найдено {len(self.global_types)} глобальных типов.")

    def analyze(self):
        """Анализирует схему и возвращает информацию о структуре."""
        if not self.schema_doc:
            print("Ошибка: Схема не загружена.")
            return {}

        print("Начало анализа структуры XSD...")
        for elem_name, elem_def in self.global_elements.items():
            print(f"  Анализ глобального элемента: {elem_name}")
            root_xpath = f"/{elem_name}"
            self._analyze_element_node(elem_def, root_xpath, None)

        print(f"Анализ XSD завершен. Найдено путей элементов: {len(self.element_paths_info)}")

        analysis_result = {
            'elements_by_path': self.element_paths_info,
            'choices': self.choice_info,
        }
        return analysis_result

    def _analyze_element_node(self, element_node, current_xpath, parent_type_name):
        """
        Рекурсивно анализирует узел элемента и собирает информацию о его пути.
        """
        elem_name = element_node.get('name')
        elem_type_ref = element_node.get('type')
        elem_min_occurs = element_node.get('minOccurs', '1')
        elem_max_occurs = element_node.get('maxOccurs', '1')

        type_def = None
        type_name = None
        if elem_type_ref:
            if ":" in elem_type_ref:
                _, local_type_name = elem_type_ref.split(":")
            else:
                local_type_name = elem_type_ref
            type_def = self.global_types.get(elem_type_ref) or self.global_types.get(local_type_name)
            type_name = local_type_name
        else:
            inline_ct = element_node.find('xs:complexType', namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'})
            inline_st = element_node.find('xs:simpleType', namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'})
            if inline_ct is not None:
                type_def = inline_ct
                type_name = f"{elem_name}_InlineComplexType"
            elif inline_st is not None:
                type_def = inline_st
                type_name = f"{elem_name}_InlineSimpleType"

        self.element_paths_info[current_xpath] = {
            'name': elem_name,
            'type': type_name,
            'minOccurs': elem_min_occurs,
            'maxOccurs': elem_max_occurs,
            'node': element_node,
            'parent_type': parent_type_name
        }

        if type_def is not None:
            self._analyze_type_definition(type_def, type_name, current_xpath)

    def _analyze_type_definition(self, type_def_node, type_name, parent_xpath):
        """
        Анализирует определение типа (complexType/simpleType) и его содержимое.
        """
        tag_localname = etree.QName(type_def_node).localname

        if tag_localname == 'simpleType':
            return

        if tag_localname != 'complexType':
            return

        simple_content = type_def_node.find('xs:simpleContent', namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'})
        if simple_content:
            ext_or_res = simple_content.xpath('(xs:extension | xs:restriction)',
                                              namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'})
            if ext_or_res:
                base_type = ext_or_res[0].get('base')
                if parent_xpath in self.element_paths_info:
                    self.element_paths_info[parent_xpath]['base_type'] = base_type
                    self.element_paths_info[parent_xpath]['is_simple_content'] = True

                attrs = []
                for attr_elem in ext_or_res[0].xpath('xs:attribute',
                                                     namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'}):
                    attr_name = attr_elem.get('name')
                    if attr_name:
                        attrs.append(attr_name)
                if parent_xpath in self.element_paths_info:
                    self.element_paths_info[parent_xpath]['attributes'] = attrs
            return

        complex_content = type_def_node.find('xs:complexContent', namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'})
        content_to_process = None
        if complex_content:
            ext_elem = complex_content.find('xs:extension', namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'})
            res_elem = complex_content.find('xs:restriction', namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'})
            content_to_process = ext_elem if ext_elem is not None else res_elem
            if content_to_process is not None:
                base_type = content_to_process.get('base')
                if parent_xpath in self.element_paths_info:
                    self.element_paths_info[parent_xpath]['base_type'] = base_type
                    self.element_paths_info[parent_xpath]['is_complex_content'] = True

                attrs = []
                for attr_elem in content_to_process.xpath('xs:attribute',
                                                          namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'}):
                    attr_name = attr_elem.get('name')
                    if attr_name:
                        attrs.append(attr_name)
                if parent_xpath in self.element_paths_info and attrs:
                    existing_attrs = self.element_paths_info[parent_xpath].get('attributes', [])
                    self.element_paths_info[parent_xpath]['attributes'] = list(set(existing_attrs + attrs))

        node_to_scan = content_to_process if content_to_process is not None else type_def_node

        for particle_type in ['sequence', 'choice', 'all']:
            particle = node_to_scan.find(f'xs:{particle_type}', namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'})
            if particle is not None:

                if particle_type == 'choice':
                    choice_branches = []
                    for i, child_elem_def in enumerate(
                            particle.xpath('xs:element', namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'})):
                        child_name = child_elem_def.get('name')
                        if child_name:
                            child_xpath = f"{parent_xpath}/{child_name}"
                            choice_branches.append(child_xpath)
                            self._analyze_element_node(child_elem_def, child_xpath, type_name)

                    self.choice_info[parent_xpath] = choice_branches

                else:  # sequence, all
                    for child_elem_def in particle.xpath('xs:element',
                                                         namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'}):
                        child_name = child_elem_def.get('name')
                        if child_name:
                            child_xpath = f"{parent_xpath}/{child_name}"
                            self._analyze_element_node(child_elem_def, child_xpath, type_name)

                break

        if complex_content is None:
            attrs = []
            for attr_elem in type_def_node.xpath('xs:attribute', namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'}):
                attr_name = attr_elem.get('name')
                if attr_name:
                    attrs.append(attr_name)
            if parent_xpath in self.element_paths_info and attrs:
                existing_attrs = self.element_paths_info[parent_xpath].get('attributes', [])
                self.element_paths_info[parent_xpath]['attributes'] = list(set(existing_attrs + attrs))


# --- 2. Анализ JSON-сценариев ---
class JSONScenarioAnalyzer:
    def __init__(self, json_paths):
        self.json_paths = json_paths
        self.scenarios_data = []
        self.analysis_results = []
        self._load_scenarios()

    def _load_scenarios(self):
        for path in self.json_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        text_content = f.read()
                    start = text_content.find('{')
                    end = text_content.rfind('}')
                    if start != -1 and end != -1 and start < end:
                        json_string = text_content[start:end + 1]
                        data = json.loads(json_string)
                    else:
                        raise ValueError("Не удалось найти корректный JSON в файле.")
                except Exception as e:
                    print(f"Ошибка при загрузке JSON-сценария {path}: {e}")
                    continue
            self.scenarios_data.append(data)
            print(f"JSON-сценарий успешно загружен из {path}")

    def analyze(self):
        """Анализирует загруженные сценарии."""
        all_analysis = {
            'field_to_id': {},
            'stored_values': {},
            'choice_fields': {},
            'flat_fields': {},
            'common_keys': set(),
            'keys_per_scenario': []
        }

        for i, data in enumerate(self.scenarios_data):
            print(f"Анализ сценария {i + 1}...")
            scenario_analysis = self._analyze_single_scenario(data)
            self.analysis_results.append(scenario_analysis)

            all_analysis['field_to_id'].update(scenario_analysis['field_to_id'])
            all_analysis['stored_values'].update(scenario_analysis['stored_values'])
            all_analysis['choice_fields'].update(scenario_analysis['choice_fields'])
            all_analysis['flat_fields'].update(scenario_analysis['flat_fields'])

            keys_in_this_scenario = set(scenario_analysis['field_to_id'].keys()) | \
                                    set(scenario_analysis['stored_values'].keys()) | \
                                    set(scenario_analysis['choice_fields'].keys())
            all_analysis['keys_per_scenario'].append(keys_in_this_scenario)
            all_analysis['common_keys'].update(keys_in_this_scenario)

        if all_analysis['keys_per_scenario']:
            common_keys = set.intersection(*all_analysis['keys_per_scenario'])
            all_analysis['common_keys'] = common_keys
            print(f"Найдено {len(common_keys)} общих ключей во всех сценариях.")

        return all_analysis

    def _analyze_single_scenario(self, data, path=""):
        """Рекурсивно анализирует один сценарий."""
        analysis = {
            'field_to_id': {},
            'stored_values': {},
            'choice_fields': {},
            'flat_fields': {},
        }

        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                if key == 'fieldToId' and isinstance(value, dict):
                    normalized_fti = {k.lstrip('$'): v for k, v in value.items()}
                    analysis['field_to_id'].update(normalized_fti)
                elif key == 'storedValues' and isinstance(value, dict):
                    analysis['stored_values'].update(value)
                elif key.endswith('Choice') and isinstance(value, dict) and 'value' in value:
                    analysis['choice_fields'][key] = value.get('value', '')
                elif key.startswith('c') and isinstance(value, dict) and 'value' in value:
                    analysis['flat_fields'][key] = new_path
                elif isinstance(value, (str, int, float, bool)) or value is None:
                    analysis['flat_fields'][key] = new_path
                elif isinstance(value, dict):
                    sub_analysis = self._analyze_single_scenario(value, new_path)
                    analysis['field_to_id'].update(sub_analysis['field_to_id'])
                    analysis['stored_values'].update(sub_analysis['stored_values'])
                    analysis['choice_fields'].update(sub_analysis['choice_fields'])
                    analysis['flat_fields'].update(sub_analysis['flat_fields'])
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        sub_analysis = self._analyze_single_scenario(item, f"{new_path}[{i}]")
                        analysis['field_to_id'].update(sub_analysis['field_to_id'])
                        analysis['stored_values'].update(sub_analysis['stored_values'])
                        analysis['choice_fields'].update(sub_analysis['choice_fields'])
                        analysis['flat_fields'].update(sub_analysis['flat_fields'])
        elif isinstance(data, list):
            for i, item in enumerate(data):
                sub_analysis = self._analyze_single_scenario(item, f"{path}[{i}]")
                analysis['field_to_id'].update(sub_analysis['field_to_id'])
                analysis['stored_values'].update(sub_analysis['stored_values'])
                analysis['choice_fields'].update(sub_analysis['choice_fields'])
                analysis['flat_fields'].update(sub_analysis['flat_fields'])

        return analysis


# --- 3. Анализ JSON-схемы услуги ---
class JSONServiceSchemaAnalyzer:
    def __init__(self, json_service_schema_path):
        self.json_service_schema_path = json_service_schema_path
        self.service_schema_data = None
        self.component_bindings = {}  # {component_id: binding_path}
        self.component_names = {}  # {component_id: component_name}
        self.component_types = {}  # {component_id: component_type}
        self._load_schema()

    def _load_schema(self):
        """Загружает и парсит JSON-схему услуги."""
        try:
            with open(self.json_service_schema_path, 'r', encoding='utf-8') as f:
                # Попробуем загрузить как JSON напрямую
                self.service_schema_data = json.load(f)
        except json.JSONDecodeError:
            # Если не получилось, попробуем извлечь из текста
            try:
                with open(self.json_service_schema_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                start = text_content.find('{')
                end = text_content.rfind('}')
                if start != -1 and end != -1 and start < end:
                    json_string = text_content[start:end + 1]
                    self.service_schema_data = json.loads(json_string)
                else:
                    raise ValueError("Не удалось найти корректный JSON в файле схемы услуги.")
            except Exception as e:
                print(f"Ошибка при загрузке JSON-схемы услуги {self.json_service_schema_path}: {e}")
                return
        print(f"JSON-схема услуги успешно загружена из {self.json_service_schema_path}")

    def analyze(self):
        """Анализирует схему услуги и извлекает привязки."""
        if not self.service_schema_data:
            print("Ошибка: Схема услуги не загружена.")
            return {}

        print("Начало анализа JSON-схемы услуги...")
        # Рекурсивно ищем компоненты и их привязки
        self._recursive_find_components(self.service_schema_data)
        print(f"Анализ JSON-схемы услуги завершен. Найдено {len(self.component_bindings)} привязок компонентов.")

        analysis_result = {
            'component_bindings': self.component_bindings,
            'component_names': self.component_names,
            'component_types': self.component_types
        }
        return analysis_result

    def _recursive_find_components(self, obj, path=""):
        """Рекурсивно ищет компоненты и их привязки в структуре JSON."""
        if isinstance(obj, dict):
            # Проверяем, является ли текущий объект компонентом
            # Обычно у компонента есть 'id' и 'binding' или 'path'
            if 'id' in obj:
                comp_id = obj.get('id')
                comp_name = obj.get('name', 'UnknownName')
                comp_type = obj.get('type', 'UnknownType')

                if comp_id:
                    self.component_names[comp_id] = comp_name
                    self.component_types[comp_id] = comp_type

                    # Ищем привязку
                    binding_path = obj.get('binding') or obj.get('path')
                    if binding_path:
                        # Привязка может быть относительной, например order.userData.lastName
                        # Для упрощения, будем хранить как есть
                        self.component_bindings[comp_id] = binding_path
                        print(f"  Найдена привязка: {comp_id} -> {binding_path}")

            # Продолжаем рекурсивный обход
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                self._recursive_find_components(value, new_path)

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]"
                self._recursive_find_components(item, new_path)


# --- 4. Автоматическое сопоставление ---
def create_mapping(xsda: XSDSchemaAnalyzer, jsa: JSONScenarioAnalyzer, jssa: JSONServiceSchemaAnalyzer):
    """Создает автоматический маппинг между полями XSD и JSON."""
    xsd_analysis = xsda.analyze()
    json_analysis = jsa.analyze()
    service_schema_analysis = jssa.analyze()

    mapping = {}
    reverse_mapping = {}

    print("\n--- Создание автоматического маппинга ---")

    # 1. Используем fieldToId из JSON сценариев
    print("1. Сопоставление по fieldToId из JSON сценариев...")
    for xsd_xpath, xsd_elem_info in xsd_analysis['elements_by_path'].items():
        xsd_elem_name = xsd_elem_info.get('name')
        if not xsd_elem_name:
            continue
        for json_fti_key, json_c_key in json_analysis['field_to_id'].items():
            if xsd_elem_name == json_fti_key:
                json_path = f"$currentValue.{json_c_key}['value']"
                vm_var = f"$request.{xsd_elem_name}"
                mapping[vm_var] = json_path
                reverse_mapping[json_c_key] = vm_var
                print(f"  [fieldToId] {vm_var} <-> {json_path}")

    # 2. Используем storedValues из JSON сценариев
    print("2. Сопоставление по storedValues из JSON сценариев...")
    for xsd_xpath, xsd_elem_info in xsd_analysis['elements_by_path'].items():
        xsd_elem_name = xsd_elem_info.get('name')
        if not xsd_elem_name:
            continue
        vm_var = f"$request.{xsd_elem_name}"
        if vm_var not in mapping:
            for stored_key in json_analysis['stored_values'].keys():
                if xsd_elem_name == stored_key:
                    json_path = f"$currentValue.storedValues.{stored_key}"
                    mapping[vm_var] = json_path
                    reverse_mapping[stored_key] = vm_var
                    print(f"  [storedValues] {vm_var} <-> {json_path}")
                    break

    # 3. Нечеткое сопоставление (по именам полей)
    print("3. Нечеткое сопоставление по именам...")
    json_keys_for_fuzzy = set(json_analysis['stored_values'].keys()) | \
                          set(json_analysis['field_to_id'].keys()) | \
                          set(json_analysis['flat_fields'].keys())

    for xsd_xpath, xsd_elem_info in xsd_analysis['elements_by_path'].items():
        xsd_elem_name = xsd_elem_info.get('name')
        if not xsd_elem_name:
            continue
        vm_var = f"$request.{xsd_elem_name}"
        if vm_var not in mapping:
            close_matches = difflib.get_close_matches(xsd_elem_name.lower(), [k.lower() for k in json_keys_for_fuzzy],
                                                      n=1, cutoff=0.6)
            if close_matches:
                matched_json_key_lower = close_matches[0]
                original_json_key = next((k for k in json_keys_for_fuzzy if k.lower() == matched_json_key_lower), None)
                if original_json_key:
                    json_path_source = "unknown"
                    if original_json_key in json_analysis['stored_values']:
                        json_path_source = f"$currentValue.storedValues.{original_json_key}"
                    elif original_json_key in json_analysis['flat_fields']:
                        raw_path = json_analysis['flat_fields'][original_json_key]
                        json_path_source = f"$currentValue.{raw_path}"
                        if raw_path.endswith('.value'):
                            json_path_source = f"$currentValue.{raw_path[:-6]}['value']"
                    elif original_json_key in json_analysis['field_to_id']:
                        c_key = json_analysis['field_to_id'][original_json_key]
                        json_path_source = f"$currentValue.{c_key}['value']"

                    mapping[vm_var] = json_path_source
                    reverse_mapping[original_json_key] = vm_var
                    print(f"  [fuzzy] {vm_var} <-> {json_path_source} (на основе '{original_json_key}')")

    # 4. Сопоставление через JSON-схему услуги (bindings)
    print("4. Сопоставление через привязки из JSON-схемы услуги...")
    # Пример: binding "order.userData.lastName" <-> XSD элемент "lastName"
    # Пример: binding "contact.email" <-> XSD элемент "Email"
    # Это сложнее, так как пути могут быть разными.
    # Попробуем сопоставить конечные части путей.
    for comp_id, binding_path in service_schema_analysis['component_bindings'].items():
        # Разбиваем binding_path на части
        # Пример: "order.userData.lastName" -> ["order", "userData", "lastName"]
        # Или "contact.email" -> ["contact", "email"]
        binding_parts = binding_path.split('.')
        if binding_parts:
            # Берем последнюю часть как потенциальное имя XSD элемента
            potential_xsd_name = binding_parts[-1]

            # Также можно попробовать сопоставить по имени компонента
            comp_name = service_schema_analysis['component_names'].get(comp_id, '')
            # Или по ID компонента (c6, c7 и т.д.), если они совпадают с ключами в fieldToId/storedValues

            # Попробуем найти XSD элемент с таким именем
            matched_xsd_xpath = None
            matched_xsd_info = None
            for xsd_xpath, xsd_elem_info in xsd_analysis['elements_by_path'].items():
                if xsd_elem_info.get('name') == potential_xsd_name:
                    matched_xsd_xpath = xsd_xpath
                    matched_xsd_info = xsd_elem_info
                    break

            if matched_xsd_xpath:
                vm_var = f"$request.{potential_xsd_name}"
                if vm_var not in mapping:  # Приоритет у предыдущих сопоставлений
                    # Формируем путь к JSON данным.
                    # Это упрощенный вариант. В реальности путь зависит от структуры сценария.
                    # Предположим, что binding "order.userData.lastName" соответствует
                    # структуре в сценарии. Тогда путь к значению может быть
                    # $currentValue.order.userData.lastName (если это storedValues)
                    # или $currentValue.c6.value (если c6 привязан к order.userData.lastName)

                    # Попробуем найти, есть ли в fieldToId или storedValues ключ,
                    # который соответствует этому binding_path или comp_id
                    found_json_path = None
                    # 1. Прямой поиск по fieldToId (если ключ fieldToId == binding_path)
                    # (редко, но возможно)
                    if binding_path in json_analysis['field_to_id']:
                        c_key = json_analysis['field_to_id'][binding_path]
                        found_json_path = f"$currentValue.{c_key}['value']"
                    # 2. Поиск по storedValues (если ключ storedValues == binding_path)
                    elif binding_path in json_analysis['stored_values']:
                        found_json_path = f"$currentValue.storedValues.{binding_path}"
                    # 3. Поиск по ID компонента (если comp_id есть в fieldToId)
                    elif comp_id in json_analysis['field_to_id']:
                        c_key = json_analysis['field_to_id'][comp_id]
                        found_json_path = f"$currentValue.{c_key}['value']"
                    # 4. Поиск по ID компонента в storedValues (если ключ storedValues == comp_id)
                    elif comp_id in json_analysis['stored_values']:
                        found_json_path = f"$currentValue.storedValues.{comp_id}"
                    # 5. Если не нашли, используем упрощенный путь (может быть неверным)
                    else:
                        # found_json_path = f"$currentValue.{binding_path}" # Очень упрощенный путь
                        pass  # Лучше не сопоставлять, если не уверены

                    if found_json_path:
                        mapping[vm_var] = found_json_path
                        reverse_mapping[f"binding:{comp_id}"] = vm_var  # Для отладки
                        print(
                            f"  [service schema binding] {vm_var} <-> {found_json_path} (через binding '{binding_path}' для компонента {comp_id})")
                    else:
                        # Можно попробовать нечеткое сопоставление для binding_path
                        # против имен XSD элементов
                        close_xsd_matches = difflib.get_close_matches(potential_xsd_name.lower(),
                                                                      [info.get('name', '').lower() for info in
                                                                       xsd_analysis['elements_by_path'].values()], n=1,
                                                                      cutoff=0.7)
                        if close_xsd_matches and close_xsd_matches[0] != potential_xsd_name.lower():
                            # Найдено похожее имя XSD элемента
                            matched_xsd_name_lower = close_xsd_matches[0]
                            # Найти оригинальное имя
                            original_xsd_name = next(
                                (info.get('name') for info in xsd_analysis['elements_by_path'].values() if
                                 info.get('name', '').lower() == matched_xsd_name_lower), None)
                            if original_xsd_name:
                                vm_var_alt = f"$request.{original_xsd_name}"
                                if vm_var_alt not in mapping:
                                    # Попробуем сопоставить с JSON по comp_id или binding_path
                                    alt_json_path = None
                                    if comp_id in json_analysis['field_to_id']:
                                        c_key = json_analysis['field_to_id'][comp_id]
                                        alt_json_path = f"$currentValue.{c_key}['value']"
                                    elif comp_id in json_analysis['stored_values']:
                                        alt_json_path = f"$currentValue.storedValues.{comp_id}"
                                    if alt_json_path:
                                        mapping[vm_var_alt] = alt_json_path
                                        reverse_mapping[f"fuzzy_binding:{comp_id}"] = vm_var_alt
                                        print(
                                            f"  [fuzzy service schema binding] {vm_var_alt} <-> {alt_json_path} (через binding '{binding_path}' для компонента {comp_id}, fuzzy match с XSD '{original_xsd_name}')")

    # 5. Специальная обработка для choice
    print("5. Сопоставление для элементов choice...")
    for elem_name, branches in xsda.choice_info.items():
        print(
            f"  [XSD choice] Элемент '{elem_name}' имеет ветки: {[b.split('/')[-1] for b in branches[:3]]}...")  # Первые 3
        # В JSON может быть поле elem_name + "Choice"
        # Или просто elem_name с числовым значением, указывающим на ветку
        # Или отдельное поле выбора (как ApplicantChoice)
        # Пока оставим это для ручной настройки или более сложной логики

    # 6. Сопоставление полей выбора (choice fields)
    print("6. Сопоставление полей выбора из JSON...")
    for choice_field_name, choice_value in json_analysis['choice_fields'].items():
        vm_choice_var = f"$request.{choice_field_name}_choice"
        json_choice_path = f"$currentValue.{choice_field_name}['value']"
        mapping[vm_choice_var] = json_choice_path
        print(f"  [choice field] {vm_choice_var} <-> {json_choice_path} (значение: {choice_value})")

    print(f"\n--- Создано {len(mapping)} сопоставлений ---")
    return mapping, reverse_mapping


# --- Основная функция ---
def generate(xsd_file_path,json_scenario_paths,json_service_schema_path):

    print("--- Анализ XSD-схемы ---")
    xsd_analyzer = XSDSchemaAnalyzer(xsd_file_path)
    # xsd_analysis = xsd_analyzer.analyze()
    # print("Структура XSD (пример):")
    # for path in list(xsd_analysis['elements_by_path'].keys())[:5]:
    #     info = xsd_analysis['elements_by_path'][path]
    #     print(f"  Путь: {path}, Имя: {info['name']}, Тип: {info['type']}")

    print("\n--- Анализ JSON-сценариев ---")
    json_analyzer = JSONScenarioAnalyzer(json_scenario_paths)
    # json_analysis = json_analyzer.analyze()
    # print("Анализ JSON (пример):")
    # print(f"  fieldToId ключей: {len(json_analysis['field_to_id'])}")
    # print(f"  storedValues ключей: {len(json_analysis['stored_values'])}")
    # print(f"  choice_fields: {list(json_analysis['choice_fields'].keys())}")

    print("\n--- Анализ JSON-схемы услуги ---")
    json_service_analyzer = JSONServiceSchemaAnalyzer(json_service_schema_path)
    # service_schema_analysis = json_service_analyzer.analyze()
    # print("Анализ JSON-схемы услуги (пример):")
    # print(f"  Найдено привязок: {len(service_schema_analysis['component_bindings'])}")
    # for cid, binding in list(service_schema_analysis['component_bindings'].items())[:5]:
    #     cname = service_schema_analysis['component_names'].get(cid, 'Unknown')
    #     print(f"  Компонент: {cid} ({cname}) -> Привязка: {binding}")

    print("\n--- Создание маппинга ---")
    mapping, reverse_mapping = create_mapping(xsd_analyzer, json_analyzer, json_service_analyzer)
    return mapping