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

  agent_type        = agent.get("type")
  seqr_name         = agent["components"]["sequencer"]["name"]
  interface_name    = agent["components"]["interface"]["name"]
  monitor_name      = agent["components"]["monitor"]["name"] 
  driver_name       = agent["components"]["driver"]["name"]   
  ##################################
  # Generate agent class
  ###################################
  with open(out_dir / f"{agent_name}.sv", "w") as f:
    f.write(f"// {agent_name} Agent\n\n")
    #f.write(f"`include \"uvm_macros.svh\"\n\n")
    f.write(f"class {agent_name} extends uvm_agent;\n\n")
    f.write(f"  `uvm_component_utils({agent_name})\n\n")
    f.write(f"  function new(string name = \"{agent_name}\", uvm_component parent);\n") 
    f.write(f"    super.new(name, parent);\n")
    f.write(f"  endfunction\n\n")
    f.write(f"  // Declare component Handles\n")
    if agent_type == "active":
      seq_item_name = agent["components"]["driver"]["sequence_item"]
      f.write(f"  uvm_sequencer #({seq_item_name}) {seqr_name}_handle;\n")
      f.write(f"  {driver_name} {driver_name}_handle;\n")
    f.write(f"  {monitor_name} {monitor_name}_handle;\n")
    f.write(f"\n")
    f.write(f"  // Build Phase\n")
    f.write(f"  function void build_phase(uvm_phase phase);\n")
    f.write(f"    super.build_phase(phase);\n")
    if agent_type == "active":      
      seq_item_name = agent["components"]["driver"]["sequence_item"]
      f.write(f"     {seqr_name}_handle = uvm_sequencer#({seq_item_name})::type_id::create(\"{seqr_name}_handle\", this);\n")
      f.write(f"     {driver_name}_handle = {driver_name}::type_id::create(\"{driver_name}_handle\", this);\n")
    f.write(f"     {monitor_name}_handle = {monitor_name}::type_id::create(\"{monitor_name}_handle\", this);\n")
    f.write(f"   endfunction\n\n")
    f.write(f"   // Connect Phase\n")
    f.write(f"   function void connect_phase(uvm_phase phase);\n")
    f.write(f"     super.connect_phase(phase);\n")
    if agent_type == "active":
      for connect in agent['connection']:
        f.write(f"     {connect['destination']}_handle.seq_item_port.connect({connect['source']}_handle.seq_item_export);\n")
    f.write(f"   endfunction\n\n")
    f.write(f"endclass\n")
  
  ##################################
  # Generate monitor class
  ###################################
  with open(out_dir / f"{monitor_name}.sv", "w") as f: 
    seq_item_name = agent["components"]["monitor"]["sequence_item"]
    ports = agent["components"]["monitor"]["ports"]
    f.write(f"// {monitor_name} Monitor\n\n")
    #f.write(f"`include \"uvm_macros.svh\"\n\n")
    f.write(f"class {monitor_name} extends uvm_monitor;\n\n")
    f.write(f"  `uvm_component_utils({monitor_name})\n\n")
    f.write(f"  function new(string name = \"{monitor_name}\", uvm_component parent);\n")
    f.write(f"    super.new(name, parent);\n")
    f.write(f"  endfunction\n\n")
    f.write(f"  virtual {interface_name} {interface_name}_handle;\n\n")
    for port in ports:
      f.write(f"  {port['type']}#({port['base_class']}) {port['name']};\n")
    f.write(f"\n  virtual function void build_phase(uvm_phase phase);\n")
    f.write(f"    super.build_phase(phase);\n")
    f.write(f"    if(!uvm_config_db#(virtual {interface_name})::get(this, \"\", \"{interface_name}_handle\", {interface_name}_handle))\n")
    f.write(f"      `uvm_fatal(\"MONITOR\", $sformatf(\"{interface_name} handle not found in config_db\"))\n")
    for port in ports:
      f.write(f"    {port['name']} = new(\"{port['name']}\", this);\n")
    f.write(f"  endfunction\n\n")
    f.write(f"  virtual task run_phase(uvm_phase phase);\n")
    f.write(f"    super.run_phase(phase);\n")
    f.write(f"    // Implement monitor behavior here\n")
    f.write(f"    forever begin\n")
    f.write(f"      // Sample interface signals and create sequence items as needed\n")
    f.write(f"    end\n")
    f.write(f"  endtask\n\n")    
    f.write(f"endclass\n")

  ##################################
  # Generate driver class
  ###################################
  if agent_type == "active":
    with open(out_dir / f"{driver_name}.sv", "w") as f:
      driver_name = agent["components"]["driver"]["name"]
      seq_item_name = agent["components"]["driver"]["sequence_item"]
      f.write(f"// {driver_name} Driver\n\n")
      #f.write(f"`include \"uvm_macros.svh\"\n\n")
      f.write(f"class {driver_name} extends uvm_driver #({seq_item_name});\n\n")
      f.write(f"  `uvm_component_utils({driver_name})\n\n")
      f.write(f"   function new(string name = \"{driver_name}\", uvm_component parent);\n")
      f.write(f"     super.new(name, parent);\n")
      f.write(f"   endfunction\n\n")
      f.write(f"   virtual {interface_name} {interface_name}_handle;\n\n")
      f.write(f"   virtual function void build_phase(uvm_phase phase);\n")
      f.write(f"     super.build_phase(phase);\n")
      f.write(f"     if(!uvm_config_db#(virtual {interface_name})::get(this, \"\", \"{interface_name}_handle\", {interface_name}_handle))\n")
      f.write(f"       `uvm_fatal(\"DRIVER\", $sformatf(\"{interface_name} handle not found in config_db\"))\n")
      f.write(f"   endfunction\n\n")
      f.write(f"   virtual task run_phase(uvm_phase phase);\n")
      f.write(f"     super.run_phase(phase);\n")
      f.write(f"     // Implement driver behavior here\n")
      f.write(f"     forever begin\n")
      f.write(f"       {seq_item_name} {seq_item_name}_handle;\n")
      f.write(f"       seq_item_port.get_next_item({seq_item_name}_handle);\n")
      f.write(f"       // Drive interface signals based on {seq_item_name}_handle fields\n")
      f.write(f"       drive_item({seq_item_name}_handle);\n")
      f.write(f"       seq_item_port.item_done();\n")
      f.write(f"     end\n")
      f.write(f"   endtask\n\n")
      f.write(f"   virtual task drive_item({seq_item_name} {seq_item_name}_handle);\n")
      f.write(f"     // Implement signal driving logic based on {seq_item_name}_handle fields\n")
      f.write(f"   endtask\n\n")
      f.write(f"endclass\n")

    ##################################
    # Generate sequencer class
    ################################### 
    with open(out_dir / f"{seqr_name}.sv", "w") as f:
      f.write(f"// {seqr_name} Sequencer\n\n")
      #f.write(f"`include \"uvm_macros.svh\"\n\n")
      f.write(f"class {seqr_name} extends uvm_sequencer #({seq_item_name});\n\n")
      f.write(f"  `uvm_component_utils({seqr_name})\n\n")
      f.write(f"   function new(string name = \"{seqr_name}\", uvm_component parent);\n")
      f.write(f"     super.new(name, parent);\n")
      f.write(f"   endfunction\n\n")
      f.write(f"endclass\n")

    


###########################################################
# Execute generation based on config
###########################################################
def main():
  
  for agent in cfg["agents"]:
    gen_agent(agent)

if __name__ == "__main__":
  main()