#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
smart_mapping_fuzzy.py
Создаёт сопоставление fieldName ↔ XSD-тег и генерирует Velocity-шаблон.
- Использует fuzzywuzzy для нестрогих совпадений
- Фильтрует служебные идентификаторы (sc123_456 и т.п.)
- Добавляет только надёжные совпадения (score ≥ threshold)
"""

import json
import re
from pathlib import Path
from lxml import etree
from fuzzywuzzy import fuzz, process
from core.main import generate_temp
# === Пути ===
FORM_PATH = Path("схема услуги.json")
XSD_PATH = Path("схема вида сведений.xsd")
YOUR_DIR = Path("outs/")
YOUR_DIR.mkdir(exist_ok=True)

MAPPING_JSON = YOUR_DIR / "mapping.json"
VM_TEMPLATE = YOUR_DIR / "template3.vm"

# === Параметры ===
FUZZY_THRESHOLD = 75  # минимальный процент схожести для включения в mapping

# === Вспомогательные функции ===
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def parse_form_field_names(obj):
    """Извлекает все fieldName или id, если fieldName отсутствует."""
    names = set()
    def _walk(o):
        if isinstance(o, dict):
            if "fieldName" in o and isinstance(o["fieldName"], str):
                names.add(o["fieldName"])
            elif "id" in o and isinstance(o["id"], str):
                names.add(o["id"])
            for v in o.values():
                _walk(v)
        elif isinstance(o, list):
            for i in o:
                _walk(i)
    _walk(obj)
    return sorted(names)

def parse_xsd_tags(xsd_path):
    """Извлекает все теги XSD."""
    ns = {"xsd": "http://www.w3.org/2001/XMLSchema"}
    tree = etree.parse(str(xsd_path))
    tags = [el.get("name") for el in tree.xpath("//xsd:element[@name]", namespaces=ns)]
    return [t for t in tags if t]

def normalize(s: str) -> str:
    """Приводит строку к простому виду для сравнения."""
    if not isinstance(s, str):
        return ""
    s = re.sub(r"([a-z])([A-Z])", r"\1_\2", s)
    return re.sub(r"[^a-z]+", "", s.lower())

def is_meaningful(name: str) -> bool:
    """Отбрасывает служебные/мусорные ID вроде sc39_2800, s12, block_1."""
    if not isinstance(name, str) or len(name) < 3:
        return False
    if re.fullmatch(r"(s|c|sc|block)\d+(_\d+)?", name, flags=re.IGNORECASE):
        return False
    if name.lower().startswith(("screen", "page", "tab", "step", "block", "start")):
        return False
    return True

def build_mapping(form_fields, xsd_tags, threshold=FUZZY_THRESHOLD):
    """Создаёт mapping fieldName → xsdTag (по прямым и fuzzy-совпадениям)."""
    mapping = {}
    xsd_tags_clean = [t for t in xsd_tags if isinstance(t, str)]
    normalized_tags = {normalize(t): t for t in xsd_tags_clean}

    for field in form_fields:
        if not is_meaningful(field):
            continue
        norm_field = normalize(field)

        # прямое совпадение
        if norm_field in normalized_tags:
            mapping[field] = normalized_tags[norm_field]
            continue

        # fuzzy-поиск
        best = process.extractOne(norm_field, xsd_tags_clean, scorer=fuzz.token_set_ratio)
        if best and isinstance(best[0], str) and best[1] >= threshold:
            mapping[field] = best[0]

    return mapping

def generate_vm(mapping : dict[str,str]):
    """Формирует текст Velocity-шаблона."""
    header = [
        "#* === Auto-generated VM Template === *#",
        "#* Использует fieldName + fuzzy matching (fuzzywuzzy) *#",
        ""
    ]
    setters, tags = [], []
    for field, tag in mapping.items():
        setters.append(f"#set(${field} = $c7['storedValues']['{field}'])")
        tags.append(f"    <{tag}>$!{{{field}}}</{tag}>")
    return "\n".join(header + setters + ["", "<Application>"] + tags + ["</Application>", ""])

# === Основная программа ===
def generate_template(json_form_path : str, xsd_path : str) -> str:
    # return generate_temp(xsd_path, json_form_path)
    form = load_json(json_form_path)
    form_fields = parse_form_field_names(form)
    xsd_tags = parse_xsd_tags(xsd_path)
    mapping = build_mapping(form_fields, xsd_tags, threshold=FUZZY_THRESHOLD)
    vm_text = generate_vm(mapping)
    return vm_text
