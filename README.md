# uvmgen-yaml

Generate complete UVM testbench environments from a YAML configuration file.

## Usage

```bash
./run.sh                          # regenerate from config/design.yaml
python3 uvmgen/main.py [yaml]     # or run the driver directly
```

The whole testbench architecture (agents, environment, connections, coverage,
RAL, tests...) is described in `config/design.yaml`. The generators emit a
compilable skeleton into `generated_tb/`; design-specific behavior is left in
clearly marked sections:

```systemverilog
// USER CODE BEGIN dff_driver_drive_item
// USER CODE END dff_driver_drive_item
```

Set `generation.overwrite_existing_files: false` in design.yaml to protect
files you have hand-edited from being regenerated.

## What gets generated

| Folder | Content |
|---|---|
| `config/` | uvm_object configuration classes (`config_objects:`) |
| `sequences/` | sequence items (with rand fields + constraints) and sequences |
| `interfaces/` | SV interfaces with clock/reset and driver/monitor clocking blocks |
| `agents/<name>/` | driver, monitor, sequencer, agent (active/passive via config object) |
| `scoreboard/` | uvm_scoreboard with analysis imp(s) |
| `coverage/` | typed `uvm_subscriber` with real covergroups, coverpoints, bins, crosses |
| `ral/` | uvm_reg / uvm_reg_block register model + uvm_reg_adapter skeleton |
| `env/` | uvm_env: instantiates everything, resolves connections, hooks up RAL |
| `tests/` | uvm_test classes: env creation, vif distribution, default sequence start |
| `pkg/` | package with compile-ordered includes |
| top level | top module (clock/reset gen, DUT placeholder, run_test), `filelist.f`, `Makefile` |

## Connections

Environment-level connections use hierarchical paths relative to the env, and
are validated before generation:

```yaml
connections:
  - source: dff_agent[0].dff_monitor.monitor_analysis_port   # agent[idx].subcomp.port
    destination: dff_scoreboard.uvm_imp                      # scoreboard.port
  - source: dff_agent.dff_monitor.monitor_analysis_port      # no index = all instances
    destination: dff_coverage.analysis_export                # coverage subscriber
```

The resolver knows the full hierarchy (env -> agent instance -> monitor ->
port) and emits the correct handle chain:

```systemverilog
dff_agent_handle_0.dff_monitor_handle.monitor_analysis_port.connect(dff_scoreboard_handle.uvm_imp);
```

A wrong component or port name fails generation with a list of every error
found, instead of producing broken SystemVerilog.

## Architecture

```
uvmgen/
  main.py          # single entry point: load -> validate -> generate
  core.py          # Model (parsed design), validation, connection resolver,
                   # SVWriter, handle-naming convention
  *_gen.py         # one generator per component kind, all driven by the Model
```

## Simulation

```bash
cd generated_tb
# add your RTL to filelist.f, fill in the DUT instantiation in <top>.sv
make TEST=dff_base_test     # Questa/ModelSim flow
```
