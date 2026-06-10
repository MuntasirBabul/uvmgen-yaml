rm -rf generated

python3 uvmgen/seq_item_gen.py
python3 uvmgen/sequence_gen.py
python3 uvmgen/interface_gen.py
python3 uvmgen/agent_gen.py
python3 uvmgen/env_gen.py
python3 uvmgen/test_gen.py
python3 uvmgen/top_gen.py
python3 uvmgen/ral_gen.py
