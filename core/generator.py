from collections import defaultdict
import os


def build_tree(xsd_fields):
    tree = {}

    for f in xsd_fields:
        parts = f["path"].split(".")
        node = tree

        for p in parts:
            if p not in node:
                node[p] = {}
            node = node[p]

        # листовой элемент содержит данные поля
        node["_field"] = f

    return tree

def render_tree(node, indent=0):
    xml = []
    pad = "  " * indent

    for key, child in node.items():
        if key == "_field":
            continue

        field_info = child.get("_field")
        open_tag = f"{pad}<{key}>"
        close_tag = f"{pad}</{key}>"

        if field_info:  # лист
            var = key
            json = field_info["json_path"]

            value = (
                f"$!{{{var}}}" if json
                else "$!{NotFound}"
            )

            xml.append(f"{open_tag}{value}{close_tag}")

        else:  # вложенный узел
            xml.append(open_tag)
            xml.extend(render_tree(child, indent + 1))
            xml.append(close_tag)

    return xml



def build_xml(node, indent=0):
    lines = []
    pad = " " * indent

    for tag, meta in node.items():
        is_leaf = meta["_leaf"]
        is_list = meta["_list"]
        iterator = meta["_iterator"]
        children = meta["_children"]

        # #### LIST ####
        if is_list:
            iter_var = iterator or tag[0].lower() + tag[1:]
            lines.append(f"{pad}#foreach(${iter_var} in ${iter_var}s)")
            lines.append(f"{pad}  <{tag}>")
            lines.append(build_xml(children, indent + 4))
            lines.append(f"{pad}  </{tag}>")
            lines.append(f"{pad}#end")
            continue

        # #### CONTAINER ####
        if not is_leaf:
            lines.append(f"{pad}<{tag}>")
            lines.append(build_xml(children, indent + 2))
            lines.append(f"{pad}</{tag}>")
            continue

        # #### LEAF FIELD ####
        lines.append(f"{pad}<{tag}>$!{{NotFound}}</{tag}>")

    return "\n".join(lines)




def generate_vm(xsd_fields):
    set_lines = []

    for f in xsd_fields:
        json = f["json_path"]
        if json:
            var = f["path"].split(".")[-1]
            json_expr = "$context['" + "']['".join(json.split(".")) + "']"
            set_lines.append(f"#set(${var} = {json_expr})")

    tree = build_tree(xsd_fields)
    xml_lines = render_tree(tree)

    return "\n".join(set_lines) + "\n\n" + "\n".join(xml_lines)


def save_vm_to_file(vm_text, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(vm_text)
    return filepath

def create_vm_file(xsd_fields):
    vm_text = generate_vm(xsd_fields)
    return vm_text
    save_vm_to_file(vm_text, output_path)
    print(f"VM шаблон сохранён в файл: {output_path}")
    return output_path
