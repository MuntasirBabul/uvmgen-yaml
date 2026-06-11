###########################################################
# top_gen.py - generate top-level testbench module
###########################################################
from core import Model, SVWriter, write_file, handle_name


def gen_top(model: Model):
  proj = model.project
  top_name = proj["name"]
  pkg = proj["package_name"]
  dut = proj["dut_name"]

  s = SVWriter()
  s.w("`include \"uvm_macros.svh\"")
  s.w()
  s.begin(f"module {top_name};")
  s.w()
  s.w("import uvm_pkg::*;")
  s.w(f"import {pkg}::*;")
  s.w()
  s.w("// ---------------------------------")
  s.w("// Interfaces")
  s.w("// ---------------------------------")
  for intf in model.interfaces.values():
    s.w(f"{intf['name']} {handle_name(intf['name'])}();")
  s.w()
  s.w("// ---------------------------------")
  s.w("// Clock / Reset generation")
  s.w("// ---------------------------------")
  for intf in model.interfaces.values():
    clock = intf.get("clock")
    reset = intf.get("reset")
    vif = handle_name(intf["name"])
    if clock:
      s.w(f"initial {vif}.{clock} = 0;")
      s.w(f"always #5 {vif}.{clock} = ~{vif}.{clock};")
    if reset:
      s.begin("initial begin")
      s.w(f"{vif}.{reset} = 1;")
      s.w(f"repeat (5) @(posedge {vif}.{clock});" if clock else "#50;")
      s.w(f"{vif}.{reset} = 0;")
      s.end("end")
  s.w()
  s.w("// ---------------------------------")
  s.w(f"// DUT instantiation ({dut})")
  s.w("// ---------------------------------")
  s.user_code(f"{dut}_instantiation")
  s.w()
  s.w("// ---------------------------------")
  s.w("// UVM start up")
  s.w("// ---------------------------------")
  s.begin("initial begin")
  s.w(f"`uvm_info(\"TOP\", \"Starting UVM testbench\", UVM_LOW)")
  s.w("// Hand interfaces to the UVM world")
  for intf in model.interfaces.values():
    vif = handle_name(intf["name"])
    s.w(f"uvm_config_db#(virtual {intf['name']})::set(null, \"uvm_test_top*\", \"{vif}\", {vif});")
  s.w("// Test selected with +UVM_TESTNAME=<test>")
  s.w("run_test();")
  s.end("end")
  s.w()
  s.end(f"endmodule : {top_name}")

  path = model.root / f"{top_name}.sv"
  write_file(path, s.text(), model.overwrite)
  model.top_file = path


def generate(model: Model):
  if model.enabled("create_top_tb"):
    gen_top(model)
