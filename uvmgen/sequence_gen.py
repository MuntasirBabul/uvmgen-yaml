###########################################################
# sequence_gen.py - generate uvm_sequence classes
###########################################################
from core import Model, SVWriter, write_file


def root_sequence_item(model: Model, seq):
  """Walk base_class chain up to the root sequence to find its item type."""
  while seq.get("base_class", "uvm_sequence") != "uvm_sequence":
    seq = model.sequences[seq["base_class"]]
  return seq["sequence_item"]


def gen_sequence(model: Model, seq):
  name = seq["name"]
  base = seq.get("base_class", "uvm_sequence")
  item = root_sequence_item(model, seq)
  parent = f"uvm_sequence #({item})" if base == "uvm_sequence" else base

  s = SVWriter()
  s.w(f"// {name} Sequence")
  s.w()
  s.begin(f"class {name} extends {parent};")
  s.w()
  s.w(f"`uvm_object_utils({name})")
  s.w()
  s.begin(f"function new(string name = \"{name}\");")
  s.w("super.new(name);")
  s.end("endfunction")
  s.w()
  if "body" in seq:
    s.begin("virtual task body();")
    num = seq["body"].get("num_transactions")
    if num is not None:
      s.begin(f"repeat ({num}) begin")
      s.w(f"req = {item}::type_id::create(\"req\");")
      s.w("start_item(req);")
      s.w("if (!req.randomize())")
      s.w(f"  `uvm_error(\"{name.upper()}\", \"randomization failed\")")
      s.user_code(f"{name}_body")
      s.w("finish_item(req);")
      s.end("end")
    else:
      s.user_code(f"{name}_body")
    s.end("endtask")
    s.w()
  s.end("endclass")

  path = model.dir("sequences") / f"{name}.sv"
  write_file(path, s.text(), model.overwrite)
  model.register("sequences", path)


def generate(model: Model):
  for seq in model.sequences.values():
    gen_sequence(model, seq)
