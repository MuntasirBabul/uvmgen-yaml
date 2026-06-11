###########################################################
# core.py - shared model, validation, path resolver and
#           SystemVerilog writer for all generators
###########################################################
import sys
import yaml
from pathlib import Path


###########################################################
# SystemVerilog writer (indentation helper)
###########################################################
class SVWriter:
  def __init__(self, indent_str="  "):
    self.lines = []
    self.level = 0
    self.indent_str = indent_str

  def w(self, line=""):
    if line == "":
      self.lines.append("")
    else:
      self.lines.append(self.indent_str * self.level + line)

  def begin(self, line):
    self.w(line)
    self.level += 1

  def end(self, line):
    self.level -= 1
    self.w(line)

  def user_code(self, tag):
    self.w(f"// USER CODE BEGIN {tag}")
    self.w(f"// USER CODE END {tag}")

  def text(self):
    return "\n".join(self.lines) + "\n"


###########################################################
# Naming convention - single source of truth for handles
###########################################################
def handle_name(name, index=None):
  if index is None:
    return f"{name}_handle"
  return f"{name}_handle_{index}"


###########################################################
# File writer honoring overwrite_existing_files
###########################################################
def write_file(path: Path, content: str, overwrite: bool):
  path.parent.mkdir(parents=True, exist_ok=True)
  if path.exists() and not overwrite:
    print(f"  [skip] {path} (exists, overwrite_existing_files=false)")
    return
  path.write_text(content)
  print(f"  [gen ] {path}")


###########################################################
# Model - loads design.yaml once and indexes every section
###########################################################
class Model:
  def __init__(self, cfg_path="config/design.yaml"):
    with open(cfg_path) as f:
      self.cfg = yaml.safe_load(f)
    cfg = self.cfg
    self.project        = cfg["project"]
    self.agents         = {a["name"]: a for a in cfg.get("agents", [])}
    self.interfaces     = {i["name"]: i for i in cfg.get("interface", [])}
    self.seq_items      = {s["name"]: s for s in cfg.get("sequence_items", [])}
    self.sequences      = {s["name"]: s for s in cfg.get("sequences", [])}
    self.scoreboards    = {s["name"]: s for s in cfg.get("scoreboard", [])}
    self.coverages      = {c["name"]: c for c in cfg.get("coverage", [])}
    self.config_objects = {c["name"]: c for c in cfg.get("config_objects", [])}
    self.envs           = {e["name"]: e for e in cfg.get("environment", [])}
    self.tests          = {t["name"]: t for t in cfg.get("tests", [])}
    self.register_model = cfg.get("register_model", {"enable": False})

    self.generation = cfg.get("generation", {})
    self.overwrite  = self.generation.get("overwrite_existing_files", True)

    out = cfg.get("output", {})
    self.root = Path(out.get("root_dir", "generated_tb"))

    # every generator registers files here so pkg/filelist can be built
    # keys are compile-order stages
    self.files = {
      "config": [], "sequence_items": [], "sequences": [], "ral": [],
      "agent_sub": [], "agent": [], "scoreboard": [], "coverage": [],
      "env": [], "tests": [],
    }
    self.interface_files = []   # compiled outside the package
    self.top_file = None

  # ------------------------------------------------------
  def dir(self, folder):
    return self.root / folder

  def enabled(self, flag, default=True):
    return self.generation.get(flag, default)

  def register(self, stage, path):
    self.files[stage].append(path)

  # ------------------------------------------------------
  # helpers to navigate the hierarchy
  # ------------------------------------------------------
  def agent_subcomponent(self, agent_def, sub_name):
    """Return (role, definition) of an agent subcomponent by its name."""
    for role, comp in agent_def.get("components", {}).items():
      if isinstance(comp, dict) and comp.get("name") == sub_name:
        return role, comp
    return None, None

  def agent_interface(self, agent_def):
    return agent_def["components"]["interface"]["name"]

  def first_env_agent(self, env):
    """Return (agent_name, agent_def) of the first agent in an env."""
    a = env["components"]["agents"][0]
    return a["name"], self.agents[a["name"]]

  def cfg_obj_has_field(self, cfg_obj_name, field_name):
    obj = self.config_objects.get(cfg_obj_name)
    if not obj:
      return False
    return any(f["name"] == field_name for f in obj.get("fields", []))


