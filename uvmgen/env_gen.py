import yaml
from pathlib import Path

with open("config/design.yaml") as f:
  cfg = yaml.safe_load(f)

###########################################################
# Generate coverage.sv
###########################################################

def gen_coverage(coverage):
  cov_name = coverage["name"]
  out_dir = Path(f"generated/env/")
  out_dir.mkdir(parents=True, exist_ok=True)

  with open(out_dir / f"{cov_name}.sv", "w") as f:
    f.write(f"// {cov_name} Coverage\n\n")
    #f.write(f"`include \"uvm_macros.svh\"\n\n")
    f.write(f"class {cov_name} extends uvm_subscriber;\n\n")
    f.write(f"  `uvm_component_utils({cov_name})\n\n")
    f.write(f"   function new(string name = \"{cov_name}\", uvm_component parent);\n")
    f.write(f"     super.new(name, parent);\n")
    f.write(f"   endfunction\n\n")
    f.write(f"   virtual function void build_phase(uvm_phase phase);\n")
    f.write(f"     super.build_phase(phase);\n")
    f.write(f"     // Subscribe to analysis ports here\n")
    f.write(f"   endfunction\n\n")
    f.write(f"endclass\n")    

###########################################################
# Generate scoreboard.sv
###########################################################
def gen_scoreboard(scoreboard):
  scoreboard_name = scoreboard["name"]
  seq_item_name = scoreboard["sequence_item"]
  out_dir = Path(f"generated/env/")
  out_dir.mkdir(parents=True, exist_ok=True)
  with open(out_dir / f"{scoreboard_name}.sv", "w") as f:
    f.write(f"// {scoreboard_name} Scoreboard\n\n")
    #f.write(f"`include \"uvm_macros.svh\"\n\n")
    f.write(f"class {scoreboard_name} extends uvm_scoreboard;\n\n")
    f.write(f"  `uvm_component_utils({scoreboard_name})\n\n")
    f.write(f"  function new(string name = \"{scoreboard_name}\", uvm_component parent);\n")
    f.write(f"    super.new(name, parent);\n")
    f.write(f"  endfunction\n\n")
    for port in scoreboard['ports']:
      f.write(f"  {port['type']} #({port['base_class']}) {port['name']}\n")
    f.write(f"\n  virtual function void build_phase(uvm_phase phase);\n")
    f.write(f"    super.build_phase(phase);\n")
    for port in scoreboard['ports']:
      f.write(f"    {port['name']} = new(\"{port['name']}\", this);\n")
    f.write(f"  endfunction\n\n")
    f.write(f"  virtual function void write_actual({seq_item_name} item);\n")
    f.write(f"    // Implement actual item processing and checking logic here\n")
    f.write(f"  endfunction\n\n")
    f.write(f"  virtual function void write_expected({seq_item_name} item);\n")
    f.write(f"    // Implement expected item processing logic here\n")
    f.write(f"  endfunction\n\n")
    f.write(f"endclass\n")

###########################################################
# Generate environment.sv
###########################################################
def gen_env(environment):
  env_name = environment["name"]
  out_dir = Path(f"generated/env/")
  out_dir.mkdir(parents=True, exist_ok=True)
  with open(out_dir / f"{env_name}.sv", "w") as f:
    f.write(f"// {env_name} Environment\n\n")
    #f.write(f"`include \"uvm_macros.svh\"\n\n")
    f.write(f"class {env_name} extends uvm_env;\n\n")
    f.write(f"  `uvm_component_utils({env_name})\n\n")
    f.write(f"   function new(string name = \"{env_name}\", uvm_component parent);\n")
    f.write(f"     super.new(name, parent);\n")
    f.write(f"   endfunction\n\n")
    f.write(f"   // Instantiate agents, scoreboard, coverage collectors here based on config\n")
    for agent in environment["components"]["agents"]:
      for i in range(agent['num_obj']):
        f.write(f"   {agent['name']} {agent['name']}_handle_{i};\n")
    f.write(f"   {environment['components']['scoreboard']} {environment['components']['scoreboard']}_handle;\n\n")
    f.write(f"   virtual function void build_phase(uvm_phase phase);\n")
    f.write(f"     super.build_phase(phase);\n")
    for agent in environment["components"]["agents"]:
      for i in range(agent['num_obj']):
        f.write(f"     {agent['name']}_handle_{i} = {agent['name']}::type_id::create(\"{agent['name']}_handle_{i}\", this);\n")
    f.write(f"     {environment['components']['scoreboard']}_handle = {environment['components']['scoreboard']}::type_id::create(\"{environment['components']['scoreboard']}_handle\", this);\n")
    f.write(f"   endfunction\n\n")
    f.write(f"  virtual function void connect_phase(uvm_phase phase);\n")
    f.write(f"    super.connect_phase(phase);\n")
    f.write(f"    // Connect analysis ports between agents and scoreboard here based on config\n")
    for connection in environment["connections"]:
      src = connection["source"]
      dst = connection["destination"]
      for i in range(agent['num_obj']):
        f.write(f"    {agent['name']}_handle_{i}.{src}.connect({dst});\n")
    f.write(f"  endfunction\n\n")
    f.write(f"endclass\n")

###########################################################
# Execute generation based on config
###########################################################
def main():
  
  for item in cfg["coverage"]:
    gen_coverage(item)

  for sb in cfg["scoreboard"]:
    gen_scoreboard(sb)

  for env in cfg["environment"]:
    gen_env(env)

if __name__ == "__main__":
  main()