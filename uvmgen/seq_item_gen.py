###########################################################
# seq_item_gen.py - generate uvm_sequence_item classes
###########################################################
from core import Model, SVWriter, write_file


def gen_sequence_item(model: Model, seq_item):
  name = seq_item["name"]
  s = SVWriter()
  s.w(f"// {name} Sequence Item")
  s.w()
  s.begin(f"class {name} extends uvm_sequence_item;")
  s.w()
  s.w("// Transaction fields")
  for field in seq_item.get("fields", []):
    rand = "rand " if field.get("rand") else ""
    s.w(f"{rand}{field['type']} {field['name']};")
  s.w()
  s.begin(f"`uvm_object_utils_begin({name})")
  for field in seq_item.get("fields", []):
    s.w(f"`uvm_field_int({field['name']}, UVM_ALL_ON)")
  s.end("`uvm_object_utils_end")
  s.w()
  s.begin(f"function new(string name = \"{name}\");")
  s.w("super.new(name);")
  s.end("endfunction")
  s.w()
  for c in seq_item.get("constraints", []) or []:
    s.begin(f"constraint {c['name']} {{")
    for item in c.get("items", []):
      s.w(item)
    s.end("}")
    s.w()
  s.user_code(f"{name}_methods")
  s.w()
  s.end("endclass")

  path = model.dir("sequences") / f"{name}.sv"
  write_file(path, s.text(), model.overwrite)
  model.register("sequence_items", path)


def generate(model: Model):
  for item in model.seq_items.values():
    gen_sequence_item(model, item)
