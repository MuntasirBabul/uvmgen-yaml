###########################################################
# config_gen.py - generate uvm_object configuration classes
###########################################################
from core import Model, SVWriter, write_file


def gen_config_object(model: Model, obj):
  name = obj["name"]
  s = SVWriter()
  s.w(f"// {name} Configuration Object")
  s.w()
  s.begin(f"class {name} extends uvm_object;")
  s.w()
  s.w(f"`uvm_object_utils({name})")
  s.w()
  for field in obj.get("fields", []):
    default = field.get("default")
    init = f" = {default}" if default is not None else ""
    s.w(f"{field['type']} {field['name']}{init};")
  s.w()
  s.begin(f"function new(string name = \"{name}\");")
  s.w("super.new(name);")
  s.end("endfunction")
  s.w()
  s.user_code(f"{name}_methods")
  s.w()
  s.end("endclass")

  path = model.dir("config") / f"{name}.sv"
  write_file(path, s.text(), model.overwrite)
  model.register("config", path)


def generate(model: Model):
  for obj in model.config_objects.values():
    gen_config_object(model, obj)