###########################################################
# Hierarchical connection path resolver
#
# Path grammar (relative to the environment):
#   <agent>[<idx>].<subcomponent>.<port>   e.g. dff_agent[0].dff_monitor.monitor_analysis_port
#   <agent>.<subcomponent>.<port>          (no index -> broadcast to all instances)
#   <scoreboard>.<port>
#   <coverage>.analysis_export
###########################################################
def _parse_token(token):
  if "[" in token:
    name, idx = token.split("[")
    return name, int(idx.rstrip("]"))
  return token, None


def resolve_endpoint(model: Model, env, path, errors):
  tokens = path.split(".")
  name, idx = _parse_token(tokens[0])
  comps = env["components"]
  env_agents = {a["name"]: a for a in comps.get("agents", [])}

  # ---- agent subcomponent endpoint -----------------------
  if name in env_agents:
    if len(tokens) != 3:
      errors.append(f"connection path '{path}': expected <agent>[i].<subcomp>.<port>")
      return []
    num = env_agents[name].get("num_obj", 1)
    if idx is not None and idx >= num:
      errors.append(f"connection path '{path}': index {idx} out of range (num_obj={num})")
      return []
    indices = [idx] if idx is not None else list(range(num))
    agent_def = model.agents.get(name)
    if agent_def is None:
      errors.append(f"connection path '{path}': agent '{name}' not defined in agents section")
      return []
    sub_name = tokens[1]
    port = tokens[2]
    role, sub = model.agent_subcomponent(agent_def, sub_name)
    if sub is None:
      errors.append(f"connection path '{path}': '{sub_name}' is not a subcomponent of agent '{name}'")
      return []
    ports = [p["name"] for p in sub.get("ports", [])]
    if port not in ports:
      errors.append(f"connection path '{path}': '{sub_name}' has no port '{port}' (ports: {ports})")
      return []
    return [f"{handle_name(name, i)}.{handle_name(sub_name)}.{port}" for i in indices]

  # ---- scoreboard endpoint -------------------------------
  if name == comps.get("scoreboard"):
    if len(tokens) != 2:
      errors.append(f"connection path '{path}': expected <scoreboard>.<port>")
      return []
    sb = model.scoreboards.get(name)
    ports = [p["name"] for p in sb.get("ports", [])] if sb else []
    if tokens[1] not in ports:
      errors.append(f"connection path '{path}': scoreboard '{name}' has no port '{tokens[1]}' (ports: {ports})")
      return []
    return [f"{handle_name(name)}.{tokens[1]}"]

  # ---- coverage endpoint (uvm_subscriber) ----------------
  if name == comps.get("coverage"):
    if len(tokens) != 2 or tokens[1] != "analysis_export":
      errors.append(f"connection path '{path}': coverage endpoint must be '{name}.analysis_export'")
      return []
    return [f"{handle_name(name)}.analysis_export"]

  errors.append(f"connection path '{path}': '{name}' is not a component of environment '{env['name']}'")
  return []


def resolve_connections(model: Model, env, errors):
  """Return list of (source_expr, dest_expr) SV pairs for an environment."""
  pairs = []
  for conn in env.get("connections", []):
    sources = resolve_endpoint(model, env, conn["source"], errors)
    dests   = resolve_endpoint(model, env, conn["destination"], errors)
    if not sources or not dests:
      continue
    if len(dests) > 1:
      errors.append(f"connection destination '{conn['destination']}' resolves to multiple instances; "
                    f"give it an explicit index")
      continue
    for s in sources:
      pairs.append((s, dests[0]))
  return pairs


