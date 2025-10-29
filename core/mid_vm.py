import core.final_gen, core.json_mapper_gen, core.vm_templ_finalizer


def generate_template(xsd_path : str, json_path : str, json_app_paths : list[str]):
    initial_vm = core.final_gen.generate(xsd_path)
    mapping =  core.json_mapper_gen.generate(xsd_path, json_app_paths, json_path)
    return core.vm_templ_finalizer.apply_mapping_to_vm_template(initial_vm, mapping)