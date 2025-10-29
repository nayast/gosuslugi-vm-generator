# auto_field_mapper.py
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
        self.element_paths = {}  # Храним путь к каждому элементу
        self.choice_info = {}  # Информация о choice: {element_name: [choice_branches]}
        self._load_schema()

    def _load_schema(self):
        try:
            with open(self.xsd_path, 'r', encoding='utf-8') as f:
                self.schema_doc = etree.parse(f)
            print(f"XSD-схема успешно загружена из {self.xsd_path}")
        except Exception as e:
            print(f"Ошибка при загрузке XSD-схемы {self.xsd_path}: {e}")
            return

        # Извлекаем глобальные элементы и типы
        for elem in self.schema_doc.xpath('//xs:element[@name]', namespaces=self.nsmap):
            name = elem.get('name')
            if name and not elem.getparent().tag.endswith('complexType'):  # Только глобальные
                self.global_elements[name] = elem

        for elem in self.schema_doc.xpath('//xs:complexType[@name] | //xs:simpleType[@name]', namespaces=self.nsmap):
            name = elem.get('name')
            if name:
                self.global_types[name] = elem

    def analyze(self):
        """Анализирует схему и возвращает информацию о структуре."""
        if not self.schema_doc:
            return {}

        analysis = {
            'elements': {},  # {element_name: {type, path, children, attributes}}
            'choices': {},  # {element_name: [choice_branch_names]}
            'simple_elements': set()  # Элементы с простым типом
        }

        for elem_name, elem_def in self.global_elements.items():
            # print(f"Анализ элемента: {elem_name}")
            elem_info = self._analyze_element_or_type(elem_def, elem_name, f"/{elem_name}")
            if elem_info:
                analysis['elements'][elem_name] = elem_info

        # Анализируем типы для поиска простых элементов и choice внутри них
        for type_name, type_def in self.global_types.items():
            # Проверим, есть ли элементы, ссылающиеся на этот тип
            referring_elements = self.schema_doc.xpath(f'//xs:element[@type="soc:{type_name}"]', namespaces=self.nsmap)
            for ref_elem in referring_elements:
                ref_name = ref_elem.get('name')
                if ref_name and ref_name in analysis['elements']:
                    # Уже проанализирован
                    pass
                elif ref_name:
                    # print(f"Анализ элемента по типу {type_name}: {ref_name}")
                    elem_info = self._analyze_element_or_type(ref_elem, ref_name, f"/{ref_name}")
                    if elem_info:
                        analysis['elements'][ref_name] = elem_info

        return analysis

    def _analyze_element_or_type(self, element_or_type_def, elem_name_hint, path):
        """Рекурсивно анализирует элемент или тип."""
        info = {
            'name': elem_name_hint,
            'path': path,
            'type': None,
            'base_type': None,
            'children': [],
            'attributes': [],
            'is_simple_content': False,
            'is_complex_type': False,
            'contains_choice': False
        }

        tag = etree.QName(element_or_type_def).localname
        is_element = tag == 'element'
        is_complex_type = tag == 'complexType'
        is_simple_type = tag == 'simpleType'

        name = element_or_type_def.get('name')
        if is_element and name:
            elem_name = name
        elif elem_name_hint:
            elem_name = elem_name_hint
        else:
            elem_name = "AnonymousTypeElement"

        info['name'] = elem_name

        # --- Обработка SimpleType ---
        if is_simple_type:
            info['type'] = 'simpleType'
            info['is_simple_content'] = True
            return info

        # --- Обработка ComplexType ---
        if is_complex_type or is_element:
            info['is_complex_type'] = True
            type_def = element_or_type_def
            if is_element:
                # Определяем тип элемента
                type_name_attr = element_or_type_def.get('type')
                if type_name_attr:
                    # Пытаемся найти определение типа
                    if ":" in type_name_attr:
                        _, local_type_name = type_name_attr.split(":")
                    else:
                        local_type_name = type_name_attr
                    type_def = self.global_types.get(local_type_name)
                    info['type'] = local_type_name
                else:
                    # Inline type
                    inline_ct = element_or_type_def.find('xs:complexType', namespaces=self.nsmap)
                    inline_st = element_or_type_def.find('xs:simpleType', namespaces=self.nsmap)
                    if inline_ct is not None:
                        type_def = inline_ct
                        info['type'] = 'inline_complex'
                    elif inline_st is not None:
                        type_def = inline_st
                        info['type'] = 'inline_simple'
                        info['is_simple_content'] = True
                        return info  # Inline simple type - это конечный элемент

            if type_def is None and is_element:
                # Элемент без типа, возможно, просто placeholder или ошибка
                return info

            # Проверяем на simpleContent или complexContent
            simple_content = type_def.find('xs:simpleContent', namespaces=self.nsmap)
            complex_content = type_def.find('xs:complexContent', namespaces=self.nsmap)

            if simple_content:
                info['is_simple_content'] = True
                ext_or_res = simple_content.xpath('(xs:extension | xs:restriction)', namespaces=self.nsmap)
                if ext_or_res:
                    base_type_name = ext_or_res[0].get('base')
                    info['base_type'] = base_type_name
                    # Атрибуты
                    for attr_elem in ext_or_res[0].xpath('xs:attribute', namespaces=self.nsmap):
                        attr_name = attr_elem.get('name')
                        if attr_name:
                            info['attributes'].append(attr_name)

            elif complex_content:
                ext_elem = complex_content.find('xs:extension', namespaces=self.nsmap)
                res_elem = complex_content.find('xs:restriction', namespaces=self.nsmap)
                content_to_process = ext_elem if ext_elem is not None else res_elem
                if content_to_process is not None:
                    base_type_name = content_to_process.get('base')
                    info['base_type'] = base_type_name
                    # Атрибуты extension/restriction
                    for attr_elem in content_to_process.xpath('xs:attribute', namespaces=self.nsmap):
                        attr_name = attr_elem.get('name')
                        if attr_name:
                            info['attributes'].append(attr_name)

                # Обрабатываем содержимое extension/restriction
                for particle_type in ['sequence', 'choice', 'all']:
                    particle = content_to_process.find(f'xs:{particle_type}',
                                                       namespaces=self.nsmap) if content_to_process is not None else None
                    if particle is not None:
                        if particle_type == 'choice':
                            info['contains_choice'] = True
                            choice_branches = []
                            for i, child_elem_def in enumerate(particle.xpath('xs:element', namespaces=self.nsmap)):
                                child_name = child_elem_def.get('name')
                                if child_name:
                                    choice_branches.append(child_name)
                            self.choice_info[elem_name] = choice_branches
                            info['children'] = choice_branches  # Для choice children - это список веток
                        else:  # sequence, all
                            for child_elem_def in particle.xpath('xs:element', namespaces=self.nsmap):
                                child_name = child_elem_def.get('name')
                                if child_name:
                                    child_path = f"{path}/{child_name}"
                                    child_info = self._analyze_element_or_type(child_elem_def, child_name, child_path)
                                    if child_info:
                                        info['children'].append(child_info['name'])

            else:
                # "Обычный" complexType
                for particle_type in ['sequence', 'choice', 'all']:
                    particle = type_def.find(f'xs:{particle_type}', namespaces=self.nsmap)
                    if particle is not None:
                        if particle_type == 'choice':
                            info['contains_choice'] = True
                            choice_branches = []
                            for i, child_elem_def in enumerate(particle.xpath('xs:element', namespaces=self.nsmap)):
                                child_name = child_elem_def.get('name')
                                if child_name:
                                    choice_branches.append(child_name)
                            self.choice_info[elem_name] = choice_branches
                            info['children'] = choice_branches  # Для choice children - это список веток
                        else:  # sequence, all
                            for child_elem_def in particle.xpath('xs:element', namespaces=self.nsmap):
                                child_name = child_elem_def.get('name')
                                if child_name:
                                    child_path = f"{path}/{child_name}"
                                    child_info = self._analyze_element_or_type(child_elem_def, child_name, child_path)
                                    if child_info:
                                        info['children'].append(child_info['name'])

            # Атрибуты на уровне самого complexType
            if type_def is not None:
                for attr_elem in type_def.xpath('xs:attribute', namespaces=self.nsmap):
                    attr_name = attr_elem.get('name')
                    if attr_name:
                        info['attributes'].append(attr_name)

        return info


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
                    # Попробуем загрузить как JSON напрямую
                    data = json.load(f)
            except json.JSONDecodeError:
                # Если не получилось, попробуем извлечь из текста
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

            # Агрегируем данные
            all_analysis['field_to_id'].update(scenario_analysis['field_to_id'])
            all_analysis['stored_values'].update(scenario_analysis['stored_values'])
            all_analysis['choice_fields'].update(scenario_analysis['choice_fields'])
            all_analysis['flat_fields'].update(scenario_analysis['flat_fields'])

            keys_in_this_scenario = set(scenario_analysis['field_to_id'].keys()) | \
                                    set(scenario_analysis['stored_values'].keys()) | \
                                    set(scenario_analysis['choice_fields'].keys())
            all_analysis['keys_per_scenario'].append(keys_in_this_scenario)
            all_analysis['common_keys'].update(keys_in_this_scenario)  # Все уникальные ключи

        # Найти общие ключи во всех сценариях
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
            'choice_fields': {},  # {choice_name: value}
            'flat_fields': {},  # {key: path}
        }

        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                if key == 'fieldToId' and isinstance(value, dict):
                    # Нормализуем ключи fieldToId (убираем $)
                    normalized_fti = {k.lstrip('$'): v for k, v in value.items()}
                    analysis['field_to_id'].update(normalized_fti)
                elif key == 'storedValues' and isinstance(value, dict):
                    analysis['stored_values'].update(value)
                elif key.endswith('Choice') and isinstance(value, dict) and 'value' in value:
                    # Предполагаем, что это поле выбора
                    analysis['choice_fields'][key] = value.get('value', '')
                elif key.startswith('c') and isinstance(value, dict) and 'value' in value:
                    # Предполагаем, что это поле формы
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


