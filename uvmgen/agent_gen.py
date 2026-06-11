###########################################################
# agent_gen.py - generate agent + driver/monitor/sequencer
###########################################################
from core import Model, SVWriter, write_file, handle_name


###########################################################
# Sequencer
###########################################################
def gen_sequencer(model: Model, agent, out_dir):
  seqr = agent["components"]["sequencer"]
  name = seqr["name"]
  item = seqr["sequence_item"]
  s = SVWriter()
  s.w(f"// {name} Sequencer")
  s.w()
  s.begin(f"class {name} extends uvm_sequencer #({item});")
  s.w()
  s.w(f"`uvm_component_utils({name})")
  s.w()
  s.begin(f"function new(string name = \"{name}\", uvm_component parent);")
  s.w("super.new(name, parent);")
  s.end("endfunction")
  s.w()
  s.end("endclass")
  path = out_dir / f"{name}.sv"
  write_file(path, s.text(), model.overwrite)
  model.register("agent_sub", path)


###########################################################
# Driver
###########################################################
def gen_driver(model: Model, agent, out_dir):
  drv = agent["components"]["driver"]
  name = drv["name"]
  item = drv["sequence_item"]
  intf = model.agent_interface(agent)
  vif = handle_name(intf)
  s = SVWriter()
  s.w(f"// {name} Driver")
  s.w()
  s.begin(f"class {name} extends uvm_driver #({item});")
  s.w()
  s.w(f"`uvm_component_utils({name})")
  s.w()
  s.w(f"virtual {intf} {vif};")
  s.w()
  s.begin(f"function new(string name = \"{name}\", uvm_component parent);")
  s.w("super.new(name, parent);")
  s.end("endfunction")
  s.w()
  s.begin("virtual function void build_phase(uvm_phase phase);")
  s.w("super.build_phase(phase);")
  s.w(f"if (!uvm_config_db#(virtual {intf})::get(this, \"\", \"{vif}\", {vif}))")
  s.w(f"  `uvm_fatal(\"{name.upper()}\", \"{intf} handle not found in config_db\")")
  s.end("endfunction")
  s.w()
  s.begin("virtual task run_phase(uvm_phase phase);")
  s.w("super.run_phase(phase);")
  s.begin("forever begin")
  s.w("seq_item_port.get_next_item(req);")
  s.w("drive_item(req);")
  s.w("seq_item_port.item_done();")
  s.end("end")
  s.end("endtask")
  s.w()
  s.begin(f"virtual task drive_item({item} item);")
  s.w(f"// Drive {intf} signals from item fields")
  s.user_code(f"{name}_drive_item")
  s.end("endtask")
  s.w()
  s.end("endclass")
  path = out_dir / f"{name}.sv"
  write_file(path, s.text(), model.overwrite)
  model.register("agent_sub", path)


###########################################################
# Monitor
###########################################################
def gen_monitor(model: Model, agent, out_dir):
  mon = agent["components"]["monitor"]
  name = mon["name"]
  item = mon["sequence_item"]
  intf = model.agent_interface(agent)
  vif = handle_name(intf)
  ports = mon.get("ports", [])
  s = SVWriter()
  s.w(f"// {name} Monitor")
  s.w()
  s.begin(f"class {name} extends uvm_monitor;")
  s.w()
  s.w(f"`uvm_component_utils({name})")
  s.w()
  s.w(f"virtual {intf} {vif};")
  for port in ports:
    s.w(f"{port['type']} #({port['base_class']}) {port['name']};")
  s.w()
  s.begin(f"function new(string name = \"{name}\", uvm_component parent);")
  s.w("super.new(name, parent);")
  s.end("endfunction")
  s.w()
  s.begin("virtual function void build_phase(uvm_phase phase);")
  s.w("super.build_phase(phase);")
  s.w(f"if (!uvm_config_db#(virtual {intf})::get(this, \"\", \"{vif}\", {vif}))")
  s.w(f"  `uvm_fatal(\"{name.upper()}\", \"{intf} handle not found in config_db\")")
  for port in ports:
    s.w(f"{port['name']} = new(\"{port['name']}\", this);")
  s.end("endfunction")
  s.w()
  s.begin("virtual task run_phase(uvm_phase phase);")
  s.w("super.run_phase(phase);")
  s.begin("forever begin")
  s.w(f"{item} trans;")
  s.w(f"trans = {item}::type_id::create(\"trans\");")
  s.w(f"// Sample {intf} signals into trans, then publish:")
  s.user_code(f"{name}_sample")
  if ports:
    s.w(f"{ports[0]['name']}.write(trans);")
  s.end("end")
  s.end("endtask")
  s.w()
  s.end("endclass")
  path = out_dir / f"{name}.sv"
  write_file(path, s.text(), model.overwrite)
  model.register("agent_sub", path)


