###########################################################
# ral_gen.py - generate UVM register model (RAL) + adapter
###########################################################
from core import Model, SVWriter, write_file


def gen_register(model: Model, s: SVWriter, reg, reg_width):
  name = reg["name"]
  s.begin(f"class {name}_reg extends uvm_reg;")
  s.w()
  s.w(f"`uvm_object_utils({name}_reg)")
  s.w()
  for field in reg.get("fields", []):
    s.w(f"rand uvm_reg_field {field['name']};")
  s.w()
  s.begin(f"function new(string name = \"{name}_reg\");")
  s.w(f"super.new(name, {reg_width}, UVM_NO_COVERAGE);")
  s.end("endfunction")
  s.w()
  s.begin("virtual function void build();")
  for field in reg.get("fields", []):
    fname = field["name"]
    access = field.get("access", "RW")
    s.w(f"{fname} = uvm_reg_field::type_id::create(\"{fname}\");")
    s.w(f"{fname}.configure(this, {field['width']}, {field['lsb']}, \"{access}\", "
        f"0, {field.get('reset', 0)}, 1, 1, 0);")
  s.end("endfunction")
  s.w()
  s.end("endclass")
  s.w()


def gen_reg_block(model: Model):
  rm = model.register_model
  block = rm["block_name"]
  reg_width = rm.get("reg_width", 32)
  byte_width = reg_width // 8

  s = SVWriter()
  s.w(f"// {block} Register Model (RAL)")
  s.w()
  for reg in rm.get("registers", []):
    gen_register(model, s, reg, reg_width)

  s.begin(f"class {block} extends uvm_reg_block;")
  s.w()
  s.w(f"`uvm_object_utils({block})")
  s.w()
  for reg in rm.get("registers", []):
    s.w(f"rand {reg['name']}_reg {reg['name']};")
  s.w()
  s.begin(f"function new(string name = \"{block}\");")
  s.w("super.new(name, UVM_NO_COVERAGE);")
  s.end("endfunction")
  s.w()
  s.begin("virtual function void build();")
  s.w(f"default_map = create_map(\"default_map\", 0, {byte_width}, UVM_LITTLE_ENDIAN);")
  for reg in rm.get("registers", []):
    rname = reg["name"]
    s.w(f"{rname} = {rname}_reg::type_id::create(\"{rname}\");")
    s.w(f"{rname}.configure(this);")
    s.w(f"{rname}.build();")
    s.w(f"default_map.add_reg({rname}, 'h{reg['address']:X}, \"RW\");")
  s.end("endfunction")
  s.w()
  s.end("endclass")

  path = model.dir("ral") / f"{block}.sv"
  write_file(path, s.text(), model.overwrite)
  model.register("ral", path)


def gen_adapter(model: Model):
  rm = model.register_model
  block = rm["block_name"]
  # bus item: sequence item of the first active agent's driver
  bus_item = None
  for agent in model.agents.values():
    drv = agent.get("components", {}).get("driver")
    if drv:
      bus_item = drv["sequence_item"]
      break
  if bus_item is None:
    bus_item = next(iter(model.seq_items), "uvm_sequence_item")

  s = SVWriter()
  s.w(f"// {block}_adapter - converts uvm_reg_bus_op <-> {bus_item}")
  s.w()
  s.begin(f"class {block}_adapter extends uvm_reg_adapter;")
  s.w()
  s.w(f"`uvm_object_utils({block}_adapter)")
  s.w()
  s.begin(f"function new(string name = \"{block}_adapter\");")
  s.w("super.new(name);")
  s.w("supports_byte_enable = 0;")
  s.w("provides_responses = 0;")
  s.end("endfunction")
  s.w()
  s.begin("virtual function uvm_sequence_item reg2bus(const ref uvm_reg_bus_op rw);")
  s.w(f"{bus_item} bus_txn = {bus_item}::type_id::create(\"bus_txn\");")
  s.w("// Map register operation (rw.kind, rw.addr, rw.data) onto bus transaction fields")
  s.user_code(f"{block}_adapter_reg2bus")
  s.w("return bus_txn;")
  s.end("endfunction")
  s.w()
  s.begin("virtual function void bus2reg(uvm_sequence_item bus_item, ref uvm_reg_bus_op rw);")
  s.w(f"{bus_item} bus_txn;")
  s.w("if (!$cast(bus_txn, bus_item))")
  s.w(f"  `uvm_fatal(\"{block.upper()}_ADAPTER\", \"bus_item is not a {bus_item}\")")
  s.w("// Map bus transaction fields back onto rw.kind / rw.addr / rw.data / rw.status")
  s.user_code(f"{block}_adapter_bus2reg")
  s.w("rw.status = UVM_IS_OK;")
  s.end("endfunction")
  s.w()
  s.end("endclass")

  path = model.dir("ral") / f"{block}_adapter.sv"
  write_file(path, s.text(), model.overwrite)
  model.register("ral", path)


def generate(model: Model):
  if not (model.register_model.get("enable") and model.enabled("create_ral_model")):
    return
  gen_reg_block(model)
  gen_adapter(model)