# --- 3. Автоматическое сопоставление ---
def create_mapping(xsda: XSDSchemaAnalyzer, jsa: JSONScenarioAnalyzer):
    """Создает автоматический маппинг между полями XSD и JSON."""
    xsd_analysis = xsda.analyze()
    json_analysis = jsa.analyze()

    mapping = {}
    reverse_mapping = {}  # Для отладки: JSON ключ -> XSD элемент

    print("\n--- Создание автоматического маппинга ---")

    # 1. Используем fieldToId из JSON
    print("1. Сопоставление по fieldToId...")
    for xsd_elem_name, xsd_elem_info in xsd_analysis['elements'].items():
        # Проверяем, есть ли xsd_elem_name в fieldToId JSON
        for json_fti_key, json_c_key in json_analysis['field_to_id'].items():
            if xsd_elem_name == json_fti_key:
                json_path = f"$currentValue.{json_c_key}['value']"  # Пример пути
                vm_var = f"$request.{xsd_elem_name}"
                mapping[vm_var] = json_path
                reverse_mapping[json_c_key] = vm_var
                print(f"  [fieldToId] {vm_var} <-> {json_path}")

    # 2. Используем storedValues из JSON
    print("2. Сопоставление по storedValues...")
    for xsd_elem_name, xsd_elem_info in xsd_analysis['elements'].items():
        vm_var = f"$request.{xsd_elem_name}"
        if vm_var not in mapping:  # Еще не сопоставлено
            for stored_key in json_analysis['stored_values'].keys():
                if xsd_elem_name == stored_key:
                    json_path = f"$currentValue.storedValues.{stored_key}"
                    mapping[vm_var] = json_path
                    reverse_mapping[stored_key] = vm_var
                    print(f"  [storedValues] {vm_var} <-> {json_path}")
                    break  # Нашли точное совпадение

    # 3. Нечеткое сопоставление (по именам полей)
    print("3. Нечеткое сопоставление по именам...")
    json_keys_for_fuzzy = set(json_analysis['stored_values'].keys()) | \
                          set(json_analysis['field_to_id'].keys()) | \
                          set(json_analysis['flat_fields'].keys())

    for xsd_elem_name in xsd_analysis['elements'].keys():
        vm_var = f"$request.{xsd_elem_name}"
        if vm_var not in mapping:  # Еще не сопоставлено
            # Используем difflib.get_close_matches для поиска похожих ключей
            close_matches = difflib.get_close_matches(xsd_elem_name.lower(), [k.lower() for k in json_keys_for_fuzzy],
                                                      n=1, cutoff=0.6)
            if close_matches:
                # Найден похожий ключ
                matched_json_key_lower = close_matches[0]
                # Найти оригинальный регистр ключа в json_keys_for_fuzzy
                original_json_key = next((k for k in json_keys_for_fuzzy if k.lower() == matched_json_key_lower), None)
                if original_json_key:
                    # Определяем, где находится этот ключ (в storedValues, flat_fields и т.д.)
                    json_path_source = "unknown"
                    if original_json_key in json_analysis['stored_values']:
                        json_path_source = f"$currentValue.storedValues.{original_json_key}"
                    elif original_json_key in json_analysis['flat_fields']:
                        # Простой путь, может потребовать уточнения
                        raw_path = json_analysis['flat_fields'][original_json_key]
                        json_path_source = f"$currentValue.{raw_path}"
                        if raw_path.endswith('.value'):
                            json_path_source = f"$currentValue.{raw_path[:-6]}['value']"  # Убираем .value и добавляем ['value']
                    elif original_json_key in json_analysis['field_to_id']:
                        c_key = json_analysis['field_to_id'][original_json_key]
                        json_path_source = f"$currentValue.{c_key}['value']"

                    mapping[vm_var] = json_path_source
                    reverse_mapping[original_json_key] = vm_var
                    print(f"  [fuzzy] {vm_var} <-> {json_path_source} (на основе '{original_json_key}')")

    # 4. Специальная обработка для choice
    print("4. Сопоставление для элементов choice...")
    # Предположим, что в XSD есть элементы с choice, и в JSON есть соответствующие поля выбора
    # Например, если в XSD есть AppDataRequest с choice (SetRequest, cancelRequest, ...),
    # а в JSON есть ApplicantChoice со значениями v1, v2, ...
    # Нужно сопоставить это.
    # Это сложнее, так как это не прямое поле-поле, а логика ветвления.
    # Пока просто отметим наличие choice в XSD.
    for elem_name, branches in xsda.choice_info.items():
        print(f"  [XSD choice] Элемент '{elem_name}' имеет ветки: {branches}")
        # В JSON может быть поле elem_name + "Choice"
        # Или просто elem_name с числовым значением, указывающим на ветку
        # Или отдельное поле выбора (как ApplicantChoice)
        # Пока оставим это для ручной настройки или более сложной логики

    # 5. Сопоставление полей выбора (choice fields)
    print("5. Сопоставление полей выбора из JSON...")
    for choice_field_name, choice_value in json_analysis['choice_fields'].items():
        # Это поле, которое управляет выбором. Его значение (choice_value) может быть "v1", "v2" и т.д.
        # Нужно связать это с конкретными ветками в XSD.
        # Например, ApplicantChoice.value = "v1" -> первая ветка AppDataRequest
        vm_choice_var = f"$request.{choice_field_name}_choice"  # Имя переменной для выбора в VM
        json_choice_path = f"$currentValue.{choice_field_name}['value']"
        mapping[vm_choice_var] = json_choice_path
        print(f"  [choice field] {vm_choice_var} <-> {json_choice_path} (значение: {choice_value})")

    print(f"\n--- Создано {len(mapping)} сопоставлений ---")
    return mapping, reverse_mapping


