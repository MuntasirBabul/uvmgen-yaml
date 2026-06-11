###########################################################
# pkg_gen.py - generate package, filelist and Makefile
#              (must run AFTER all other generators so the
#               model knows every generated file)
###########################################################
import os
from core import Model, SVWriter, write_file

# compile order inside the package
STAGE_ORDER = [
  "config", "sequence_items", "sequences", "ral",
  "agent_sub", "agent", "scoreboard", "coverage", "env", "tests",
]


def rel(path, start):
  return os.path.relpath(path, start).replace("\\", "/")


def gen_pkg(model: Model):
  pkg = model.project["package_name"]
  pkg_dir = model.dir("pkg")

  s = SVWriter()
  s.w(f"// {pkg} - testbench package (compile-order include list)")
  s.w()
  s.begin(f"package {pkg};")
  s.w()
  s.w("import uvm_pkg::*;")
  s.w("`include \"uvm_macros.svh\"")
  s.w()
  for stage in STAGE_ORDER:
    files = model.files.get(stage, [])
    if not files:
      continue
    s.w(f"// --- {stage} ---")
    for f in files:
      s.w(f"`include \"{rel(f, pkg_dir)}\"")
    s.w()
  s.end(f"endpackage : {pkg}")

  path = pkg_dir / f"{pkg}.sv"
  write_file(path, s.text(), model.overwrite)
  return path


def gen_filelist(model: Model, pkg_path):
  root = model.root
  lines = ["// Auto-generated filelist", "+incdir+" + rel(model.dir("pkg"), root), ""]
  lines.append("// Interfaces (compiled outside the package)")
  for f in model.interface_files:
    lines.append(rel(f, root))
  lines.append("")
  lines.append("// Testbench package")
  lines.append(rel(pkg_path, root))
  lines.append("")
  lines.append("// DUT files - add your RTL here")
  lines.append(f"// <path to {model.project['dut_name']} rtl>")
  lines.append("")
  if model.top_file:
    lines.append("// Top module")
    lines.append(rel(model.top_file, root))
  write_file(root / "filelist.f", "\n".join(lines) + "\n", model.overwrite)


def gen_makefile(model: Model):
  top = model.project["name"]
  first_test = next(iter(model.tests), "")
  content = f"""# Auto-generated Makefile (Questa/ModelSim flow)
TEST    ?= {first_test}
TOP     ?= {top}
VERBOSITY ?= UVM_MEDIUM

all: compile run

compile:
\tvlib work
\tvlog -sv +acc -f filelist.f

run:
\tvsim -c $(TOP) +UVM_TESTNAME=$(TEST) +UVM_VERBOSITY=$(VERBOSITY) -do "run -all; quit -f"

clean:
\trm -rf work transcript vsim.wlf

.PHONY: all compile run clean
"""
  write_file(model.root / "Makefile", content, model.overwrite)


def generate(model: Model):
  pkg_path = None
  if model.enabled("create_pkg"):
    pkg_path = gen_pkg(model)
  if model.enabled("create_filelist") and pkg_path:
    gen_filelist(model, pkg_path)
  if model.enabled("create_makefile"):
    gen_makefile(model)
