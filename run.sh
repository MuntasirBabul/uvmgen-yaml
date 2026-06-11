#!/bin/bash
# Regenerate the UVM testbench from config/design.yaml
rm -rf generated_tb

python3 uvmgen/main.py "$@"
