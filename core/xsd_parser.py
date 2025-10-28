from lxml import etree

def parse_xsd(xsd_path):
    tree = etree.parse(xsd_path)
    root = tree.getroot()

    # Detect prefix dynamically
    xsd_ns = None
    for k, v in root.nsmap.items():
        if v == "http://www.w3.org/2001/XMLSchema":
            xsd_ns = k
            break
    if not xsd_ns:
        raise RuntimeError("XSD namespace not found")

    ns = { "xs": root.nsmap[xsd_ns] }

    results = []

    def is_list(el):
        max_occurs = el.get("maxOccurs", "1")
        return max_occurs == "unbounded" or max_occurs.isdigit() and int(max_occurs) > 1

    def walk(node, prefix=""):
        for el in node.findall(f"./xs:element", ns):

            name = el.get("name")
            if not name:
                continue

            path = f"{prefix}.{name}" if prefix else name
            list_flag = is_list(el)

            # Inline complex type
            complex_type = el.find("./xs:complexType", ns)
            if complex_type is not None:
                walk(complex_type, path)
                continue

            # Reference to named complexType
            el_type = el.get("type")
            if el_type:
                type_name = el_type.split(":")[-1]
                ct = root.find(f".//xs:complexType[@name='{type_name}']", ns)
                if ct is not None:
                    walk(ct, path)
                else:
                    # Primitive leaf
                    results.append({
                        "path": path,
                        "type": el_type,
                        "list": list_flag
                    })
            else:
                # Primitive leaf without type attr
                results.append({
                    "path": path,
                    "type": None,
                    "list": list_flag
                })

        # Also follow sequences and choices
        for seq in node.findall("./xs:sequence", ns):
            walk(seq, prefix)

        for ch in node.findall("./xs:choice", ns):
            walk(ch, prefix)

    # Start from schema root
    walk(root)

    return results
