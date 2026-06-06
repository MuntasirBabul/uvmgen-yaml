from multiprocessing.dummy import connection

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

  agent_type        = agent.get("type", "active")
  seqr_name         = agent["components"]["sequencer"]["name"]
  interface_name    = agent["components"]["interface"]["name"]
  monitor_name      = agent["components"]["monitor"]["name"] 
  driver_name       = agent["components"]["driver"]["name"]   
  ##################################
  # Generate agent class
  ###################################
  with open(out_dir / f"{agent_name}.sv", "w") as f:
    f.write(f"// {agent_name} Agent\n\n")
    #f.write("`include \"uvm_macros.svh\"\n\n")
    f.write(f"class {agent_name} extends uvm_agent;\n\n")
    f.write(f"  `uvm_component_utils({agent_name})\n\n")
    f.write("   function new(string name, uvm_component parent);\n") 
    f.write("     super.new(name, parent);\n")
    f.write("   endfunction\n\n")
    f.write("   // Declare component Handles\n")
    if agent_type == "active":
      seq_item_name = agent["components"]["driver"]["sequence_item"]
      f.write(f"   uvm_sequencer #({seq_item_name}) {seqr_name}_handle;\n")
      f.write(f"   {driver_name} {driver_name}_handle;\n")
    f.write(f"   {monitor_name} {monitor_name}_handle;\n")
    f.write("\n")
    f.write("   // Build Phase\n")
    f.write("   function void build_phase(uvm_phase phase);\n")
    f.write("     super.build_phase(phase);\n")
    if agent_type == "active":      
      seq_item_name = agent["components"]["driver"]["sequence_item"]
      f.write(f"     {seqr_name}_handle = uvm_sequencer#({seq_item_name})::type_id::create(\"{seqr_name}_handle\", this);\n")
      f.write(f"     {driver_name}_handle = {driver_name}::type_id::create(\"{driver_name}_handle\", this);\n")
    f.write(f"     {monitor_name}_handle = {monitor_name}::type_id::create(\"{monitor_name}_handle\", this);\n")
    f.write("   endfunction\n\n")
    f.write("   // Connect Phase\n")
    f.write("   function void connect_phase(uvm_phase phase);\n")
    f.write("     super.connect_phase(phase);\n")
    if agent_type == "active":
      f.write(f"     {driver_name}_handle.seq_item_port.connect({seqr_name}_handle.seq_item_export); // Connect driver to sequencer\n")
    f.write("   endfunction\n\n")
    f.write("endclass\n")
  
  ##################################
  # Generate monitor class
  ###################################
  with open(out_dir / f"{monitor_name}.sv", "w") as f: 
    seq_item_name = agent["components"]["monitor"]["sequence_item"]
    f.write(f"// {monitor_name} Monitor\n\n")
    #f.write("`include \"uvm_macros.svh\"\n\n")
    f.write(f"class {monitor_name} extends uvm_monitor;\n\n")
    f.write(f"  `uvm_component_utils({monitor_name})\n\n")
    f.write(f"   function new(string name, uvm_component parent);\n")
    f.write(f"     super.new(name, parent);\n")
    f.write(f"   endfunction\n\n")
    f.write(f"   virtual {interface_name} {interface_name}_handle;\n\n")
    f.write(f"   uvm_analysis_port#({seq_item_name}) monitor_analysis_port;\n\n")
    f.write(f"   virtual function void build_phase(uvm_phase phase);\n")
    f.write(f"     super.build_phase(phase);\n")
    f.write(f"     if(!uvm_config_db#(virtual {interface_name})::get(this, \"\", \"{interface_name}_handle\", {interface_name}_handle))\n")
    f.write(f"       `uvm_fatal(\"MONITOR\", $sformatf(\"{interface_name} handle not found in config_db\"))\n")
    f.write(f"     monitor_analysis_port = new(\"monitor_analysis_port\", this);\n")
    f.write(f"   endfunction\n\n")
    f.write(f"   virtual task run_phase(uvm_phase phase);\n")
    f.write(f"     super.run_phase(phase);\n")
    f.write(f"     // Implement monitor behavior here\n")
    f.write(f"     forever begin\n")
    f.write(f"       // Sample interface signals and create sequence items as needed\n")
    f.write(f"     end\n")
    f.write(f"   endtask\n\n")    
    f.write(f"endclass\n")

  ##################################
  # Generate interface 
  ###################################
  with open(out_dir / f"{interface_name}.sv", "w") as f:
    f.write(f"// {interface_name} Interface\n\n")
    f.write(f"interface {interface_name};\n\n")
    for signal in agent["components"]["interface"]["signals"]:
      f.write(f"  {signal['type']} {signal['name']};\n")
    f.write("\nendinterface\n")

  ##################################
  # Generate driver class
  ###################################
  if agent_type == "active":
    with open(out_dir / f"{driver_name}.sv", "w") as f:
      driver_name = agent["components"]["driver"]["name"]
      seq_item_name = agent["components"]["driver"]["sequence_item"]
      f.write(f"// {driver_name} Driver\n\n")
      #f.write("`include \"uvm_macros.svh\"\n\n")
      f.write(f"class {driver_name} extends uvm_driver #({seq_item_name});\n\n")
      f.write(f"  `uvm_component_utils({driver_name})\n\n")
      f.write(f"   function new(string name, uvm_component parent);\n")
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
      #f.write("`include \"uvm_macros.svh\"\n\n")
      f.write(f"class {seqr_name} extends uvm_sequencer #({seq_item_name});\n\n")
      f.write(f"  `uvm_component_utils({seqr_name})\n\n")
      f.write(f"   function new(string name, uvm_component parent);\n")
      f.write("     super.new(name, parent);\n")
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