###########################################################
# Whole-config validation - collect ALL errors then bail
###########################################################
def validate(model: Model):
  errors = []
  e = errors.append

  if not isinstance(model.project, dict):
    e("project: must be a mapping (name/dut_name/top_env/package_name), not a list")
    print("FATAL: " + errors[0])
    sys.exit(1)

  for key in ("name", "dut_name", "top_env", "package_name"):
    if key not in model.project:
      e(f"project: missing key '{key}'")

  if model.project.get("top_env") not in model.envs:
    e(f"project.top_env '{model.project.get('top_env')}' not found in environment section")

  # agents -------------------------------------------------
  for name, agent in model.agents.items():
    comps = agent.get("components", {})
    if "monitor" not in comps:
      e(f"agent '{name}': monitor is required")
    if "interface" not in comps:
      e(f"agent '{name}': interface is required")
    elif comps["interface"]["name"] not in model.interfaces:
      e(f"agent '{name}': interface '{comps['interface']['name']}' not defined")
    if agent.get("type") == "active":
      for role in ("driver", "sequencer"):
        if role not in comps:
          e(f"agent '{name}': active agent requires a {role}")
    for role in ("driver", "monitor", "sequencer"):
      comp = comps.get(role)
      if comp and "sequence_item" in comp and comp["sequence_item"] not in model.seq_items:
        e(f"agent '{name}' {role}: sequence_item '{comp['sequence_item']}' not defined")
    cfg_obj = agent.get("config_object")
    if cfg_obj and cfg_obj not in model.config_objects:
      e(f"agent '{name}': config_object '{cfg_obj}' not defined")

  # environments -------------------------------------------
  for name, env in model.envs.items():
    comps = env.get("components", {})
    for a in comps.get("agents", []):
      if a["name"] not in model.agents:
        e(f"environment '{name}': agent '{a['name']}' not defined")
    sb = comps.get("scoreboard")
    if sb and sb not in model.scoreboards:
      e(f"environment '{name}': scoreboard '{sb}' not defined")
    cov = comps.get("coverage")
    if cov and cov not in model.coverages:
      e(f"environment '{name}': coverage '{cov}' not defined")
    cfg_obj = env.get("config_object")
    if cfg_obj and cfg_obj not in model.config_objects:
      e(f"environment '{name}': config_object '{cfg_obj}' not defined")
    resolve_connections(model, env, errors)

  # scoreboards --------------------------------------------
  for name, sb in model.scoreboards.items():
    if sb.get("sequence_item") not in model.seq_items:
      e(f"scoreboard '{name}': sequence_item '{sb.get('sequence_item')}' not defined")

  # coverage -----------------------------------------------
  for name, cov in model.coverages.items():
    item_name = cov.get("sequence_item")
    if item_name not in model.seq_items:
      e(f"coverage '{name}': sequence_item '{item_name}' not defined")
      continue
    fields = [f["name"] for f in model.seq_items[item_name].get("fields", [])]
    for cg in cov.get("covergroups", []):
      for cp in cg.get("coverpoints", []):
        if cp["field"] not in fields:
          e(f"coverage '{name}' covergroup '{cg['name']}': field '{cp['field']}' "
            f"not in sequence_item '{item_name}' (fields: {fields})")
      for cr in cg.get("crosses", []):
        cp_fields = [cp["field"] for cp in cg.get("coverpoints", [])]
        for it in cr.get("items", []):
          if it not in cp_fields:
            e(f"coverage '{name}' cross '{cr['name']}': '{it}' is not a coverpoint of '{cg['name']}'")

  # sequences ----------------------------------------------
  for name, seq in model.sequences.items():
    base = seq.get("base_class", "uvm_sequence")
    if base != "uvm_sequence" and base not in model.sequences:
      e(f"sequence '{name}': base_class '{base}' not defined")
    if base == "uvm_sequence":
      if seq.get("sequence_item") not in model.seq_items:
        e(f"sequence '{name}': root sequence needs a valid sequence_item "
          f"(got '{seq.get('sequence_item')}')")

  # tests --------------------------------------------------
  for name, test in model.tests.items():
    if test.get("environment") not in model.envs:
      e(f"test '{name}': environment '{test.get('environment')}' not defined")
    base = test.get("base_class", "uvm_test")
    if base != "uvm_test" and base not in model.tests:
      e(f"test '{name}': base_class '{base}' not defined")
    seq = test.get("default_sequence")
    if seq and seq not in model.sequences:
      e(f"test '{name}': default_sequence '{seq}' not defined")

  if errors:
    print(f"design.yaml validation failed with {len(errors)} error(s):")
    for err in errors:
      print(f"  - {err}")
    sys.exit(1)
