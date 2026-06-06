import yaml
from pathlib import Path

with open("config/design.yaml") as f:
  cfg = yaml.safe_load(f)



###########################################################
# Generate agent.sv
###########################################################
def gen_agent(agent):
  agent_name = agent["name"]
  out_dir = Path(f"generated/{agent_name}")
  out_dir.mkdir(parents=True, exist_ok=True)

  enable_driver     = agent.get("components", {}).get("driver", {}).get("generate", False)
  enable_monitor    = agent.get("components", {}).get("monitor", {}).get("generate",False)
  enable_sequencer  = agent.get("components", {}).get("sequencer", {}).get("generate", False)
  enable_coverage   = agent.get("components", {}).get("coverage", {}).get("enable", False)
  agent_type        = agent.get("type", "active")
  seq_item_name     = agent["components"]["driver"]["components"]["sequence_item"]
  seqr_name         = agent["components"]["sequencer"]["name"]
  driver_name       = agent["components"]["driver"]["name"]
  monitor_name      = agent["components"]["monitor"]["name"]  
  
  with open(out_dir / f"{seqr_name}.sv", "w") as f:
    f.write(f"// {seqr_name} Sequencer\n\n")
    #f.write("`include \"uvm_macros.svh\"\n\n")
    f.write(f"class {seqr_name} extends uvm_sequencer #({seq_item_name});\n\n")
    f.write(f"  `uvm_component_utils({seqr_name})\n\n")
    f.write(f"   function new(string name, uvm_component parent);\n")
    f.write("     super.new(name, parent);\n")
    f.write("   endfunction\n\n")
    f.write("endclass\n")
    
  with open(out_dir / f"{agent_name}.sv", "w") as f:
    f.write(f"// {agent_name} Agent\n\n")
    #f.write("`include \"uvm_macros.svh\"\n\n")
    f.write(f"class {agent_name} extends uvm_agent;\n\n")
    f.write(f"  `uvm_component_utils({agent_name})\n\n")
    f.write("   function new(string name, uvm_component parent);\n") 
    f.write("     super.new(name, parent);\n")
    f.write("   endfunction\n\n")
    f.write("   // Declare component Handles\n")
    if enable_sequencer and agent_type == "active":
      f.write(f"   uvm_sequencer #({seq_item_name}) {seqr_name}_handle;\n")
    if enable_driver and agent_type == "active":
      f.write(f"   {driver_name} {driver_name}_handle;\n")
    if enable_monitor:
      f.write(f"   {monitor_name} {monitor_name}_handle;\n")
    f.write("\n")
    f.write("   // Build Phase\n")
    f.write("   function void build_phase(uvm_phase phase);\n")
    f.write("     super.build_phase(phase);\n")
    if enable_sequencer and agent_type == "active":      
      f.write(f"     {seqr_name}_handle = uvm_sequencer#({seq_item_name})::type_id::create(\"{seqr_name}_handle\", this);\n")
    if enable_driver and agent_type == "active":
      f.write(f"     {driver_name}_handle = {driver_name}::type_id::create(\"{driver_name}_handle\", this);\n")
    if enable_monitor:
      f.write(f"     {monitor_name}_handle = {monitor_name}::type_id::create(\"{monitor_name}_handle\", this);\n")
    f.write("   endfunction\n\n")
    f.write("   // Connect Phase\n")
    f.write("   function void connect_phase(uvm_phase phase);\n")
    f.write("     super.connect_phase(phase);\n")
    if enable_driver and enable_sequencer and agent_type == "active":
      f.write(f"     {driver_name}_handle.seq_item_port.connect({seqr_name}_handle.seq_item_export); // Connect driver to sequencer\n")
    f.write("   endfunction\n\n")
    f.write("endclass\n")
  
###########################################################
# Generate sequence_item.sv
###########################################################
def gen_sequence_item(seq_item):
  seq_item_name = seq_item["name"]
  out_dir = Path(f"generated/seq_items/")
  out_dir.mkdir(parents=True, exist_ok=True)
  with open(out_dir / f"{seq_item_name}.sv", "w") as f:
    f.write(f"// {seq_item_name} Sequence Item\n\n")
    #f.write("`include \"uvm_macros.svh\"\n\n")
    f.write(f"class {seq_item_name} extends uvm_sequence_item;\n\n")
    f.write(f"  `uvm_object_utils({seq_item_name})\n\n")
    f.write(f"   function new(string name = \"{seq_item_name}\");\n")
    f.write("     super.new(name);\n")
    f.write("   endfunction\n\n")
    f.write("   // Declare transaction fields\n")
    for field in seq_item["fields"]:
      f.write(f"   {field['type']} {field['name']};\n")
    f.write("\n")
    f.write("   // Use utility macros to implement standard functions\n")
    f.write(f"   `uvm_object_utils_begin({seq_item_name})\n")
    for field in seq_item["fields"]:      
      f.write(f"    `uvm_field_int({field['name']}, UVM_ALL_ON)\n")
    f.write("   `uvm_object_utils_end\n\n")

    if "constraints" in seq_item:
      f.write("   // Constraints\n")
      for c in seq_item["constraints"]:
        f.write(f"   constraint {c['name']} \n")
        f.write("   { \n")
        for item in c['items']:
          f.write(f"     {item}\n")
        f.write("   }\n\n")
    
    f.write("endclass\n")
  
def main():
  
  for agent in cfg["agents"]:
    gen_agent(agent)

  for seq_item in cfg["sequence_items"]:
    gen_sequence_item(seq_item)

if __name__ == "__main__":
  main()
