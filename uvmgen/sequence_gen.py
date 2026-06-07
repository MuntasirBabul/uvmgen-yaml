import yaml
from pathlib import Path

with open("config/design.yaml") as f:
  cfg = yaml.safe_load(f)

###########################################################
# Generate sequence.sv
###########################################################
def gen_sequence(sequence):
  sequence_name = sequence["name"]
  out_dir = Path(f"generated/test/sequences/")
  out_dir.mkdir(parents=True, exist_ok=True)
  with open(out_dir / f"{sequence_name}.sv", "w") as f:
    f.write(f"// {sequence_name} Sequence\n\n")
    #f.write(f"`include \"uvm_macros.svh\"\n\n")
    base_class = sequence.get("base_class", "uvm_sequence")
    f.write(f"class {sequence_name} extends {base_class};\n\n")
    f.write(f"  `uvm_object_utils({sequence_name})\n\n")
    f.write(f"   function new(string name = \"{sequence_name}\");\n")
    f.write(f"     super.new(name);\n")
    f.write(f"   endfunction\n\n")
    if "body" in sequence:
      f.write(f"   virtual task body();\n")
      f.write(f"     // Implement sequence body here\n")
      if "num_transactions" in sequence["body"]:
        num_txns = sequence["body"]["num_transactions"]
        f.write(f"     repeat({num_txns}) begin\n")
        f.write(f"       // Create and start child sequences or generate transactions here\n")
        f.write(f"     end\n")
      else:
        f.write(f"     // Create and start child sequences or generate transactions here\n")
      f.write(f"   endtask\n\n")
    f.write(f"endclass\n")

###########################################################
# Execute generation based on config
###########################################################
def main():
  
  for seq in cfg["sequences"]:
    gen_sequence(seq)

if __name__ == "__main__":
  main()