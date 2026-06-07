import yaml
from pathlib import Path

with open("config/design.yaml") as f:
  cfg = yaml.safe_load(f)

###########################################################
# Generate sequence_item.sv
###########################################################
def gen_sequence_item(seq_item):
  seq_item_name = seq_item["name"]
  out_dir = Path(f"generated/test/seq_items/")
  out_dir.mkdir(parents=True, exist_ok=True)
  with open(out_dir / f"{seq_item_name}.sv", "w") as f:
    f.write(f"// {seq_item_name} Sequence Item\n\n")
    #f.write(f"`include \"uvm_macros.svh\"\n\n")
    f.write(f"class {seq_item_name} extends uvm_sequence_item;\n\n")
    f.write(f"  `uvm_object_utils({seq_item_name})\n\n")
    f.write(f"   function new(string name = \"{seq_item_name}\");\n")
    f.write(f"     super.new(name);\n")
    f.write(f"   endfunction\n\n")
    f.write(f"   // Declare transaction fields\n")
    for field in seq_item["fields"]:
      f.write(f"   {field['type']} {field['name']};\n")
    f.write(f"\n")
    f.write(f"   // Use utility macros to implement standard functions\n")
    f.write(f"   `uvm_object_utils_begin({seq_item_name})\n")
    for field in seq_item["fields"]:      
      f.write(f"    `uvm_field_int({field['name']}, UVM_ALL_ON)\n")
    f.write(f"   `uvm_object_utils_end\n\n")

    if "constraints" in seq_item:
      f.write(f"   // Constraints\n")
      for c in seq_item["constraints"]:
        f.write(f"   constraint {c['name']} \n")
        f.write("   { \n")
        for item in c['items']:
          f.write(f"     {item}\n")
        f.write("   }\n\n")
    f.write(f"endclass\n")

###########################################################
# Execute generation based on config
###########################################################
def main():
  
  for item in cfg["sequence_items"]:
    gen_sequence_item(item)

if __name__ == "__main__":
  main()