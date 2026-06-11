###########################################################
# test_gen.py - generate uvm_test classes
###########################################################
from core import Model, SVWriter, write_file, handle_name


def env_interfaces(model: Model, env):
  """All interfaces used by agents of an env: [(intf_name, agent_entry), ...]"""
  result = []
  for a in env["components"].get("agents", []):
    agent_def = model.agents[a["name"]]
    result.append((model.agent_interface(agent_def), a))
  return result


def gen_test(model: Model, test):
  name = test["name"]
  base = test.get("base_class", "uvm_test")
  is_root = base == "uvm_test"
  env_name = test["environment"]
  env = model.envs[env_name]
  env_h = handle_name(env_name)
  seq = test.get("default_sequence")

  s = SVWriter()
  s.w(f"// {name} Test")
  s.w()
  s.begin(f"class {name} extends {base};")
  s.w()
  s.w(f"`uvm_component_utils({name})")
  s.w()
  if is_root:
    s.w(f"{env_name} {env_h};")
    intf_names = sorted({i for i, _ in env_interfaces(model, env)})
    for intf in intf_names:
      s.w(f"virtual {intf} {handle_name(intf)};")
    s.w()
  s.begin(f"function new(string name = \"{name}\", uvm_component parent);")
  s.w("super.new(name, parent);")
  s.end("endfunction")
  s.w()
  if is_root:
    s.begin("virtual function void build_phase(uvm_phase phase);")
    s.w("super.build_phase(phase);")
    s.w(f"{env_h} = {env_name}::type_id::create(\"{env_h}\", this);")
    intf_names = sorted({i for i, _ in env_interfaces(model, env)})
    for intf in intf_names:
      vif = handle_name(intf)
      s.w(f"if (!uvm_config_db#(virtual {intf})::get(this, \"\", \"{vif}\", {vif}))")
      s.w(f"  `uvm_fatal(\"{name.upper()}\", \"{intf} handle not found in config_db\")")
    # pass the right virtual interface down to each agent instance
    for intf, a in env_interfaces(model, env):
      vif = handle_name(intf)
      for i in range(a.get("num_obj", 1)):
        s.w(f"uvm_config_db#(virtual {intf})::set(this, "
            f"\"{env_h}.{handle_name(a['name'], i)}.*\", \"{vif}\", {vif});")
    s.end("endfunction")
    s.w()
    s.begin("virtual function void end_of_elaboration_phase(uvm_phase phase);")
    s.w("super.end_of_elaboration_phase(phase);")
    s.w("uvm_top.print_topology();")
    s.end("endfunction")
    s.w()
  if seq:
    # start the default sequence on the first active agent's sequencer
    agents = env["components"].get("agents", [])
    seqr_path = None
    for a in agents:
      agent_def = model.agents[a["name"]]
      if agent_def.get("type") == "active":
        seqr = agent_def["components"]["sequencer"]["name"]
        seqr_path = f"{env_h}.{handle_name(a['name'], 0)}.{handle_name(seqr)}"
        break
    s.begin("virtual task run_phase(uvm_phase phase);")
    s.w(f"{seq} seq;")
    s.w("phase.raise_objection(this);")
    s.w(f"seq = {seq}::type_id::create(\"seq\");")
    if seqr_path:
      s.w(f"seq.start({seqr_path});")
    else:
      s.w("// No active agent found in env - start the sequence manually")
      s.user_code(f"{name}_run")
    s.w("phase.drop_objection(this);")
    s.end("endtask")
    s.w()
  s.end("endclass")

  path = model.dir("tests") / f"{name}.sv"
  write_file(path, s.text(), model.overwrite)
  model.register("tests", path)


def generate(model: Model):
  for test in model.tests.values():
    gen_test(model, test)
