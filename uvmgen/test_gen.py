import yaml
from pathlib import Path

with open("config/design.yaml") as f:
  cfg = yaml.safe_load(f)

###########################################################
# Generate test.sv
###########################################################
def gen_test(test):
  test_name = test["name"]
  interfaces = cfg['interface']
  out_dir = Path(f"generated/test/")
  out_dir.mkdir(parents=True, exist_ok=True)
  with open(out_dir / f"{test_name}.sv", "w") as f:
    f.write(f"// {test_name} Test\n\n")
    #f.write(f"`include \"uvm_macros.svh\"\n\n")
    f.write(f"class {test_name} extends {test['base_class']};\n\n")
    f.write(f"  `uvm_component_utils({test_name})\n\n")
    f.write(f"  function new(string name = \"{test_name}\", uvm_component parent);\n")
    f.write(f"    super.new(name, parent);\n")
    f.write(f"  endfunction\n\n")
    f.write(f"  {test['environment']} {test['environment']}_handle;\n")
    for intf in interfaces:
      f.write(f"  virtual {intf['name']} {intf['name']}_handle;\n")
    f.write(f"\n  virtual function void build_phase(uvm_phase phase);\n")
    f.write(f"    super.build_phase(phase);\n")
    f.write(f"    // Instantiate environment here based on config\n")
    f.write(f"    {test['environment']}_handle = {test['environment']}::type_id::create(\"{test['environment']}_handle\", this);\n")
    f.write(f"    if (!uvm_config_db#(virtual {intf['name']})::get(this, \"\", \"{intf['name']}_handle\", {intf['name']}_handle))\n")
    f.write(f"      `uvm_fatal(\"TEST\", \"Did not get vif\")\n")
    f.write(f"    else\n")
    # TODO fix accessing agent obj
    f.write(f"      uvm_config_db#(virtual {intf['name']})::set(this, \"{test['environment']}_handle.dff_agent_obj.*\", \"{intf['name']}_handle\", {intf['name']}_handle);\n")
    f.write(f"  endfunction\n\n")
    f.write(f"  virtual task run_phase(uvm_phase phase);\n")
    f.write(f"    super.run_phase(phase);\n")
    f.write(f"    // Start the test sequence here\n")
    f.write(f"  endtask\n\n")
    f.write(f"endclass\n")

###########################################################
# Execute generation based on config
###########################################################
def main():
  
  for test in cfg["tests"]:
    gen_test(test)

if __name__ == "__main__":
  main()