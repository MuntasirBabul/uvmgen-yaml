import yaml
from pathlib import Path

with open("config/design.yaml") as f:
  cfg = yaml.safe_load(f)

###########################################################
# Generate coverage.sv
###########################################################

def _find_coverage_seq_item(cov_name):
  """Infer the sequence_item type for a coverage class from the agent that uses it."""
  for agent in cfg.get("agents", []):
    agent_cov = agent["components"].get("coverage", {})
    if agent_cov.get("name") == cov_name:
      return agent["components"]["monitor"]["sequence_item"]
  return "uvm_sequence_item"

def gen_coverage(coverage):
  cov_name = coverage["name"]
  seq_item = _find_coverage_seq_item(cov_name)
  out_dir = Path(f"generated/env/")
  out_dir.mkdir(parents=True, exist_ok=True)

  with open(out_dir / f"{cov_name}.sv", "w") as f:
    f.write(f"// {cov_name} Coverage\n\n")
    f.write(f"class {cov_name} extends uvm_subscriber #({seq_item});\n\n")
    f.write(f"  `uvm_component_utils({cov_name})\n\n")

    # Covergroup definitions
    for cg in coverage.get("covergroups", []):
      f.write(f"  covergroup {cg['name']};\n")
      for cp in cg.get("coverpoints", []):
        field = cp["field"]
        bins_list = cp.get("bins", [])
        if bins_list:
          f.write(f"    {field}_cp: coverpoint trans.{field} {{\n")
          for b in bins_list:
            f.write(f"      bins {b} = {{[0:0]}}; // TODO: set range for {b}\n")
          f.write(f"    }}\n")
        else:
          f.write(f"    {field}_cp: coverpoint trans.{field};\n")
      f.write(f"  endgroup : {cg['name']}\n\n")

    f.write(f"  {seq_item} trans;\n\n")
    f.write(f"  function new(string name = \"{cov_name}\", uvm_component parent);\n")
    f.write(f"    super.new(name, parent);\n")
    for cg in coverage.get("covergroups", []):
      f.write(f"    {cg['name']} = new();\n")
    f.write(f"  endfunction\n\n")

    f.write(f"  virtual function void build_phase(uvm_phase phase);\n")
    f.write(f"    super.build_phase(phase);\n")
    f.write(f"  endfunction\n\n")

    f.write(f"  virtual function void write({seq_item} t);\n")
    f.write(f"    trans = t;\n")
    for cg in coverage.get("covergroups", []):
      f.write(f"    {cg['name']}.sample();\n")
    f.write(f"  endfunction\n\n")

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
    f.write(f"class {scoreboard_name} extends uvm_scoreboard;\n\n")
    f.write(f"  `uvm_component_utils({scoreboard_name})\n\n")
    f.write(f"  function new(string name = \"{scoreboard_name}\", uvm_component parent);\n")
    f.write(f"    super.new(name, parent);\n")
    f.write(f"  endfunction\n\n")
    for port in scoreboard['ports']:
      f.write(f"  {port['type']} #({port['base_class']}) {port['name']};\n")
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
  components = environment["components"]
  scoreboard_name = components.get("scoreboard")
  coverage_name = components.get("coverage")
  agents = components["agents"]

  # Lookup full agent config by name
  agent_cfg_map = {a["name"]: a for a in cfg.get("agents", [])}

  out_dir = Path(f"generated/env/")
  out_dir.mkdir(parents=True, exist_ok=True)
  with open(out_dir / f"{env_name}.sv", "w") as f:
    f.write(f"// {env_name} Environment\n\n")
    f.write(f"class {env_name} extends uvm_env;\n\n")
    f.write(f"  `uvm_component_utils({env_name})\n\n")
    f.write(f"  function new(string name = \"{env_name}\", uvm_component parent);\n")
    f.write(f"    super.new(name, parent);\n")
    f.write(f"  endfunction\n\n")

    # Declare component handles
    for agent in agents:
      for i in range(agent['num_obj']):
        f.write(f"  {agent['name']} {agent['name']}_handle_{i};\n")
    if scoreboard_name:
      f.write(f"  {scoreboard_name} {scoreboard_name}_handle;\n")
    if coverage_name:
      f.write(f"  {coverage_name} {coverage_name}_handle;\n")
    f.write(f"\n")

    # build_phase
    f.write(f"  virtual function void build_phase(uvm_phase phase);\n")
    f.write(f"    super.build_phase(phase);\n")
    for agent in agents:
      for i in range(agent['num_obj']):
        f.write(f"    {agent['name']}_handle_{i} = {agent['name']}::type_id::create(\"{agent['name']}_handle_{i}\", this);\n")
    if scoreboard_name:
      f.write(f"    {scoreboard_name}_handle = {scoreboard_name}::type_id::create(\"{scoreboard_name}_handle\", this);\n")
    if coverage_name:
      f.write(f"    {coverage_name}_handle = {coverage_name}::type_id::create(\"{coverage_name}_handle\", this);\n")
    f.write(f"  endfunction\n\n")

    # connect_phase
    f.write(f"  virtual function void connect_phase(uvm_phase phase);\n")
    f.write(f"    super.connect_phase(phase);\n")

    # Explicit connections from yaml: source is agent-relative, destination is env-level
    for connection in environment.get("connections", []):
      src = connection["source"]   # e.g. dff_monitor_handle.monitor_analysis_port
      dst = connection["destination"]  # e.g. dff_scoreboard_handle.uvm_imp
      for agent in agents:
        for i in range(agent['num_obj']):
          f.write(f"    {agent['name']}_handle_{i}.{src}.connect({dst});\n")

    # Auto-connect coverage (uvm_subscriber.analysis_export) to monitor analysis ports
    if coverage_name:
      for agent in agents:
        agent_cfg = agent_cfg_map.get(agent['name'])
        if agent_cfg:
          monitor_name = agent_cfg["components"]["monitor"]["name"]
          monitor_ports = agent_cfg["components"]["monitor"].get("ports", [])
          for port in monitor_ports:
            for i in range(agent['num_obj']):
              f.write(f"    {agent['name']}_handle_{i}.{monitor_name}_handle.{port['name']}.connect({coverage_name}_handle.analysis_export);\n")

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