def gen_coverage(coverage):
  coverage_name = coverage["name"]
  out_dir = Path(f"generated/coverage/")
  out_dir.mkdir(parents=True, exist_ok=True)
  with open(out_dir / f"{coverage_name}.sv", "w") as f:
    f.write(f"// {coverage_name} Coverage\n\n")
    #f.write("`include \"uvm_macros.svh\"\n\n")
    f.write(f"class {coverage_name} extends uvm_subscriber;\n\n")
    f.write(f"  `uvm_component_utils({coverage_name})\n\n")
    f.write(f"   function new(string name, uvm_component parent);\n")
    f.write("     super.new(name, parent);\n")
    f.write("   endfunction\n\n")
    f.write("   virtual function void build_phase(uvm_phase phase);\n")
    f.write("     super.build_phase(phase);\n")
    f.write("     // Subscribe to analysis ports here\n")
    f.write("   endfunction\n\n")
    f.write("endclass\n")

def gen_sequence(sequence):
  sequence_name = sequence["name"]
  out_dir = Path(f"generated/sequences/")
  out_dir.mkdir(parents=True, exist_ok=True)
  with open(out_dir / f"{sequence_name}.sv", "w") as f:
    f.write(f"// {sequence_name} Sequence\n\n")
    #f.write("`include \"uvm_macros.svh\"\n\n")
    base_class = sequence.get("base_class", "uvm_sequence")
    f.write(f"class {sequence_name} extends {base_class};\n\n")
    f.write(f"  `uvm_object_utils({sequence_name})\n\n")
    f.write(f"   function new(string name = \"{sequence_name}\");\n")
    f.write(f"     super.new(name);\n")
    f.write(f"   endfunction\n\n")
    if "body" in sequence:
      f.write("   virtual task body();\n")
      f.write("     // Implement sequence body here\n")
      if "num_transactions" in sequence["body"]:
        num_txns = sequence["body"]["num_transactions"]
        f.write(f"     repeat({num_txns}) begin\n")
        f.write("       // Create and start child sequences or generate transactions here\n")
        f.write("     end\n")
      else:
        f.write("     // Create and start child sequences or generate transactions here\n")
      f.write("   endtask\n\n")
    f.write("endclass\n")

