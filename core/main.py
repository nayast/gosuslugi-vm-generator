from core.json_scheme_parser import parse_json_scheme
from core.xsd_parser import parse_xsd
from core.matcher import match_fields
from core.generator import create_vm_file

def generate_temp(xsd_path, json_path):
    res1 = parse_xsd(xsd_path)
    res2 = parse_json_scheme(json_path)

    res3 = match_fields(res1, res2)
    return create_vm_file(res3)

