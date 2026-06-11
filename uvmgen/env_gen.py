###########################################################
# env_gen.py - generate scoreboard, coverage and environment
###########################################################
from core import Model, SVWriter, write_file, handle_name, resolve_connections


###########################################################
# Coverage (typed uvm_subscriber with real covergroups)
###########################################################
def gen_coverage(model: Model, cov):
  name = cov["name"]
  item = cov["sequence_item"]
  s = SVWriter()
  s.w(f"// {name} Coverage")
  s.w()
  s.begin(f"class {name} extends uvm_subscriber #({item});")
  s.w()
  s.w(f"`uvm_component_utils({name})")
  s.w()
  s.w(f"{item} trans;")
  s.w()
  for cg in cov.get("covergroups", []):
    s.begin(f"covergroup {cg['name']};")
    s.w("option.per_instance = 1;")
    for cp in cg.get("coverpoints", []):
      field = cp["field"]
      bins = cp.get("bins")
      if bins:
        s.begin(f"cp_{field} : coverpoint trans.{field} {{")
        for b in bins:
          if isinstance(b, dict):
            s.w(f"bins {b['name']} = {{{b['values']}}};")
          else:
            s.w(f"bins {b} = {{{b}}}; // TODO: give 'values' for bin '{b}' in design.yaml")
        s.end("}")
      else:
        s.w(f"cp_{field} : coverpoint trans.{field};")
    for cr in cg.get("crosses", []):
      items = ", ".join(f"cp_{i}" for i in cr["items"])
      s.w(f"{cr['name']} : cross {items};")
    s.end("endgroup")
    s.w()
  s.begin(f"function new(string name = \"{name}\", uvm_component parent);")
  s.w("super.new(name, parent);")
  for cg in cov.get("covergroups", []):
    s.w(f"{cg['name']} = new();")
  s.end("endfunction")
  s.w()
  s.begin(f"virtual function void write({item} t);")
  s.w("trans = t;")
  for cg in cov.get("covergroups", []):
    s.w(f"{cg['name']}.sample();")
  s.user_code(f"{name}_write")
  s.end("endfunction")
  s.w()
  s.begin("virtual function void report_phase(uvm_phase phase);")
  s.w("super.report_phase(phase);")
  for cg in cov.get("covergroups", []):
    s.w(f"`uvm_info(\"{name.upper()}\", $sformatf(\"{cg['name']} coverage: %0.2f%%\", "
        f"{cg['name']}.get_inst_coverage()), UVM_LOW)")
  s.end("endfunction")
  s.w()
  s.end("endclass")

  path = model.dir("coverage") / f"{name}.sv"
  write_file(path, s.text(), model.overwrite)
  model.register("coverage", path)


###########################################################
# Scoreboard
###########################################################
def gen_scoreboard(model: Model, sb):
  name = sb["name"]
  item = sb["sequence_item"]
  ports = sb.get("ports", [])
  s = SVWriter()
  s.w(f"// {name} Scoreboard")
  s.w()
  s.begin(f"class {name} extends uvm_scoreboard;")
  s.w()
  s.w(f"`uvm_component_utils({name})")
  s.w()
  for port in ports:
    s.w(f"{port['type']} #({port['base_class']}) {port['name']};")
  s.w()
  s.begin(f"function new(string name = \"{name}\", uvm_component parent);")
  s.w("super.new(name, parent);")
  s.end("endfunction")
  s.w()
  s.begin("virtual function void build_phase(uvm_phase phase);")
  s.w("super.build_phase(phase);")
  for port in ports:
    s.w(f"{port['name']} = new(\"{port['name']}\", this);")
  s.end("endfunction")
  s.w()
  s.begin(f"virtual function void write({item} t);")
  s.w("// Checking logic: compare observed transaction against expected behavior")
  s.user_code(f"{name}_write")
  s.end("endfunction")
  s.w()
  s.begin("virtual function void report_phase(uvm_phase phase);")
  s.w("super.report_phase(phase);")
  s.user_code(f"{name}_report")
  s.end("endfunction")
  s.w()
  s.end("endclass")

  path = model.dir("scoreboard") / f"{name}.sv"
  write_file(path, s.text(), model.overwrite)
  model.register("scoreboard", path)


