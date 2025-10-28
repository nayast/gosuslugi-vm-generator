from json_scheme_parser import parse_json_scheme
file_path = r"C:\Projects\Python_projects\gosuslugi-vm-generator\core\files\normalno.json"
file_path4 = r"C:\Projects\Python_projects\gosuslugi-vm-generator\core\files\simple_json_scheme.json"
from xsd_parser import parse_xsd
file_path2 = r"C:\Projects\Python_projects\gosuslugi-vm-generator\core\files\xsd_cheme.xsd"
file_path3 = r"C:\Projects\Python_projects\gosuslugi-vm-generator\core\files\simple_xsd_cheme.xsd"

res = parse_xsd(file_path3)
print(f"Элементов в xsd схеме:", len(res), ":\n", res)
print(sum(1 for x in res if x["list"]))

fields = parse_json_scheme(file_path4)
# fields_set = set(fields)
print(fields)
# print(len(fields_set), len(fields))

from matcher import match_fields
matches = match_fields(res, fields)
print(matches)



from generator import create_vm_file
json_path = r"C:\Projects\Python_projects\gosuslugi-vm-generator\core\files\simple_json_scheme.json"
xsd_path = r"C:\Projects\Python_projects\gosuslugi-vm-generator\core\files\simple_xsd_cheme.xsd"
out_path = r"C:\Projects\Python_projects\gosuslugi-vm-generator\core\files\mapper.vm"

create_vm_file(res, out_path)