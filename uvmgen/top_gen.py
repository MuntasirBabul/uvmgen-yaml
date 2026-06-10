import yaml
from pathlib import Path

with open("config/design.yaml") as f:
  cfg = yaml.safe_load(f)

###########################################################
# Generate top.sv
###########################################################
def gen_top(project):
  out_dir = Path(f"generated/")
  out_dir.mkdir(parents=True, exist_ok=True)
  with open(out_dir / f"{project['name']}.sv", "w") as f:
    f.write(f"`include \"uvm_macros.svh\"\n")
    f.write(f"import uvm_pkg::*;\n")
    f.write(f"`include \"{project['dut_name']}_include_files.sv\"\n\n")
    f.write(f"module {project['name']};\n")
    f.write(f"  // --------------------------------- \n")
    f.write(f"  // Clock generation \n")
    f.write(f"  // --------------------------------- \n")
    f.write(f"  // --------------------------------- \n")
    f.write(f"  // Instantiate Interfaces Here \n")
    f.write(f"  // --------------------------------- \n")
    for intf in cfg['interface']:
      f.write(f"  {intf['name']} {intf['name']}_handle();\n")

    f.write(f"  // --------------------------------- \n")
    f.write(f"  // DUT instantiate \n")
    f.write(f"  // --------------------------------- \n")
    f.write(f"  // --------------------------------- \n")
    f.write(f"  // UVM Start up \n")
    f.write(f"  // --------------------------------- \n")
    f.write(f"  initial begin\n")
    f.write(f"    `uvm_info(\"INFO-TOP\", \"Starting UVM testbench\", UVM_LOW)\n")
    f.write(f"    // Give interface to UVM world\n")
    for intf in cfg['interface']:
      f.write(f"    uvm_config_db#(virtual {intf['name']})::set(null, \"*\", \"{intf['name']}_handle\", {intf['name']}_handle);\n")
    f.write(f"    // Provide test name\n")
    f.write(f"    run_test(\"\");\n")
    f.write(f"  end\n")
    f.write(f"endmodule : {project['name']}\n")

###########################################################
# Execute generation based on config
###########################################################
def main():
  for project in cfg['project']:
    gen_top(project)

if __name__ == "__main__":
  main()