def gen_scoreboard(scoreboard):
  scoreboard_name = scoreboard["name"]
  seq_item_name = scoreboard["sequence_item"]
  out_dir = Path(f"generated/env/")
  out_dir.mkdir(parents=True, exist_ok=True)
  with open(out_dir / f"{scoreboard_name}.sv", "w") as f:
    f.write(f"// {scoreboard_name} Scoreboard\n\n")
    #f.write("`include \"uvm_macros.svh\"\n\n")
    f.write(f"class {scoreboard_name} extends uvm_scoreboard;\n\n")
    f.write(f"  `uvm_component_utils({scoreboard_name})\n\n")
    f.write(f"  function new(string name, uvm_component parent);\n")
    f.write(f"    super.new(name, parent);\n")
    f.write(f"  endfunction\n\n")
    f.write(f"  uvm_analysis_imp #({seq_item_name},{scoreboard_name}) actual;\n")
    f.write(f"  uvm_analysis_imp #({seq_item_name},{scoreboard_name}) expected;\n\n")
    f.write(f"  virtual function void build_phase(uvm_phase phase);\n")
    f.write(f"    super.build_phase(phase);\n")
    f.write(f"    actual = new(\"actual\", this);\n")
    f.write(f"    expected = new(\"expected\", this);\n")
    f.write(f"  endfunction\n\n")
    f.write(f"  virtual function void write_actual({seq_item_name} item);\n")
    f.write(f"    // Implement actual item processing and checking logic here\n")
    f.write(f"  endfunction\n\n")
    f.write(f"  virtual function void write_expected({seq_item_name} item);\n")
    f.write(f"    // Implement expected item processing logic here\n")
    f.write(f"  endfunction\n\n")
    f.write(f"endclass\n")

def gen_env(environment):
  env_name = environment["name"]
  out_dir = Path(f"generated/env/")
  out_dir.mkdir(parents=True, exist_ok=True)
  with open(out_dir / f"{env_name}.sv", "w") as f:
    f.write(f"// {env_name} Environment\n\n")
    #f.write("`include \"uvm_macros.svh\"\n\n")
    f.write(f"class {env_name} extends uvm_env;\n\n")
    f.write(f"  `uvm_component_utils({env_name})\n\n")
    f.write(f"   function new(string name, uvm_component parent);\n")
    f.write(f"     super.new(name, parent);\n")
    f.write(f"   endfunction\n\n")
    f.write(f"   // Instantiate agents, scoreboard, coverage collectors here based on config\n")
    for agent in environment["components"]["agents"]:
      f.write(f"   {agent} {agent}_handle;\n")
    f.write(f"   {environment['components']['scoreboard']} {environment['components']['scoreboard']}_handle;\n\n")
    f.write(f"   virtual function void build_phase(uvm_phase phase);\n")
    f.write(f"     super.build_phase(phase);\n")
    for agent in environment["components"]["agents"]:
      f.write(f"     {agent}_handle = {agent}::type_id::create(\"{agent}_handle\", this);\n")
    f.write(f"     {environment['components']['scoreboard']}_handle = {environment['components']['scoreboard']}::type_id::create(\"{environment['components']['scoreboard']}_handle\", this);\n")
    f.write(f"   endfunction\n\n")
    f.write(f"  virtual function void connect_phase(uvm_phase phase);\n")
    f.write(f"    super.connect_phase(phase);\n")
    f.write(f"    // Connect analysis ports between agents and scoreboard here based on config\n")
    for connection in environment["connections"]:
      src = connection["source"]
      dst = connection["destination"]
      f.write(f"    {src}.connect({dst});\n")
    
    
    f.write(f"  endfunction\n\n")
    f.write("endclass\n")



def main():
  
  for agent in cfg["agents"]:
    gen_agent(agent)

  for seq_item in cfg["sequence_items"]:
    gen_sequence_item(seq_item)

  for sequence in cfg["sequences"]:
    gen_sequence(sequence)

  for scoreboard in cfg["scoreboard"]:
    gen_scoreboard(scoreboard)

  for env in cfg["environment"]:
    gen_env(env)
if __name__ == "__main__":
  main()
