import yaml
from pathlib import Path

with open("config/design.yaml") as f:
  cfg = yaml.safe_load(f)

###########################################################
# Generate RAL register classes and block
###########################################################
def gen_ral():
  reg_model = cfg.get("register_model")
  if not reg_model or not reg_model.get("enable"):
    return

  block_name = reg_model["block_name"]
  registers  = reg_model["registers"]
  out_dir    = Path("generated/ral/")
  out_dir.mkdir(parents=True, exist_ok=True)

  with open(out_dir / f"{block_name}.sv", "w") as f:

    # One uvm_reg subclass per register
    for reg in registers:
      reg_class = f"{block_name}_{reg['name'].lower()}_reg"
      f.write(f"// {reg['name']} register\n")
      f.write(f"class {reg_class} extends uvm_reg;\n\n")
      f.write(f"  `uvm_object_utils({reg_class})\n\n")
      for field in reg["fields"]:
        f.write(f"  rand uvm_reg_field {field['name']};\n")
      f.write(f"\n  function new(string name = \"{reg_class}\");\n")
      f.write(f"    super.new(name, 32, UVM_NO_COVERAGE);\n")
      f.write(f"  endfunction\n\n")
      f.write(f"  virtual function void build();\n")
      for field in reg["fields"]:
        f.write(f"    {field['name']} = uvm_reg_field::type_id::create(\"{field['name']}\");\n")
        # configure(parent, size, lsb_pos, access, volatile, reset, has_reset, is_rand, individually_accessible)
        f.write(f"    {field['name']}.configure(this, {field['width']}, {field['lsb']}, \"RW\", 0, 0, 1, 1, 0);\n")
      f.write(f"  endfunction\n\n")
      f.write(f"endclass\n\n")

    # Register block
    f.write(f"// {block_name} register block\n")
    f.write(f"class {block_name} extends uvm_reg_block;\n\n")
    f.write(f"  `uvm_object_utils({block_name})\n\n")
    for reg in registers:
      reg_class  = f"{block_name}_{reg['name'].lower()}_reg"
      reg_handle = reg['name'].lower()
      f.write(f"  rand {reg_class} {reg_handle};\n")
    f.write(f"\n  function new(string name = \"{block_name}\");\n")
    f.write(f"    super.new(name, UVM_NO_COVERAGE);\n")
    f.write(f"  endfunction\n\n")
    f.write(f"  virtual function void build();\n")
    f.write(f"    default_map = create_map(\"default_map\", 0, 4, UVM_LITTLE_ENDIAN);\n")
    for reg in registers:
      reg_class  = f"{block_name}_{reg['name'].lower()}_reg"
      reg_handle = reg['name'].lower()
      f.write(f"    {reg_handle} = {reg_class}::type_id::create(\"{reg_handle}\");\n")
      f.write(f"    {reg_handle}.build();\n")
      f.write(f"    {reg_handle}.configure(this);\n")
      f.write(f"    default_map.add_reg({reg_handle}, {reg['address']}, \"RW\");\n")
    f.write(f"  endfunction\n\n")
    f.write(f"endclass\n")

###########################################################
# Execute generation based on config
###########################################################
def main():
  gen_ral()

if __name__ == "__main__":
  main()