# --- Основная функция ---
def main():
    # Пути к файлам
    xsd_file_path = r"C:\Users\1\Desktop\MPITGOSUSLUGI\assets\схема вида сведений.xsd"
    json_scenario_paths = [
        r"C:\Users\1\Desktop\MPITGOSUSLUGI\assets\сценарий1.txt",
        r"C:\Users\1\Desktop\MPITGOSUSLUGI\assets\сценарий2.txt"
    ]

    print("--- Анализ XSD-схемы ---")
    xsd_analyzer = XSDSchemaAnalyzer(xsd_file_path)
    # xsd_structure = xsd_analyzer.analyze()
    # print("Структура XSD (пример):")
    # for elem_name, elem_info in list(xsd_structure['elements'].items())[:3]:
    #     print(f"  Элемент: {elem_name}, Путь: {elem_info['path']}, Дети: {elem_info['children'][:5]}...") # Первые 5 детей

    print("\n--- Анализ JSON-сценариев ---")
    json_analyzer = JSONScenarioAnalyzer(json_scenario_paths)
    # json_analysis = json_analyzer.analyze()
    # print("Анализ JSON (пример):")
    # print(f"  fieldToId ключей: {len(json_analysis['field_to_id'])}")
    # print(f"  storedValues ключей: {len(json_analysis['stored_values'])}")
    # print(f"  choice_fields: {list(json_analysis['choice_fields'].keys())}")

    print("\n--- Создание маппинга ---")
    mapping, reverse_mapping = create_mapping(xsd_analyzer, json_analyzer)

    # Вывод результатов
    print("\n--- Результирующий маппинг (первые 20) ---")
    for i, (vm_var, json_expr) in enumerate(list(mapping.items())[:20]):
        print(f"  {vm_var} -> {json_expr}")
    if len(mapping) > 20:
        print(f"  ... и еще {len(mapping) - 20} сопоставлений")

    # Сохранение маппинга в файл (опционально)
    output_mapping_file = r"C:\Users\1\Desktop\MPITGOSUSLUGI\assets\auto_mapping.json"
    try:
        serializable_mapping = {k: v for k, v in mapping.items()}  # Убедимся, что ключи/значения сериализуемы
        with open(output_mapping_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_mapping, f, ensure_ascii=False, indent=2)
        print(f"\nМаппинг сохранен в {output_mapping_file}")
    except Exception as e:
        print(f"Ошибка при сохранении маппинга: {e}")


if __name__ == "__main__":
    main()