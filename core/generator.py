import json
import yaml
from lxml import etree
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path


class JsonToXmlTransformer:
    def __init__(self, mapping_file: str):
        self.mappings = self.load_mappings(mapping_file)
        self.logger = logging.getLogger(__name__)

    def load_mappings(self, mapping_file: str) -> Dict:
        """Загрузка словаря сопоставлений из YAML"""
        with open(mapping_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_value_from_json_path(self, data: Dict, json_path: str) -> Any:
        """Извлечение значения по JSON-path"""
        try:
            parts = json_path.split('.')
            current = data
            for part in parts:
                if part in current:
                    current = current[part]
                else:
                    return None
            return current
        except (KeyError, TypeError):
            return None

    def generate_vm_template(self, json_schema: Dict, xsd_schema: str, test_files: List[Dict]) -> str:
        """Генерация VM-шаблона"""

        vm_lines = [
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            "<soc:AppDataRequest xmlns:soc=\"http://socit.ru/kalin/orders/2.0.0\">"
        ]

        # Анализ XSD для понимания структуры
        xsd_root = etree.fromstring(xsd_schema.encode('utf-8'))

        # Генерация маппингов на основе анализа данных
        vm_lines.extend(self.generate_mappings_section())

        # Основная логика преобразования
        vm_lines.extend(self.generate_main_template())

        vm_lines.append("</soc:AppDataRequest>")

        return "\n".join(vm_lines)

    def generate_mappings_section(self) -> List[str]:
        """Генерация секции маппингов переменных"""
        lines = []

        # Базовые маппинги
        base_mappings = [
            ("userLastName", "PersonalInfo.storedValues.lastName"),
            ("userFirstName", "PersonalInfo.storedValues.firstName"),
            ("userBirthDate", "PersonalInfo.storedValues.birthDate"),
        ]

        for var_name, json_path in base_mappings:
            lines.append(f"#set(${var_name} = $jsonPathTool.get('{json_path}'))")

        return lines

    def generate_main_template(self) -> List[str]:
        """Генерация основной логики шаблона"""
        lines = [
            "  <soc:SetRequest>",
            "    <soc:orderId>$orderId</soc:orderId>",
            "    <soc:ServiceCode>$serviceCode</soc:ServiceCode>",
            "",
            "    <!-- Данные заявителя -->",
            "    <soc:userData>",
            "      <soc:lastName>$!{userLastName}</soc:lastName>",
            "      <soc:firstName>$!{userFirstName}</soc:firstName>",
            "      #if($userMiddleName && $userMiddleName != \"\")",
            "      <soc:middleName>$!{userMiddleName}</soc:middleName>",
            "      #end",
            "      <soc:birthDate>$!{userBirthDate}</soc:birthDate>",
            "    </soc:userData>",
            "",
            "    <!-- Условные блоки -->",
            self.generate_conditional_blocks(),
            "",
            "    <!-- Циклические блоки (дети) -->",
            self.generate_loop_blocks(),
            "  </soc:SetRequest>"
        ]

        return lines

    def generate_conditional_blocks(self) -> str:
        """Генерация условных блоков"""
        return """#if($ApplicantChoice == \"v1\")
    <!-- Блок для заявителя -->
    <soc:DelegateInfo>1</soc:DelegateInfo>
#else
    <!-- Блок для представителя -->
    <soc:DelegateInfo>2</soc:DelegateInfo>
    <!-- Данные представителя -->
#end"""

    def generate_loop_blocks(self) -> str:
        """Генерация циклических блоков"""
        return """#if($c2 && !$c2.isEmpty())
    <soc:children>
    #foreach($child in $c2)
        <soc:child>
            <soc:childData>
                <soc:lastName>$!{child.c6}</soc:lastName>
                <soc:firstName>$!{child.c7}</soc:firstName>
                #if($child.c12 && $child.c12 != \"\")
                <soc:middleName>$!{child.c12}</soc:middleName>
                #end
            </soc:childData>
        </soc:child>
    #end
    </soc:children>
#end"""


class JsonPathTool:
    """Утилита для работы с JSON-path"""

    @staticmethod
    def get(data: Dict, path: str, default: Any = 0) -> Any:
        """Получение значения по пути с fallback"""
        try:
            parts = path.split('.')
            current = data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                elif isinstance(current, list) and part.isdigit():
                    current = current[int(part)]
                else:
                    return default
            return current if current is not None else default
        except (KeyError, IndexError, TypeError, ValueError):
            logging.warning(f"Path not found: {path}")
            return default


def main():
    # Загрузка файлов
    with open('xsd_schema.txt', 'r', encoding='utf-8') as f:
        xsd_content = f.read()

    with open('sample_file1.txt', 'r', encoding='utf-8') as f:
        json_sample = json.load(f)

    # Инициализация трансформера
    transformer = JsonToXmlTransformer('mappings.yaml')

    # Генерация шаблона
    vm_template = transformer.generate_vm_template({}, xsd_content, [json_sample])

    # Сохранение результата
    with open('template.vm', 'w', encoding='utf-8') as f:
        f.write(vm_template)


if __name__ == "__main__":
    main()
