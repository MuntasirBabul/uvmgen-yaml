###########################################################
# main.py - single entry point for UVM testbench generation
#
#   python3 uvmgen/main.py [path/to/design.yaml]
###########################################################
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core import Model, validate
import config_gen
import seq_item_gen
import sequence_gen
import interface_gen
import agent_gen
import ral_gen
import env_gen
import test_gen
import top_gen
import pkg_gen


def main():
  cfg_path = sys.argv[1] if len(sys.argv) > 1 else "config/design.yaml"
  print(f"Loading {cfg_path} ...")
  model = Model(cfg_path)

  print("Validating design ...")
  validate(model)

  print(f"Generating testbench into {model.root}/ ...")
  config_gen.generate(model)
  seq_item_gen.generate(model)
  sequence_gen.generate(model)
  interface_gen.generate(model)
  agent_gen.generate(model)
  ral_gen.generate(model)
  env_gen.generate(model)
  test_gen.generate(model)
  top_gen.generate(model)
  pkg_gen.generate(model)   # last: needs the full file list

  print("Done.")


if __name__ == "__main__":
  main()