###########################################################
# Environment
###########################################################
def gen_env(model: Model, env):
  name = env["name"]
  comps = env["components"]
  agents = comps.get("agents", [])
  sb = comps.get("scoreboard")
  cov = comps.get("coverage")
  env_cfg = env.get("config_object")
  ral = model.register_model.get("enable") and model.enabled("create_ral_model")
  block = model.register_model.get("block_name") if ral else None

  errors = []
  conn_pairs = resolve_connections(model, env, errors)

  has_sb_guard = env_cfg and sb and model.cfg_obj_has_field(env_cfg, "has_scoreboard")
  has_cov_guard = env_cfg and cov and model.cfg_obj_has_field(env_cfg, "has_coverage")

  s = SVWriter()
  s.w(f"// {name} Environment")
  s.w()
  s.begin(f"class {name} extends uvm_env;")
  s.w()
  s.w(f"`uvm_component_utils({name})")
  s.w()
  s.w("// Component handles")
  for a in agents:
    for i in range(a.get("num_obj", 1)):
      s.w(f"{a['name']} {handle_name(a['name'], i)};")
  if sb:
    s.w(f"{sb} {handle_name(sb)};")
  if cov:
    s.w(f"{cov} {handle_name(cov)};")
  if env_cfg:
    s.w(f"{env_cfg} {handle_name(env_cfg)};")
  for a in agents:
    a_cfg = a.get("config_object")
    if a_cfg:
      for i in range(a.get("num_obj", 1)):
        s.w(f"{a_cfg} {handle_name(a_cfg, i)};")
  if ral:
    s.w(f"{block} {handle_name(block)};")
    s.w(f"{block}_adapter {handle_name(block + '_adapter')};")
  s.w()
  s.begin(f"function new(string name = \"{name}\", uvm_component parent);")
  s.w("super.new(name, parent);")
  s.end("endfunction")
  s.w()
  # ---- build_phase ---------------------------------------
  s.begin("virtual function void build_phase(uvm_phase phase);")
  s.w("super.build_phase(phase);")
  if env_cfg:
    cfg_h = handle_name(env_cfg)
    s.w(f"if (!uvm_config_db#({env_cfg})::get(this, \"\", \"cfg\", {cfg_h}))")
    s.w(f"  {cfg_h} = {env_cfg}::type_id::create(\"{cfg_h}\");")
  for a in agents:
    a_cfg = a.get("config_object")
    for i in range(a.get("num_obj", 1)):
      if a_cfg:
        cfg_h = handle_name(a_cfg, i)
        s.w(f"{cfg_h} = {a_cfg}::type_id::create(\"{cfg_h}\");")
        s.w(f"uvm_config_db#({a_cfg})::set(this, \"{handle_name(a['name'], i)}\", \"cfg\", {cfg_h});")
      s.w(f"{handle_name(a['name'], i)} = {a['name']}::type_id::create(\"{handle_name(a['name'], i)}\", this);")
  if sb:
    if has_sb_guard:
      s.w(f"if ({handle_name(env_cfg)}.has_scoreboard)")
      s.w(f"  {handle_name(sb)} = {sb}::type_id::create(\"{handle_name(sb)}\", this);")
    else:
      s.w(f"{handle_name(sb)} = {sb}::type_id::create(\"{handle_name(sb)}\", this);")
  if cov:
    if has_cov_guard:
      s.w(f"if ({handle_name(env_cfg)}.has_coverage)")
      s.w(f"  {handle_name(cov)} = {cov}::type_id::create(\"{handle_name(cov)}\", this);")
    else:
      s.w(f"{handle_name(cov)} = {cov}::type_id::create(\"{handle_name(cov)}\", this);")
  if ral:
    blk_h = handle_name(block)
    s.begin(f"if ({blk_h} == null) begin")
    s.w(f"{blk_h} = {block}::type_id::create(\"{blk_h}\");")
    s.w(f"{blk_h}.build();")
    s.w(f"{blk_h}.lock_model();")
    s.end("end")
    s.w(f"{handle_name(block + '_adapter')} = {block}_adapter::type_id::create(\"{handle_name(block + '_adapter')}\");")
  s.end("endfunction")
  s.w()
  # ---- connect_phase -------------------------------------
  s.begin("virtual function void connect_phase(uvm_phase phase);")
  s.w("super.connect_phase(phase);")
  for src, dst in conn_pairs:
    dst_top = dst.split(".")[0]
    guard = None
    if sb and dst_top == handle_name(sb) and has_sb_guard:
      guard = f"{handle_name(env_cfg)}.has_scoreboard"
    if cov and dst_top == handle_name(cov) and has_cov_guard:
      guard = f"{handle_name(env_cfg)}.has_coverage"
    if guard:
      s.w(f"if ({guard})")
      s.w(f"  {src}.connect({dst});")
    else:
      s.w(f"{src}.connect({dst});")
  if ral and agents:
    first = agents[0]
    agent_def = model.agents[first["name"]]
    if agent_def.get("type") == "active":
      seqr = agent_def["components"]["sequencer"]["name"]
      s.w("// Hook the register model to the bus sequencer through the adapter")
      s.w(f"{handle_name(block)}.default_map.set_sequencer("
          f"{handle_name(first['name'], 0)}.{handle_name(seqr)}, {handle_name(block + '_adapter')});")
      s.w(f"{handle_name(block)}.default_map.set_auto_predict(1);")
  s.end("endfunction")
  s.w()
  s.end("endclass")

  path = model.dir("env") / f"{name}.sv"
  write_file(path, s.text(), model.overwrite)
  model.register("env", path)


def generate(model: Model):
  if model.enabled("create_coverage"):
    for cov in model.coverages.values():
      gen_coverage(model, cov)
  if model.enabled("create_scoreboard"):
    for sb in model.scoreboards.values():
      gen_scoreboard(model, sb)
  for env in model.envs.values():
    gen_env(model, env)