###########################################################
# Agent
###########################################################
def gen_agent_class(model: Model, agent, out_dir):
  name = agent["name"]
  comps = agent["components"]
  is_active = agent.get("type") == "active"
  cfg_obj = agent.get("config_object")
  mon = comps["monitor"]["name"]
  s = SVWriter()
  s.w(f"// {name} Agent")
  s.w()
  s.begin(f"class {name} extends uvm_agent;")
  s.w()
  s.w(f"`uvm_component_utils({name})")
  s.w()
  s.w("// Component handles")
  if is_active:
    seqr = comps["sequencer"]["name"]
    drv = comps["driver"]["name"]
    s.w(f"{seqr} {handle_name(seqr)};")
    s.w(f"{drv} {handle_name(drv)};")
  s.w(f"{mon} {handle_name(mon)};")
  if cfg_obj:
    s.w(f"{cfg_obj} {handle_name(cfg_obj)};")
  s.w()
  s.begin(f"function new(string name = \"{name}\", uvm_component parent);")
  s.w("super.new(name, parent);")
  s.end("endfunction")
  s.w()
  s.begin("virtual function void build_phase(uvm_phase phase);")
  s.w("super.build_phase(phase);")
  if cfg_obj:
    cfg_h = handle_name(cfg_obj)
    s.w(f"if (!uvm_config_db#({cfg_obj})::get(this, \"\", \"cfg\", {cfg_h}))")
    s.w(f"  {cfg_h} = {cfg_obj}::type_id::create(\"{cfg_h}\");")
  if is_active:
    seqr = comps["sequencer"]["name"]
    drv = comps["driver"]["name"]
    if cfg_obj and model.cfg_obj_has_field(cfg_obj, "is_active"):
      s.begin(f"if ({handle_name(cfg_obj)}.is_active == UVM_ACTIVE) begin")
    else:
      s.begin("begin")
    s.w(f"{handle_name(seqr)} = {seqr}::type_id::create(\"{handle_name(seqr)}\", this);")
    s.w(f"{handle_name(drv)} = {drv}::type_id::create(\"{handle_name(drv)}\", this);")
    s.end("end")
  s.w(f"{handle_name(mon)} = {mon}::type_id::create(\"{handle_name(mon)}\", this);")
  s.end("endfunction")
  s.w()
  s.begin("virtual function void connect_phase(uvm_phase phase);")
  s.w("super.connect_phase(phase);")
  if is_active:
    if cfg_obj and model.cfg_obj_has_field(cfg_obj, "is_active"):
      s.begin(f"if ({handle_name(cfg_obj)}.is_active == UVM_ACTIVE) begin")
    else:
      s.begin("begin")
    for conn in agent.get("connection", []):
      src = conn["source"]
      dst = conn["destination"]
      s.w(f"{handle_name(dst)}.seq_item_port.connect({handle_name(src)}.seq_item_export);")
    s.end("end")
  s.end("endfunction")
  s.w()
  s.end("endclass")
  path = out_dir / f"{name}.sv"
  write_file(path, s.text(), model.overwrite)
  model.register("agent", path)


def generate(model: Model):
  for agent in model.agents.values():
    out_dir = model.dir("agents") / agent["name"]
    gen_monitor(model, agent, out_dir)
    if agent.get("type") == "active":
      gen_sequencer(model, agent, out_dir)
      gen_driver(model, agent, out_dir)
    gen_agent_class(model, agent, out_dir)
