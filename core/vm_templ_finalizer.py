import re


def apply_mapping_to_vm_template(template_str: str, mapping: dict) -> str:
    """
    Применяет маппинг к сгенерированному VM-шаблону, заменяя переменные.

    Args:
        template_str (str): Строка сгенерированного VM-шаблона.
        mapping (dict): Словарь маппинга вида {"$request.varName": "$currentValue.path.to.data"}.

    Returns:
        str: VM-шаблон с замененными переменными.
    """
    if not mapping:
        print("Предупреждение: Маппинг пуст. Шаблон возвращается без изменений.")
        return template_str

    modified_template = template_str
    replacements_made = 0

    # Сортируем ключи маппинга по длине по убыванию.
    # Это помогает избежать частичной замены более коротких переменных,
    # которые являются подстроками более длинных.
    # Например, сначала заменить $request.firstNameBeforeMarriage,
    # а потом $request.firstName.
    sorted_vm_vars = sorted(mapping.keys(), key=len, reverse=True)

    for vm_variable in sorted_vm_vars:
        json_path = mapping[vm_variable]

        # Экранируем специальные символы в переменной VM для регулярного выражения
        # $request.firstName -> \$request\.firstName
        escaped_vm_var = re.escape(vm_variable)

        # Используем word boundaries (\b) для более точной замены, если это возможно.
        # Однако \b не работает корректно с символами $ и .,
        # поэтому используем lookahead и lookbehind.
        # (?<!\w) - отрицательный lookbehind: не буква/цифра/_ перед
        # (?!\w) - отрицательный lookahead: не буква/цифра/_ после
        # pattern = f"(?<!\\w){escaped_vm_var}(?!\\w)"
        # Более надежный способ для $request.*: убедиться, что перед $request нет $
        # и после переменной нет буквы/цифры/_
        # pattern = f"(?<!\\$){escaped_vm_var}(?!\\w)"

        # Еще более точный способ: искать $request.varName как отдельное слово в контексте.
        # Учитывая, что переменные обычно находятся внутри тегов или атрибутов,
        # можно искать их как есть, полагаясь на сортировку по длине.
        # Для максимальной точности можно использовать более сложные паттерны,
        # но для большинства случаев простая замена с сортировкой должна работать хорошо.

        # Заменяем все вхождения
        # re.subn возвращает кортеж (новая_строка, количество_замен)
        modified_template, count = re.subn(escaped_vm_var, json_path, modified_template)
        replacements_made += count

    print(f"Выполнено {replacements_made} замен в шаблоне на основе маппинга.")
    return modified_template