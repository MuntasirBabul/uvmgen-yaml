###########################################################
# interface_gen.py - generate SystemVerilog interfaces
###########################################################
from core import Model, SVWriter, write_file


def gen_interface(model: Model, intf):
  name = intf["name"]
  clock = intf.get("clock")
  reset = intf.get("reset")

  s = SVWriter()
  s.w(f"// {name} Interface")
  s.w()
  s.begin(f"interface {name};")
  s.w()
  if clock:
    s.w(f"logic {clock};")
  if reset:
    s.w(f"logic {reset};")
  for sig in intf.get("signals", []):
    s.w(f"{sig['type']} {sig['name']};")
  s.w()
  if clock:
    s.begin(f"clocking drv_cb @(posedge {clock});")
    s.w("default input #1step output #1;")
    s.user_code(f"{name}_drv_cb_directions")
    s.end("endclocking")
    s.w()
    s.begin(f"clocking mon_cb @(posedge {clock});")
    s.w("default input #1step;")
    s.user_code(f"{name}_mon_cb_directions")
    s.end("endclocking")
    s.w()
  s.end("endinterface")

  path = model.dir("interfaces") / f"{name}.sv"
  write_file(path, s.text(), model.overwrite)
  model.interface_files.append(path)


def generate(model: Model):
  if not model.enabled("create_interface"):
    return
  for intf in model.interfaces.values():
    gen_interface(model, intf)
